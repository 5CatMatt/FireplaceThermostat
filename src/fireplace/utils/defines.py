# src/fireplace/utils/defines.py
import os

DEVELOPER_MODE = True
# DEVELOPER_MODE = False

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname((os.path.abspath(__file__))))

# Define paths to asset directories
IMAGES_DIR = os.path.join(PROJECT_ROOT, "Images")
BACKGROUNDS_DIR = os.path.join(IMAGES_DIR, "Backgrounds")
WEATHER_ICONS_DIR = os.path.join(IMAGES_DIR, "Icons/Weather")
FONTS_DIR = os.path.join(PROJECT_ROOT, "Fonts")

WEATHER_CONDITION_IMPORTANCE = {
    "clear sky": {"dayIcon": "01d.png", "nightIcon": "01n.png", "importance": 1},
    "few clouds": {"dayIcon": "02d.png", "nightIcon": "02n.png", "importance": 2},
    "scattered clouds": {"dayIcon": "03d.png", "nightIcon": "03n.png", "importance": 3},
    "broken clouds": {"dayIcon": "04d.png", "nightIcon": "04n.png", "importance": 4},
    "overcast clouds": {"dayIcon": "04d.png", "nightIcon": "04n.png", "importance": 5},
    "light rain": {"dayIcon": "10d.png", "nightIcon": "10n.png", "importance": 6},
    "moderate rain": {"dayIcon": "10d.png", "nightIcon": "10d.png", "importance": 7},
    "heavy intensity rain": {"dayIcon": "10d.png", "nightIcon": "10d.png", "importance": 8},
    "very heavy rain": {"dayIcon": "10d.png", "nightIcon": "10d.png", "importance": 9},
    "extreme rain": {"dayIcon": "10d.png", "nightIcon": "10d.png", "importance": 10},
    "freezing rain": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 11},
    "light intensity shower rain": {"dayIcon": "09d.png", "nightIcon": "09n.png", "importance": 12},
    "shower rain": {"dayIcon": "09d.png", "nightIcon": "09n.png", "importance": 13},
    "heavy intensity shower rain": {"dayIcon": "10d.png", "nightIcon": "10n.png", "importance": 14},
    "ragged shower rain": {"dayIcon": "09d.png", "nightIcon": "09n.png", "importance": 15},
    "thunderstorm": {"dayIcon": "11d.png", "nightIcon": "11n.png", "importance": 16},
    "light snow": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 17},
    "snow": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 18},
    "heavy snow": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 19},
    "sleet": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 20},
    "light shower sleet": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 21},
    "shower sleet": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 22},
    "light rain and snow": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 23},
    "rain and snow": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 24},
    "light shower snow": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 25},
    "shower snow": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 26},
    "heavy shower snow": {"dayIcon": "13d.png", "nightIcon": "13n.png", "importance": 27},
    "mist": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 28},
    "smoke": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 29},
    "haze": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 30},
    "sand/dust whirls": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 31},
    "fog": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 32},
    "sand": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 33},
    "dust": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 34},
    "volcanic ash": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 35},
    "squalls": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 36},
    "tornado": {"dayIcon": "50d.png", "nightIcon": "50n.png", "importance": 37}
}

ICON_FILE_NAMES = [
    "01d.png", "01n.png", "02d.png", "02n.png", "03d.png", "03n.png",
    "04d.png", "04n.png", "09d.png", "09n.png", "10d.png", "10n.png",
    "11d.png", "11n.png", "13d.png", "13n.png", "50d.png", "50n.png"
]

COLORS = {
    "palBlue": (20, 105, 151),       # #146997
    "palRed": (219, 46, 52),         # #db2e34
    "palLtBlue": (137, 191, 184),    # #89bfb8
    "palGreen": (85, 114, 110),      # #55726e
    "palLtGreen": (225, 248, 214),   # #e1f8d6
    "palWhite": (255, 255, 255),     # #ffffff
    "palBlack": (0, 0, 0),           # #000000
    "palYellow": (255, 223, 0),      # #ffdf00
    "palOrange": (255, 165, 0),      # #ffa500
    "palPurple": (128, 0, 128),      # #800080
    "palPink": (255, 192, 203),      # #ffc0cb
    "palGray": (128, 128, 128),      # #808080
    "palLtGray": (211, 211, 211),    # #d3d3d3
    "palDkGray": (64, 64, 64),       # #404040
    "palCyan": (0, 255, 255),        # #00ffff
    "palMagenta": (255, 0, 255),     # #ff00ff
    "palBrown": (165, 42, 42),       # #a52a2a
    "palLtBrown": (210, 180, 140),   # #d2b48c
    "palTeal": (0, 128, 128),        # #008080
    "palLavender": (230, 230, 250),  # #e6e6fa
    "palMaroon": (128, 0, 0),        # #800000
    "palOlive": (128, 128, 0),       # #808000
    "palNavy": (0, 0, 128),          # #000080
    "palCoral": (255, 127, 80),      # #ff7f50
    "palGold": (255, 215, 0),        # #ffd700
    "palSilver": (192, 192, 192),    # #c0c0c0
    "palIndigo": (75, 0, 130),       # #4b0082
    "palViolet": (238, 130, 238),    # #ee82ee
    "palKhaki": (240, 230, 140),     # #f0e68c
    "palSalmon": (250, 128, 114),    # #fa8072
    "palTurquoise": (64, 224, 208),  # #40e0d0
    "palBeige": (245, 245, 220),     # #f5f5dc
    "palMint": (189, 252, 201),      # #bdfcc9
    "palSkyBlue": (135, 206, 235),   # #87ceeb
    "palSlateBlue": (106, 90, 205),  # #6a5acd
    "palTomato": (255, 99, 71),      # #ff6347
    "palPlum": (221, 160, 221),      # #dda0dd
    "palPeru": (205, 133, 63),       # #cd853f
    "palOrchid": (218, 112, 214),    # #da70d6
    "palLime": (0, 255, 0),          # #00ff00
    "palCrimson": (220, 20, 60),     # #dc143c
    "palChocolate": (210, 105, 30),  # #d2691e
    "palTan": (210, 180, 140),       # #d2b48c
    "palAqua": (0, 255, 255),        # #00ffff
    "palFuchsia": (255, 0, 255),     # #ff00ff
    "palWheat": (245, 222, 179),     # #f5deb3
    "palGainsboro": (220, 220, 220), # #dcdcdc
    "palHoneydew": (240, 255, 240),  # #f0fff0
    "palIvory": (255, 255, 240),     # #fffff0
    "palAzure": (240, 255, 255),     # #f0ffff
    "palSnow": (255, 250, 250),      # #fffafa
    "palMistyRose": (255, 228, 225), # #ffe4e1
    "palDarkSlateGray": (47, 79, 79),# #2f4f4f
    "palDarkCyan": (0, 139, 139),    # #008b8b
    "palDeepPink": (255, 20, 147),   # #ff1493
    "palDarkOrange": (255, 140, 0),  # #ff8c00
    "palDarkSalmon": (233, 150, 122),# #e9967a
    "palDarkSeaGreen": (143, 188, 143), # #8fbc8f
    "palDarkKhaki": (189, 183, 107), # #bdb76b
    "palDarkMagenta": (139, 0, 139), # #8b008b
    "palDarkOliveGreen": (85, 107, 47), # #556b2f
    "palDarkOrchid": (153, 50, 204), # #9932cc
    "palDarkRed": (139, 0, 0),       # #8b0000
    "palDarkSlateBlue": (72, 61, 139), # #483d8b
    "palDarkTurquoise": (0, 206, 209), # #00ced1
    "palDarkViolet": (148, 0, 211),  # #9400d3
    "palDeepSkyBlue": (0, 191, 255), # #00bfff
    "palDimGray": (105, 105, 105),   # #696969
    "palDodgerBlue": (30, 144, 255), # #1e90ff
    "palFireBrick": (178, 34, 34),   # #b22222
    "palFloralWhite": (255, 250, 240), # #fffaf0
    "palForestGreen": (34, 139, 34), # #228b22
    "palGhostWhite": (248, 248, 255), # #f8f8ff
    "palGreenYellow": (173, 255, 47), # #adff2f
    "palHotPink": (255, 105, 180),   # #ff69b4
    "palIndianRed": (205, 92, 92),   # #cd5c5c
    "palLightCoral": (240, 128, 128), # #f08080
    "palLightGoldenrodYellow": (250, 250, 210), # #fafad2
    "palLightPink": (255, 182, 193), # #ffb6c1
    "palLightSalmon": (255, 160, 122), # #ffa07a
    "palLightSeaGreen": (32, 178, 170), # #20b2aa
    "palLightSkyBlue": (135, 206, 250), # #87cefa
    "palLightSlateGray": (119, 136, 153), # #778899
    "palLightSteelBlue": (176, 196, 222), # #b0c4de
    "palLimeGreen": (50, 205, 50),   # #32cd32
    "palMediumAquamarine": (102, 205, 170), # #66cdaa
    "palMediumBlue": (0, 0, 205),    # #0000cd
    "palMediumOrchid": (186, 85, 211), # #ba55d3
    "palMediumPurple": (147, 112, 219), # #9370db
    "palMediumSeaGreen": (60, 179, 113), # #3cb371
    "palMediumSlateBlue": (123, 104, 238), # #7b68ee
    "palMediumSpringGreen": (0, 250, 154), # #00fa9a
    "palMediumTurquoise": (72, 209, 204), # #48d1cc
    "palMediumVioletRed": (199, 21, 133), # #c71585
    "palMidnightBlue": (25, 25, 112), # #191970
    "palMintCream": (245, 255, 250), # #f5fffa
    "palNavajoWhite": (255, 222, 173), # #ffdead
    "palOldLace": (253, 245, 230),   # #fdf5e6
    "palOliveDrab": (107, 142, 35),  # #6b8e23
    "palPaleGoldenrod": (238, 232, 170), # #eee8aa
    "palPaleGreen": (152, 251, 152), # #98fb98
    "palPaleTurquoise": (175, 238, 238), # #afeeee
    "palPaleVioletRed": (219, 112, 147), # #db7093
    "palPapayaWhip": (255, 239, 213), # #ffefd5
    "palPeachPuff": (255, 218, 185), # #ffdab9
    "palPowderBlue": (176, 224, 230), # #b0e0e6
    "palRosyBrown": (188, 143, 143), # #bc8f8f
    "palRoyalBlue": (65, 105, 225),  # #4169e1
    "palSaddleBrown": (139, 69, 19), # #8b4513
    "palSandyBrown": (244, 164, 96), # #f4a460
    "palSeaGreen": (46, 139, 87),    # #2e8b57
    "palSeaShell": (255, 245, 238),  # #fff5ee
    "palSienna": (160, 82, 45),      # #a0522d
    "palSpringGreen": (0, 255, 127), # #00ff7f
    "palSteelBlue": (70, 130, 180),  # #4682b4
    "palThistle": (216, 191, 216),   # #d8bfd8
    "palYellowGreen": (154, 205, 50) # #9acd32
}
