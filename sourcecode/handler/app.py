import json
import os
import boto3
from time import sleep
from flask import Flask
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from slack_sdk.webhook import WebhookClient
from twilio.rest import Client
from botocore.exceptions import ClientError

load_dotenv()
app = Flask(__name__)


# Set up the AWS credentials and create an SQS client, similar to your initial script
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
region_name = os.getenv('AWS_REGION')

sqs_client = boto3.client('sqs', aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name="eu-west-2")

# Create a new SES resource and specify a region.
ses_client = boto3.client('ses',region_name=region_name)


# get the three priority queues
high_queue_url = sqs_client.get_queue_url(QueueName="high_priority")['QueueUrl']
medium_low_queue_url = sqs_client.get_queue_url(QueueName="medium_low_priority")['QueueUrl']
dlq_queue_url = sqs_client.get_queue_url(QueueName="dlq_priority")['QueueUrl']

# Set up slack webhook URL, Twilio credentials and email configurations
slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_sender_number = os.getenv('TWILIO_SENDER_NUMBER')
twilio_receiver_numbers = os.getenv('TWILIO_RECEIVER_NUMBERS')
email_sender = os.getenv('EMAIL_SENDER')
email_receiver = os.getenv('EMAIL_RECEIVER')


for email in [email_sender, email_receiver]:
    # Get a list of already verified emails on the aws account
    verified_email_response = ses_client.list_verified_email_addresses()
    verified_email_list = verified_email_response['VerifiedEmailAddresses']
    print(verified_email_list)
    # If the current email being checked for is already verified, move to the next email
    if email in verified_email_list:
        continue
    else:
        # Else send a verification email to the current email being checked
        email_identity_response = ses_client.verify_email_identity(EmailAddress=email)
        # Check that the verification email was successfully sent
        assert email_identity_response['ResponseMetadata']['HTTPStatusCode'] == 200
        while True:
            # Get the verification status of the current email being checked
            email_verification_attributes = ses_client.get_identity_verification_attributes(Identities=[email])
            email_verification_status = email_verification_attributes['VerificationAttributes'][email]['VerificationStatus']
            # Check if user has not clicked on the link sent in the email
            if email_verification_status == "Pending":
                print(f"Verify your identity using the email sent to {email}")
                sleep(5)
            # Check if within 24 hrs user never clicked verification link and the link expired
            elif email_verification_status == "Failed":
                email_identity_response = ses_client.verify_email_identity(EmailAddress=email)
                assert email_identity_response['ResponseMetadata']['HTTPStatusCode'] == 200
                sleep(5)
            # If user verifies email using the verification link, move on to the next email to be checked
            else:
                print(f"{email_verification_status} -> Email Identity for {email} verified successfully")
                break
            continue

# Slack handler which utilizes slack webhook to create high priority messages
def createSlackMessage(messageDict):
    # Create slack webhook client
    slack_webhook = WebhookClient(slack_webhook_url)
    # Create slack message with appropriate attributes to be sent to slack channel
    slack_response = slack_webhook.send(
        text="Bug Message",
        blocks=[
            {
                "type": "section",
                "text": {
                    "text": f"Bug Description: {messageDict['bug_desc']}",
                    "type": "mrkdwn"
                },
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Title*"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Priority*"
                    },
                    {
                        "type": "plain_text",
                        "text": f"*{messageDict['bug_title']}*"
                    },
                    {
                        "type": "plain_text",
                        "text": f"*{messageDict['bug_class']}*"
                    }
                ]
            }
        ]
    )

    # Check if response returned is successful
    assert slack_response.status_code == 200


def createTwilloMessage(messageDict):
    # Create twilio client using twilio credentials
    twilio_client = Client(twilio_account_sid, twilio_auth_token)
    # Send message to phone numbers using twilio client
    message_response = twilio_client.messages.create(
        body=f"{messageDict['bug_title']}\n" + f"{messageDict['bug_class']}\n" + f"{messageDict['bug_desc']}",
        from_=twilio_sender_number,
        to=twilio_receiver_numbers
    )

    # Check if message was sent successfully
    assert message_response.status == "sent"

def createEmailMessage(messageDict):
    # The subject line for the email.
    SUBJECT = "Bug Report"

    # The HTML body of the email.
    BODY_HTML = f"""<html>
    <head></head>
    <body>
      <h1>{messageDict['bug_title']}</h1>
      <p>Type: {messageDict['bug_class']}</p>
      <p>Description: {messageDict['bug_desc']}.</p>
    </body>
    </html>"""

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Try to send the email.
    try:
        # Provide the contents of the email.
        response = ses_client.send_email(
            Destination={
                'ToAddresses': [
                    email_receiver,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=email_sender
        )

    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])



@app.route("/message", methods=['POST'])
def consumeMessages():
    print("Message Consumer function called")

    while True:
        # Process high priority messages and send to Slack
        response_high = sqs_client.receive_message(
            QueueUrl=high_queue_url,
            MaxNumberOfMessages=10,  # Adjusted to receive up to 10 messages at once
            WaitTimeSeconds=10
        )

        if 'Messages' in response_high:
            for message in response_high['Messages']:
                message_body = json.loads(message['Body'])
                createSlackMessage(message_body['data'])
                sqs_client.delete_message(
                    QueueUrl=high_queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
        else:
            break  # Exit loop if no more messages

        # Process medium and low priority messages and send to email
        response_medium_low = sqs_client.receive_message(
            QueueUrl=medium_low_queue_url,
            MaxNumberOfMessages=10,  # Adjusted to receive up to 10 messages at once
            WaitTimeSeconds=10
        )

        if 'Messages' in response_medium_low:
            for message in response_medium_low['Messages']:
                message_body = json.loads(message['Body'])
                createEmailMessage(message_body['data'])
                sqs_client.delete_message(
                    QueueUrl=medium_low_queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
        else:
            break  # Exit loop if no more messages

    print("Finished processing all messages in the queue.")


scheduler = BackgroundScheduler()
scheduler.add_job(func=consumeMessages, trigger="interval", seconds=10)
scheduler.start()

if __name__ == '__main__':
    app.run("0.0.0.0", port=5001)