# src/fireplace/main.py
# -*- coding: utf-8 -*-

'''
The infamous, maybe in-famous, fireplace thermostat; first doc found = early 2018

not a fireplace, nor a thermostat... yet

requirements.this.project.was.done.without.requiremnts.IMPORTANT
    Thermostat:
        - Control a relay to turn on and off an actual gas fireplace in a house
            - Use thermostat logic with feedback loop and hysterisis
            - Expose thermostat controls to home assistant
            - Don't cause a hazard, and mean it
        - Gain weather data from and external API
            - Maybe use this to alter thermostat behavior
            - Current solution is Open Weather Map
        - Learn and transmit IR signals for control of nearby devices
        - Sense user proximity for power consumption and interactive activites
        - Sense temperature, and why not humidity
    Fireplace:
        Well prety much anything can be one and some of the best laid plans became
        one on accident. Current solution is a gas fireplace which simply needs a
        short between two conductors to activate.

Hardware:
Pi 3 B+
7" Pi LCD with touch
SHT41 temperature and humidity sensor
PIR motion sensor for occupancy
9960 light sensor for gesture and light
IR sense and transmit 

The display backlight controls have gone through many changes over the years
it is simple to dim the display, for now, but the touch events remain active.
In inital tests I would check the LCD for heat with my whole hand and there 
are some bonkers events going on via VNC. It would be nice to stop all events.

Low power state(ish) can be done by stopping the pygame updates but the button 
functions should be halted as well in code. TODO investigate actually quitting 
pygame for low power. I worry the startup time will be annoying but it is too 
soon to tell in dev.

The home screen desktop system can be a bit annoying. I added a few more and
the static code is difficult to update. If more screens are to be added in the
future a refactor is in order. Generating a save file and a dynamic element
posistioning method is somewhat straigtforeward. 

TODO Some functions have proper comment structure, many do not.
TODO Investigate includes, some may be unused
TODO The OOP pattern used to display pages may benefit from a refactor

'''

import pygame

from fireplace.library.libraryFunctions import *
from fireplace.utils.defines import *
from fireplace.utils.keys import *

from homeassistant_api.models.domains import Domain

import os
import os.path

import paho.mqtt.client as mqtt

displayStartPosistionX = 0
displayStartPosistionY = 0
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d, %d" % (displayStartPosistionX, displayStartPosistionY)

imgPath, imgDirs, imgFiles = next(os.walk(BACKGROUNDS_DIR))
imgFileCnt = len(imgFiles)

iconPath, iconDirs, iconFiles = next(os.walk(WEATHER_ICONS_DIR))

import RPi.GPIO as GPIO

import ast

from itertools import count

import json

import requests
import pandas as pd
apiKey = WEATHER_API_KEY

import io
import time
from datetime import datetime
import schedule

# temp and hum sensor - SHT41 - i2c
import adafruit_sht4x
import board
i2c = board.I2C()
sht = adafruit_sht4x.SHT4x(i2c)
sht.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

# Initialize gesture detection - APDS9960 sensor - i2c 
from adafruit_apds9960.apds9960 import APDS9960
import digitalio

int_pin = digitalio.DigitalInOut(board.D5)
int_pin.switch_to_input(pull=digitalio.Pull.UP)
apds = APDS9960(i2c)

apds.enable_proximity = True
apds.enable_gesture = True

# Broadcom naming convention for GIPO pins
GPIO.setmode(GPIO.BCM)

# PIR sensor
motionSensorPin = 18
GPIO.setup(motionSensorPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# Fireplace control pin - PWM provides "heartbeat" to relay controller, lower frequecies are more stable
fireplaceControlPin = 19
lowFireplaceFrequecy = 75
highFireplaceFrequecy = 250
currentFireplaceFrequecy = lowFireplaceFrequecy
fireplaceRelayClosed = True

# This PWM method is much more accurate but requires an annoying sudo pigpiod command in the virtual environment
# import pigpio
# pi = pigpio.pi()
# pi.hardware_PWM(fireplaceControlPin, 250, 500000)  # 250Hz, 50% duty

GPIO.setup(fireplaceControlPin, GPIO.OUT)
fireplaceOutput = GPIO.PWM(fireplaceControlPin, currentFireplaceFrequecy)
fireplaceOutput.start(50)

# Backlight auto dim settings, fade in and out as well as power on/off
motionCounter = 0
turnOffBacklightAfter = 100
backlightBrightness = 42
backlightFadeOutTime = 2.5
backlightFadeInTime = 1.5

homeAssistantLightStatus = False

from rpi_backlight import Backlight
backlight = Backlight()

backlight.power = False
backlight.brightness = 0

pygame.init()
pygame.font.init()
pygame.mixer.quit()

pygame.display.set_caption("Fireplace")

pygame.mouse.set_cursor(*pygame.cursors.broken_x)
pygame.mouse.set_visible(False)

screenSize = width, height = 800, 480

# You can get trapped in full screen pygame, also useful items for testing and debugging go here
if DEVELOPER_MODE:
    screen = pygame.display.set_mode(screenSize)
    motionCounterResetValue = 300000
else:
    screen = pygame.display.set_mode(screenSize, pygame.FULLSCREEN)
    motionCounterResetValue = 300000

fonts = {
    "entryFont": pygame.font.Font(None, 40),    # TODO - this speeds up application launch significantly and I don't remeber why

    "tempFont": pygame.font.SysFont("DroidSansFallbackFull", 30),
    "jsonFont": pygame.font.SysFont('DroidSansFallbackFull', 38),
    
    "smallText": pygame.font.Font("freesansbold.ttf", 15),
    "medText": pygame.font.Font("freesansbold.ttf", 42),
    "largeText": pygame.font.Font("freesansbold.ttf", 48),

    "fontCen120": pygame.font.Font(FONTS_DIR + "/Century Gothic.ttf", 120),
    "fontCen80": pygame.font.Font(FONTS_DIR + "/Century Gothic.ttf", 80),
    "fontCen60": pygame.font.Font(FONTS_DIR + "/Century Gothic.ttf", 60),
    "fontCen48": pygame.font.Font(FONTS_DIR + "/Century Gothic.ttf", 48),
    "fontCen40": pygame.font.Font(FONTS_DIR + "/Century Gothic.ttf", 40),
    "fontCen32": pygame.font.Font(FONTS_DIR + "/Century Gothic.ttf", 32),
    "fontCen28": pygame.font.Font(FONTS_DIR + "/Century Gothic.ttf", 28),
    "fontCen18": pygame.font.Font(FONTS_DIR + "/Century Gothic.ttf", 18)
}

data = {
    "time": None,
    "date": None,
    "dayLong": None,
    "dayShort": None,
    "downstairs": 69,
    "outside": 69,
    "humidity": None
}

colors = COLORS

from homeassistant_api import Client

# Connect to the home assistant API and get all of the office lights, we can iterate through each service in a domain
client = Client(HOME_ASSISTANT_URL, HOME_ASSISTANT_API_KEY)
service = client.get_domain("light")

# Conditions are sent in 3 hour packs, this ranks them by severity and selects the most severe weather icon for the day
weatherConditionImportance = WEATHER_CONDITION_IMPORTANCE
iconFilenames = ICON_FILE_NAMES

# Index to track the active home screen background which drives the element layout
currentDesktopIndex = 0

screen.fill(colors["palLtBlue"])
pygame.display.update()

# Home screen element layout settings for each background image
layoutFile = PROJECT_ROOT + "/layoutHomeScreen.json"

fireOn = pygame.image.load(PROJECT_ROOT + '/Images/fireOn.png').convert_alpha()
fireOff = pygame.image.load(PROJECT_ROOT + '/Images/fireOff.png').convert_alpha()

def toggleFireplaceHeartbeat():
    '''
    Toggle between two PWM output frequencies when fireplace relay (N.O.) should be closed at 50% duty cycle.
    This runs via schedual currently set at 1 second.

    Manipulates the global currentFireplaceFrequecy

    >>> toggleFireplaceHeartbeat()
    if higher frequecy is defined, switch to lower and vise versa
    if the relay should be deactivated, stop PWM output
    '''
    global currentFireplaceFrequecy
    
    # 
    if fireplaceRelayClosed:
        if currentFireplaceFrequecy == lowFireplaceFrequecy:
            currentFireplaceFrequecy = highFireplaceFrequecy
        else:
            currentFireplaceFrequecy = lowFireplaceFrequecy

        fireplaceOutput.ChangeFrequency(currentFireplaceFrequecy)

    else:
        fireplaceOutput.stop()

def switchDesktop(target):
    """Update the active desktop to the target desktop."""
    activeScreen.update(target)

def read_gesture_safely(retries=3):
    '''
    Pulled from chat, this might be helpful if the lockups continue, they are happening in C not Python

    Added 4.7k resistors to the SDA and SCL lines which also long dupont jumpers, hardware might be the fault
    '''
    for _ in range(retries):
        try:
            return apds.gesture()
        except OSError as e:
            print("Gesture I2C error:", e)
            time.sleep(0.1)
    return 0

def handleGesture():
    '''
    APDS 9960 light sensor via i2c. Can be set to trigger on proximity, light,
    color, and gesture.

    if gesture == 1:
        print("up")
    if gesture == 2:
        print("down")
    if gesture == 3:
        print("left")
    if gesture == 4:
        print("right")

    TODO this changes a global to switch desktops, refactor for return values

    '''
    global currentDesktopIndex

    try:
        gesture = apds.gesture()
    except:
        gesture = 0
        print("i2c device error, gesture sensor (APDS 9960) not responding.")

    if gesture == 3:  # Left swipe
        currentDesktopIndex = (currentDesktopIndex + 1) % len(desktops)
        switchDesktop(desktops[currentDesktopIndex])
    elif gesture == 4:  # Right swipe
        currentDesktopIndex = (currentDesktopIndex - 1) % len(desktops)
        switchDesktop(desktops[currentDesktopIndex])

def textHandler(text, font, color):
    '''
    Simple text display function which returns the size of the text object

    >>> textSurf, textRect = textHandler("Text to display", fonts["fontCen18"], colors["palBlue"])
    Display text and return text object size

    :param string: Text displayed
    :param font: Pygame font
    :param tuple: RGB color
    '''
    textSurface = font.render(text, True, color)
    return textSurface, textSurface.get_rect()

def waitForLiftup():
    holdIt = True
    while holdIt:
        ev = pygame.event.get()
        for event in ev:
            if event.type == pygame.MOUSEBUTTONUP:
                holdIt = False

def button(butText: str, butFont: pygame.font.Font, butTextColor: tuple, butColor,  butX: int, butY: int, butW: int, butH: int, action: str):
    '''
    Creates a pygame rectangular button and handles the touch/click logic as well as button action. 

    >>> button("Reload", fonts["fontCen18"], colors["palBlack"], colors["palBlue"], 580, 325, 80, 40, "reload")
    Display a Reload button and assign the reload action

    :param string: Text displayed on the button, centered X and Y. No handing for text string larger than button outline.
    :param font: Pygame font
    :param tuple: RGB color
    :param int: Button X posistion
    :param int: Button Y posistion
    :param int: Button width
    :param int: Button height
    :param string: Button action defined inside this function
    '''
    global currentDesktopIndex

    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
  
    # do all them button handling
    if butX + butW > mouse[0] > butX and butY + butH > mouse[1] > butY:

        # tab menu
        if click[0] == 1 and action == "quit":
            backlight.brightness = 0
            client.loop_stop()
            client.disconnect()
            GPIO.cleanup()
            pygame.quit()
            quit()

        if click[0] == 1 and action == "fire":
            pass

        if click[0] == 1 and action == "weather":
            activeScreen.update(weatherBG)

        if click[0] == 1 and action == "settings":
            activeScreen.update(settingsBG)

        # settings page buttons
        if click[0] == 1 and action == "setDesktop":
            print(settingsBG.selectedThumb)
            switchDesktop(settingsBG.selectedThumb)

        if click[0] == 1 and action == "backHome":
            switchDesktop(activeScreen.lastDesktop)
            waitForLiftup()

        # Used for page reload when working on layout json
        if click[0] == 1 and action == "reload":
            reloadLayoutData()
            switchDesktop(desktops[currentDesktopIndex])
              
    pygame.draw.rect(screen, butColor, (butX, butY, butW, butH), 0)
    textSurf, textRect = textHandler(butText, butFont, butTextColor)
    textRect.center = ((butX + (butW / 2)), (butY + (butH / 2)) )
    screen.blit(textSurf, textRect)

def textPrint(font, text, color, x, y):
    textSurface = []
    textSurface = font.render(text, True, color)
    textWidth = textSurface.get_width()
    textHeight = textSurface.get_height()
    screen.blit(textSurface, (x, y))

    return textWidth, textHeight

class dateTimeNow():
    def __init__(self):
        now = datetime.today()     
        self.timeNow = to12hour(now)
        self.dateNow = now.strftime("%b %d")
        self.dayLong = now.strftime("%A")
        self.dayShort = now.strftime("%a")

    def update(self):
        now = datetime.today()  
        self.timeNow = to12hour(now)        
        self.dateNow = now.strftime("%b %d")
        self.dayLong = now.strftime("%A")
        self.dayShort = now.strftime("%a")

        publishMQTT(client, timeTopic, self.timeNow)
        publishMQTT(client, longDayTopic, self.dayLong)
        publishMQTT(client, shortDayTopic, self.dayShort)

class currentTemp():
    def __init__(self):
        self.temperature, self.humidity = (round(value, 1) for value in sht.measurements)

    def update(self):
        self.temperature, self.humidity = (round(value, 1) for value in sht.measurements)
        self.temperature = truncate(CtoF(self.temperature), 1)
        publishMQTT(client, downstairsTempTopic, self.temperature)

def coordAssignment(xType, yType, yOffsetVal, selfWidth, selfHeight, refX, refY, refWidth, refHeight) :
    try:
        # x coords
        if xType == 'center' :
            X = (refWidth / 2) + refX - (selfWidth / 2)
        elif xType == 'right' :
            X = (refWidth) + refX - (selfWidth)
        elif xType == 'left' :
            X = refX
        # y coords
        if yType == 'bottom' :
            Y = refHeight + refY + yOffsetVal
        elif yType == 'top' :
            Y = refY - selfHeight + yOffsetVal
        elif yType == 'middle' :
            Y = refY - ((selfHeight / 2) + yOffsetVal)
    except:
        X, Y = 0, 0 # the first pass will inject a list from the json file and correct itself afterwards

    return X, Y

def thumbAssign(classIn):
    settingsBG.activeThumbnail = pygame.transform.scale(eval(classIn).backgroundImage, (133, 80))
    settingsBG.selectedThumb = eval(classIn)

def desktopPick(butText, butFont, butTextColor, butColor, butX, butY, butW, butH, butL, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if butX + butW > mouse[0] > butX and butY + butH > mouse[1] > butY:

        if click[0] == 1:
            thumbAssign(action)

    else:
        pygame.draw.rect(screen, butColor, (butX, butY, butW, butH), 0)

    pygame.draw.rect(screen, butColor, (butX, butY, butW, butH), 0)
    textSurf, textRect = textHandler(butText, butFont, butTextColor)
    textRect.center = ( (butX + (butW / 2)), (butY + (butH / 2)) )
    screen.blit(textSurf, textRect)

def headerPrint():
    tempSurface = fonts["fontCen40"].render(str(data["outside"]), True, colors["palWhite"])
    timeSurface = fonts["fontCen40"].render(str(data["time"]), True, colors["palDarkSlateGray"])

    tempWidth = tempSurface.get_width()

    elementPaddingX = 10
    elementPaddingY = 10

    screen.blit(tempSurface, ((screenSize[0] - (tempWidth + elementPaddingX)),
                               elementPaddingY))
    
    screen.blit(timeSurface, (elementPaddingX, 
                              elementPaddingY))

def weekdayCalc(day: int) -> str:
    '''
    Depricated - proper datetime objects don't need this. This was brought over from the 
    original C++ version, python didn't have a switch alt back then.

    Returns a long form string representing the day of the week. Zero indexed so be careful.  

    >>> day_of_week(0)
    Monday
    >>> day_of_week(6)
    Sunday

    :param integer: day of week expressed as a zero indexed int
    :type: 
    :return string: long form day of week
    :rtype:
    '''

    if not isinstance(day, int) or (day < 0 or day > 6):
        raise TypeError(f'Only integers from 0-6 allowed')

    if day == 0:
        dayName = 'Monday'
    if day == 1:
        dayName = 'Tuesday'
    if day == 2:
        dayName = 'Wednesday'
    if day == 3:
        dayName = 'Thursday'
    if day == 4:
        dayName = 'Friday'
    if day == 5:
        dayName = 'Saturday'
    if day == 6:
        dayName = 'Sunday'

    return dayName

def lightControl(service: Domain, onOff: str):                   
    '''
    Home Assistant light control. Will loop through all entities in the service and
    command them either on or off based on passed in string. A status bool is used
    to latch the state of the lights. Motion detection fires multiple times and can
    flood the network with home assistant data.

    >>> day_of_week(homeassistant_api.models.domains.Domain, 'on')
    All entites switched on
    >>> day_of_week(homeassistant_api.models.domains.Domain, 'off')
    All entites switched off

    :param domain: Home Assistant light control service
    :param string: Pass either 'on' or 'off' to toggle lights
    '''

    lightControlEnabled = True # Simple switch to turn off light control

    if not lightControlEnabled:
        return
    
    global homeAssistantLightStatus

    if onOff == homeAssistantLightStatus:   # No change, do nothing
        return  
    
    homeAssistantLightStatus = onOff    # Update to current state

    try:
        for entity in entities:
            if (onOff == 'on'):
                service.turn_on(entity_id = entity)

            if (onOff == 'off'):
                service.turn_off(entity_id = entity)

    except Exception as e:
            print(f"Error controlling home assistant entity {entity}: {e}")

def backlightController():
    '''
    Run this periodically to check the status of the motion sensor. If motion is
    detected the backlight will turn on, then back off when no motion is detected
    for a delay based on turnOffBacklightAfter and motionCounter. 
    '''
    global motionCounter

    motionStatus = GPIO.input(motionSensorPin)

    # Debug
    # print(motionCounter)
    # print(f"Status of GPIO{motionSensorPin}: {'HIGH' if motionStatus else 'LOW'}")

    if (motionStatus):
        motionCounter = 0
        backlight.power = True

        # This will stop code blocking, motion is true often
        if (backlight.brightness == 0):
            with backlight.fade(duration = backlightFadeInTime):
                backlight.brightness = backlightBrightness
        
    else:
        motionCounter += 1
        if (motionCounter >= turnOffBacklightAfter):
            with backlight.fade(duration = backlightFadeOutTime):
                backlight.brightness = 0

            backlight.power = False    

        # Keep the counter under control a bit
        if (motionCounter >= motionCounterResetValue):
            motionCounter = turnOffBacklightAfter

class getCurrentWeather():
    def __init__(self):
        # Call current weather data 
        currentURL = 'https://api.openweathermap.org/data/2.5/weather?zip=80109&units=imperial&appid='

        self.weatherURL = currentURL + apiKey

        self.temperatue = None
        self.humidity = None

    def update(self):
        try:
            response = requests.get(self.weatherURL)
        except:
            print("getCurrentWeather responce failed")

        if response.status_code == 200:  # Success
            data = response.json()

            # Extract and round temperature and humidity
            self.temperatue = round(data['main']['temp'])
            self.humidity = round(data['main']['humidity'])

            self.currentData = pd.json_normalize(data['main'])
            self.currentData.to_csv("current_weather_data.csv", index=False)

            publishMQTT(client, outsideTempTopic, self.temperatue)

class getWeatherForecast():
    def __init__(self):
        # Call 5 day / 3 hour forecast data
        forecastURL = 'http://api.openweathermap.org/data/2.5/forecast?zip=80109&units=imperial&appid='
        
        self.weatherURL = forecastURL + apiKey

        self.currentWeatherData = pd.DataFrame(columns=[
            'day_of_month', 'min_temp', 'max_temp', 'total_snow_inches',
            'weather_main', 'weather_icon', 'weather_description', 'day_of_week'
        ])

        self.iconCache = self.loadIcons()  # Load weather condition icons

    def loadIcons(self):
        iconCache = {}

        for filename in iconFilenames:
            iconPath = f"{WEATHER_ICONS_DIR}/{filename}"
            
            try:
                iconCache[filename] = pygame.image.load(iconPath).convert_alpha()
            except FileNotFoundError:
                print(f"Icon file not found: {iconPath}")
            except Exception as e:
                print(f"Error loading icon {filename}: {e}")

        return iconCache

    def update(self):
        try:
            response = requests.get(self.weatherURL)
        except:
            print("getWeatherForecast responce failed")

        if response.status_code == 200:  # Success
            data = response.json()

            weatherData = pd.json_normalize(data['list'])

            # Convert to datetime and extract relevant date components
            weatherData['dt_txt'] = pd.to_datetime(weatherData['dt_txt'])
            weatherData['day_of_month'] = weatherData['dt_txt'].dt.day
            weatherData['day_of_week'] = weatherData['dt_txt'].dt.day_name()
            weatherData['date'] = weatherData['dt_txt'].dt.date  # Add a full date column for sorting

            # Extract relevant data from the 'weather' column
            weatherData['weather_main'] = weatherData['weather'].apply(lambda x: x[0]['main'])
            weatherData['weather_description'] = weatherData['weather'].apply(lambda x: x[0]['description'])
            weatherData['weather_icon'] = weatherData['weather'].apply(lambda x: x[0]['icon'])
            try:
                weatherData['snow_inches'] = weatherData['snow.3h'] * 0.0393701  # Convert to inches
            except:
                weatherData['snow_inches'] = 0

            # Get the most important weather condition for the day to drive the condition icon
            weatherData['importance'] = weatherData['weather_description'].map(
                lambda x: weatherConditionImportance[x]['importance'] if x in weatherConditionImportance else 0)
            
            # Group by full date to ensure correct sorting across months
            dailyWeather = weatherData.loc[
                weatherData.groupby('date')['importance'].idxmax()][
                    ['date', 'day_of_month', 'weather_main', 'weather_icon', 'weather_description']]

            weatherData.drop(labels=['dt', 'dt_txt', 'weather', 'visibility', 'pop', 'main.temp', 'main.feels_like',
                                    'main.pressure', 'main.sea_level', 'main.grnd_level', 'main.humidity',
                                    'main.temp_kf', 'clouds.all', 'wind.speed', 'wind.deg', 'sys.pod'], axis=1, inplace=True)
            
            # Store min and max temp for each day
            dailyTemps = weatherData.groupby('date').agg(
                dailyMinTemp=('main.temp_min', 'min'),
                dailyMaxTemp=('main.temp_max', 'max'),
                total_snow_inches=('snow_inches', 'sum')
            ).reset_index()

            # Merge temperature and weather data
            self.fullWeatherData = pd.merge(dailyWeather, dailyTemps, on='date', how='left')

            # Add day of the week to the final data
            self.fullWeatherData['day_of_week'] = self.fullWeatherData['date'].map(
                weatherData.set_index('date')['day_of_week'].to_dict()
            )
            
            # Sort the final data by date to ensure correct order
            self.fullWeatherData = self.fullWeatherData.sort_values(by='date').reset_index(drop=True)

            # Debug
            # Save the final data to a file
            self.fullWeatherData.to_csv("final_weather_data.csv", index=False)

            # Convert date objects to strings for JSON serialization
            weatherData['date'] = weatherData['date'].astype(str)  # Convert date to string
            self.fullWeatherData['date'] = self.fullWeatherData['date'].astype(str)  # Convert date to string

            # Testing DataFrame
            weatherDataJson = weatherData.to_dict(orient='records')
            formattedJson = json.dumps(weatherDataJson, indent=4)
            with open("WeatherOutput.txt", "w") as file:
                file.write(formattedJson)

class screenWeather():
    def __init__(self):
        self.backgroundImage = pygame.image.load(BACKGROUNDS_DIR + '/weatherBG.png').convert()
        self.tempSurface = []

    def update(self):
        screen.blit(self.backgroundImage, (0, 0))

        headerPrint()

        containerCenter = [100 , 250, 399, 547, 694]
        dayName_Y = 72
        weatherIcon_Y = 100
        mainCondition_Y = 180
        highTemp_Y = 220
        lowTemp_Y = 280
        weatherDesc_Y = 369
        
        # This will go out of range late in the day as a sixth day will start showing up in the API response so slice it
        slicedWeatherData = weatherForecast.fullWeatherData.head(len(containerCenter))

        # Loop through the DataFrame from weatherForecast
        for index, row in slicedWeatherData.iterrows():
            try:
                # Days of the week text in each container
                daySurface = fonts["fontCen18"].render(f"{row['day_of_week']}", True, colors["palWhite"])
                dayWidth = daySurface.get_width()
                screen.blit(daySurface, (containerCenter[index] - (dayWidth / 2), dayName_Y))

                # Weather condition header
                mainConditionSurface = fonts["fontCen18"].render(f"{row['weather_main']}", True, colors["palWhite"])
                mainConditionWidth = mainConditionSurface.get_width()
                screen.blit(mainConditionSurface, (containerCenter[index] - (mainConditionWidth / 2), mainCondition_Y))

                # Most important weather icon for the day
                iconFilename = f"{row['weather_icon']}.png"
                if iconFilename in weatherForecast.iconCache:
                    weatherIcon = weatherForecast.iconCache[iconFilename]
                    screen.blit(weatherIcon, (containerCenter[index] - (weatherIcon.get_width() / 2), weatherIcon_Y))
                else:
                    print(f"Icon not found in cache: {iconFilename}")

                # High daily temperature
                maxTempSurface = fonts["fontCen48"].render(f"{round(row['dailyMaxTemp'])}°", True, colors["palWhite"])
                maxTempWidth = maxTempSurface.get_width()
                screen.blit(maxTempSurface, (containerCenter[index] - (maxTempWidth / 2), highTemp_Y))

                # Low daily temperature
                lowTempSurface = fonts["fontCen40"].render(f"{round(row['dailyMinTemp'])}°", True, colors["palLtBlue"])
                lowTempWidth = lowTempSurface.get_width()
                screen.blit(lowTempSurface, (containerCenter[index] - (lowTempWidth / 2), lowTemp_Y))

                # Long weather description text - verbose to print one word per line, the response can get a bit long
                weather_desc_words = row['weather_description'].split()                             

                # Render each word as a separate surface
                weatherDescSurfaces = []
                for word in weather_desc_words:
                    weatherDescSurface = fonts["fontCen18"].render(word, True, colors["palWhite"])
                    weatherDescSurfaces.append(weatherDescSurface)

                # Calculate the total height of the text block
                totalTextHeight = sum(weatherDescSurface.get_height() for weatherDescSurface in weatherDescSurfaces)

                # Calculate the starting Y position to center the text block vertically
                start_Y = weatherDesc_Y - (totalTextHeight // 2)

                # Blit each word surface
                current_Y = start_Y
                for weatherDescSurface in weatherDescSurfaces:
                    weatherDescWidth = weatherDescSurface.get_width()
                    screen.blit(weatherDescSurface, (containerCenter[index] - (weatherDescWidth / 2), current_Y))
                    current_Y += weatherDescSurface.get_height()  # Move down for the next word   

            except KeyError as e:
                print(f"KeyError: {e}. Check column names.")
            except Exception as e:
                print(f"An error occurred: {e}")

        button("Back", fonts["fontCen18"], colors["palBlack"], colors["palBlue"], 680, 450, 120, 30, "backHome")

class screenSettings():
    def __init__(self):
        self.backgroundImage = pygame.image.load(BACKGROUNDS_DIR + '/displayBG.png').convert()
        self.activeThumbnail = pygame.transform.scale(activeScreen.desktop.backgroundImage, (133, 80))
        self.selectedThumb = ''

    def update(self):
        screen.blit(self.backgroundImage, (0, 0))

        headerPrint()

        buttonColor, buttonFont, buttonFontColor = colors["palWhite"], fonts["fontCen18"], colors["palBlue"]
        startX, startY, bWidth, bHeight = 30, 120, 140, 40

        desktopPick('Black Cat', buttonFont, buttonFontColor, buttonColor, startX, startY, bWidth, bHeight, 0, "blackCatBG")
        desktopPick('Blue Waves', buttonFont, buttonFontColor, buttonColor, startX, startY + 60, bWidth, bHeight, 0, "blueWavesBG")
        desktopPick('Sail Boat', buttonFont, buttonFontColor, buttonColor, startX, startY + 120, bWidth, bHeight, 0, "sailBoatBG")
        desktopPick('Water Drop', buttonFont, buttonFontColor, buttonColor, startX, startY + 180, bWidth, bHeight, 0, "waterDropBG")
        desktopPick('Pac Man', buttonFont, buttonFontColor, buttonColor, startX, startY + 240, bWidth, bHeight, 0, "pacManBG")

        desktopPick('Fire Bird', buttonFont, buttonFontColor, buttonColor, startX + 180, startY, bWidth, bHeight, 0, "fireBirdBG")
        desktopPick('Heart Book', buttonFont, buttonFontColor, buttonColor, startX + 180, startY + 60, bWidth, bHeight, 0, "heartBookBG")
        desktopPick('Imperial', buttonFont, buttonFontColor, buttonColor, startX + 180, startY + 120, bWidth, bHeight, 0, "imperialBG")
        desktopPick('Lego Chase', buttonFont, buttonFontColor, buttonColor, startX + 180, startY + 180, bWidth, bHeight, 0, "legoChaseBG")
        desktopPick('Moon Closeup', buttonFont, buttonFontColor, buttonColor, startX + 180, startY + 240, bWidth, bHeight, 0, "moonBG")

        desktopPick('Winter Penguins', buttonFont, buttonFontColor, buttonColor, startX + 360, startY, bWidth, bHeight, 0, "penguinsBG")
        desktopPick('Shadow Girl', buttonFont, buttonFontColor, buttonColor, startX + 360, startY + 60, bWidth, bHeight, 0, "shadowGirlBG")
        desktopPick('Purple Deer', buttonFont, buttonFontColor, buttonColor, startX + 360, startY + 120, bWidth, bHeight, 0, "purpleDeerBG")
        desktopPick('Wet Stone', buttonFont, buttonFontColor, buttonColor, startX + 360, startY + 180, bWidth, bHeight, 0, "wetStoneBG")
        desktopPick('Dark Earth', buttonFont, buttonFontColor, buttonColor, startX + 360, startY + 240, bWidth, bHeight, 0, "darkEarthBG")

        print("active thumb: " + str(self.activeThumbnail))
        screen.blit(self.activeThumbnail, (600, 200))
        button("Set", fonts["fontCen18"], colors["palBlack"], colors["palBlue"], 620, 300, 120, 40, "setDesktop")

        #tab menu
        button("Back", fonts["fontCen18"], colors["palBlack"], colors["palBlue"], 680, 450, 120, 30, "backHome")

class screenFire():
    def update(self):
        pass
    
class screenHome():
    def __init__(self, homeLayoutDict, fonts, colors, screen):
        self.screen = screen
        self.fonts = fonts
        self.colors = colors
        self.layout = homeLayoutDict

        # Load background image
        self.backgroundImage = pygame.image.load(BACKGROUNDS_DIR + self.layout['bgImg']).convert()

        # Initialize elements
        self.elements = {}
        self.InitializeElements()

        # Pre-render static elements
        self.PreRenderStaticElements()

    def InitializeElements(self):
        for elementName, config in self.layout.items():
            if elementName == "bgImg" or elementName == "menu":
                continue
            self.elements[elementName] = {
                "config": config,
                "surface": None,
                "position": (0, 0)
            }

    def PreRenderStaticElements(self):
        for elementName, element in self.elements.items():
            config = element["config"]
            if "defaultText" in config:  # Pre-render elements with default text
                self.RenderElement(elementName, config["defaultText"])
                self.PositionElement(elementName)

    def RenderElement(self, elementName, text):
        config = self.elements[elementName]["config"]
        font = self.fonts[config["font"]]
        color = self.colors[config["color"]]

        self.elements[elementName]["surface"] = font.render(str(text), True, color)

    def PositionElement(self, elementName: str):
        '''
         

        >>> day_of_week(0)
        Monday
        >>> day_of_week(6)
        Sunday

        :param string: name of element, e.g. Time, Date, Humidity - pulled from layout json file
        :type: 
        :return None: sets element posistion as part of the function call, element["position"] = (x, y)
        :rtype:
        ''' 
        element = self.elements[elementName]
        config = element["config"]
        surface = element["surface"]

        if config["pos"] != "none":

            if config["pos"] == "coords":
                # Direct coordinates
                x = int(config["Xpos"])
                y = int(config["Ypos"])
                element["position"] = (x, y)

            elif config["pos"] == "relative":
                
                relativeTo = config["Xpos"].strip()  # Ensure no extra spaces

                # In this mode the json value needs to be parsed, ast handles it
                try:
                    ySettings = ast.literal_eval(config["Ypos"])
                    alignment, anchor, spacing = ySettings
                except (ValueError, SyntaxError) as e:
                    print(f"Error parsing Ypos for element '{elementName}': {e}")
                    return

                # Relative posistion to the screen
                if relativeTo == 'screen':

                    # Calculate X position
                    if alignment == "left":
                        x = 0
                    elif alignment == "right":
                        x = screenSize[0] - surface.get_width()
                    elif alignment == "center":
                        x = (screenSize[0] - surface.get_width()) // 2

                    # Calculate Y position
                    if anchor == "top":
                        y = 0
                    elif anchor == "bottom":
                        y = screenSize[1] - surface.get_height()
                    elif anchor == "center":
                        y = (screenSize[1] - surface.get_height()) // 2

                    # Apply spacing
                    if alignment == "left":
                        x += spacing
                    elif alignment == "right":
                        x -= spacing
                    elif anchor == "top":
                        y += spacing
                    elif anchor == "bottom":
                        y -= spacing

                    element["position"] = (x, y)
                
                # Relative positioning to another surface
                elif relativeTo in self.elements:
                    relativeSurface = self.elements[relativeTo]["surface"]
                    relativeX, relativeY = self.elements[relativeTo]["position"]

                    # Calculate X position
                    if alignment == "left":
                        x = relativeX
                    elif alignment == "right":
                        if anchor == "bottom":  #  Special treatment for right and bottom justification
                            endX_relative = relativeX + relativeSurface.get_width()
                            x = endX_relative - surface.get_width()
                        else:
                            x = relativeX + relativeSurface.get_width()
                    elif alignment == "center":
                        x = relativeX + (relativeSurface.get_width() - surface.get_width()) // 2

                    # Calculate Y position
                    if anchor == "top":
                        y = relativeY
                    elif anchor == "bottom":
                        y = relativeY + relativeSurface.get_height()
                    elif anchor == "center":
                        y = relativeY + (relativeSurface.get_height() - surface.get_height()) // 2

                    # Apply spacing
                    if alignment == "left" or alignment == "right":
                        x += spacing
                    elif anchor == "top" or anchor == "bottom":
                        y += spacing

                    element["position"] = (x, y)
                else:
                    print(f"Error: '{relativeTo}' not found in self.elements.")
            else:
                print(f"Error: Invalid positioning mode '{config['pos']}' for element '{elementName}'.")

    def update(self):
        # Draw background
        self.screen.blit(self.backgroundImage, (0, 0))

        # Render and position elements
        for elementName, element in self.elements.items():
            config = element["config"]

            if elementName == "temperature":
                # Special handling for temperature color
                temp = data["downstairs"]
                if temp >= 71.9:
                    color = self.colors[config["highTempColor"]]
                elif temp <= 68.9:
                    color = self.colors[config["lowTempColor"]]
                else:
                    color = self.colors[config["normalTempColor"]]
                text = f"{temp}°"
                font = self.fonts[config["font"]]
                element["surface"] = font.render(text, True, color)
                self.PositionElement(elementName)

            elif elementName not in ["bgImg", "menu", "reload"]:
                self.RenderElement(elementName, data[elementName])
                self.PositionElement(elementName)

            # Draw element
            if config["pos"] != "none":
                self.screen.blit(element["surface"], element["position"])

            if elementName == "reload" and config["enable"] == "True":
                button("Reload", fonts["fontCen18"], colors["palBlack"], colors["palBlue"], 580, 325, 80, 40, "reload")

        self.DrawMenu()

    def DrawMenu(self):
        menuConfig = self.layout["menu"]
        menuX = 680 if "Right" in menuConfig["pos"] else 360
        menuY = 450 if "bottom" in menuConfig["pos"] else 0

        buttons = ["Fireplace", "Weather", "Settings", "Exit"]
        xOffset = 121
                
        #tab menu
        xOffset = 121

        menuConfig = self.layout["menu"]
        font = self.fonts["fontCen18"]
        color = self.colors[menuConfig["fontColor"]]
        bgColor = self.colors[menuConfig["color"]]
        divColor = self.colors[menuConfig["dividerColor"]]

        #TODO - Poor code, feel bad for poor code 
        buttons = [
            {"label": "Fireplace", "action": "fire"},
            {"label": "Weather", "action": "weather"},
            {"label": "Settings", "action": "settings"},
            {"label": "Exit", "action": "quit"}
        ]

        # Initial x position for the first button
        x_position = menuX - (xOffset * 3)

        # Loop through the buttons list
        for i, btn in enumerate(buttons):
            # Draw the button
            button(btn["label"], font, color, bgColor, x_position, menuY, 120, 30, btn["action"])
            
            # Draw a divider after the button (except for the last button)
            if i < len(buttons) - 1:
                pygame.draw.rect(screen, divColor, (x_position + 120, menuY, 1, 30), 0)
            
            # update the x position for the next button
            x_position += xOffset

class tabHandler:
    def __init__(self):
        # Initialize attributes to None
        self.desktop = None
        self.lastDesktop = None

    def setInitialDesktop(self, initialDesktop):
        """Set the initial desktop."""
        self.desktop = initialDesktop
        self.lastDesktop = initialDesktop

    def update(self, target):
        """Update the active desktop."""
        self.lastDesktop = self.desktop
        self.desktop = target

def createDesktops(homeLayoutData):
    # Create desktop instances using layout data from the json file
    return {
        "Black Cat": screenHome(homeLayoutData["Black Cat"], fonts, colors, screen),
        "Blue Waves": screenHome(homeLayoutData["Blue Waves"], fonts, colors, screen),
        "Sail Boat": screenHome(homeLayoutData["Sail Boat"], fonts, colors, screen),
        "Water Drop": screenHome(homeLayoutData["Water Drop"], fonts, colors, screen),
        "Pac Man": screenHome(homeLayoutData["Pac Man"], fonts, colors, screen),

        "Fire Bird": screenHome(homeLayoutData["Fire Bird"], fonts, colors, screen),
        "Heart Book": screenHome(homeLayoutData["Heart Book"], fonts, colors, screen),
        "Imperial Dest": screenHome(homeLayoutData["Imperial Dest"], fonts, colors, screen),
        "Lego Chase": screenHome(homeLayoutData["Lego Chase"], fonts, colors, screen),
        "Moon Close": screenHome(homeLayoutData["Moon Close"], fonts, colors, screen),

        "Penguins": screenHome(homeLayoutData["Penguins"], fonts, colors, screen),
        "Shadow Girl": screenHome(homeLayoutData["Shadow Girl"], fonts, colors, screen),
        "Purple Deer": screenHome(homeLayoutData["Purple Deer"], fonts, colors, screen),
        "Wet Stone": screenHome(homeLayoutData["Wet Stone"], fonts, colors, screen),
        "Dark Earth": screenHome(homeLayoutData["Dark Earth"], fonts, colors, screen)   
    }

def reloadLayoutData():
    global homeLayoutData, desktops, currentDesktopIndex

    # Reload the JSON file
    homeLayoutData = loadLayoutData(layoutFile)

    # Recreate desktop instances
    desktopInstances = createDesktops(homeLayoutData)

    # Update the desktops list
    desktops = list(desktopInstances.values())

def loadLayoutData(json_file_path):
    # Load layout data from JSON file
    try:
        with open(layoutFile) as json_file:  
            homeLayoutData = json.load(json_file)
    except FileNotFoundError:
        print(f'"{layoutFile}" not found, file path error.')
    except Exception as e:
        print(f'Unhandled error with json file: {repr(e)}')

    with open(json_file_path) as json_file:
        return json.load(json_file)

def screenSaver():
    global currentDesktopIndex

    if (activeScreen.desktop != weatherBG or settingsBG):
        currentDesktopIndex = (currentDesktopIndex + 1) % len(desktops)

        with backlight.fade(duration = .5):
            backlight.brightness = 0

        switchDesktop(desktops[currentDesktopIndex])

        activeScreen.desktop.update()
        pygame.display.update()
        time.sleep(.5)

        with backlight.fade(duration = .5):
            backlight.brightness = backlightBrightness

def publishMQTT(client, topic, payload):
    """
    Publishes the temperature value to the MQTT broker.

    Args:
        client (mqtt.Client): The MQTT client instance.
        temperature (float): The temperature value to publish.
    """
    try:
        payload = str(payload)
        client.publish(topic, payload)
        
    except Exception as e:
        print(f"Failed to publish message: {e}")

def onConnectMQTT(client, userdata, flags, rc):
    # Callback when the client receives a CONNACK response from the server.

    print(f"Connected with result code {rc}")
    # Subscribe to the topic
    client.subscribe(motionTopic)
    client.subscribe(temperatureTopic)
    client.subscribe(humidityTopic)
    client.subscribe(batteryTopic)

def onMessageMQTT(client, userdata, msg):
    # Callback when a PUBLISH message is received from the server.

    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    if msg.topic == temperatureTopic:
        officeTemperature = msg.payload.decode() + "°F"
        # print(f"Received Temperature: {msg.payload.decode()} °F")
    elif msg.topic == humidityTopic:
        officeHumidity = msg.payload.decode() + "%"
        # print(f"Received Humidity: {msg.payload.decode()} %")
    elif msg.topic == batteryTopic:
        officeBattery = msg.payload.decode() + "V"
        # print(f"Received Battery: {msg.payload.decode()} Volts")
    elif msg.topic == motionTopic:
        officeMotion = msg.payload.decode()
        print(f"Received Motion: {msg.payload.decode()}")
        if (officeMotion == "true"):
            lightControl(service, 'on')
        if (officeMotion == "false"):
            lightControl(service, 'off')

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callbacks
client.on_connect = onConnectMQTT
client.on_message = onMessageMQTT

# Connect to the broker
client.connect(brokerAddress, brokerPort, 60)

# Start the loop to process network traffic and dispatch callbacks
client.loop_start()

homeLayoutData = loadLayoutData(layoutFile)
desktopInstances = createDesktops(homeLayoutData)
desktops = list(desktopInstances.values())
currentDesktopIndex = 0

# Keeps main loop running
done = False

# Create objects
todayNow = dateTimeNow()
downstairs = currentTemp()
currentWeather = getCurrentWeather()
weatherForecast = getWeatherForecast()
weatherBG = screenWeather()
activeScreen = tabHandler()
# Must set a desktop here, settings below needs the active screen set to generate thumbnails
activeScreen.setInitialDesktop(desktops[currentDesktopIndex])
settingsBG = screenSettings()

currentWeather.update()
weatherForecast.update()

# setup schedule
schedule.every(5).seconds.do(downstairs.update)
schedule.every(1).seconds.do(todayNow.update)
schedule.every(10).minutes.do(currentWeather.update)
schedule.every(23).minutes.do(screenSaver)
# schedule.every(3).seconds.do(screenSaver)
schedule.every(93).minutes.do(weatherForecast.update)
schedule.every(1).seconds.do(backlightController)

schedule.every(1).seconds.do(toggleFireplaceHeartbeat)

clock = pygame.time.Clock()

if __name__ == "__main__":
    while not done:

        schedule.run_pending()
        
        activeScreen.desktop.update()

        pygame.display.update()

        # Check for gestures
        handleGesture()

        data = {
            "time": str(todayNow.timeNow),
            "date": str(todayNow.dateNow),
            "dayLong": str(todayNow.dayLong),
            "dayShort": str(todayNow.dayShort),
            "downstairs": downstairs.temperature,
            "outside": str(currentWeather.temperatue) + "°",
            "humidity": str(downstairs.humidity) + "%"
        }

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                
                done = True

        clock.tick(60)

GPIO.cleanup()
pygame.quit()

# sys.exit()
