import requests
import yaml
import logging
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
import os
import json
from datetime import datetime, timedelta
from statistics import mean
import connexion
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from connexion import NoContent
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

if not os.path.isfile(APP_CONFIG['datastore']['filename']):
    base_stats = {
        "num_enrolled_students": 0,
        "min_enrolled_student_gpa": 0,
        "avg_enrolled_student_gpa": 0,
        "num_drop_out_students": 0,
        "max_drop_out_student_gpa": 0,
        "avg_drop_out_student_gpa": 0,
        "last_updated": datetime.strftime(datetime.now() - timedelta(seconds=5), '%Y-%m-%dT:%H:%M:%S')
    }
    with open(APP_CONFIG['datastore']['filename'], "w", encoding='utf-8') as f:
        json.dump(base_stats, f, indent=4)

def get_json_data():
    if os.path.isfile(APP_CONFIG['datastore']['filename']):
        with open(APP_CONFIG['datastore']['filename'], 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {
            "num_enrolled_students": 0,
               "min_enrolled_student_gpa": 4.0,
              "avg_enrolled_student_gpa": 0,
               "num_drop_out_students": 0,
              "max_drop_out_student_gpa": 0.0,
              "avg_drop_out_student_gpa": 0,
            "last_updated": datetime.strftime(datetime.now() - timedelta(seconds=5), '%Y-%m-%dT:%H:%M:%S')
        }


def populate_stats():
    """Periodically update stats"""
    logger.info("Periodic processing has started")

    json_data = get_json_data()

    logger.debug(json_data)

    try:
        start_timestamp = json_data['last_updated']
        current_date = datetime.strftime(datetime.now(), '%Y-%m-%dT:%H:%M:%S')
    except:
        logger.debug("OH MY GOSH")
    logger.debug("\n DATE\n")
    logger.debug(current_date)

    header = {"Content-Type": "application/json"}
    params = {"start_timestamp": start_timestamp, "end_timestamp": current_date}
    enroll_response = ""
    drop_out_response = {}
    try:
        enroll_response = requests.get(f"{APP_CONFIG['eventstore']['url']}/enroll", 
                                       params=params, headers=header)
        drop_out_response = requests.get(f"{APP_CONFIG['eventstore']['url']}/drop-out", 
                                         params=params, headers=header)
        logger.debug("ENROLL RESPONSE\n---------------\n")
        logger.debug(enroll_response.json())
        logger.info("Received %d enroll events", len(enroll_response.json()))
        logger.info("Received %d drop-out events", len(drop_out_response.json()))

        if enroll_response.status_code != 200:
            logger.error("Did not receive a 200 response code from enroll endpoint")
            return
        if drop_out_response.status_code != 200:
            logger.error("Did not receive a 200 response code from drop-out endpoint")
            return

        enroll_gpa = [event["highschool_gpa"] for event in enroll_response.json()]
        drop_out_gpa = [event["program_gpa"] for event in drop_out_response.json()]

        enroll_gpa += [json_data["min_enrolled_student_gpa"]]
        drop_out_gpa += [json_data["max_drop_out_student_gpa"]]

        json_data["num_enrolled_students"] += len(enroll_response.json())
        json_data["min_enrolled_student_gpa"] = min(enroll_gpa)
        json_data["avg_enrolled_student_gpa"] = mean(enroll_gpa)
        json_data["num_drop_out_students"] += len(drop_out_response.json())
        json_data["max_drop_out_student_gpa"] = max(drop_out_gpa)
        json_data["avg_drop_out_student_gpa"] = mean(drop_out_gpa)
        json_data["last_updated"] = current_date

        logger.debug(json_data)

        with open(APP_CONFIG['datastore']['filename'], 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=4)
    except Exception as e:
        logger.exception(e)

def get_stats():
    """
    Receives a GET request for the data stored in the json datastore.
    
    returns:
        object: the events in the json data store
        int: a 200 status code saying the events were retrieved
        
    """
    logger.info("Request for statistics has been received")

    statistics = {}
    try:
        with open(APP_CONFIG['datastore']['filename'], encoding='utf-8') as f:
            statistics = json.load(f)
            logger.info(statistics)
    except FileNotFoundError:
        logger.error("No statistics found")
        return NoContent, 404


    logger.debug(f"Statistics: {statistics}")
    logger.info("Request has been completed")

    return statistics, 200


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
                  'interval',
                  seconds=APP_CONFIG['scheduler']['period_sec'])
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", base_path="/processing", strict_validation=True, validate_responses=True)

# Connexion wraps around Flask, and app.app allows you to access the underlying Flask application
if not "TARGET_ENV" in os.environ or os.environ['TARGET_ENV'] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

# app.add_middleware(
# 	CORSMiddleware,
# 	position=MiddlewarePosition.BEFORE_EXCEPTION, # can apply custom exceptions
# 	allow_origins=['*'],
# 	allow_credentials=True,
# 	allow_methods=['GET'],
# 	allow_headers=['*']
# )

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
