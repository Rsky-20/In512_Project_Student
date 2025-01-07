__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *

from threading import Thread
import numpy as np
from time import sleep, time
import random
import math
from datetime import datetime
import traceback

class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip, verbose):
        self.nav_state = {
                            "nav_state": 'nav',
                            "last_direction": None,
                            "last_value": 0.0,
                            "last_coord":(None, None),
                            "key": {
                                "coord": (None, None),  # Coordonnées de la clé
                                "has_key": False        # Indique si le robot possède la clé
                            },
                            "box": {
                                "coord": (None, None),  # Coordonnées de la boîte
                                "box_unlocked": False   # Indique si la boîte est déverrouillée
                            },
                            "visited_cell_count":0
                        }
        self.internal_agent_broadcast_stat = {"nb_send":0, "nb_receive":0, "box_coord_found_by_other":False, "key_coord_found_by_other":False}
        self.forbidden_cells = set()

        # DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.verbose = verbose
        self.network.send({"header": GET_DATA})
        self.msg = {}
        env_conf = self.network.receive()
        self.nb_agent_expected = 0
        self.nb_agent_connected = 0
        self.x, self.y = env_conf["x"], env_conf["y"]  # initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]  # environment dimensions

        self.visited_cells = []  # Track visited cells
        self.visited_unic_cells = set()
        cell_val = env_conf["cell_val"]  # value of the cell the agent is located in
        Thread(target=self.msg_cb, daemon=True).start()
        self.wait_for_connected_agent()
        print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'__init__'] - Name: Agent_{self.agent_id}{CONSOLE_COLOR['RESET']}")

        sleep(5)
        
        self.start_date_time = datetime.now()
        self.end_date_time = None
        self.last_display_time = datetime.now()  # Dernière fois que l'affichage a été mis à jour
        self.points_of_interest = []            
        

    def msg_cb(self):
        """ Method used to handle incoming messages """
        while self.running:
            try:
                data = self.network.receive()
                if not data:  # Vérifie si des données valides ont été reçues
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'msg_cb'] - Received empty data. Connection might be closed.{CONSOLE_COLOR['RESET']}")
                    break
                self.msg = data
                if self.msg["header"] == MOVE:
                    self.x, self.y = self.msg["x"], self.msg["y"]
                elif self.msg["header"] == GET_NB_AGENTS:
                    self.nb_agent_expected = self.msg["nb_agents"]
                elif self.msg["header"] == GET_NB_CONNECTED_AGENTS:
                    self.nb_agent_connected = self.msg["nb_connected_agents"]
                elif self.msg["header"] == BROADCAST_MSG:
                    self.handle_broadcast_message(self.msg)
            except EOFError:
                if self.verbose:
                    print(f"{CONSOLE_COLOR['RED']}[ERROR>'msg_cb'] - Connection closed by peer (EOFError).{CONSOLE_COLOR['RESET']}")
                    traceback.print_exc()
                break
            except ConnectionResetError:
                if self.verbose:
                    print(f"{CONSOLE_COLOR['RED']}[ERROR>'msg_cb'] - Connection reset by peer.{CONSOLE_COLOR['RESET']}")
                    traceback.print_exc()
                break
            except Exception as e:
                if self.verbose:
                    print(f"{CONSOLE_COLOR['RED']}[ERROR>'msg_cb'] - {e}{CONSOLE_COLOR['RESET']}")
                    traceback.print_exc()
                break


    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                if self.verbose:
                    print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'wait_for_connected_agent'] - both connected!{CONSOLE_COLOR['RESET']}")
                check_conn_agent = False
    
    
    def calculate_points(self, factor=10):
        num_points = math.ceil(self.h / factor) + math.ceil(self.w / factor)
        return num_points


    def get_random_interest_points(self, factor=10, min_distance=5):
        """
        Generate random interest points spread across the grid.
        Exclude forbidden cells.
        """
        num_points = self.calculate_points(factor)
        points = []

        while len(points) < num_points:
            #point = (random.randint(0, self.w - 1), random.randint(0, self.h - 1))
            point_bord_1 = (random.randint(0, self.w - 1), random.randint(self.h-4, self.h - 1))
            point_bord_2 = (random.randint(0, 4), random.randint(0, self.h - 1))
            point_bord_3 = (random.randint(0, self.w - 1), random.randint(0, 4))
            point_bord_4 = (random.randint(self.w - 4, self.w - 1), random.randint(0, self.h - 1))
            eucli_dist_bord = []
            L = [point_bord_1,point_bord_2,point_bord_3,point_bord_4]
            
            for i in range(len(L)):
                eucli_dist_bord.append(self.calculate_euclidean_distance((self.x,self.y),L[i]))
            min_valeur = min(eucli_dist_bord)
            index_min = eucli_dist_bord.index(min_valeur)
            del L[index_min]
            
            point = L[randint(0,2)]
            

            if point not in self.forbidden_cells and all(
                self.calculate_euclidean_distance(point, existing_point) >= min_distance
                for existing_point in points
            ):
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
        path = [tuple(current_pos)]

        while current_pos != list(target_pos):
            dx = target_pos[0] - current_pos[0]
            dy = target_pos[1] - current_pos[1]

            if dx > 0 and dy > 0:
                commands.append(DOWN_RIGHT)
                current_pos[0] += 1
                current_pos[1] += 1
            elif dx > 0 and dy < 0:
                commands.append(UP_RIGHT)
                current_pos[0] += 1
                current_pos[1] -= 1
            elif dx < 0 and dy > 0:
                commands.append(DOWN_LEFT)
                current_pos[0] -= 1
                current_pos[1] += 1
            elif dx < 0 and dy < 0:
                commands.append(UP_LEFT)
                current_pos[0] -= 1
                current_pos[1] -= 1
            elif dx > 0:
                commands.append(RIGHT)
                current_pos[0] += 1
            elif dx < 0:
                commands.append(LEFT)
                current_pos[0] -= 1
            elif dy > 0:
                commands.append(DOWN)
                current_pos[1] += 1
            elif dy < 0:
                commands.append(UP)
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
            current_pos = point

        return all_commands, full_path


    def navigate_to_points(self):
        """
        Navigate through the given path, execute associated commands, and update the lists.
        """
        while self.nav_state["nav_state"] != 'mission_completed':
            
            self.handle_discovery()
            
            if self.nav_state["key"]["has_key"] and self.nav_state["box"]["coord"] != (None, None) and self.nav_state["box"]["box_unlocked"] == False:
                self.nav_state["nav_state"] = 'moving_to_box'
                self.move_to_coordinates(self.nav_state["box"]["coord"][0],self.nav_state["box"]["coord"][1])
                
                if self.verbose:
                    print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'navigate_to_points']{CONSOLE_COLOR['RESET']} - Moving directly to open the box ({self.x}, {self.y}) -> {self.nav_state["box"]["coord"]}.{CONSOLE_COLOR['RESET']}")
            
            if self.nav_state["nav_state"] == 'moving_to_key':
                self.move_to_coordinates(self.nav_state["key"]["coord"][0],self.nav_state["key"]["coord"][1])
                if self.verbose:
                    print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'navigate_to_points']{CONSOLE_COLOR['RESET']} - Moving directly to open the box ({self.x}, {self.y}) -> {self.nav_state["box"]["coord"]}.{CONSOLE_COLOR['RESET']}")
        
            
            if not self.points_of_interest:
                self.points_of_interest = self.get_random_interest_points()
                self.points_of_interest = self.determine_order(self.points_of_interest, (self.x, self.y))
                self.orders, self.path = self.generate_path()

            if self.nav_state["nav_state"] == 'nav':
                if not self.orders or not self.path:
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'navigate_to_points'] - ERROR: Orders or Path is empty during navigation! Regenerating...{CONSOLE_COLOR['RESET']}")
                    self.points_of_interest = []
                    continue

                target = self.points_of_interest[0]
                if target in self.forbidden_cells:
                    self.points_of_interest.pop(0)
                    continue

                while self.orders and self.nav_state["nav_state"] != 'mission_completed':
                    command = self.orders.pop(0)
                    self.nav_state["last_direction"] = command
                    self.nav_state["last_coord"] = (self.x, self.y)
                    self.path.pop(0)
                    self.move(command)
                    cell_type, _ = self.get_data()
                    self.visit_cell((self.x, self.y))
                    
                    if self.nav_state["key"]["coord"] != (None, None) and self.nav_state["key"]["has_key"] == False:
                        self.nav_state["nav_state"] = 'moving_to_key'
                        self.orders = []
                        self.path = []
                        break
                    
                    if cell_type == "OBSTACLE_NEIGHBOR":
                        self.avoid_obstacle()
                        break

                    if cell_type in ["KEY_NEIGHBOR", "KEY_OUTER"] and self.nav_state["key"]["has_key"] == False:
                        if self.verbose:
                            print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'navigate_to_points']{CONSOLE_COLOR['RESET']} - Switching to hot/cold search near ({self.x}, {self.y}).{CONSOLE_COLOR['RESET']}")
                        self.nav_state["nav_state"] = 'hot_cold_search_KEY'
                        self.hot_cold_search()
                        self.orders = []
                        self.path = []
                        break
                    
                    if cell_type in ["BOX_NEIGHBOR", "BOX_OUTER"] and self.nav_state["box"]["coord"] == (None, None):
                        if self.verbose:
                            print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'navigate_to_points']{CONSOLE_COLOR['RESET']} - Switching to hot/cold search near ({self.x}, {self.y}).{CONSOLE_COLOR['RESET']}")
                        self.nav_state["nav_state"] = 'hot_cold_search_BOX'
                        self.hot_cold_search()
                        self.orders = []
                        self.path = []
                        break

                    sleep(0.1)

            
        print(f"{CONSOLE_COLOR['GREEN']}[INFO>'navigate_to_points'] - Stopping navigation process.{CONSOLE_COLOR['RESET']}")


    def move_to_coordinates(self, target_x, target_y):
        """
        Déplace le robot vers les coordonnées cibles (target_x, target_y) en utilisant
        une logique cohérente avec calculate_euclidean_distance et determine_order.
        """
                
        self.orders, self.path = self.generate_commands((self.x, self.y), (target_x, target_y))
        print(self.path)
        print(self.orders)
        is_opposite = False
        while self.orders:
            command = self.orders.pop(0)
            self.nav_state["last_direction"] = command
            self.nav_state["last_coord"] = (self.x, self.y)
            self.path.pop(0)
            last_dist = self.calculate_euclidean_distance((self.x, self.y),(target_x, target_y))
            if is_opposite:
                self.move(OPPOSITE_DIRECTION_INDEX[command])
            else:
                self.move(command)
            new_dist = self.calculate_euclidean_distance((self.x, self.y),(target_x, target_y))
            self.visit_cell((self.x, self.y))
            if new_dist>last_dist:
                is_opposite = True
            
            sleep(1)
        
        

    def avoid_obstacle(self):
        """
        Handle obstacle by stepping back using directions from DIRECTION and OPPOSITE_DIRECTION_INDEX.
        Clears the current path after stepping back.
        """
        if self.verbose:
            print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'avoid_obstacle'] - Obstacle detected. Changing path...{CONSOLE_COLOR['RESET']}")

        # Vérification et initialisation de la dernière direction connue
        if self.nav_state["last_direction"] is None:
            if self.verbose:
                print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'avoid_obstacle'] - No last direction recorded. Cannot step back.{CONSOLE_COLOR['RESET']}")
            return

        # Obtenir la direction opposée
        reverse_direction = OPPOSITE_DIRECTION_INDEX[self.nav_state["last_direction"]]

        # Reculer de 2 cases dans la direction opposée
        for _ in range(2):  # Boucle pour reculer de 2 cases
            self.move(reverse_direction)  # Utilisation de la direction
            if self.verbose:
                print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'avoid_obstacle']{CONSOLE_COLOR['RESET']} - Stepped back in direction '{DIRECTION[reverse_direction]}'.")

        # Effacer les ordres et le chemin
        self.orders = []
        self.path = []
        if self.verbose:
            print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'avoid_obstacle']{CONSOLE_COLOR['RESET']} - Path cleared. Navigation will reprogram if needed.")


    def hot_cold_search(self):
        """
        Implement a hot/cold strategy to locate cells with value 1.0.
        The robot explores neighboring cells and decides the best path based on cell values and types.
        """
        if self.verbose:
            print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'hot_cold_search']{CONSOLE_COLOR['RESET']} - Hot/Cold search initiated.{CONSOLE_COLOR['RESET']}")

        while True:
            sleep(0.2)
            _, current_cell_value = self.get_data()  # Obtenez les données de la cellule actuelle
            max_value = current_cell_value  # Initialisez la valeur max avec la valeur actuelle
            original_x, original_y = self.x, self.y  # Stockez la position actuelle
            if self.verbose:
                print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'hot_cold_search']{CONSOLE_COLOR['RESET']} - Current position: ({self.x}, {self.y}), Value: {current_cell_value}.")

            # Explorer toutes les directions
            for direction_index, (dx, dy) in DIRECTION_MAP.items():
                nx, ny = self.x + dx, self.y + dy

                # Vérifiez les limites de la grille et les cellules visitées
                if 0 <= nx < self.w and 0 <= ny < self.h and (nx, ny):
                    self.move(direction_index)  # Déplacez le robot dans la direction donnée
                    self.visit_cell((self.x, self.y))
                    neighbor_cell_type, neighbor_cell_value = self.get_data()
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['GREEN']}[INFO>'hot_cold_search']{CONSOLE_COLOR['RESET']} - Checked cell ({nx}, {ny}): Type {neighbor_cell_type}, Value {neighbor_cell_value}.")

                    # Si une cellule cible est atteinte
                    if neighbor_cell_value == 1.0:
                        print(f"{CONSOLE_COLOR['GREEN']}[INFO>'hot_cold_search']{CONSOLE_COLOR['RESET']} - Target found at ({self.x}, {self.y})!")
                        self.handle_discovery()
                        return
                    
                    # Si la cellule a une meilleure valeur
                    if neighbor_cell_value > max_value:
                        max_value = neighbor_cell_value
                        if self.verbose:
                            print(f"{CONSOLE_COLOR['GREEN']}[INFO>'hot_cold_search']{CONSOLE_COLOR['RESET']}Better cell found at ({nx}, {ny}) with value {neighbor_cell_value}.")
                        break
                    elif neighbor_cell_value == max_value:
                        self.move(OPPOSITE_DIRECTION_INDEX[direction_index])  # Revenez en arrière
                        self.visit_cell((self.x, self.y))
                    else:
                        # Si la valeur est inférieure ou égale, revenir à la cellule d'origine
                        self.move(OPPOSITE_DIRECTION_INDEX[direction_index])  # Revenez en arrière
                        self.visit_cell((self.x, self.y))
                        

    def handle_discovery(self):
        """
        Handle the discovery of keys or boxes and communicate as needed.
        """
        cell_type, _ = self.get_data()
        if cell_type == "TARGET":
            discovered_coord = (self.x, self.y)
            owner, item_type = self.get_owner()
            
            if item_type == KEY_TYPE:
                self.communicate_discovery(KEY_TYPE, owner, *discovered_coord)
            elif item_type == BOX_TYPE:
                self.communicate_discovery(BOX_TYPE, owner, *discovered_coord)

            if owner == self.agent_id:
                
                # Ajouter la cellule et ses voisines dans forbidden_cells
                for dx in range(-1, 2):  # Cases voisines (-1, 0, +1)
                    for dy in range(-1, 2):
                        forbidden_x, forbidden_y = discovered_coord[0] + dx, discovered_coord[1] + dy
                        if 0 <= forbidden_x < self.w and 0 <= forbidden_y < self.h:
                            self.forbidden_cells.add((forbidden_x, forbidden_y))
                
                # Mise à jour de l'état après découverte
                if not self.nav_state["key"]["has_key"] and item_type == KEY_TYPE:
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'handle_discovery']{CONSOLE_COLOR['RESET']} Key picked up! We take it...")
                    self.nav_state["key"]["coord"] = discovered_coord
                    self.nav_state["key"]["has_key"] = True
                    if self.nav_state["box"]["coord"] == (None, None):
                        # Décalage après découverte
                        if self.verbose:
                            print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'handle_discovery']{CONSOLE_COLOR['RESET']} - Shifting 3 cells after discovery to avoid cycles.")
                        self.shift_position(3)
                    else:
                        self.nav_state["nav_state"] = 'moving_to_box'
                    
                if self.nav_state["box"]["coord"] == (None, None) and item_type == BOX_TYPE:
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'handle_discovery']{CONSOLE_COLOR['RESET']} - Box found! We save coordinate in case ...")
                    self.nav_state["box"]["coord"] = discovered_coord
                    
                if not self.nav_state["key"]["has_key"]:
                    # Décalage après découverte
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'handle_discovery']{CONSOLE_COLOR['RESET']} - Shifting 3 cells after discovery to avoid cycles.")
                    self.shift_position(3)
                
                if self.nav_state["key"]["has_key"] and self.nav_state["box"]["box_unlocked"] == False and self.nav_state["box"]["coord"] != (None, None) and item_type == BOX_TYPE:
                    self.nav_state["box"]["box_unlocked"] = True
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'handle_discovery']{CONSOLE_COLOR['RESET']} - Box found & has Key ! Unboxing ...")
                        
                    print(f"{CONSOLE_COLOR['GREEN']}[INFO>'handle_discovery']{CONSOLE_COLOR['RESET']} - Mission completed!")
                    self.nav_state["nav_state"] = 'mission_completed'
                    self.end_date_time = datetime.now()
                    
            else: 
                if self.verbose:
                    print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'handle_discovery']{CONSOLE_COLOR['RESET']} - Shifting 3 cells after discovery to avoid cycles.")
                    self.shift_position(3)
                
            

    def handle_broadcast_message(self, msg):
        """
        Gère les messages de type BROADCAST_MSG pour mettre à jour les coordonnées des clés ou des boîtes.
        """
        if msg["header"] == BROADCAST_MSG:
            discovery_type = msg.get("type")  # Type d'élément découvert (clé ou boîte)
            position = msg.get("position")  # Coordonnées de l'élément découvert
            owner = msg.get("owner")  # Propriétaire de l'élément découvert
            self.internal_agent_broadcast_stat['nb_receive']+=1

            if owner != None and int(owner) == int(self.agent_id):
                if int(discovery_type) == KEY_TYPE :
                    # Met à jour les coordonnées de la clé si elle appartient à cet agent
                    self.nav_state["key"]["coord"] = position
                    self.internal_agent_broadcast_stat['key_coord_found_by_other'] = True
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['GREEN']}[INFO>'handle_broadcast_message']{CONSOLE_COLOR['RESET']} - Updated key position to {position} for agent {self.agent_id}.")

                if int(discovery_type) == BOX_TYPE:
                    # Met à jour les coordonnées de la boîte si elle appartient à cet agent
                    self.nav_state["box"]["coord"] = position
                    self.internal_agent_broadcast_stat['box_coord_found_by_other'] = True
                    if self.verbose:
                        print(f"{CONSOLE_COLOR['GREEN']}[INFO>'handle_broadcast_message']{CONSOLE_COLOR['RESET']} - Updated box position to {position} for agent {self.agent_id}.")

            else:
                if self.verbose:
                    print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'handle_broadcast_message'] - Ignored broadcast message for another agent {owner}.{CONSOLE_COLOR['RESET']}")


    def shift_position(self, shift_distance):
        """
        Déplace le robot de shift_distance cases dans une direction aléatoire.
        """
        # Revenir en mode navigation
        if self.nav_state["nav_state"] != 'mission_completed':
            directions = list(DIRECTION.keys())  # Toutes les directions possibles
            direction = random.choice(directions)  # Choisit une direction aléatoire
            for _ in range(shift_distance):
                dx, dy = DIRECTION_MAP[direction]
                self.move(direction)
                self.x += dx
                self.y += dy
                if self.verbose:
                    print(f"{CONSOLE_COLOR['GREEN']}[INFO>'shift_position']{CONSOLE_COLOR['RESET']}Shifted randomly to ({self.x}, {self.y}) in direction {DIRECTION[direction]}.")

            self.nav_state["nav_state"] = 'nav'
            if self.verbose:
                print(f"{CONSOLE_COLOR['CYAN']}[BEHAVIOR>'shift_position']{CONSOLE_COLOR['RESET']} - Shift completed. Returning to navigation mode.")
       

    def communicate_discovery(self, discovery_type, owner, x, y):
        """
        Envoie un message de découverte à tous les agents via le serveur.
        Gère les erreurs réseau et vérifie l'état de la connexion avant l'envoi.

        Args:
            discovery_type (str): Type de l'élément découvert (clé ou boîte).
            x (int): Coordonnée X de l'élément découvert.
            y (int): Coordonnée Y de l'élément découvert.
        """
        msg = {
            "sender": self.agent_id,
            "header": BROADCAST_MSG,
            "type": discovery_type,
            "position": (x, y),
            "owner": owner
        }
        try:
            # Vérifier si l'agent est encore actif
            if not self.running:
                if self.verbose:
                    print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'communicate_discovery'] - Agent not running. Message not sent.{CONSOLE_COLOR['RESET']}")
                return

            # Envoi du message
            if owner != self.agent_id:
                self.network.send(msg)
                self.internal_agent_broadcast_stat['nb_send']+=1
                if self.verbose:
                    print(f"{CONSOLE_COLOR['MAGENTA']}[BROADCAST>'communicate_discovery'] - {msg}{CONSOLE_COLOR['RESET']}")

            # Ajout d'un délai pour éviter la surcharge réseau
            sleep(0.1)

        except ConnectionResetError:
            self.running = False
            if self.verbose:
                print(f"{CONSOLE_COLOR['RED']}[ERROR>'communicate_discovery'] - Connection reset by server.{CONSOLE_COLOR['RESET']}")
                traceback.print_exc()

        except BrokenPipeError:
            self.running = False
            if self.verbose:
                print(f"{CONSOLE_COLOR['RED']}[ERROR>'communicate_discovery'] - Broken pipe. Server may be down.{CONSOLE_COLOR['RESET']}")
                traceback.print_exc()

        except Exception as e:
            if self.verbose:
                print(f"{CONSOLE_COLOR['RED']}[ERROR>'communicate_discovery'] - Unexpected error: {e}{CONSOLE_COLOR['RESET']}")
                traceback.print_exc()


    def communicate_completed_mission(self):
        msg = {
            "sender":self.agent_id,
            "header": BROADCAST_MSG,
            "nav_state": COMPLETED
        }
        self.network.send(msg)
        self.internal_agent_broadcast_stat['nb_send']+=1
        if self.verbose:
            print(f"{CONSOLE_COLOR['MAGENTA']}[BRODCAST>'communicate_completed_mission'] - {msg}{CONSOLE_COLOR['RESET']}")
        

    def move(self, direction):
        self.network.send({'sender': self.agent_id, 'header': 2, 'direction': direction})
        sleep(0.05)
        
        
    def visit_cell(self, cell):
        """
        Ajoute une cellule à la liste des cellules visitées et met à jour les cellules uniques.
        :param cell: Tuple représentant les coordonnées de la cellule (x, y)
        """
        self.visited_cells.append(cell)  # Ajouter à la liste
        self.visited_unic_cells.add(cell)  # Ajouter à l'ensemble (unique par nature)


    def get_unique_cell_count(self):
        """
        Retourne le nombre de cellules uniques visitées.
        :return: Nombre d'éléments dans visited_unic_cells
        """
        return len(self.visited_unic_cells)
    
    
    def get_visited_cell_count(self):
        """
        Retourne le nombre de cellules uniques visitées.
        :return: Nombre d'éléments dans visited_unic_cells
        """
        return len(self.visited_cells)
    
    
    def get_total_cells(self):
        total_cells = self.w * self.h
        return total_cells


    def get_data(self):
        """
        Get the value of the current cell and classify it based on known percentages.
        Returns:
            cell_type (str): The type of the cell (e.g., "KEY_NEIGHBOR", "OBSTACLE").
            cell_value (float): The raw value of the cell for numeric comparisons.
        """
        try:
            self.network.send({'sender': self.agent_id, 'header': 1})
            cell_value = float(self.msg['cell_val'])

            # Interpretation of values
            if cell_value == KEY_NEIGHBOUR_PERCENTAGE:
                return "KEY_NEIGHBOR", cell_value
            elif cell_value == 0.25:
                return "KEY_OUTER", cell_value
            elif cell_value == BOX_NEIGHBOUR_PERCENTAGE:
                return "BOX_NEIGHBOR", cell_value
            elif cell_value == 0.3:
                return "BOX_OUTER", cell_value
            elif cell_value == OBSTACLE_NEIGHBOUR_PERCENTAGE:
                return "OBSTACLE_NEIGHBOR", cell_value
            elif cell_value == 1.0:
                return "TARGET", cell_value
            else:
                return "EMPTY", cell_value
        except:
            return "UNKNOWN", -1.0  # Default return in case of error


    def get_owner(self, timeout=5):
        """
        Get the value of the current cell and classify it based on known percentages.
        Waits for a valid response with a timeout.
        Args:
            timeout (int): Maximum time in seconds to wait for a valid response.
        Returns:
            (owner, item_type): Tuple containing the owner ID and item type if successful.
            ("UNKNOWN", -1.0): Default return in case of timeout or error.
        """
        start_time = time()
        try:
            while time() - start_time < timeout:
                self.network.send({'sender': self.agent_id, 'header': GET_ITEM_OWNER})
                sleep(0.1)  # Donne un peu de temps pour recevoir une réponse

                owner = self.msg
                
                if "owner" in owner and owner["owner"] is not None:
                    return (owner["owner"], owner["type"])

            # Timeout atteint
            if self.verbose:
                print(f"{CONSOLE_COLOR['YELLOW']}[WARNING>'get_owner'] - Timeout reached while waiting for owner response.{CONSOLE_COLOR['RESET']}")
            return "UNKNOWN", -1.0

        except Exception as e:
            if self.verbose:
                print(f"{CONSOLE_COLOR['RED']}[ERROR>'get_owner'] - {e}{CONSOLE_COLOR['RESET']}")
                traceback.print_exc()
            return "UNKNOWN", -1.0  # Retour en cas d'erreur

        
    def display_robot_stat(self):
        # Utilisez l'heure actuelle pour les calculs
        end_time = self.end_date_time if self.end_date_time else datetime.now()
        
        # Calcul du temps écoulé
        elapsed_time = end_time - self.start_date_time
        elapsed_seconds = elapsed_time.total_seconds()
        
        # Nombre de cellules uniques visitées et total de cellules
        unique_cells = self.get_unique_cell_count()
        total_cells = self.get_total_cells()
        
        # Calcul du pourcentage de découverte
        percentage_discovered = (unique_cells / total_cells) * 100 if total_cells > 0 else 0
        ration_unique_vs_visited = 1 - (unique_cells/total_cells)

        print(f"""
{CONSOLE_COLOR['BLUE']}============ Robot Information ============{CONSOLE_COLOR['RESET']}
[TIME PROCESSING]
 > Start Date Time: {CONSOLE_COLOR['YELLOW']}{self.start_date_time.strftime("%Y-%m-%d %H:%M:%S")}{CONSOLE_COLOR['RESET']}
 > End Date Time: {CONSOLE_COLOR['YELLOW']}{end_time.strftime("%Y-%m-%d %H:%M:%S")}{CONSOLE_COLOR['RESET']}
 > Discovering Time: {CONSOLE_COLOR['GREEN']}{elapsed_seconds:.2f} seconds{CONSOLE_COLOR['RESET']}

 > Navigation status:
{CONSOLE_COLOR['BLUE']}{self.nav_state}{CONSOLE_COLOR['RESET']}

 > Robot coord : ({self.x}, {self.y})

[MAP INFORMATION]
 > Number of visited cells: {CONSOLE_COLOR['YELLOW']}{self.get_visited_cell_count()}{CONSOLE_COLOR['RESET']}
 > Number of unique visited cells: {CONSOLE_COLOR['GREEN']}{unique_cells}/{total_cells}{CONSOLE_COLOR['RESET']}
 > Percentage of Discovering: {CONSOLE_COLOR['GREEN']}{percentage_discovered:.2f}%{CONSOLE_COLOR['RESET']}
 > Ration of effecient discovering (total visited / unique cell discovered): {ration_unique_vs_visited}

[COMM-LINK WITH OTHER]
 > Nuber of BROADCAST_MSG send : {self.internal_agent_broadcast_stat['nb_send']}
 > Nuber of BROADCAST_MSG receive : {self.internal_agent_broadcast_stat['nb_receive']}
 > Box coord. found by other ? : {self.internal_agent_broadcast_stat['box_coord_found_by_other']}
 > Key coord. found by other ? : {self.internal_agent_broadcast_stat['key_coord_found_by_other']}
    """)

    def periodic_display(self):
        while self.running and self.nav_state["nav_state"] != 'mission_completed':  # Continue seulement si self.running est True
            current_time = datetime.now()
            if (current_time - self.last_display_time).total_seconds() >= 20:
                self.display_robot_stat()
                self.last_display_time = current_time
            sleep(1)  # Réduire l'utilisation du CPU
        self.display_robot_stat()


    def start_display_thread(self):
        display_thread = Thread(target=self.periodic_display, daemon=True)
        display_thread.start()
        print("Display thread started!")
        
    def stop(self):
        self.running = False
        print("Stopping all threads...")
        
    def wating_other_to_finished(self):
        while self.msg['header']:
            pass


if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    parser.add_argument("-r", "--run", help="Run the agent with our behavior or not : autonomous/manual", type=str, default="manual")
    parser.add_argument("-d", "--display_info", help="Display the information in agent console : false/true", type=str, default='false')
    parser.add_argument("-v", "--verbose", help="Verbose level to display in agent console : false/true", type=str, default='true')

    
    args = parser.parse_args()
    if args.verbose == 'true':
        verbose = True
    else: 
        verbose = False

    agent = Agent(args.server_ip, verbose)
    
    if args.display_info == 'true':
        agent.start_display_thread()
        
    if args.run == "autonomous":
        agent.navigate_to_points()
        agent.communicate_completed_mission()
        agent.display_robot_stat()
    else:
        try:
            while True:
                cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
                if cmds["header"] == BROADCAST_MSG:
                    cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
                    cmds["position"] = (agent.x, agent.y)
                    cmds["owner"] = randint(0, 3)
                elif cmds["header"] == MOVE:
                    cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
                agent.network.send(cmds)
        except KeyboardInterrupt:
            # Appeler stop() pour arrêter proprement les threads
            traceback.print_exc()
            pass
    agent.stop()
    print("Program terminated.")