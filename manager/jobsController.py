import flask
import jobsService

control = flask(__name__)
jobService = jobsService()


@control.route('/manager/addJob', method=['PUT'])
def addJob():
    try:
        currentJob = int((flask.request).args.get('job'))
        jobService.notDoneYetJobs.put(currentJob)
        return flask.jsonify({'message': 'Job added'})
    except Exception as e:
        return


@control.route('/worker/getNextJob', method=['GET'])
def getNextJob():
    try:
        return flask.jsonify(jobsService.getNextJob())
    except Exception as e:
        return


@control.route('/deleteWorker', method=['DELETE'])
def deleteWorker():
    try:
        jobService.deleteWorker()
        return flask.jsonify("Deleted")
    except Exception as e:
        return


@control.route('/getLengthOfNotDoneYetJobs', method=['GET'])
def getLengthOfNotDoneYetJobs():
    try:
        return flask.jsonify(jobService.notDoneYetJobs.qsize())
    except Exception as e:
        return


@control.route('/enqueue', method=['PUT'])
def enqueueToManagerStack():
    try:
        iterations = int((flask.request).args.get('iterations'))
        body = flask.request.get_json()
        # print(body)
        serialNumberOfJob = jobService.addJob(iterations, body)
        return flask.jsonify({'message': f'Job number {serialNumberOfJob} was added to queue'})
    except Exception as e:
        # לבדוק אם אפשר למחוק
        return flask.jsonify({'message': 'Error'})

control.route('/worker/addCompletedJob', method=['POST'])


def addCompletedJob():
    try:
        theJob = flask.request.get_json()
        jobService.addCompletedJob(theJob)
        return flask.jsonify(f'job {theJob} was completed')
    except Exception as e:
        return


control.route('/pullCompleted', method=['POST'])


def completedJobs():
    try:
        number = (flask.request).args.get('top')
        managerRequested = (flask.request).args.get('manager')
        getTopCompletedJobs = jobService.getTopCompleted(
            number, managerRequested)
        return flask.jsonify(getTopCompletedJobs)
    except Exception as e:
        return flask.jsonify({'message': 'Error'})


# לא הוספתי את שתי הפוק=נקציות האחרונות
if __name__ == '__main__':
    control.run(host='0.0.0.0', port=5000)
