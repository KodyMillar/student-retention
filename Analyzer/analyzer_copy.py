import yaml
import logging
import logging.config
import json
from pykafka import KafkaClient
import os
import connexion
from flask_cors import CORS


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

logger.info("App Conf File: %s", APP_CONF_FILE)
logger.info("Log Conf File: %s", LOG_CONF_FILE)


def get_enroll_student(index):
    """Get enroll event by index in History"""
    hostname = "%s:%d" % (APP_CONFIG['events']['hostname'],
                          APP_CONFIG['events']['port'])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(APP_CONFIG['events']['topic'])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)
    logger.info("Retrieving student enroll event at index %d", index)
    try:
        count = 0
        for msg in consumer:
            offset = msg.offset
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg['type'] == "enroll":
                if index == count:
                    return msg['payload'], 200
                else:
                    count += 1
    except:
        logger.error("No more messages found")
    logger.error("Could not find enroll event at index %d",  index)
    return { "message": "Not Found" }, 404


def get_drop_out_student(index):
    """Get drop_out event by index in History"""
    hostname = "%s:%d" % (APP_CONFIG['events']['hostname'],
                          APP_CONFIG['events']['port'])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(APP_CONFIG['events']['topic'])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)
    logger.info("Retrieving student enroll event at index %d", index)
    try:
        count = 0
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg['type'] == "drop_out":
                if index == count:
                    return msg['payload'], 200
                else:
                    count += 1
    except:
        logger.error("No more messages found")
    logger.error("Could not find enroll event at index %d",  index)
    return { "message": "Not Found" }, 404


def get_event_stats():
    """Get BP Reading in History"""
    hostname = "%s:%d" % (APP_CONFIG['events']['hostname'],
                          APP_CONFIG['events']['port'])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(APP_CONFIG['events']['topic'])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)

    logger.info("Retrieving stats")
    num_enrolls = 0
    num_drop_outs = 0
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            if msg['type'] == "enroll":
                num_enrolls += 1
            elif msg['type'] == "drop_out":
                num_drop_outs += 1
    except:
        logger.error("No more messages found")
    logger.info("Got %d enroll events and %d drop out events", num_enrolls, num_drop_outs)
    return { "num_enrolls": num_enrolls, "num_drop_outs": num_drop_outs }, 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", base_path="/analyzer", strict_validation=True, validate_responses=True)

if not "TARGET_ENV" in os.environ or os.environ['TARGET_ENV'] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")
