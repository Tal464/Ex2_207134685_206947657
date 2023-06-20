import threading
import uuid
import os
import boto3
import requests
import datetime
import queue
import time


class jobsService():
    def __init__(self):
        self.numWorkers = 0
        self.numMaxWorkers = 2
        self.thisManagerIP = os.environ.get('MyIp')
        self.otherMangerIp = os.environ.get('OtherIp')
        self.notDoneYetJobs = queue.Queue()
        self.doneJobs = queue.Queue()
        threading.Thread(target=self.manageWorkers).start()
        self.settingUp = False

    def addJob(self, iterations, body):
        randomId = str(uuid.uuid4())
        thisJob = ({"id": randomId, "iterations": iterations, "body": body})
        try:
            otherMangerQueueLength = requests.get(
                f'http://{self.otherMangerIp}:5000/getLengthOfNotDoneYetJobs', timeout=7).json()
            if (self.notDoneYetJobs.qsize() > otherMangerQueueLength):
                requests.put(
                    f"http://{self.otherMangerIp}:5000/manager/addJob?job={thisJob}", timeout=7)
            else:
                self.notDoneYetJobs.put(thisJob)
        except Exception as e:
            self.notDoneYetJobs.put(thisJob)
        return randomId

    def getNextJob(self):
        if self.notDoneYetJobs.empty():
            return None
        else:
            return self.notDoneYetJobs.get()

    def deleteWorker(self):
        if self.worker > 0:
            self.workers -= 1
        return True

    def addCompletedJob(self, body):
        self.doneJobs.put(body)
        return True

    def setUpNewWorker(self):
        EC2_IP1 = os.environ.get("MY_IP")
        EC2_IP2 = os.environ.get("OTHER_IP")
        SECURITY_GROUP = os.environ.get("SECURITY_GROUP_ID")
        ec2 = boto3.client('ec2', region_name="us-east-1")
        theInstance = ec2.run_instances(
            ImageId="ami-042e8287309f5df03",
            InstanceType="t3.micro",
            SecurityGroups=[SECURITY_GROUP],
            InstanceInitiatedShutdownBehavior='terminate',
            MinCount=1,
            MaxCount=1,
            UserData=f'''#!/bin/bash
        sudo apt update -y
        sudo apt install -y python3
        sudo apt install -y python3-pip
        sudo apt install -y git
        echo "export EC2IP1={EC2_IP1}" | sudo tee -a /etc/environment
        echo "export EC2IP2={EC2_IP2}" | sudo tee -a /etc/environment
        echo "export WORKER_DELTA=6" | sudo tee -a /etc/environment
        source /etc/environment
        git clone https://github.com/Tal464/Ex2_207134685_206947657.git
        cd Ex2_207134685_206947657/Worker
        sudo chmod 777 app.py
        sudo chmod 777 shutDownEc2.sh
        sudo pip3 install boto3
        sudo pip3 install paramiko
        sudo python3 app.py
        ''',
        )
        print("EC2 created:", theInstance)
        instance_id = theInstance['Instances'][0]['InstanceId']
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        print(f'{instance_id} is running')

    def manageWorkers(self):
        while True:
            time.sleep(6)
            if (not self.settingUp) and (not self.notDoneYetJobs.empty()):
                currentJob = self.notDoneYetJobs.queue[0]
                if (self.numMaxWorkers > self.numWorkers):
                    try:
                        self.numWorkers += 1
                        self.settingUp = True
                        self.setUpNewWorker()
                    except Exception as e:
                        self.numWorkers -= 1
                        self.settingUp = False

    def getTopCompleted(self,  number, managerRequested):
        jobsToShow = []
        while number > 0 and self.doneJobs.qsize():
            currentJob = self.doneJobs.get()["id"]
            jobsToShow.append(currentJob)
            number -= 1
        if number > 0 and managerRequested != 'manager':
            try:
                otherManager = requests.post(
                    f"http://{self.otherMangerIp}:5000/pullCompleted?top={number}&manager=manager", timeout=7).json()
                jobsToShow += otherManager
            except Exception as e:
                return jobsToShow
        return jobsToShow
