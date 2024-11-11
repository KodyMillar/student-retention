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
from pykafka import KafkaClient


with open("app_conf.yml", "r") as f:
	app_config = yaml.safe_load(f.read())

with open("log_conf.yml", "r") as f:
	log_config = yaml.safe_load(f.read())
	logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def enroll_student(body):
	body["trace_id"] = str(uuid.uuid4())

	logger.info(f"Received event enroll request with a trace id of {body['trace_id']}")

	# header = {"Content-Type": "application/json"}
	
	# response = requests.post(app_config["enroll"]["url"], json=body, headers=header)
	client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
	topic = client.topics[str.encode(app_config['events']['topic'])]
	producer = topic.get_sync_producer()
	msg = {
		"type": "enroll",
		"datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
		"payload": body
	}

	msg_str = json.dumps(msg)
	producer.produce(msg_str.encode('utf-8'))
	
	# logger.info(f"Returned event enroll response (id: {body["trace_id"]}) with status {response.status_code}")

	return NoContent, 201


def withdraw_student(body):
	body["trace_id"] = str(uuid.uuid4())

	logger.info(f"Received event drop-out request with a trace id of {body['trace_id']}")

	# header = {"Content-Type": "application/json"}
	# response = requests.post(app_config["drop-out"]["url"], json=body, headers=header)

	client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
	topic = client.topics[str.encode(app_config['events']['topic'])]
	producer = topic.get_sync_producer()
	
	msg = {
		"type": "drop_out",
		"datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
		"payload": body
	}

	msg_str = json.dumps(msg)
	producer.produce(msg_str.encode('utf-8'))

	# logger.info(f"Returned event drop-out response (id: {body["trace_id"]}) with status 201")
	
	return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
	app.run(port=8080, host="0.0.0.0")
