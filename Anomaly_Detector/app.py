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

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

if not os.path.isfile(app_config['store']['file']):
    with open(app_config['store']['file'], 'w') as f:
        json.dump([], f)

def connect_to_broker():
    """
    Connects to the Kafka broker specified in the app_config.yml file

    Returns:
        object: a simple consumer Kafka instance

    Raises:
        ConnectionRefusedError: If unable to connect to Kafka broker after 5 tries
    """
    hostname = "%s:%d" % (app_config['events']['hostname'],
                         app_config['events']['port'])
    
    max_retries = app_config['events']['retries']
    current_retry = 0
    while current_retry <= max_retries:
        try:
            logger.info("retry %s of connecting to kafka broker", current_retry)
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config['events']['topic'])]
            consumer = topic.get_simple_consumer(consumer_group=b"anomaly_group",
                                                reset_offset_on_start=False,
                                                auto_offset_reset=OffsetType.LATEST)
            logger.info("Successfully connected to Kafka broker")
            return consumer
        except Exception as e:
            logger.error("Error: %s" % e)
            time.sleep(app_config['events']['retry_delay'])
            current_retry += 1
    raise ConnectionRefusedError("Could not connect to Kafka Broker")

def get_events():
    """
    Consumes all kafka messages and checks for any anomalies
    to add to the JSON datastore

    Returns:
        None
    """
    with open(app_config['store']['file'], 'r') as f:
        current_anomalies = json.load(f)
    
    consumer = connect_to_broker()

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
                    "event_id": payload['student_id'],
                    "trace_id": payload['trace_id'],
                    "event_type": "enroll",
                    "anomaly_type": "Too High",
                    "description": f"High School GPA {payload['highschool_gpa']} is above {enroll_threshold}",
                    "timestamp": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
                }
                current_anomalies.append(anomaly)

                with open(app_config['store']['file'], "w") as f:
                    json.dump(current_anomalies, f, indent=4)
                    
                logger.info("Anomaly added to database: %s" % anomaly)
                
            elif msg['type'] == "drop_out" and payload['program_gpa'] < drop_out_threshold:
                anomaly = {
                    "event_id": payload['student_id'],
                    "trace_id": payload['trace_id'],
                    "event_type": "drop_out",
                    "anomaly_type": "Too Low",
                    "description": f"Program GPA {payload['program_gpa']} is below {drop_out_threshold}",
                    "timestamp": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
                }
                current_anomalies.append(anomaly)
                
                with open(app_config['store']['file'], "w") as f:
                    json.dump(current_anomalies, f, indent=4)

                logger.info("Anomaly added to database: %s" % anomaly)
                
            consumer.commit_offsets()
        except Exception as e:
            logger.error(f"Error: {e}")
        
def get_anomalies(anomaly_type):
    """
    Runs when a GET request is sent to the /anomalies endpoint
    Retrieves all anomalies by the anomaly type requested
    
    :param string anomaly_type: the type of anomaly

    Returns:
        list: A list of anomaly objects that match the anomaly type requested
        int: Status code 200 if the anomalies are retrieved successfully
    """
    try:
        logger.debug("Received request for anomaly type %s" % anomaly_type)

        with open(app_config['store']['file'], 'r') as f:
            current_anomalies = json.load(f)

        requested_anomalies = []

        for event in current_anomalies:
            if event['anomaly_type'].replace(' ', '') == anomaly_type:
                requested_anomalies.append(event)

        requested_anomalies = sorted(requested_anomalies, key=sort_by_date, reverse=True)

        logger.info("Anomalies returned: %s" % requested_anomalies)

        return requested_anomalies, 200
    except Exception as e:
        logger.error("Error: %s" % e)

def sort_by_date(event):
    return datetime.strptime(event['timestamp'], "%Y-%m-%d %H:%M:%S")

app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api('openapi.yaml', base_path="/anomalies", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=get_events)
    t1.daemon = True
    t1.start()
    app.run(port=8120, host="0.0.0.0")

    logger.info("Threshold of enroll High School GPA: Higher than %s", 
                app_config['thresholds']['enroll'])
    logger.info("Threshold of drop_out Program GPA: Lower than %s", 
                app_config['thresholds']['drop_out'])
