import connexion
from connexion import NoContent
from datetime import datetime
import time

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from base import Base
from enroll import Enroll
from drop_out import DropOut

import yaml
import logging
import logging.config
import json

from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import os


app_conf_file = ""
log_conf_file = ""

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
        print("In test environment")
        app_conf_file = "/config/app_conf.yml"
        log_conf_file = "/config/log_conf.yml"
else:
        print("In Dev Environment")
        app_conf_file = "app_conf.yml"
        log_conf_file = "log_conf.yml"

with open(app_conf_file, "r") as f:
        app_config = yaml.safe_load(f.read())

with open(log_conf_file, "r") as f:
        log_config = yaml.safe_load(f.read())
        logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

user = app_config['datastore']['user']
password = app_config['datastore']['password']
host = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']

# create_engine creates an engine object to provide a source of database connectivity
# creates a dialect tailored to Postgresql as well as pool object which will establish DBAPI connection
# in this case, mysql is the dialect and pymysql is the name of the DBAPI 
# pool_recycle will replace the connection after 10 minutes
# pool_pre_ping will run a test query and replace connection if not responding
# pool_size will accept up to 10 connections at a time or else will queue the query
# Size of 10 to accomodate 10 thread requests per loop
DB_ENGINE = create_engine(f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}',
						  pool_recycle=600, pool_pre_ping=True, pool_size=10)
Base.metadata.bind = DB_ENGINE
Base.metadata.create_all(DB_ENGINE)
DB_SESSION = sessionmaker(bind=DB_ENGINE)

logger.info(f"Connecting to DB. Hostname:{host}, Port:{port}")

def enroll_student(payload):
	session = DB_SESSION()
	
	try:
		enrolled_student = Enroll(payload['student_id'], 
								payload['program'], 
								payload['highschool_gpa'], 
								datetime.strptime(payload['student_acceptance_date'], "%m-%d-%Y"), 
								datetime.strptime(payload['program_starting_date'], "%m-%d-%Y"),
								payload['trace_id'])

		session.add(enrolled_student)
		session.commit()

		logger.debug(f"Stored event enroll with a trace id of {payload['trace_id']}")
	except Exception as e:
		session.rollback()
		print(e)
	finally:
		session.close()
		return NoContent, 201


def withdraw_student(payload):
	session = DB_SESSION()

	try:
		withdrawn_student = DropOut(payload['student_id'],
									payload['program'],
									payload['program_gpa'],
									datetime.strptime(payload['student_dropout_date'], "%m-%d-%Y"),
									payload['trace_id'])
		
		session.add(withdrawn_student)
		
		session.commit()
		logger.debug(f"Stored event drop-out with a trace id of {payload['trace_id']}")
	except Exception as e:
		session.rollback()
		print(e)
	finally:
		session.close()
		return NoContent, 201
	

def get_enroll_student(start_timestamp, end_timestamp):
	logger.info("received request")
	session = DB_SESSION()

	logger.debug(start_timestamp)
	logger.debug(end_timestamp)

	try:
		start_timestamp_datetime = datetime.strptime(start_timestamp, "%Y-%m-%dT:%H:%M:%S")
		end_timestamp_datetime = datetime.strptime(end_timestamp, "%Y-%m-%dT:%H:%M:%S")
		logger.debug(start_timestamp_datetime)
		logger.debug(end_timestamp_datetime)
		results = session.query(Enroll).filter(
				and_(Enroll.date_created >= start_timestamp_datetime, 
				Enroll.date_created < end_timestamp_datetime))
	except Exception as e:
		logger.debug(e)
	
	results_list = []

	for reading in results:
		results_list.append(reading.to_dict())

	logger.debug("\nRESULTS RECEIVED")
	logger.debug(results_list)
	
	session.close()

	logger.info("Query for enrolled students %s returns %d results" %(start_timestamp_datetime, len(results_list)))
	
	return results_list, 200


def get_drop_out_student(start_timestamp, end_timestamp):
	session = DB_SESSION()

	start_timestamp_datetime = datetime.strptime(start_timestamp, "%Y-%m-%dT:%H:%M:%S")
	end_timestamp_datetime = datetime.strptime(end_timestamp, "%Y-%m-%dT:%H:%M:%S")

	results = session.query(DropOut).filter(
			and_(DropOut.date_created >= start_timestamp_datetime, 
			DropOut.date_created < end_timestamp_datetime))
	
	results_list = []

	for reading in results:
		results_list.append(reading.to_dict())
	
	session.close()

	logger.info("Query for drop out students %s returns %d results" %(start_timestamp, len(results_list)))

	return results_list, 200


def process_messages():
	hostname = "%s:%d" % (app_config['events']['hostname'],
						app_config['events']['port'])
	
	consumer = None
	max_retries = app_config['events']['retries']
	current_retries = 0 
	while current_retries < max_retries:
		logger.info(f"Attempting to connect to Kafka broker: {current_retries} retries")
		try:
			client = KafkaClient(hosts=hostname)
			topic = client.topics[str.encode(app_config['events']['topic'])]
			consumer = topic.get_simple_consumer(consumer_group=b"event_group",
								reset_offset_on_start=False, # keep offset position
								auto_offset_reset=OffsetType.LATEST) # reset to latest if no offset
			logger.info("Sucessfully connected to Kafka broker")
			break
		except:
			logger.error("Kafka connection failed")
			time.sleep(app_config['events']['retry_delay'])
			current_retries += 1
			

	for msg in consumer:
		msg_str = msg.value.decode('utf-8')
		msg = json.loads(msg_str)
		logger.info("Message: %s" % msg)

		try: 
			payload = msg['payload']

			if msg['type'] == "enroll":
				logger.info("Storing enroll event to database")
				enroll_student(payload)
			elif msg['type'] == "drop_out":
				logger.info("Storing drop_out event to database")
				withdraw_student(payload)
			
			consumer.commit_offsets()

		except Exception as e:
			logger.error(f"Error: {e}")
	


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
	t1 = Thread(target=process_messages)
	t1.setDaemon(True)
	t1.start()
	app.run(port=8090, host="0.0.0.0")
	
