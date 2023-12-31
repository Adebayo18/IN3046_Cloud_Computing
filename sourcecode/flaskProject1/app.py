import boto3
import os
import json
import uuid
import re
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template

load_dotenv()

# Retrieve the IAM access keys and region from environment variables
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')
# setup boto3 configuration
sqs_client = boto3.client('sqs', aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name=region_name)

# create three priority queues
high_queue_response = sqs_client.create_queue(QueueName='high_priority')
high_queue_url = high_queue_response['QueueUrl']
medium_low_queue_response = sqs_client.create_queue(QueueName='medium_low_priority')
medium_low_queue_url = medium_low_queue_response['QueueUrl']
dlq_queue_response = sqs_client.create_queue(QueueName='dlq_priority')
dlq_queue_url = dlq_queue_response['QueueUrl']


# regex pattern that validates a variable is a string
pattern = r'^\s*([\'"])([^\1]*)\1\s*$'


# This function sends the bugreport to the queue
def sendToQueueHighHandler(payload: str) -> int:
    # convert the Python dictionary to a JSON string
    jsonPayload = json.dumps({"data": payload})
    # send a message to the queue
    response = sqs_client.send_message(
        QueueUrl=high_queue_url,
        MessageBody=jsonPayload
    )
    # get the response status code
    response_status = response['ResponseMetadata']['HTTPStatusCode']
    # return the response status code
    return response_status


# This function sends the bugreport to the queue
def sendToQueueMediumLowHandler(payload: str) -> int:
    # convert the Python dictionary to a JSON string
    jsonPayload = json.dumps({"data": payload})
    # send a message to the queue
    response = sqs_client.send_message(
        QueueUrl=medium_low_queue_url,
        MessageBody=jsonPayload
    )
    # get the response status code
    response_status = response['ResponseMetadata']['HTTPStatusCode']
    # return the response status code
    return response_status


# This function sends the bugreport to the queue
def sendToQueueDLQHandler(payload: str) -> int:
    # convert the Python dictionary to a JSON string
    jsonPayload = json.dumps({"data": payload})
    # send a message to the queue
    response = sqs_client.send_message(
        QueueUrl=dlq_queue_url,
        MessageBody=jsonPayload
    )
    # get the response status code
    response_status = response['ResponseMetadata']['HTTPStatusCode']
    # return the response status code
    return response_status


# This function sorts the bugreports into different classes
def sortBug(bug_id_number: str, bug_title: str, bug_class: str, bug_description: str) -> int:
    # Build a payload dictionary containing the bug data
    payload = {"bug_id_number": bug_id_number,
               "bug_title": bug_title,
               "bug_class": bug_class,
               "bug_desc": bug_description
               }
    # Check if the user has not entered any priority, or it's not one of the predefined priorities
    if not bug_class or bug_class not in ("high", "medium", "low"):
        payload["bug_class"] = "dlq"

    # Check that the values match the regex pattern
    if not all(isinstance(value, str) and re.match(pattern, repr(value)) for value in payload.values()):
        # If any of the values are not strings or do not match the pattern, set the bug_class to "dlq"
        payload["bug_class"] = "dlq"

    if payload["bug_class"] == "high":
        # If the bug class is "high", send the bug to the HighPriority queue
        res = sendToQueueHighHandler(payload)
        return res
    elif payload["bug_class"] in ("medium", "low"):
        # If the bug class is "medium" or "low", send the bug to the MediumLowPriority queue
        res = sendToQueueMediumLowHandler(payload)
        return res
    elif payload["bug_class"] == "dlq":
        # If the bug class is "dlq", send the bug to the DLQ queue
        res = sendToQueueDLQHandler(payload)
        return res


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def bugSubmissionPage():
    # if the request is post
    if request.method == 'POST':
        # sets vars from form
        bug_title = request.form["user"]
        bug_class = request.form["priority"]
        bug_description = request.form["description"]
        # Generate a UUID from a string
        bug_id = uuid.uuid5(uuid.NAMESPACE_DNS, bug_title).hex
        # Call the sortBug function to submit the bug report to the appropriate queue
        response_status = sortBug(bug_id, bug_title, bug_class, bug_description)
        print(f"Response Status: {response_status}")
        # passes in vars to bug sorter
        print(bug_title, bug_class, bug_description)
        # returns submission complete and passes in info for jinja template
        return render_template("SubmissionComplete.html", bugIdNumber=bug_id, bugClass=bug_class, bugTitle=bug_title,
                               bugDesc=bug_description)
    return render_template("index.html")


# This Flask endpoint receives a POST request to submit a bug report.
@app.route('/api/submit_bug', methods=['POST'])
def submit_bug():
    # The bug data is retrieved from the POST request body in JSON format.
    bug_data = request.get_json()
    # The bug title, class and description are extracted from the JSON data.
    bug_title = bug_data["BugTitle"]
    bug_class = bug_data["BugClassification"]
    bug_description = bug_data["BugDescription"]
    # A UUID is generated using the bug title as a namespace and converted to hex.
    bug_id = uuid.uuid5(uuid.NAMESPACE_DNS, bug_title).hex
    # The bug data is sent to the sortBug function to be prioritized and added to a queue.
    res = sortBug(bug_id, bug_title, bug_class, bug_description)
    # If the response status code is 200, the endpoint returns a json body and the status code.
    if res == 200:
        return jsonify({"message": "Success!"}), res
    # Otherwise, it returns a json body and a 400 status code.
    return jsonify({"message": "Something went wrong!"}), 400


# runs flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)