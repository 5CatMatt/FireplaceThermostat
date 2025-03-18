import RPi.GPIO as GPIO

# PIR sensor
GPIO.setmode(GPIO.BCM)
motionSensorPin = 18
GPIO.setup(motionSensorPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Backlight auto dim settings, fade in and out as well as power on/off
motionCounter = 0
turnOffBacklightAfter = 100
backlightBrightness = 42
backlightFadeOutTime = 2.5
backlightFadeInTime = 1.5

homeAssistantLightStatus = False

from rpi_backlight import Backlight
backlight = Backlight()

while True:
    motionStatus = GPIO.input(motionSensorPin)


    if (motionStatus):
        print(f'true: {motionStatus}')
    else:
        print(f'false: {motionStatus}')

    user_input = input("Enter '0' to turn lights off, '1' to turn lights on, or 'q' to quit: ")

    if user_input == '0':
        backlight.brightness = 0
    elif user_input == '1':
        backlight.brightness = backlightBrightness
    elif user_input.lower() == 'q':
        print("Exiting program.")
        break
    else:
        print("Invalid input. Please enter '0', '1', or 'q'.")