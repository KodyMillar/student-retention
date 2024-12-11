import logging
import logging.config
import yaml
import json
from apscheduler.schedulers.background import BackgroundScheduler
import connexion
import requests
from requests.exceptions import Timeout, ConnectionError

with open('app_conf.yml', 'r', encoding='utf-8') as file:
    app_config = yaml.safe_load(file.read())

with open('log_conf.yml', "r", encoding='utf-8') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

RECEIVER_URL = app_config['receiver']['url']
STORAGE_URL = app_config['storage']['url']
PROCESSING_URL = app_config['processor']['url']
ANALYZER_URL = app_config['analyzer']['url']
TIMEOUT = app_config['timeout']['seconds']

def check_services():
    """ Called periodically """
    global receiver_status
    receiver_status = "Unavailable"
    try:
        response = requests.get(RECEIVER_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            receiver_status = "Healthy"
            logger.info("Receiver is Healthly")
        else:
            logger.info("Receiver returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Receiver is Not Available")

    global storage_status
    storage_status = "Unavailable"
    try:
        response = requests.get(STORAGE_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            storage_json = response.json()
            storage_status = f"Storage has {storage_json['num_enrolls']} enrolled students and {storage_json['num_drop_outs']} student drop outs"
            logger.info("Storage is Healthy")
        else:
            logger.info("Storage returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Storage is Not Available")
    
    global processor_status
    processor_status = "Unavailable"
    try:
        response = requests.get(PROCESSING_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            processor_json = response.json()
            processor_status = f"Processor has {processor_json['num_enrolled_students']} enrolled students and {processor_json['num_drop_out_students']} student drop outs"
            logger.info("Processor is healthy")
        else:
            logger.info("Processor returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Processor is Not Available")

    global analyzer_status
    analyzer_status = "Unavailable"
    try:
        response = requests.get(ANALYZER_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            analyzer_json = response.json()
            analyzer_status = f"Analyzer has {analyzer_json['num_enrolls']} enrolled students and {analyzer_json['num_drop_outs']} student drop outs"
            logger.info("Analyzer is healthy")
        else:
            logger.info("Analyzer returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Analyzer is Not Available")
    
    status_json = {
        "receiver": receiver_status,
        "storage": storage_status,
        "processing": processor_status,
        "analyzer": analyzer_status
    }

    with open('status.json', 'w', encoding='utf-8') as file:
        json.dump(status_json, file, indent=4)

def get_checks():
    """Get checks in status storage file"""
    try:
        with open('status.json', 'r', encoding='utf-8') as file:
            status_json = json.load(file)
        return status_json, 200
    except FileNotFoundError:
        return { "message": "File does not exist" }, 404
    
def init_scheduler():
    """Start the periodic scheduling"""
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(check_services,
                  'interval',
                  seconds=app_config['scheduler']['seconds'])
    sched.start()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/check", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8130, host="0.0.0.0")
