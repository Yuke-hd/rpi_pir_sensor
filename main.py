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

class Logic:
    def __init__(self): 
        self._running = True
        print("Init....")
        GPIO.setmode(GPIO.BOARD) # Here I use Pin 7 connect to OUTPUT of the sensor.
        GPIO.setwarnings(False)
        GPIO.setup(12, GPIO.IN)
        #self.off()
        #time.sleep(0.5)
        self.setBrightness(1,)
      
    def terminate(self): 
        self._running = False

    def run(self,checkTimeEvent):
        trigger = 0
        try:
            while self._running:
                if (GPIO.input(12)):
                    #print('detected')
                    trigger = trigger + 1
                    if (trigger > 5):
                        #print('movement detected')
                        self.setBrightness(25,)
                elif (trigger >= 35):
                    print('delay 3s')
                    time.sleep(3)
                    self.setBrightness(1,)
                    trigger = 0
                else:
                    #print('off')
                    self.setBrightness(1,)
                    trigger = 0
                time.sleep(0.1)
                checkTimeEvent.wait()
        except KeyboardInterrupt:  # capture the Ctrl+c， before it exit, I clean the GPIO
            print("Interrupt received.")
        finally:
            GPIO.cleanup()
            requests.put(
                url=API_ENDPOINT, data=json.dumps(OFF_DATA), headers=headers) # focre off
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

    def setBrightness(self, value):
        global currentBrightness
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
        localtz = timezone('Australia/Melbourne')
        self.onTime = parser.parse("18:00:00+10:00").astimezone(localtz).time()
        self.offTime = parser.parse("2:00:00+10:00").astimezone(localtz).time()
        self.currentTime = datetime.now(tz = localtz).time()

    def terminate(self): 
        self._running = False

    def run(self,checkTimeEvent):
        logic = Logic()
        logicThread = Thread(target = logic.run,args=(checkTimeEvent,)) 
        logicThread.start() 

        print('deamon is running')
        print(self.currentTime)
        print(self.offTime)
        print(self.onTime)
        try:
            while self._running:
                if self.currentTime > self.offTime and self.currentTime < self.onTime:
                    checkTimeEvent.clear()
                    print('deamon: pausing logic')
                if self.currentTime < self.offTime or self.currentTime > self.onTime:
                    checkTimeEvent.set()
                    print('deamon: resuming logic')
                time.sleep(36000)
        except KeyboardInterrupt:
            print('stopping deamon')
            logic.terminate()
            checkTimeEvent.set()
            # Wait for actual termination 
            logicThread.join()  

def main():
    checkTimeEvent = threading.Event()
    deamon = Deamon()
    deamonThread = Thread(target = deamon.run,args=(checkTimeEvent,))
    deamonThread.run()
    return


if __name__ == "__main__":
    main()

