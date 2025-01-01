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
        self.forbidden_cells = set()

        # DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        self.msg = {}
        env_conf = self.network.receive()
        self.nb_agent_expected = 0
        self.nb_agent_connected = 0
        self.x, self.y = env_conf["x"], env_conf["y"]  # initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]  # environment dimensions
        self.agent_state = None
        self.visited_cells = set()  # Track visited cells
        cell_val = env_conf["cell_val"]  # value of the cell the agent is located in
        Thread(target=self.msg_cb, daemon=True).start()
        self.wait_for_connected_agent()

        sleep(5)

        self.points_of_interest = []
        self.navigate_to_points()
        

    def msg_cb(self):
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            self.msg = msg
            if msg["header"] == MOVE:
                self.x, self.y = msg["x"], msg["y"]
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
            point = (random.randint(0, self.w - 1), random.randint(0, self.h - 1))
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
                commands.append(DOWN_LEFT)
                current_pos[0] += 1
                current_pos[1] -= 1
            elif dx < 0 and dy > 0:
                commands.append(UP_RIGHT)
                current_pos[0] -= 1
                current_pos[1] += 1
            elif dx < 0 and dy < 0:
                commands.append(UP_LEFT)
                current_pos[0] -= 1
                current_pos[1] -= 1
            elif dx > 0:
                commands.append(DOWN)
                current_pos[0] += 1
            elif dx < 0:
                commands.append(UP)
                current_pos[0] -= 1
            elif dy > 0:
                commands.append(RIGHT)
                current_pos[1] += 1
            elif dy < 0:
                commands.append(LEFT)
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
            if not self.points_of_interest:
                self.points_of_interest = self.get_random_interest_points()
                self.points_of_interest = self.determine_order(self.points_of_interest, (self.x, self.y))
                self.orders, self.path = self.generate_path()

            if self.nav_state["nav_state"] == 'nav':
                if not self.orders or not self.path:
                    print(f"{CONSOLE_COLOR['RED']}ERROR: Orders or Path is empty during navigation! Regenerating...{CONSOLE_COLOR['RESET']}")
                    self.points_of_interest = []
                    continue

                target = self.points_of_interest[0]
                if target in self.forbidden_cells:
                    print(f"{CONSOLE_COLOR['MAGENTA']}Skipping forbidden target {target}.{CONSOLE_COLOR['RESET']}")
                    self.points_of_interest.pop(0)
                    continue

                while self.orders:
                    command = self.orders.pop(0)
                    self.nav_state["last_direction"] = command
                    self.nav_state["last_coord"] = (self.x, self.y)
                    self.move(command)
                    self.x, self.y = self.path.pop(0)
                    cell_type, cell_value = self.get_data()
                    self.visited_cells.add((self.x, self.y))

                    print(f"{CONSOLE_COLOR['CYAN']}Navigating to ({self.x}, {self.y}): {cell_type}, {cell_value}.{CONSOLE_COLOR['RESET']}")

                    if cell_type == "OBSTACLE_NEIGHBOR":
                        self.avoid_obstacle()
                        break

                    if cell_type in ["KEY_NEIGHBOR", "BOX_NEIGHBOR", "KEY_OUTER", "BOX_OUTER"]:
                        print(f"{CONSOLE_COLOR['BLUE']}Switching to hot/cold search near ({self.x}, {self.y}).{CONSOLE_COLOR['RESET']}")
                        self.nav_state["nav_state"] = 'hot_cold_search'
                        self.hot_cold_search()
                        self.orders = []
                        self.path = []
                        break

                    if cell_type == "TARGET":
                        self.handle_discovery()
                        break
                    sleep(0.1)



    def avoid_obstacle(self):
        """
        Handle obstacle by stepping back using directions from DIRECTION and OPPOSITE_DIRECTION_INDEX.
        Clears the current path after stepping back.
        """
        print(f"{CONSOLE_COLOR['YELLOW']}Obstacle detected. Changing path...{CONSOLE_COLOR['RESET']}")

        # Vérification et initialisation de la dernière direction connue
        if self.nav_state["last_direction"] is None:
            print(f"{CONSOLE_COLOR['RED']}No last direction recorded. Cannot step back.{CONSOLE_COLOR['RESET']}")
            return

        # Obtenir la direction opposée
        reverse_direction = OPPOSITE_DIRECTION_INDEX[self.nav_state["last_direction"]]

        # Reculer de 2 cases dans la direction opposée
        for _ in range(2):  # Boucle pour reculer de 2 cases
            self.move(reverse_direction)  # Utilisation de la direction
            print(f"{CONSOLE_COLOR['CYAN']}Stepped back in direction '{DIRECTION[reverse_direction]}'.{CONSOLE_COLOR['RESET']}")

        # Effacer les ordres et le chemin
        self.orders = []
        self.path = []
        print(f"{CONSOLE_COLOR['MAGENTA']}Path cleared. Navigation will reprogram if needed.{CONSOLE_COLOR['RESET']}")


    def hot_cold_search(self):
        """
        Implement a hot/cold strategy to locate cells with value 1.0.
        The robot explores neighboring cells and decides the best path based on cell values and types.
        """
        print(f"{CONSOLE_COLOR['CYAN']}Hot/Cold search initiated.{CONSOLE_COLOR['RESET']}")

        while True:
            current_cell_type, current_cell_value = self.get_data()  # Obtenez les données de la cellule actuelle
            best_direction = None
            max_value = current_cell_value  # Initialisez la valeur max avec la valeur actuelle
            original_x, original_y = self.x, self.y  # Stockez la position actuelle

            print(f"{CONSOLE_COLOR['BLUE']}Current position: ({self.x}, {self.y}), Value: {current_cell_value}.{CONSOLE_COLOR['RESET']}")

            # Explorer toutes les directions
            for direction_index, (dx, dy) in DIRECTION_MAP.items():
                nx, ny = self.x + dx, self.y + dy

                # Vérifiez les limites de la grille et les cellules visitées
                if 0 <= nx < self.w and 0 <= ny < self.h and (nx, ny) not in self.visited_cells:
                    self.move(direction_index)  # Déplacez le robot dans la direction donnée
                    self.x, self.y = nx, ny
                    neighbor_cell_type, neighbor_cell_value = self.get_data()
                    print(f"{CONSOLE_COLOR['YELLOW']}Checked cell ({nx}, {ny}): Type {neighbor_cell_type}, Value {neighbor_cell_value}.{CONSOLE_COLOR['RESET']}")

                    # Si la cellule a une meilleure valeur
                    if neighbor_cell_value > max_value:
                        max_value = neighbor_cell_value
                        best_direction = direction_index
                        print(f"{CONSOLE_COLOR['GREEN']}Better cell found at ({nx}, {ny}) with value {neighbor_cell_value}.{CONSOLE_COLOR['RESET']}")
                        break

                    # Si la valeur est inférieure ou égale, revenir à la cellule d'origine
                    self.move(OPPOSITE_DIRECTION_INDEX[direction_index])  # Revenez en arrière
                    self.x, self.y = original_x, original_y

            # Si une cellule cible est atteinte
            if max_value == 1.0:
                print(f"{CONSOLE_COLOR['GREEN']}Target found at ({self.x}, {self.y})!{CONSOLE_COLOR['RESET']}")
                self.handle_discovery()
                return

            # Si une meilleure cellule a été trouvée, continuez à partir de là
            if best_direction:
                print(f"{CONSOLE_COLOR['CYAN']}Moving to better cell in direction {DIRECTION[best_direction]} with value {max_value}.{CONSOLE_COLOR['RESET']}")
                self.move(best_direction)
                dx, dy = DIRECTION_MAP[best_direction]
                self.x += dx
                self.y += dy
                self.visited_cells.add((self.x, self.y))
            else:
                # Si aucune meilleure cellule n'est trouvée, revenez en navigation
                print(f"{CONSOLE_COLOR['MAGENTA']}No better cells found. Returning to navigation.{CONSOLE_COLOR['RESET']}")
                self.nav_state["nav_state"] = 'nav'
                return
            

    def handle_discovery(self):
        """
        Handle the discovery of keys or boxes and communicate as needed.
        """
        cell_type, _ = self.get_data()
        if cell_type == "TARGET":
            discovered_coord = (self.x, self.y)

            # Ajouter la cellule et ses voisines dans forbidden_cells
            for dx in range(-1, 2):  # Cases voisines (-1, 0, +1)
                for dy in range(-1, 2):
                    forbidden_x, forbidden_y = discovered_coord[0] + dx, discovered_coord[1] + dy
                    if 0 <= forbidden_x < self.w and 0 <= forbidden_y < self.h:
                        self.forbidden_cells.add((forbidden_x, forbidden_y))

            # Mise à jour de l'état après découverte
            if not self.nav_state["key"]["has_key"]:
                print(f"{CONSOLE_COLOR['CYAN']}Key picked up! Updating state.{CONSOLE_COLOR['RESET']}")
                self.nav_state["key"] = {"coord": discovered_coord, "has_key": True}
                self.communicate_discovery("key", *discovered_coord)

            elif not self.nav_state["box"]["box_unlocked"]:
                print(f"{CONSOLE_COLOR['CYAN']}Box found! Unlocking...{CONSOLE_COLOR['RESET']}")
                self.nav_state["box"] = {"coord": discovered_coord, "box_unlocked": True}
                self.communicate_discovery("box", *discovered_coord)

            # Décalage après découverte
            print(f"{CONSOLE_COLOR['MAGENTA']}Shifting 3 cells after discovery to avoid cycles.{CONSOLE_COLOR['RESET']}")
            self.shift_position(3)

            if self.nav_state["key"]["has_key"] and self.nav_state["box"]["box_unlocked"]:
                print(f"{CONSOLE_COLOR['GREEN']}Mission completed!{CONSOLE_COLOR['RESET']}")
                self.nav_state["nav_state"] = 'mission_completed'


    def shift_position(self, shift_distance):
        """
        Déplace le robot de shift_distance cases dans une direction disponible.
        """
        directions = [1, 2, 3, 4]  # left, right, up, down
        for direction in directions:
            valid_shift = True
            for _ in range(shift_distance):
                dx, dy = DIRECTION_MAP[direction]
                nx, ny = self.x + dx, self.y + dy
                # Vérifie si la cellule cible est valide
                if 0 <= nx < self.w and 0 <= ny < self.h and (nx, ny) not in self.forbidden_cells:
                    self.move(direction)
                    self.x, self.y = nx, ny
                    print(f"{CONSOLE_COLOR['GREEN']}Shifted to ({nx}, {ny}).{CONSOLE_COLOR['RESET']}")
                else:
                    valid_shift = False
                    break

            # Si une direction a permis de compléter le décalage, on arrête la recherche
            if valid_shift:
                return

        # Si aucune direction n'était valide pour le décalage, afficher un message d'erreur
        print(f"{CONSOLE_COLOR['RED']}Failed to shift position! Staying at ({self.x}, {self.y}).{CONSOLE_COLOR['RESET']}")



    def communicate_discovery(self, discovery_type, x, y):
        msg = {
            "header": BROADCAST_MSG,
            "type": discovery_type,
            "position": (x, y),
            "owner": self.agent_id
        }
        self.network.send(msg)
        print(f"{CONSOLE_COLOR['MAGENTA']}Broadcasted discovery: {msg}{CONSOLE_COLOR['RESET']}")


    def move(self, direction):
        self.network.send({'header': 2, 'direction': direction})
        sleep(0.05)


    def get_data(self):
        """
        Get the value of the current cell and classify it based on known percentages.
        Returns:
            cell_type (str): The type of the cell (e.g., "KEY_NEIGHBOR", "OBSTACLE").
            cell_value (float): The raw value of the cell for numeric comparisons.
        """
        try:
            self.network.send({'header': 1})
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


if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)

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
        pass
