import requests
import os
import hashlib
import time
import subprocess


def provideJobs():
    ec2Ip1 = os.environ.get("IpOfFirstEc2")
    ec2Ip2 = os.environ.get("IpOfSecondEc2")
    timeToWait = 10
    numberOfJobRequests = 0

    while True:
        if numberOfJobRequests > 7:
            os.chmod("./shutDownEc2.sh", 0o111)
            subprocess.run(['bash', './shutDownEc2.sh'])
        time.sleep(timeToWait)
        numberOfJobRequests += 1
        manager1 = tryGettingQueueLength(ec2Ip1)
        manager2 = tryGettingQueueLength(ec2Ip2)
        if manager1 > manager2:
            workingManager = ec2Ip1
            notWorkingManager = ec2Ip2
        else:
            workingManager = ec2Ip2
            notWorkingManager = ec2Ip1
        try:
            jobDone = requests.get(
                f'http://{workingManager}:5000/worker/job', timeout=8).json()
        except Exception as e:
            continue
        if jobDone != None:
            result = work(jobDone["data"], jobDone["iterations"])
            jobDone["data"] = str(result)
            # לא עשינו סנדינג פיניש
            numberOfJobRequests = 0

# getting queue length to decide


def tryGettingQueueLength(ip):
    try:
        length = requests.get(
            f"http://{ip}:5000/length", timeout=3).json()
    except Exception as e:
        length = 0
    return length

# the job a worker does


def work(data, iterations):
    output = hashlib.sha512(data.encode()).digest()
    for i in range(iterations - 1):
        output = hashlib.sha512(output).digest()
    return str(output)

# לא עשינו להודיע למנג'ר


if __name__ == '__main__':
    provideJobs()
