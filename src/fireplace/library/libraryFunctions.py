# src/fireplace/library/libraryfunctions.py
from fireplace.utils.defines import *
import math

def to12hour(time):
    '''
    Returns time in 12-hour format without am/pm 

    >>> to12hour(14:05)
    '2:05'

    :param string: timeNow
    :return string: formatted current time, 12-hour format without am/pm
    '''
    hour = time.hour % 12 or 12
    return f"{hour}:{time.minute:02}"

def truncate(number, digits):
    '''
    Returns the number passed in truncated to the provided number of digits.

    >>> truncate(4.123, 1)
    '4.1'

    :param float: Input number, typically temperature
    :param int: Number of digits to truncate input number to
    :return float: Truncated input number
    '''
    stepper = pow(10.0, digits)
    return math.trunc(stepper * number) / stepper

def CtoF(tempInC):
    '''
    Converts celcius to farenheight temperature

    >>> to12hour(35)
    '95'

    :param float: Celcius temperature
    :return float: Farenheight temperature
    '''
    tempInF = 9.0/5.0 * tempInC + 32
    return tempInF