# src/fireplace/library/libraryfunctions.py
from fireplace.utils.defines import *
import math

def to12hour(time):
    # Returns a clean hour and leading zero min string without am or pm
    hour = time.hour
    minute = time.minute

    timeNow = ''

    # Correct for midnight and 24 hr time
    if hour == 0:
        hour = 12
    elif hour > 12:
        hour -= 12

    timeNow += str(hour) + ":"

    # Add leading zero to mins
    if minute < 10:
        timeNow += "0"

    timeNow += str(minute)

    return timeNow

def truncate(number, digits):
    # Multiply the number by the stepper to shift the digits, truncate to remove extra decimals,
    # then divide by the stepper to shift the digits back to their original position
    stepper = pow(10.0, digits)
    return math.trunc(stepper * number) / stepper

def CtoF(tempInC):
    tempInF = 9.0/5.0 * tempInC + 32
    return tempInF