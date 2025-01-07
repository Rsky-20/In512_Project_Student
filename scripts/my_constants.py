__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

""" This file contains all the 'constants' shared by all the scripts """

""" MSG HEADERS """
BROADCAST_MSG = 0
GET_DATA = 1    #get the current location of the agent and the dimension of the environment (width and height)
MOVE = 2
GET_NB_CONNECTED_AGENTS = 3
GET_NB_AGENTS = 4
GET_ITEM_OWNER = 5

""" ALLOWED MOVES """
STAND = 0   #do not move
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
UP_LEFT = 5
UP_RIGHT = 6
DOWN_LEFT = 7
DOWN_RIGHT = 8
DIRECTION = {1: 'left', 2: 'right', 3: 'up', 4: 'down', 5: 'up_left', 6: 'up_right', 7: 'down_left', 8: 'down_right'}
OPPOSITE_DIRECTION_INDEX = {1: 2, 2: 1, 3: 4, 4: 3, 5: 8, 6: 7, 7: 6, 8: 5}
DIRECTION_MAP = {
            1: (0, -1),   # left
            2: (0, 1),    # right
            3: (-1, 0),   # up
            4: (1, 0),    # down
            5: (-1, -1),  # up_left
            6: (-1, 1),   # up_right
            7: (1, -1),   # down_left
            8: (1, 1)     # down_right
        }

# Directions perpendiculaires dans le sens horaire
CLOCKWISE_DIRECTION_INDEX = {
    1: 3,  # left -> up
    3: 2,  # up -> right
    2: 4,  # right -> down
    4: 1,  # down -> left
    5: 6,  # up_left -> up_right
    6: 8,  # up_right -> down_right
    8: 7,  # down_right -> down_left
    7: 5   # down_left -> up_left
}

# Directions perpendiculaires dans le sens anti-horaire
COUNTERCLOCKWISE_DIRECTION_INDEX = {
    1: 4,  # left -> down
    4: 2,  # down -> right
    2: 3,  # right -> up
    3: 1,  # up -> left
    5: 7,  # up_left -> down_left
    7: 8,  # down_left -> down_right
    8: 6,  # down_right -> up_right
    6: 5   # up_right -> up_left
}

""" BROADCAST TYPES """
KEY_DISCOVERED = 1  #inform other agents that you discovered a key
BOX_DISCOVERED = 2
COMPLETED = 3   #inform other agents that you discovered your key and you reached your own box

""" GAME """
GAME_ID = -1    #id of the game when it sends a message to an agent
KEY_NEIGHBOUR_PERCENTAGE = 0.5  #value of an adjacent cell to a key
BOX_NEIGHBOUR_PERCENTAGE = 0.6  #value of an adjacent cell to a key
OBSTACLE_NEIGHBOUR_PERCENTAGE = 0.35
KEY_TYPE = 0    #one of the types of item that is output by the 'Get item owner' request
BOX_TYPE = 1

""" GUI """
BG_COLOR = (255, 255, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
CONSOLE_COLOR = {
    "RESET": "\033[0m",        # Réinitialiser les couleurs
    "BOLD": "\033[1m",         # Texte en gras
    "UNDERLINE": "\033[4m",    # Texte souligné
    "REVERSED": "\033[7m",     # Inverser les couleurs

    # Couleurs de texte
    "BLACK": "\033[30m",
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",

    # Couleurs d'arrière-plan
    "BG_BLACK": "\033[40m",
    "BG_RED": "\033[41m",
    "BG_GREEN": "\033[42m",
    "BG_YELLOW": "\033[43m",
    "BG_BLUE": "\033[44m",
    "BG_MAGENTA": "\033[45m",
    "BG_CYAN": "\033[46m",
    "BG_WHITE": "\033[47m",
}
