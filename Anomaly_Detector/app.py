import connexion
from connexion import NoContent
from datetime import datetime
import time

import yaml
import logging
import logging.config
import json
import os

from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Must change json to list and read from json file first to update data
def get_events():
    hostname = "%s:%d", (app_config['events']['hostname'],
                         app_config['events']['port'])
    
    max_retries = app_config['events']['retries']
    current_retry = 0
    while current_retry <= max_retries:
        try:
            logger.info("retry %s of connecting to kafka broker", current_retry)
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config['events']['topic'])]
            consumer = topic.get_simple_consumer(consumer_group=b"event_group",
                                                reset_offset_on_start=False,
                                                auto_offset_reset=OffsetType.LATEST)
            logger.info("Successfully connected to Kafka broker")
            break
        except Exception as e:
            logger.error("Error: %s", e)
            time.sleep(app_config['events']['retry_delay'])
            current_retry += 1
    
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        logger.info("Message: %s" % msg_str)
        msg = json.loads(msg_str)
    
        try:
            payload = msg['payload']
            enroll_threshold = app_config['thresholds']['enroll']
            drop_out_threshold = app_config['thresholds']['drop_out']
            if msg['type'] == "enroll" and payload['highschool_gpa'] > enroll_threshold:
                anomaly = {
                    "event_uuid": payload['student_id'],
                    "trace_id": payload['trace_id'],
                    "event_type": "enroll",
                    "anomaly_type": "TooHigh",
                    "description": f"High School GPA {payload['highschool_gpa']} is above {enroll_threshold}",
                    "date_detected": datetime.now()
                }
                with open("anomalies.json", "a") as f:
                    json.dump(anomaly, f, indent=4)

                logger.info("Anomaly added to database: %s", anomaly)
                
            elif msg['type'] == "drop_out" and payload['program_gpa'] > drop_out_threshold:
                anomaly = {
                    "event_uuid": payload['student_id'],
                    "trace_id": payload['trace_id'],
                    "event_type": "drop_out",
                    "anomaly_type": "TooHigh",
                    "description": f"Program GPA {payload['program_gpa']} is above {drop_out_threshold}",
                    "date_detected": datetime.now()
                }
                with open("anomalies.json", "a") as f:
                    json.dump(anomaly, f, indent=4)
                
                logger.info("Anomaly added to database: %s", anomaly)
                
            consumer.commit_offsets()
        except Exception as e:
            logger.info(f"Error: {e}")


def get_anomalies(anomaly_type):
    logger.debug("Received request for anomaly type %s", anomaly_type)