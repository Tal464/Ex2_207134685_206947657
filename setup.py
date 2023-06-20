import os
import uuid
import requests
import boto3
import paramiko

# Create a new EC2 in specific region
region = 'us-east-1'
print(f"Sets region {region}")
# Generates a random UUID
endOfKeyName = str(uuid.uuid4())

# Start of key name
keyName = 'cloud-course-ex2-' + endOfKeyName
print(f"Generates a random UUID {endOfKeyName}")
print(f"So key and stack name is {keyName}")

# Create clients
manager = boto3.client('cloudformation', region_name=region)
instanceEc2 = boto3.client('ec2', region_name=region)

# Create and get a key pair
print('Creates and get a key pair')
newKeyPair = instanceEc2.create_key_pair(KeyName=keyName)
keyMaterial = newKeyPair['KeyMaterial']
print(f"key materials: {keyMaterial}")

# create .pem files for ec2s
with open(f'{keyName}.pem', 'w') as f:
    f.write(keyMaterial)
os.chmod(f'{keyName}.pem', 0o400)

print(".pem file created for RSA")

with open('managerTemplate.yaml', 'r') as file:
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

print(f"This is the stack : {newStack}")

print("Stack creation")
# Create a waiter object for stack creation completion
waiting = manager.get_waiter('stack_create_complete')

# Wait until the stack creation is complete
waiting.wait(StackName=keyName)
print("Stack was created")
# Get Instances from stack
informationRetrieveStack = manager.describe_stacks(StackName=keyName)

# Access the stack details from the informationRetrieveStack
detailsStackOutputs = informationRetrieveStack['Stacks'][0]['Outputs']
print(detailsStackOutputs)

idOfInstance1 = None
idOfInstance2 = None
publicIpOfInstance1 = None
publicIpOfInstance2 = None
for output in detailsStackOutputs:
    if output['OutputKey'] == "publicIp1":
        publicIpOfInstance1 = output['OutputValue']
    if output['OutputKey'] == "publicIp2":
        publicIpOfInstance2 = output['OutputValue']
    if output['OutputKey'] == "id1":
        idOfInstance1 = output['OutputValue']
    if output['OutputKey'] == "id2":
        idOfInstance2 = output['OutputValue']

print(f"publicIp1:{publicIpOfInstance1}, publicIp2:{publicIpOfInstance2}")
print(f"id1:{idOfInstance1}, id2:{idOfInstance2}")
print("Waiting for instances creation")
# Wait to instance1
waitingForInstance1 = instanceEc2.get_waiter('instance_status_ok')
waitingForInstance1.wait(InstanceIds=[idOfInstance1])

# Wait to instance2
waitingForInstance1 = instanceEc2.get_waiter('instance_status_ok')
waitingForInstance1.wait(InstanceIds=[idOfInstance2])
print("Instances created")

print("Waiting for our app to run on instances")
# Run the app on two instances
# Our friends bar and niv helped us with this function

keyForRunning = paramiko.RSAKey(filename=f"{keyName}.pem")
sshForInstances = paramiko.SSHClient()
sshForInstances.set_missing_host_key_policy(paramiko.AutoAddPolicy())

bash_commands = '''
    sudo apt install -y python3
    sudo apt install -y python3-pip
    echo "export OTHER_IP={other_ip}" | sudo tee -a /etc/environment
    echo "export MY_IP={instance_ip}" | sudo tee -a /etc/environment
    source /etc/environment
    git clone https://github.com/tal464/Ex2_207134685_206947657.git
    cd Ex2_207134685_206947657/Manager
    sudo chmod 777 app.py
    sudo pip3 install -r requirements.txt
    sudo nohup python3 app.py > flask.log 2>&1 &
'''

try:
    sshForInstances.connect(publicIpOfInstance1,
                            username='ubuntu', pkey=keyForRunning)
    _, stdout, _ = sshForInstances.exec_command(bash_commands.format(
        other_ip=publicIpOfInstance2, instance_ip=publicIpOfInstance1))

    output = stdout.read().decode()
    print(output)
except paramiko.AuthenticationException:
    print(f"failed to run on {publicIpOfInstance1}")
except paramiko.SSHException as e:
    print(f"failed to run on {publicIpOfInstance1}")
finally:
    sshForInstances.close()
    print(f"Server with IP: {publicIpOfInstance1} is ready to use")

try:
    sshForInstances.connect(publicIpOfInstance2,
                            username='ubuntu', pkey=keyForRunning)
    _, stdout, _ = sshForInstances.exec_command(bash_commands.format(
        other_ip=publicIpOfInstance1, instance_ip=publicIpOfInstance2))
    output = stdout.read().decode()
    print(output)
except paramiko.AuthenticationException:
    print(f"failed to run on {publicIpOfInstance2}")
except paramiko.SSHException as e:
    print(f"failed to run on {publicIpOfInstance2}")
finally:
    sshForInstances.close()
    print(f"Server with IP: {publicIpOfInstance2} is ready to use")

print(f"Instances ready on {publicIpOfInstance2}, {publicIpOfInstance1}")
