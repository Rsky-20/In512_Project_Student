__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *

from threading import Thread
import numpy as np
from time import sleep
import random


class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):
        #TODO: DEINE YOUR ATTRIBUTES HERE

        #DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        self.msg = {}
        env_conf = self.network.receive()
        self.nb_agent_expected = 0
        self.nb_agent_connected = 0
        self.x, self.y = env_conf["x"], env_conf["y"]   #initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]   #environment dimensions
        self.agent_state = None
        cell_val = env_conf["cell_val"] #value of the cell the agent is located in
        Thread(target=self.msg_cb, daemon=True).start()
        self.wait_for_connected_agent()
        sleep(5)
        self.orders, self.path = self.generate_directions()
        self.explore()
        #Thread(target=self.explore, daemon=True).start()
    
        
    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            self.msg = msg
            if msg["header"] == MOVE:
                self.x, self.y =  msg["x"], msg["y"]
            elif msg["header"] == GET_NB_AGENTS:
                self.nb_agent_expected = msg["nb_agents"]
            elif msg["header"] == GET_NB_CONNECTED_AGENTS:
                self.nb_agent_connected = msg["nb_connected_agents"]            


    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("[Agents] - both connected!")
                check_conn_agent = False
                  

    #TODO: CREATE YOUR METHODS HERE...
    def generate_directions(self):
        current_pos = (self.x, self.y)
        to_visit = set()  # Suivi des cases visitées
        to_visit.add(current_pos)
        orders = []  # Liste des ordres de direction
        points = [current_pos]  # Liste des points visités (pour dessiner le chemin)

        # Fonction pour convertir un mouvement en coordonnées
        def move(position, direction):
            x, y = position
            dir_name = DIRECTION[direction]  # Récupérer le nom de la direction
            if dir_name == "up":
                return x - 1, y
            elif dir_name == "down":
                return x + 1, y
            elif dir_name == "left":
                return x, y - 1
            elif dir_name == "right":
                return x, y + 1
            elif dir_name == "up_left":
                return x - 1, y - 1
            elif dir_name == "up_right":
                return x - 1, y + 1
            elif dir_name == "down_left":
                return x + 1, y - 1
            elif dir_name == "down_right":
                return x + 1, y + 1
            return position

        # Fonction pour déterminer les mouvements valides
        def valid_moves(position):
            x, y = position
            moves = []
            for direction in DIRECTION:  # Parcourir les clés du dictionnaire
                nx, ny = move((x, y), direction)
                if 0 <= nx < self.w and 0 <= ny < self.h:  # Rester dans les limites de la grille
                    moves.append(direction)
            return moves

        # Génération du chemin
        while len(to_visit) < self.w * self.h:
            # Récupérer les mouvements valides
            valid_directions = valid_moves(current_pos)

            # Priorité : éviter de revisiter les cases si possible
            next_moves = [
                direction for direction in valid_directions
                if move(current_pos, direction) not in to_visit
            ]

            # Si toutes les cases voisines sont visitées, autoriser la revisite
            if not next_moves:
                next_moves = valid_directions

            # Choisir une direction au hasard parmi les options
            chosen_direction = random.choice(next_moves)

            # Appliquer le mouvement
            current_pos = move(current_pos, chosen_direction)
            orders.append(chosen_direction)  # Ajouter la direction (clé numérique)
            points.append(current_pos)  # Ajouter le nouveau point visité
            to_visit.add(current_pos)

        return orders, points

    def explore(self):
        # Obtenir les ordres et les points générés par generate_directions
        orders, points = self.generate_directions()

        # Explorer en suivant les ordres générés
        for direction in orders:
            self.move(direction)  # Effectuer le mouvement
            sleep(0.1)  # Pause pour visualisation (ajuster si nécessaire)



                
    def move(self, direction):
        self.network.send({'header': 2, 'direction': direction})
        sleep(0.05)
        
    def get_data(self):
        try:
            self.network.send({'header': 1})
            print(self.msg)
            return self.msg['cell_val']
        except:
            return None
        
    def communicate_discovery(self, discovery_type, x, y):
        msg = {
            "header": BROADCAST_MSG,
            "type": discovery_type,  # 1 -> clé, 2 -> coffre
            "position": (x, y),
            "owner": self.agent_id
        }
        self.network.send(msg)
        print(f"[agent {self.agent_id}] - Broadcasted discovery: {msg}")


            
 
if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)
    
    try:    #Manual control test0
        while True:
            cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
            if cmds["header"] == BROADCAST_MSG:
                cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
                cmds["position"] = (agent.x, agent.y)
                cmds["owner"] = randint(0,3) # TODO: specify the owner of the item
            elif cmds["header"] == MOVE:
                cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
            agent.network.send(cmds)
    except KeyboardInterrupt:
        pass
# it is always the same location of the agent first location



