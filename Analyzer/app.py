import connexion
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
from connexion import NoContent
import requests
import yaml
import logging
import logging.config
import json
from pykafka import KafkaClient


with open("app_conf.yml", "r") as f:
	app_config = yaml.safe_load(f.read())

with open("log_conf.yml", "r") as f:
	log_config = yaml.safe_load(f.read())
	logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


def get_enroll_student(index):
	"""Get enroll event by index in History"""
	hostname = "%s:%d" % (app_config['events']['hostname'], 
					      app_config['events']['port'])
	client = KafkaClient(hosts=hostname)
	topic = client.topics[str.encode(app_config['events']['topic'])]
	consumer = topic.get_simple_consumer(reset_offset_on_start=True,
										 consumer_timeout_ms=1000)	
	logger.info("Retrieving student enroll event at index %d" % index)
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
	logger.error("Could not find enroll event at index %d" % index)
	return { "message": "Not Found" }, 404


def get_drop_out_student(index):
	"""Get drop_out event by index in History"""
	hostname = "%s:%d" % (app_config['events']['hostname'], 
					      app_config['events']['port'])
	client = KafkaClient(hosts=hostname)
	topic = client.topics[str.encode(app_config['events']['topic'])]
	consumer = topic.get_simple_consumer(reset_offset_on_start=True,
										 consumer_timeout_ms=1000)	
	logger.info("Retrieving student enroll event at index %d" % index)
	try:
		count = 0
		for msg in consumer:
			offset = msg.offset
			msg_str = msg.value.decode('utf-8')
			msg = json.loads(msg_str)
			if msg['type'] == "drop_out":
				if index == count:
					return msg['payload'], 200
				else:
					count += 1
	except:
		logger.error("No more messages found")
	logger.error("Could not find enroll event at index %d" % index)
	return { "message": "Not Found" }, 404


def get_event_stats():
	"""Get BP Reading in History"""
	hostname = "%s:%d" % (app_config['events']['hostname'], 
					      app_config['events']['port'])
	client = KafkaClient(hosts=hostname)
	topic = client.topics[str.encode(app_config['events']['topic'])]
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
	logger.info("Got %s enroll events and %d drop out events" % (num_enrolls, num_drop_outs))
	return { "num_enrolls": num_enrolls, "num_drop_outs": num_drop_outs }, 200


# def enroll_student(body):
# 	body["trace_id"] = str(uuid.uuid4())

# 	logger.info(f"Received event enroll request with a trace id of {body['trace_id']}")

# 	# header = {"Content-Type": "application/json"}
	
# 	# response = requests.post(app_config["enroll"]["url"], json=body, headers=header)
# 	client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
# 	topic = client.topics[str.encode(app_config['events']['topic'])]
# 	producer = topic.get_sync_producer()
# 	msg = {
# 		"type": "enroll",
# 		"datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
# 		"payload": body
# 	}

# 	msg_str = json.dumps(msg)
# 	producer.produce(msg_str.encode('utf-8'))
	
# 	# logger.info(f"Returned event enroll response (id: {body["trace_id"]}) with status {response.status_code}")

# 	return NoContent, 201


# def withdraw_student(body):
# 	body["trace_id"] = str(uuid.uuid4())

# 	logger.info(f"Received event drop-out request with a trace id of {body['trace_id']}")

# 	# header = {"Content-Type": "application/json"}
# 	# response = requests.post(app_config["drop-out"]["url"], json=body, headers=header)

# 	client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
# 	topic = client.topics[str.encode(app_config['events']['topic'])]
# 	producer = topic.get_sync_producer()
	
# 	msg = {
# 		"type": "drop_out",
# 		"datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
# 		"payload": body
# 	}

# 	msg_str = json.dumps(msg)
# 	producer.produce(msg_str.encode('utf-8'))

# 	# logger.info(f"Returned event drop-out response (id: {body["trace_id"]}) with status 201")
	
# 	return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

app.add_middleware(
	CORSMiddleware,
	position=MiddlewarePosition.BEFORE_EXCEPTION, # can apply custom exceptions
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['GET'],
	allow_headers=['*']
)

if __name__ == "__main__":
	app.run(port=8110, host="0.0.0.0")
