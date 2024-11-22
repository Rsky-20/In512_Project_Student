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
        self.nav_state = {"nav_state":'nav', "last_direction":None, "last_value":None, "key":None, "box":None}

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
        
        self.points_of_interest = self.get_random_interest_points()
        print(f"{CONSOLE_COLOR['MAGENTA']}Interesting point (size={len(self.points_of_interest)}): {self.points_of_interest}{CONSOLE_COLOR['RESET']}")
        self.points_of_interest = self.determine_order(self.points_of_interest, (self.x, self.y))
        print(f"{CONSOLE_COLOR['MAGENTA']}Interesting point ordered (size={len(self.points_of_interest)}): {self.points_of_interest}{CONSOLE_COLOR['RESET']}")
        
        self.orders, self.path = self.generate_path()
        
        if self.orders and self.path:
            self.navigate_to_points()
        else:
            print(f"{CONSOLE_COLOR['RED']}{CONSOLE_COLOR['BOLD']}WARNING:{CONSOLE_COLOR['RESET']}{CONSOLE_COLOR['RED']} No path or No commands to move{CONSOLE_COLOR['RESET']}")
    
        
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
                print(f"{CONSOLE_COLOR['YELLOW']}[Agents] - both connected!{CONSOLE_COLOR['RESET']}")
                check_conn_agent = False
                  

    #TODO: CREATE YOUR METHODS HERE...
    
    def calculate_points(self, factor=10):
        num_points = math.ceil(self.h / factor) + math.ceil(self.w / factor)
        return num_points

    def get_random_interest_points(self, factor=10, min_distance=5):
        """
        Génère des points d'intérêt aléatoires, dispersés sur la carte.
        :param factor: Facteur pour calculer le nombre de points.
        :param min_distance: Distance minimale entre les points.
        :return: Liste des points d'intérêt.
        """
        num_points = self.calculate_points(factor)
        points = []

        while len(points) < num_points:
            point = (random.randint(0, self.w - 1), random.randint(0, self.h - 1))

            # Vérifier que le point respecte la distance minimale avec les points existants
            if all(self.calculate_euclidean_distance(point, existing_point) >= min_distance for existing_point in points):
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
            if self.nav_state["nav_state"] == 'nav':
                # Vérifier que des commandes et un path sont disponibles
                if not self.orders or not self.path:
                    print(f"{CONSOLE_COLOR['RED']}{CONSOLE_COLOR['BOLD']}ERROR:{CONSOLE_COLOR['RESET']}{CONSOLE_COLOR['RED']} Orders or Path is empty during navigation!{CONSOLE_COLOR['RESET']}")
                    break

                # Prochain point d'intérêt (ne supprime pas les points d'intérêt ici)
                target = self.points_of_interest[0]  # Ne retire pas le point d'intérêt

                # Générer les commandes et le path pour atteindre la cible si nécessaire
                if not self.orders or not self.path:
                    self.orders, self.path = self.generate_commands((self.x, self.y), target)

                # Exécuter les commandes pour atteindre le point cible
                while self.orders:
                    command = self.orders.pop(0)  # Retirer la commande suivante
                    self.move(command)  # Déplacer l'agent selon la commande
                    self.x, self.y = self.path.pop(0)  # Mettre à jour la position avec le path

                    # Vérifier la valeur de la case actuelle
                    cell_value = self.get_data()
                    if cell_value in [0.25, 0.5] and self.nav_state['key'] == None:
                        # Si une valeur est détectée, supprimer le path et changer l'état
                        print(f"{CONSOLE_COLOR['YELLOW']}>>> Key near (value: {cell_value}). Clearing path!{CONSOLE_COLOR['RESET']}")
                        self.path = []  # Supprimer le path
                        self.nav_state["nav_state"] = 'discover_key'
                        break
                    """elif cell_value in [0.3, 0.6] and self.nav_state['box'] == None:
                        # Si une valeur est détectée, supprimer le path et changer l'état
                        print(f"{CONSOLE_COLOR['YELLOW']}>>> Box near (value: {cell_value}). Clearing path!{CONSOLE_COLOR['RESET']}")
                        self.path = []  # Supprimer le path
                        self.nav_state["nav_state"] = 'discover_box'
                        break
                    elif cell_value == 0.35:
                        print(f"{CONSOLE_COLOR['YELLOW']}>>> Obstacle detected. Clearing path!{CONSOLE_COLOR['RESET']}")
                        self.path = []  # Supprimer le path
                        self.nav_state["nav_state"] = 'obstacle_avoidance'
                        break"""

                # Mettre à jour la position
                if self.points_of_interest:
                    print(f"{CONSOLE_COLOR['MAGENTA']}Navigation complete. Next points: {self.points_of_interest[0]}{CONSOLE_COLOR['RESET']}")
                else:
                    print(f"{CONSOLE_COLOR['MAGENTA']}Navigation complete. No more points !{CONSOLE_COLOR['RESET']}")
                
            """elif self.nav_state["nav_state"] == 'discover_key':
                print(f"{CONSOLE_COLOR['CYAN']}Discovering key...{CONSOLE_COLOR['RESET']}")

                # Position initiale de la recherche
                search_start = self.nav_state.get("search_start", (self.x, self.y))
                self.nav_state["search_start"] = search_start  # Mettre à jour si non défini
                last_value = self.nav_state.get("last_value", 0.0)

                # Déplacements définis par les indices de DIRECTION
                movement_vectors = {
                    1: (0, -1),  # left
                    2: (0, 1),   # right
                    3: (-1, 0),  # up
                    4: (1, 0),   # down
                    5: (-1, -1), # up_left
                    6: (-1, 1),  # up_right
                    7: (1, -1),  # down_left
                    8: (1, 1),   # down_right
                }

                # Fonction pour vérifier les limites de la carte
                def in_bounds(x, y):
                    return 0 <= x < self.w and 0 <= y < self.h

                # Boucle de recherche
                for direction, (dx, dy) in movement_vectors.items():
                    new_x, new_y = self.x + dx, self.y + dy

                    if in_bounds(new_x, new_y):
                        print(f"{CONSOLE_COLOR['CYAN']}Exploring {DIRECTION[direction]} at ({new_x}, {new_y})...{CONSOLE_COLOR['RESET']}")
                        
                        # Déplacer le robot
                        self.move(DIRECTION[direction])
                        self.x, self.y = new_x, new_y  # Mettre à jour les coordonnées

                        # Vérifier la nouvelle valeur après le déplacement
                        new_value = self.get_data()

                        if new_value == 1.0:
                            print(f"{CONSOLE_COLOR['GREEN']}Key discovered at ({self.x}, {self.y})!{CONSOLE_COLOR['RESET']}")
                            self.nav_state["nav_state"] = 'key_found'
                            return
                        elif new_value > last_value:
                            print(f"{CONSOLE_COLOR['YELLOW']}Approaching key: {new_value}{CONSOLE_COLOR['RESET']}")
                            self.nav_state["last_value"] = new_value
                            self.nav_state["search_start"] = (self.x, self.y)  # Mise à jour de la position de recherche
                            return
                        else:
                            print(f"{CONSOLE_COLOR['MAGENTA']}Value unchanged or lower ({new_value}), continuing...{CONSOLE_COLOR['RESET']}")"""






            """elif self.nav_state["nav_state"] == 'discover_box':
                print(f"{CONSOLE_COLOR['CYAN']}Discovering box...{CONSOLE_COLOR['RESET']}")
                # Logique spécifique pour découvrir une boîte ou gérer cet état

            elif self.nav_state["nav_state"] == 'obstacle_avoidance':
                print(f"{CONSOLE_COLOR['CYAN']}Avoiding obstacle...{CONSOLE_COLOR['RESET']}")
                # Logique spécifique pour contourner un obstacle ou gérer cet état"""

                
    def move(self, direction):
        self.network.send({'header': 2, 'direction': direction})
        sleep(0.05)
        
    def get_data(self):
        try:
            self.network.send({'header': 1})
            return float(self.msg['cell_val'])
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
        print(f"{CONSOLE_COLOR['MAGENTA']}Broadcasted discovery: {msg}{CONSOLE_COLOR['RESET']}")


            
 
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



