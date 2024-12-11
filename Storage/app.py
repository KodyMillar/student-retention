import os
from datetime import datetime
import time

import yaml
import logging
import logging.config
import json

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from base import Base
from enroll import Enroll
from drop_out import DropOut

from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import connexion
from connexion import NoContent


APP_CONF_FILE = ""
LOG_CONF_FILE = ""

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
        print("In test environment")
        APP_CONF_FILE = "/config/app_conf.yml"
        LOG_CONF_FILE = "/config/log_conf.yml"
else:
        print("In Dev Environment")
        APP_CONF_FILE = "app_conf.yml"
        LOG_CONF_FILE = "log_conf.yml"

with open(APP_CONF_FILE, "r", encoding='utf-8') as f:
        APP_CONFIG = yaml.safe_load(f.read())

with open(LOG_CONF_FILE, "r", encoding='utf-8') as f:
        LOG_CONFIG = yaml.safe_load(f.read())
        logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s",  APP_CONF_FILE)
logger.info("Log Conf File: %s", LOG_CONF_FILE)

user = APP_CONFIG['datastore']['user']
password = APP_CONFIG['datastore']['password']
host = APP_CONFIG['datastore']['hostname']
port = APP_CONFIG['datastore']['port']
db = APP_CONFIG['datastore']['db']

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

logger.info("Connecting to DB. Hostname:%s, Port:%s", host, port)

def enroll_student(payload):
    """
    Stores enroll events in the enroll table

    args:
        object payload: the payload from the Kafka message containing the event
    
    returns:
        object: A NoContent connexion object
        int: a 201 status code saying the events were stored successfully
        
    """
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

        logger.debug("Stored event enroll with a trace id of %s", payload['trace_id'])
    except Exception as e:
        session.rollback()
        print(e)
    finally:
        session.close()
        return NoContent, 201


def withdraw_student(payload):
    """
    Stores drop_out events in the drop_out table

    args:
        object payload: the payload from the Kafka message containing the event
    
    returns:
        object: A NoContent connexion object
        int: a 201 status code saying the events were stored successfully
        
    """
    session = DB_SESSION()

    try:
        withdrawn_student = DropOut(payload['student_id'],
                                    payload['program'],
                                    payload['program_gpa'],
                                    datetime.strptime(payload['student_dropout_date'], "%m-%d-%Y"),
                                    payload['trace_id'])

        session.add(withdrawn_student)

        session.commit()
        logger.debug("Stored event drop-out with a trace id of %s", {payload['trace_id']})
    except Exception as e:
        session.rollback()
        print(e)
    finally:
        session.close()
        return NoContent, 201


def get_enroll_student(start_timestamp, end_timestamp):
    """
    Receives a GET request with a start time and end time
    and retrieves enroll events created within that timeframe

    args:
        string start_timestamp: the start of the timeframe
        string end_timestamp: the end of the timeframe
    
    returns:
        list: A list of events created within the timeframe
        int: a 200 status code saying the events were retrieved
        
    """
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

    logger.info("Query for enrolled students %s returns %d results", start_timestamp_datetime, len(results_list))

    return results_list, 200


def get_drop_out_student(start_timestamp, end_timestamp):
    """
    Receives a GET request with a start time and end time
    and retrieves drop_out events created within that timeframe

    args:
        string start_timestamp: the start of the timeframe
        string end_timestamp: the end of the timeframe
    
    returns:
        list: A list of events created within the timeframe
        int: a 200 status code saying the events were retrieved
        
    """
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

    logger.info("Query for drop out students %s returns %d results", start_timestamp, len(results_list))

    return results_list, 200

def get_event_stats():
    session = DB_SESSION()

    enroll_count = session.query(Enroll).count()
    drop_out_count = session.query(DropOut).count()

    session.close()

    return { "num_enrolls": enroll_count, "num_drop_outs": drop_out_count }, 200



def process_messages():
    """
    Consumes messages from the Kafka broker and stores the events
    in the enroll and drop_out tables in the database. 
    
    returns:
        None
        
    """
    hostname = "%s:%d" % (APP_CONFIG['events']['hostname'],
                        APP_CONFIG['events']['port'])

    consumer = None
    max_retries = APP_CONFIG['events']['retries']
    current_retries = 0
    while current_retries < max_retries:
        logger.info(f"Attempting to connect to Kafka broker: {current_retries} retries")
        try:
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(APP_CONFIG['events']['topic'])]
            consumer = topic.get_simple_consumer(consumer_group=b"event_group",
                                reset_offset_on_start=False, # keep offset position
                                auto_offset_reset=OffsetType.LATEST) # reset to latest if no offset
            logger.info("Sucessfully connected to Kafka broker")
            break
        except:
            logger.error("Kafka connection failed")
            time.sleep(APP_CONFIG['events']['retry_delay'])
            current_retries += 1


    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s", msg)

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
app.add_api("openapi.yaml", base_path="/storage", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090, host="0.0.0.0")

