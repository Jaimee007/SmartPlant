# coding=utf-8
# needed modules will be imported and initialised
import glob
import time
from time import sleep
import RPi.GPIO as GPIO

# here you can modify the break between the measurements
sleeptime = 1

# the one-wire input pin will be declared and the integrated pullup-resistor will be enabled
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# After the enabling of the pullup-resistor you have to wait till the communication with the DS18B20 sensor has started
print 'wait for initialisation...'

base_dir = '/sys/bus/w1/devices/'
while True:
    try:
        device_folder = glob.glob(base_dir + '28*')[0]
        break
    except IndexError:
        sleep(0.5)
        continue
device_file = device_folder + '/w1_slave'


# The function to read currently measurement at the sensor will be defined.
def TemperatureMeasure():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

# To initialise, the sensor will be read "blind"
TemperatureMeasure()

# Analysis of temperature: At the Raspberry Pi
# noticed one-wire slaves at the directory /sys/bus/w1/devices/
# will be assigned to a own subfolder.
# In this folder is the file in which the data from the one-wire bus will be saved.<br /># In this function, the data will be analyzed, the temperature read and returned to the main program.<br />
def TemperatureAnalysis():
    lines = TemperatureMeasure()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = TemperatureMeasure()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

# main program loop
# The measured temperature will be displayed via console, between the measurements is a break.
# The break time can be configured by the variable "sleeptime"
try:
    while True:
        print '---------------------------------------'
        print "Temperature:", TemperatureAnalysis(), "°C"
        time.sleep(sleeptime)

except KeyboardInterrupt:
    GPIO.cleanup()
