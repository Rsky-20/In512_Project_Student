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
import math


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
        #self.explore()
        #Thread(target=self.explore, daemon=True).start()
        self.points_of_interest = self.get_random_interest_points()
        print(f"[agent_{self.agent_id}] - Interesting point (size={len(self.points_of_interest)}): {self.points_of_interest}")
        self.points_of_interest = self.determine_order(self.points_of_interest, (self.x, self.y))
        print(f"[agent_{self.agent_id}] - Interesting point ordered (size={len(self.points_of_interest)}): {self.points_of_interest}")
        
        self.orders, self.path = self.generate_path()
        #print(f"[agent_{self.agent_id}] - Commands: {self.orders}")
        #print(f"[agent_{self.agent_id}] - Path: {self.path}")
        
        if self.orders and self.path:
            self.navigate_to_points()
        else:
            print(f"[agent_{self.agent_id}] - WARNING: No path or No commands to move")
    
        
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
    
    def calculate_points(self, factor=10):
        num_points = math.ceil(self.h / factor) + math.ceil(self.w / factor)
        return num_points

    def get_random_interest_points(self, factor=10):
        num_points = self.calculate_points(factor)
        points = []

        while len(points) < num_points:
            point = (random.randint(0, self.w - 1), random.randint(0, self.h - 1))
            if point not in points:  # Éviter les doublons
                points.append(point)

        return points
    
    def calculate_euclidean_distance(self, point1, point2):
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    def determine_order(self, points, start_pos):
        remaining_points = points[:]
        current_pos = start_pos
        ordered_points = []

        while remaining_points:
            farthest_point = max(
                remaining_points,
                key=lambda p: self.calculate_euclidean_distance(current_pos, p)
            )
            ordered_points.append(farthest_point)
            remaining_points.remove(farthest_point)
            current_pos = farthest_point

        return ordered_points

    def generate_commands(self, start_pos, target_pos):
        commands = []
        current_pos = list(start_pos)
        path = [tuple(current_pos)]  # Inclure la position initiale

        while current_pos != list(target_pos):
            dx = target_pos[0] - current_pos[0]
            dy = target_pos[1] - current_pos[1]

            if dx > 0 and dy > 0:
                commands.append(DOWN_RIGHT) #"down_right"
                current_pos[0] += 1
                current_pos[1] += 1
            elif dx > 0 and dy < 0:
                commands.append(DOWN_LEFT) #"down_left"
                current_pos[0] += 1
                current_pos[1] -= 1
            elif dx < 0 and dy > 0:
                commands.append(UP_RIGHT) #"up_right"
                current_pos[0] -= 1
                current_pos[1] += 1
            elif dx < 0 and dy < 0:
                commands.append(UP_LEFT) #"up_left"
                current_pos[0] -= 1
                current_pos[1] -= 1
            elif dx > 0:
                commands.append(DOWN) #"down"
                current_pos[0] += 1
            elif dx < 0:
                commands.append(UP) #"up"
                current_pos[0] -= 1
            elif dy > 0:
                commands.append(RIGHT) #"right"
                current_pos[1] += 1
            elif dy < 0:
                commands.append(LEFT) #"left"
                current_pos[1] -= 1

            path.append(tuple(current_pos))

        return commands, path

    def generate_path(self):
        all_commands = []
        full_path = []
        current_pos = (self.x, self.y)

        for point in self.points_of_interest:
            commands, path = self.generate_commands(current_pos, point)
            all_commands.extend(commands)
            full_path.extend(path)
            current_pos = point  # Mettre à jour la position actuelle

        return all_commands, full_path

    def navigate_to_points(self):
        """
        Navigue à travers le chemin donné, exécute les commandes associées et met à jour les listes.
        """
        while self.points_of_interest:
            # Vérifier que des commandes et un path sont disponibles
            if not self.orders or not self.path:
                print(f"[agent_{self.agent_id}] - ERROR: Orders or Path is empty during navigation!")
                break

            # Prochain point d'intérêt
            target = self.points_of_interest.pop(0)  # Retirer le point d'intérêt atteint
            commands, path = self.generate_commands((self.x, self.y), target)

            # Exécuter les commandes pour atteindre le point cible
            for command in commands:
                if self.orders:  # Vérifier que des commandes restent
                    self.move(command)  # Déplacer l'agent
                    self.orders.pop(0)  # Retirer la commande exécutée
                else:
                    print(f"[agent_{self.agent_id}] - WARNING: No more commands to execute!")
                    break

            # Supprimer le chemin parcouru
            for _ in path:
                if self.path:  # Vérifier que le path n'est pas vide
                    self.path.pop(0)
                else:
                    print(f"[agent_{self.agent_id}] - WARNING: No more path to remove!")
                    break

            # Mettre à jour la position
            if path:
                self.x, self.y = path[-1]  # Dernière position atteinte

            print(f"[agent_{self.agent_id}] - Navigation complete. Remaining points: {self.points_of_interest}")

                
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



