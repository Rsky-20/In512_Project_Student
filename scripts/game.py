__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"


import json, os
import numpy as np

from my_constants import *
from gui import GUI
from time import sleep
import random

class Game:
    """ Handle the whole game """
    def __init__(self, nb_agents, map_id):
        self.nb_agents = nb_agents
        self.nb_ready = 0
        self.agent_id = 0
        self.moves = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]
        self.agent_paths = [None]*nb_agents
        self.load_map(map_id)
        self.load_obstacles(num_obstacles=nb_agents)
        #Generate obstacle randomly
        self.gui = GUI(self)
        
    
    def load_obstacles(self, num_obstacles=3):
        """
        Génère et place des obstacles en forme de L sur la carte.
        """
        def create_L_shape():
            """Crée une matrice représentant un obstacle en forme de L avec rotation aléatoire."""
            base_L = np.array([
                [0.35, 0.35, 0.35, 0, 0],
                [0.35, 1.0,  0.35, 0, 0],
                [0.35, 1.0,  0.35, 0.35, 0.35],
                [0.35, 1.0,  1.0,  1.0,  0.35],
                [0.35, 0.35, 0.35, 0.35, 0.35]
            ])
            rotations = random.choice([0, 1, 2, 3])  # Rotation aléatoire (0°, 90°, 180°, 270°)
            return np.rot90(base_L, rotations)

        obstacle_size = 5  # Taille des obstacles
        for _ in range(num_obstacles):
            placed = False
            attempts = 0

            while not placed and attempts < 100:
                attempts += 1
                obstacle = create_L_shape()
                x = random.randint(0, self.map_h - obstacle_size)
                y = random.randint(0, self.map_w - obstacle_size)

                # Vérifie si la zone est libre pour placer tout l'obstacle
                if np.sum(self.map_real[x:x + obstacle_size, y:y + obstacle_size]) == 0:
                    # Place tout l'obstacle
                    self.map_real[x:x + obstacle_size, y:y + obstacle_size] = obstacle
                    placed = True

            if not placed:
                print(f"Impossible de placer un obstacle après {attempts} tentatives.")



    
    def load_map(self, map_id):
        """ Load a map """
        json_filename = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "config.json")
        with open(json_filename, "r") as json_file:
            self.map_cfg = json.load(json_file)[f"map_{map_id}"]        
        
        self.agents, self.keys, self.boxes = [], [], []
        for i in range(self.nb_agents):
            self.agents.append(Agent(i+1, self.map_cfg[f"agent_{i+1}"]["x"], self.map_cfg[f"agent_{i+1}"]["y"], self.map_cfg[f"agent_{i+1}"]["color"]))
            self.keys.append(Key(self.map_cfg[f"key_{i+1}"]["x"], self.map_cfg[f"key_{i+1}"]["y"]))
            self.boxes.append(Box(self.map_cfg[f"box_{i+1}"]["x"], self.map_cfg[f"box_{i+1}"]["y"]))
            self.agent_paths[i] = [(self.agents[i].x, self.agents[i].y)]
        
        self.map_w, self.map_h = self.map_cfg["width"], self.map_cfg["height"]
        self.map_real = np.zeros(shape=(self.map_h, self.map_w))
        items = []
        items.extend(self.keys)
        items.extend(self.boxes)
        offsets = [[(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)], [(-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), ( 2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)]]
        for item in items:
            for i, sub_list in enumerate(offsets):
                for dx, dy in sub_list:
                    if dx != 0 or dy != 0:
                        self.add_val(item.x + dx, item.y + dy, item.neighbour_percent/(i+1))
                    else:
                        self.add_val(item.x, item.y, 1)
        
    
    def add_val(self, x, y, val):
        """ Add a value if x and y coordinates are in the range [map_w; map_h] """
        if 0 <= x < self.map_w and 0 <= y < self.map_h:
            self.map_real[y, x] = val


    def process(self, msg, agent_id):
        """ Process data sent by agent whose id is specified """
        self.agent_id = agent_id
        if msg["header"] == MOVE:
            return self.handle_move(msg, agent_id)
        elif msg["header"] == GET_DATA:
            return {"sender": GAME_ID, "header": GET_DATA, "agent_id" : self.agent_id, "x": self.agents[agent_id].x, "y": self.agents[agent_id].y, "w": self.map_w, "h": self.map_h, "cell_val": self.map_real[self.agents[agent_id].y, self.agents[agent_id].x]}
        elif msg["header"] == GET_NB_CONNECTED_AGENTS:
            return {"sender": GAME_ID, "header": GET_NB_CONNECTED_AGENTS, "nb_connected_agents": self.nb_ready}
        elif msg["header"] == GET_NB_AGENTS:
            return {"sender": GAME_ID, "header": GET_NB_AGENTS, "nb_agents": self.nb_agents}
        elif msg["header"] == GET_ITEM_OWNER:
            return self.handle_item_owner_request(agent_id)
        elif msg["header"] == BROADCAST_MSG:
            # Diffuser le message à tous les agents sauf l'expéditeur
            self.broadcast_message(msg, agent_id)
        

    def handle_move(self, msg, agent_id):
        """ Make sure the desired move is allowed and update the agent's position """
        if msg["direction"] in range(9):
            dx, dy = self.moves[msg["direction"]]
            x, y = self.agents[agent_id].x, self.agents[agent_id].y
            if 0 <= x + dx < self.map_w and 0 <= y + dy < self.map_h:  
                self.agents[agent_id].x, self.agents[agent_id].y = x + dx, y + dy
                if (self.agents[agent_id].x, self.agents[agent_id].y) not in self.agent_paths[agent_id]:    #add the current agent pose in the path only if it is the first time it goes to its current cell
                    self.agent_paths[agent_id].append((self.agents[agent_id].x, self.agents[agent_id].y))
                    #sleep(0.5)
        return {"sender": GAME_ID, "header": MOVE, "x": self.agents[agent_id].x, "y": self.agents[agent_id].y, "cell_val": self.map_real[self.agents[agent_id].y, self.agents[agent_id].x]}



    def handle_item_owner_request(self, agent_id):
        if self.map_real[self.agents[agent_id].y, self.agents[agent_id].x] != 1.0:  #make sure the agent is located on an item
            return {"sender": GAME_ID, "header": GET_ITEM_OWNER, "owner": None}
        for i, key in enumerate(self.keys): #check if it's a key
            if (self.agents[agent_id].x == key.x) and (self.agents[agent_id].y == key.y):
                return  {"sender": GAME_ID, "header": GET_ITEM_OWNER, "owner": i, "type": KEY_TYPE}
        for i, box in enumerate(self.boxes):    #check if it's a box
            if (self.agents[agent_id].x == box.x) and (self.agents[agent_id].y == box.y):
                return  {"sender": GAME_ID, "header": GET_ITEM_OWNER, "owner": i, "type": BOX_TYPE}

    def broadcast_message(self, msg, sender_id):
        """
        Diffuse un message à tous les agents sauf l'expéditeur.
        Args:
            msg (dict): Le message à diffuser.
            sender_id (int): L'identifiant de l'expéditeur.
        """
        for agent_id in range(self.nb_agents):
            if agent_id != sender_id:
                try:
                    # Simuler l'envoi du message à un agent
                    print(f"Broadcasting message to agent {agent_id}: {msg}")
                    # Logique d'envoi réel à implémenter si nécessaire
                except Exception as e:
                    print(f"Error broadcasting message to agent {agent_id}: {e}")


class Agent:
    def __init__(self, id, x, y, color):
        self.id = id
        self.x, self.y = x, y
        self.color = color

    def __repr__(self):
        return f"Agent's id: {self.id}, x: {self.x}, y: {self.y}, color: {self.color}"
    

class Item:
    def __init__(self, x, y, neighbor_percent, type):
        self.x, self.y = x, y
        self.neighbour_percent = neighbor_percent
        self.type = type

    def __repr__(self):
        return f"type: {self.type}, x: {self.x}, y: {self.y}"


class Key(Item):
    def __init__(self, x, y):
        Item.__init__(self, x, y, KEY_NEIGHBOUR_PERCENTAGE, "key")
    

class Box(Item):
    def __init__(self, x, y):
        Item.__init__(self, x, y, BOX_NEIGHBOUR_PERCENTAGE, "box")