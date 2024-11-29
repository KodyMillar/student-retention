import connexion
from connexion import NoContent
from pathlib import Path
import requests
import yaml
import logging
import logging.config
import uuid
import json
import datetime
import time
from pykafka import KafkaClient
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

producer = None
max_retries = app_config['events']['retries']
current_retry = 0
while current_retry <= max_retries:
	try:
		logger.info(f"Retry {current_retry} of connecting to kafka broker")
		client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
		topic = client.topics[str.encode(app_config['events']['topic'])]
		producer = topic.get_sync_producer()
		logger.info("Successfully connected to Kafka broker")
		break
	except:
		logger.error("Could not connect to Kafka broker")
		time.sleep(app_config['events']['retry_delay'])
		current_retry += 1


def enroll_student(body):
	body["trace_id"] = str(uuid.uuid4())

	logger.info(f"Received event enroll request with a trace id of {body['trace_id']}")

	# header = {"Content-Type": "application/json"}
	
	# response = requests.post(app_config["enroll"]["url"], json=body, headers=header)
	# client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
	# topic = client.topics[str.encode(app_config['events']['topic'])]
	# producer = topic.get_sync_producer()
	msg = {
		"type": "enroll",
		"datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
		"payload": body
	}

	msg_str = json.dumps(msg)
	logger.info(msg_str)
	global producer
	producer.produce(msg_str.encode('utf-8'))
	
	# logger.info(f"Returned event enroll response (id: {body["trace_id"]}) with status {response.status_code}")

	return NoContent, 201


def withdraw_student(body):
	body["trace_id"] = str(uuid.uuid4())

	logger.info(f"Received event drop-out request with a trace id of {body['trace_id']}")

	# header = {"Content-Type": "application/json"}
	# response = requests.post(app_config["drop-out"]["url"], json=body, headers=header)
	msg = {
		"type": "drop_out",
		"datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
		"payload": body
	}

	msg_str = json.dumps(msg)
	logger.info(msg_str)
	global producer
	producer.produce(msg_str.encode('utf-8'))

	# logger.info(f"Returned event drop-out response (id: {body["trace_id"]}) with status 201")
	
	return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
	app.run(port=8080, host="0.0.0.0")
