from flask import Flask, request, jsonify
from datetime import datetime
from parkingLot import ParkingLotManager

app = Flask(__name__)

parkingLotManager = ParkingLotManager()


@app.route('/entry', methods=['POST'])
def entry():
    currentParkingLotId = request.args.get('parkingLot')
    currentLicensePlate = request.args.get('plate')
    if parkingLotManager.checkIfCarExistInParkingLot(currentLicensePlate):
        return jsonify({'error': f'car with plate number {currentLicensePlate} is already in a parking lot- '
                                 f'please try again!'})
    entryTime = datetime.now()
    return jsonify(parkingLotManager.addCarToParkingLot(currentParkingLotId, currentLicensePlate, entryTime))


@app.route('/exit', methods=['POST'])
def exit():
    carToExitParkingLot = request.args.get('ticketId')
    return jsonify(parkingLotManager.removeCarFromParkingLot(carToExitParkingLot))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
