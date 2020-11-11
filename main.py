#!/usr/bin/python
import time
import time
import uuid
import socket
import requests
import json
import RPi.GPIO as GPIO
from random import randrange
from threading import Thread
import threading
from dateutil import parser
from datetime import datetime
from datetime import timedelta
from pytz import timezone

flag = False
deviceAid = 13
currentBrightness = 0
API_ENDPOINT = "http://localhost:51272/characteristics"
headers = {
    "authorization": "208-19-142",
    "Content-Type": "application/json"
}

ON_DATA = {
    "characteristics": [
        {
            "aid": deviceAid,
            "iid": 10,
            "value": True,
            "status": 0
        }
    ]
}
OFF_DATA = {
    "characteristics": [
        {
            "aid": deviceAid,
            "iid": 10,
            "value": False,
            "status": 0
        }
    ]
}

COORDINATES = {
    "Melbourne": {"lat":-37.799305,"lng":145.164842},
    "Sydney": {"lat":-33.8688,"lng":151.2093}
}

class Logic:
    def __init__(self):
        global flag
        print("Init....")
        # Here I use Pin 7 connect to OUTPUT of the sensor.
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(12, GPIO.IN)
        self._running = True
        self._mode = 1
        self.setBrightness(1,)
        flag = True

    def terminate(self):
        self._running = False

    def changeMode(self, mode):
        if self._mode == mode:
            return
        if mode == 1:
            self.on()
        elif mode == 2:
            self.forceOff()
        self._mode = mode

    def run(self, checkTimeEvent):
        trigger = 0
        try:
            while self._running:
                if (GPIO.input(12)):  # detect
                    trigger = trigger + 1
                    if (trigger > 5):
                        if self._mode == 1:
                            self.setBrightness(25,)
                        if self._mode == 2:
                            self.on()
                elif (trigger >= 35):
                    print('delay 3s')
                    time.sleep(3)
                    if self._mode == 1:
                        self.setBrightness(1,)
                    if self._mode == 2:
                        self.off()
                    trigger = 0
                else:
                    if self._mode == 1:
                        self.setBrightness(1,)
                    if self._mode == 2:
                        self.off()
                    trigger = 0
                time.sleep(0.1)
                checkTimeEvent.wait()
        except KeyboardInterrupt:  # capture the Ctrl+c， before it exit, I clean the GPIO
            print("Interrupt received.")
        finally:
            GPIO.cleanup()
            self.forceOff()  # focre off
            print("User abort.")
        return

    def on(self):
        global flag
        if flag == False:
            requests.put(
                url=API_ENDPOINT, data=json.dumps(ON_DATA), headers=headers)
            flag = True
        return

    def onWithColor(self):
        global flag
        if flag == False:
            requests.put(
                url=API_ENDPOINT, data=json.dumps(self.changeColor()), headers=headers)
            flag = True
        return

    def off(self):
        global flag
        if flag == True:
            requests.put(
                url=API_ENDPOINT, data=json.dumps(OFF_DATA), headers=headers)
            flag = False
        return

    def forceOff(self):
        global flag
        requests.put(
            url=API_ENDPOINT, data=json.dumps(OFF_DATA), headers=headers)
        flag = False
        return

    def setBrightness(self, value):
        global currentBrightness
        global flag
        if value == currentBrightness:
            return
        currentBrightness = value
        brightness_DATA = {
            "characteristics": [
                {
                    "aid": deviceAid,
                    "iid": 11,
                    "value": value,
                    "status": 0
                }
            ]
        }
        requests.put(
            url=API_ENDPOINT, data=json.dumps(brightness_DATA), headers=headers)
        flag = True

    def changeColor(self):
        colorCoder = randrange(12) * 30
        Color_DATA = {
            "characteristics": [
                {
                    "aid": deviceAid,
                    "iid": 12,
                    "value": 100,
                    "status": 0
                },
                {
                    "aid": deviceAid,
                    "iid": 13,
                    "value": colorCoder,
                    "status": 0
                }
            ]
        }
        return Color_DATA


class Deamon:
    def __init__(self):
        self._running = True
        self.setKeyTimes()
        self.dailyReset = False
        
    def terminate(self):
        self._running = False

    def setKeyTimes(self):
        city = COORDINATES["Melbourne"]
        URL = f"https://api.sunrise-sunset.org/json?lat={city['lat']}&lng={city['lng']}&formatted=0"
        resp = requests.get(url = URL)
        data = resp.json()['results']

        self.localtz = timezone('Australia/Melbourne')
        self.onTime = parser.parse(
            data["sunset"]).astimezone(self.localtz).time()
        self.mode1Time = (parser.parse(
            data["solar_noon"]).astimezone(self.localtz)- timedelta(hours=12)).time()  # 00:00
        self.mode2Time = parser.parse(
            data["sunrise"]).astimezone(self.localtz).time()
        self.currentTime = datetime.now(tz=self.localtz).time()


    def run(self, checkTimeEvent):
        logic = Logic()
        logicThread = Thread(target=logic.run, args=(checkTimeEvent,))
        logicThread.start()

        print(f'[{ self.currentTime}] init: deamon is running')
        print(f'[{ self.currentTime}] init: midnight {self.mode1Time}')
        print(f'[{ self.currentTime}] init: sunrise time {self.mode2Time}')
        print(f'[{ self.currentTime}] init: sunset time {self.onTime}')
        try:
            while self._running:
                self.currentTime = datetime.now(tz=self.localtz).time()
                if self.currentTime > self.mode2Time and self.currentTime < self.onTime: # pause (day)
                    checkTimeEvent.clear()
                    print(f'[{ self.currentTime}] deamon: pausing logic')
                    requests.put(
                        url=API_ENDPOINT, data=json.dumps(OFF_DATA), headers=headers)  # focre off
                if self.currentTime > self.onTime: # night
                    if self.dailyReset == True:
                        self.dailyReset = False
                    logic.changeMode(1)
                    checkTimeEvent.set()
                    print(f'[{ self.currentTime}] deamon: now in mode 1 (brightness)')
                if self.currentTime < self.mode2Time and self.currentTime > self.mode1Time: # dawn
                    if self.dailyReset == False:
                        setKeyTimes() # update the times
                        self.dailyReset = True 
                    logic.changeMode(2)
                    checkTimeEvent.set()
                    print(f'[{ self.currentTime}] deamon: now in mode 2 (on/off)')
                time.sleep(600)
        except KeyboardInterrupt:
            print('stopping deamon')
            logic.terminate()
            checkTimeEvent.set()
            # Wait for actual termination
            logicThread.join()


def main():
    checkTimeEvent = threading.Event()
    deamon = Deamon()
    deamonThread = Thread(target=deamon.run, args=(checkTimeEvent,))
    deamonThread.run()
    return


if __name__ == "__main__":
    main()
