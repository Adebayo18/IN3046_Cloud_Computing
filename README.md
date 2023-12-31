# Bug Tracking Application

This application focuses on making handling bug reports of different priority easier. It has two parts (The UI and the handler/message consumer) which are deployed separately into two different elastic compute instances on AWS. It creates 3 priority queues to store messages for different priority levels such as high, medium and low priority. The handler uses a scheduler which polls the priority queues for bug report messages at intervals of 10 seconds. Once it polls for messages and gets any message, it constructs messages in different forms to be consumed by different webhooks and clients. It sends the high priority bug reports to a slack channel using a webhook and then sends the medium and low priority bug report messages to receiver emails using Amazon SMTP. Once the messages are consumed and handled appropriately, the handlers then proceed to delete the messages from the queue to avoid multiple consumption of the messages.

## Usage on Local machine
### Running the UI
Ensure you have python and git installed on your system. Clone the repo using the git clone command.

```bash
git clone git@github.com:Charle-Mary/ec2-bugtrackapp.git
```

Navigate to the flaskproject1 directory under the sourcecode directory which contains the UI app.

```bash
cd sourcecode/flaskproject1
```

Install the required libraries and packages using pip

```bash
pip install -r requirements.txt
```
Edit the .env file to use the correct environmental variables

```bash
PYTHON_ENV="XXXXXXXX"
PORT=5001
AWS_ACCESS_KEY_ID='XXXXXXXXX'
AWS_SECRET_ACCESS_KEY='XXXXXXXXXXXXX'
AWS_REGION='eu-west-2'
```
Run the python script

```bash
python3 app.py
```

Verify that the 3 priority queues are created and you're able to access the application on ```localhost:5000```.

### Running the handler

Open a new terminal and navigate to the handler directory under the sourcecode directory which contains the handler app.

```bash
cd sourcecode/handler
```

Install the required libraries and packages using pip

```bash
pip install -r requirements.txt
```

Create a channel in slack named ```monitoring``` or any other name of your choice.

Follow step 1-3 in order to get your [slack webhook url](https://api.slack.com/messaging/webhooks) for the channel you just created

Edit the .env file to use the correct environmental variables

```bash
PYTHON_ENV="XXXXXXXX"
PORT=5001
AWS_ACCESS_KEY_ID='XXXXXXXXX'
AWS_SECRET_ACCESS_KEY='XXXXXXXXXXXXX'
AWS_REGION='eu-west-2'
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXX/XXXXXXXXXXXXX"
TWILIO_ACCOUNT_SID='XXXXXXXXXXXXXXXXX'
TWILIO_AUTH_TOKEN='XXXXXXXXXXXXXXX'
TWILIO_SENDER_NUMBER='XXXXXXXXX'
TWILIO_RECEIVER_NUMBERS="XXXXXXXXXX"
EMAIL_SENDER="XXXXXXXXXXX@gmail.com"
EMAIL_RECEIVER="XXXXXXXXXX@gmail.com"
```
Run the python script

```bash
python3 app.py
```
Verify that the bug report messages are sent to the appropriate social media platform. ```high priority -> slack``` and ```medium or low priority -> email```.

## Running the Application on an EC2 Instance

Clone the repo using the git clone command

```bash
git clone git@github.com:Charle-Mary/ec2-bugtrackapp.git
```
Navigate to the root of the project directory and initialize the project as a terraform project using:

```bash
terraform init
```

Create a new file app.env, copy the following variables into it and edit as required using the correct details. Also create a keypair(preferrably with name "bugtrackapp") on the AWS console and download the keypair into the project directory. Take note of the keypair name.

```bash
# Create app.env file
touch app.env

# Copy the following variables into it and edit as required using correct details
PYTHON_ENV=production
PORT=5001
AWS_ACCESS_KEY_ID=XXXXXXXXX
AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXX
AWS_REGION=eu-west-2
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXXXXXXXXX/XXXXXXX/XXXXXXXXXXXXX
TWILIO_ACCOUNT_SID=XXXXXXXXXXXXXXXXX
TWILIO_AUTH_TOKEN=XXXXXXXXXXXXXXX
TWILIO_SENDER_NUMBER=XXXXXXXXX
TWILIO_RECEIVER_NUMBERS=XXXXXXXXXX
EMAIL_SENDER=XXXXXXXXXXX@gmail.com
EMAIL_RECEIVER=XXXXXXXXXXX@gmail.com
```
Create a new file terraform.tfvars, copy the following variables into it and edit as required using the correct details

```bash
# Create terraform variables file
touch terraform.tfvars

# Copy the following variables into it and edit as required using correct details
aws_access_key_id ="XXXXXXXXXXXXXXXXX"
aws_secret_access_key ="XXXXXXXXXXXXXXXXXX"
aws_region ="eu-west-2"
```

Create the infrastructure and deploy the application using the either of the commands below:
```bash
terraform apply

# Bypass the prompt which asks whether to create the infrastructure
terraform apply --auto-approve 
```

Copy the application URL in the output of the terminal and then access the application on ```port 5000```.

```bash
# The application URL with the port should be similar to this. Access it on your browser
ec2-18-130-242-214.eu-west-2.compute.amazonaws.com:5000
```

A verification emails would be sent to the email you have provided in the app.env file, be sure to click on the verification links. 

Once application usage is complete, delete the EKS Cluster and the entire infrastructure using the following command:

```bash
terraform destroy --auto-approve
```

Also ensure to login to the AWS Console and delete the SQS queues if necessary.


