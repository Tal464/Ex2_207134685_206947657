import os
import uuid
import requests
import boto3
import subprocess

# Create a new EC2 in specific region
print('Sets region')
region = 'us-east-1'

# Generates a random UUID
print('Generates a random UUID')
endOfKeyName = str(uuid.uuid4())

# Start of key name
keyName = 'cloud-course-ex2-' + endOfKeyName

# Create clients
manager = boto3.client('cloudformation', region_name=region)
instanceEc2 = boto3.client('ec2', region_name=region)

# Create and get a key pair
print('Creates and get a key pair')
newKeyPair = instanceEc2.create_key_pair(KeyName=keyName)
keyMaterial = newKeyPair['KeyMaterial']

with open('managerTemplate.json', 'r') as file:
    managerTemplateConnection = file.read()

# Create the stack for managing the app
newStack = manager.create_stack(
    StackName=keyName,
    TemplateBody=managerTemplateConnection,
    Parameters=[
        {
            'ParameterKey': 'MyIP',
            'ParameterValue': '0.0.0.0/0',
        },
        {
            "ParameterKey": "KeySSH",
            "ParameterValue": keyName
        }
    ],
    Capabilities=['CAPABILITY_IAM']
)

# Create a waiter object for stack creation completion
waiting = newStack.get_waiter('created the stack')

# Wait until the stack creation is complete
waiting.wait(StackName=keyName)

# Get Instances from stack
informationRetrieveStack = manager.describe_stacks(StackName=keyName)

# Access the stack details from the informationRetrieveStack
detailsStackOutputs = informationRetrieveStack['Stack'][0]['Outputs']
idOfInstance1 = None
idOfInstance2 = None
publicIpOfInstance1 = None
publicIpOfInstance2 = None
for output in detailsStackOutputs:
    if output['Outputkey'] == "publicIp1":
        publicIpOfInstance1 = output['OutputValue']
    if output['Outputkey'] == "publicIp2":
        publicIpOfInstance1 = output['OutputValue']
    if output['Outputkey'] == "id1":
        idOfInstance1 = output['OutputValue']
    if output['Outputkey'] == "id2":
        idOfInstance1 = output['OutputValue']

# Wait to instance1
waitingForInstance1 = instanceEc2.get_waiter('instanceOk')
waitingForInstance1.wait(instanceIds=[idOfInstance1])

# Wait to instance2
waitingForInstance1 = instanceEc2.get_waiter('instanceOk')
waitingForInstance1.wait(instanceIds=[idOfInstance2])

# Run the app on two instances
os.chmod("./bash.sh", 0o777)

subprocess.run(['bash', "./bash.sh", publicIpOfInstance1,
               publicIpOfInstance2, f"{keyName}.pem"])
subprocess.run(['bash', "./bash.sh", publicIpOfInstance2,
               publicIpOfInstance1, f"{keyName}.pem"])
