# Needed modules will be imported and configured
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
# Declaration of the break between the changes of the relay status (in seconds)
delayTime = 1

# Declaration of the input pin which is connected with the sensor. Additional to that, the pullup resistor will be activated.
RELAIS_PIN = 10
GPIO.setup(RELAIS_PIN, GPIO.OUT)
GPIO.output(RELAIS_PIN, False)

print "Sensor-test [press ctrl+c to end]"


# Main program loop
try:
        while True:
            GPIO.output(RELAIS_PIN, True) # NO is now connected through
            time.sleep(delayTime)
            GPIO.output(RELAIS_PIN, False) # NC is now connected through
            time.sleep(delayTime)

# Scavenging work after the end of the program
except KeyboardInterrupt:
        GPIO.cleanup()
