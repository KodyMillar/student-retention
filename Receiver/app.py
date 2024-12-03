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

with open(APP_CONF_FILE, "r") as f:
    APP_CONFIG = yaml.safe_load(f.read())

with open(LOG_CONF_FILE, "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s", APP_CONF_FILE)
logger.info("Log Conf File: %s", LOG_CONF_FILE)

producer = None
max_retries = APP_CONFIG['events']['retries']
current_retry = 0
while current_retry <= max_retries:
    try:
        logger.info("Retry %d of connecting to kafka broker", current_retry)
        client = KafkaClient(hosts=f"{APP_CONFIG['events']['hostname']}:{APP_CONFIG['events']['port']}")
        topic = client.topics[str.encode(APP_CONFIG['events']['topic'])]
        producer = topic.get_sync_producer()
        logger.info("Successfully connected to Kafka broker")
        break
    except:
        logger.error("Could not connect to Kafka broker")
        time.sleep(APP_CONFIG['events']['retry_delay'])
        current_retry += 1


def enroll_student(body):
    body["trace_id"] = str(uuid.uuid4())

    logger.info("Received event enroll request with a trace id of %s", body['trace_id'])

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

    logger.info("Received event drop-out request with a trace id of %s", body['trace_id'])

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
app.add_api("openapi.yaml", base_path="/receiver", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
