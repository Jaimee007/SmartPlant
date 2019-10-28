# coding=utf-8
# Needed modules will be imported and configured
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

# You can pick the input and output pins here
Trigger_OutputPin = 17
Echo_InputPin    = 27

# You can set the delay (in seconds) between the single measurements here
sleeptime = 0.8

# Here, the input and output pins will be configured
GPIO.setup(Trigger_OutputPin, GPIO.OUT)
GPIO.setup(Echo_InputPin, GPIO.IN)
GPIO.output(Trigger_OutputPin, False)

# Main program loop
try:
    while True:
        # Distance measurement will be started with a 10us long trigger signal
        GPIO.output(Trigger_OutputPin, True)
        time.sleep(0.00001)
        GPIO.output(Trigger_OutputPin, False)

        # The stop watch will start here
        Start_time = time.time()
        while GPIO.input(Echo_InputPin) == 0:
            Start_time = time.time() # The time will be saved till the signal is active

        while GPIO.input(Echo_InputPin) == 1:
            Finish_time = time.time() # The last time will be recorded in which the signal was active

        # The difference between the times gives the searched duration
        Duration_time = Finish_time - Start_time
        # With it you can calculate the distance which equals the v=e/t with the speed of sound and over 2 because it goes forth and back
        Distance = (Duration_time * 34300) / 2

        # Here you check if the measured value is in the permitted range
        if Distance < 2 or (round(Distance) > 300):
            # If not an error message will be shown
            print("Distance is not in the permitted range")
            print("------------------------------")
        else:
            # The value of the distance will be reduced to 2 numbers behind the comma
            Distance = format((Distance * 34300) / 2, '.2f')
            # The calculated distance will be shown at the terminal
            print("The distance is:"), Distance,("cm")
            print("------------------------------")

        # Break between the single measurements
        time.sleep(sleeptime)

# Scavenging work after the end of the program
except KeyboardInterrupt:
    GPIO.cleanup()
