#!/usr/bin/python



import os

import datetime

from time import sleep

import RPi.GPIO as GPIO



GPIO.setmode(GPIO.BCM)



def RCtime (RCpin):

    reading = 0

    GPIO.setup(RCpin, GPIO.OUT)

    GPIO.output(RCpin, GPIO.LOW)

    sleep(.1)



    GPIO.setup(RCpin, GPIO.IN)

    # This takes about 1 millisecond per loop cycle

    while (GPIO.input(RCpin) == GPIO.LOW):

        reading += 1

    return reading



while True:

    GetDateTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    LDRReading = RCtime(26)

    print RCtime(26)


    sleep(1)
