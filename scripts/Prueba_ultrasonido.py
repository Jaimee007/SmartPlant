# coding=utf-8
# Needed modules will be imported and configured
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
# You can pick the input and output pins here
Trigger_AusgangsPin = 17
Echo_EingangsPin = 27
# You can set the delay (in seconds) between the single measurements here
sleeptime = 0.8
# Here, the input and output pins will be configured
GPIO.setup(Trigger_AusgangsPin, GPIO.OUT)
GPIO.setup(Echo_EingangsPin, GPIO.IN)
GPIO.output(Trigger_AusgangsPin, False)
# Main program loop
try:
while True:
# Distance measurement will be started with a 10us long trigger signal
GPIO.output(Trigger_AusgangsPin, True)
time.sleep(0.00001)
GPIO.output(Trigger_AusgangsPin, False)
# The stop watch will start here
EinschaltZeit = time.time()
while GPIO.input(Echo_EingangsPin) == 0:
EinschaltZeit = time.time()
while GPIO.input(Echo_EingangsPin) == 1:
AusschaltZeit = time.time()
# The difference between the times gives the searched duration
Dauer = AusschaltZeit - EinschaltZeit
# With it you can calculate the distance
Abstand = (Dauer * 34300) / 2
# Here you check if the measured value is in the permitted range
if Abstand < 2 or (round(Abstand) > 300):
# If not an error message will be shown
print("Distance is not in the permitted range")
print("------------------------------")
else:
# The value of the distance will be reduced to 2 numbers behind the comma
Abstand = format((Dauer * 34300) / 2, '.2f')
# The calculated distance will be shown at the terminal
print("The distance is:"), Abstand,("cm")
print("------------------------------")
# Break between the single measurements
time.sleep(sleeptime)
# Scavenging work after the end of the program
except KeyboardInterrupt:
GPIO.cleanup()
