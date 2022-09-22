#!/usr/bin/python

import os
import time

import httpx
import RPi.GPIO as GPIO

# So no randos can post to my site
API_KEY = os.getenv("GARAGE_API_KEY")
if not API_KEY:
    raise ValueError("GARAGE_API_KEY not set")

HOST = os.getenv("GARAGE_HOST")
if not HOST:
    raise ValueError("GARAGE_HOST not set")

PIN_TRIGGER = 7
PIN_ECHO = 11
GPIO.setmode(GPIO.BOARD)
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)
GPIO.output(PIN_TRIGGER, GPIO.LOW)

print("Waiting for sensor to settle")
time.sleep(3)

try:
    while True:
        GPIO.output(PIN_TRIGGER, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(PIN_TRIGGER, GPIO.LOW)

        while GPIO.input(PIN_ECHO) == 0:
            pulse_start_time = time.time()
        while GPIO.input(PIN_ECHO) == 1:
            pulse_end_time = time.time()

        pulse_duration = pulse_end_time - pulse_start_time
        distance = round((pulse_duration * 17150) / 2.54, 2)
        try:
            r = httpx.post(
                HOST,
                json={"message": distance},
                headers={"X-Api-Key": API_KEY}
            )
            print(f"OK: distance={distance} inches")
        except httpx.HTTPError as ex:
            print(ex)
            time.sleep(10)
        time.sleep(4)

finally:
    GPIO.cleanup()
