__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

import pygame, os
from my_constants import * 

img_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "img")


class GUI:
    def __init__(self, game, fps=10, cell_size=25):
        self.game = game
        self.w, self.h = self.game.map_w, self.game.map_h
        self.fps = fps
        self.clock = pygame.time.Clock()
        self.cell_size = cell_size
        self.screen_res = (self.w*cell_size, self.h*cell_size)      


    def on_init(self):
        pygame.init()
        self.screen = pygame.display.set_mode(self.screen_res)
        pygame.display.set_icon(pygame.image.load(img_folder + "/icon.png"))
        pygame.display.set_caption("IN512 Project")
        self.create_items()        
        self.running = True


    def create_items(self):
        #box
        box_img = pygame.image.load(img_folder + "/box.png")
        box_img = pygame.transform.scale(box_img, (self.cell_size, self.cell_size))
        self.boxes = [box_img.copy() for _ in range(self.game.nb_agents)]
        #keys
        key_img = pygame.image.load(img_folder + "/key.png")
        key_img = pygame.transform.scale(key_img, (self.cell_size, self.cell_size))
        self.keys = [key_img.copy() for _ in range(self.game.nb_agents)]
        #agent text number
        self.font = pygame.font.SysFont("Arial", self.cell_size//4, True)
        self.text_agents = [self.font.render(f"{i+1}", True, self.game.agents[i].color) for i in range(self.game.nb_agents)]
        #agent_img
        agent_img = pygame.image.load(img_folder + "/robot.png")
        agent_img = pygame.transform.scale(agent_img, (self.cell_size, self.cell_size))
        self.agents = [agent_img.copy() for _ in range(self.game.nb_agents)]
        #obstacle_img
        obstacle_img = pygame.image.load(img_folder + "/obstacle.png")
        obstacle_img = pygame.transform.scale(obstacle_img, (self.cell_size, self.cell_size))  # Utilise obstacle_img
        self.obstacle = [obstacle_img.copy() for _ in range(self.game.nb_agents)]


    
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

    
    def on_cleanup(self):
        pygame.event.pump()
        pygame.quit()
    

    def render(self):
        try:
            self.on_init()
            while self.running:
                for event in pygame.event.get():
                    self.on_event(event)    
                self.draw()
                self.clock.tick(self.fps)
            self.on_cleanup()
        except Exception:
            pass
    

    def draw(self):
        self.screen.fill(BG_COLOR)
        #Grid
        for i in range(1, self.h):
            pygame.draw.line(self.screen, BLACK, (0, i*self.cell_size), (self.w*self.cell_size, i*self.cell_size))
        for j in range(1, self.w):
            pygame.draw.line(self.screen, BLACK, (j*self.cell_size, 0), (j*self.cell_size, self.h*self.cell_size))
            
        # Display cell values
        if hasattr(self.game, "map_real"):
            for y in range(self.game.map_real.shape[0]):
                for x in range(self.game.map_real.shape[1]):
                    cell_value = self.game.map_real[y, x]
                    text_surface = self.font.render(f"{cell_value:.2f}", True, (169, 169, 169))  # Gray color
                    text_rect = text_surface.get_rect(center=(x * self.cell_size + self.cell_size // 2, y * self.cell_size + self.cell_size // 2))
                    self.screen.blit(text_surface, text_rect)

        for i in range(self.game.nb_agents):
            #agent_paths
            for x, y in self.game.agent_paths[i]:
                pygame.draw.rect(self.screen, self.game.agents[i].color, (x*self.cell_size, y*self.cell_size, self.cell_size, self.cell_size))

        for i in range(self.game.nb_agents):            
            #keys
            pygame.draw.rect(self.screen, self.game.agents[i].color, (self.game.keys[i].x*self.cell_size, self.game.keys[i].y*self.cell_size, self.cell_size, self.cell_size), width=3)
            self.screen.blit(self.keys[i], self.keys[i].get_rect(topleft=(self.game.keys[i].x*self.cell_size, self.game.keys[i].y*self.cell_size)))
            
            #boxes
            pygame.draw.rect(self.screen, self.game.agents[i].color, (self.game.boxes[i].x*self.cell_size, self.game.boxes[i].y*self.cell_size, self.cell_size, self.cell_size), width=3)
            self.screen.blit(self.boxes[i], self.boxes[i].get_rect(topleft=(self.game.boxes[i].x*self.cell_size, self.game.boxes[i].y*self.cell_size)))
            
            #agents
            self.screen.blit(self.agents[i], self.agents[i].get_rect(center=(self.game.agents[i].x*self.cell_size + self.cell_size//2, self.game.agents[i].y*self.cell_size + self.cell_size//2)))
            self.screen.blit(self.text_agents[i], self.text_agents[i].get_rect(center=(self.game.agents[i].x*self.cell_size + self.cell_size-self.text_agents[i].get_width()//2, self.game.agents[i].y*self.cell_size + self.cell_size-self.text_agents[i].get_height()//2)))
            
        # Affiche les obstacles
        if hasattr(self.game, 'map_real'):  # Vérifie si la matrice existe
            for y in range(self.game.map_real.shape[0]):  # Parcourt les lignes de la matrice
                for x in range(self.game.map_real.shape[1]):  # Parcourt les colonnes de la matrice
                    cell_value = self.game.map_real[y, x]
                    
                    # Vérifie si c'est un centre d'obstacle (1.0)
                    if cell_value == 1.0:
                        # Vérifie que cette cellule n'est pas masquée par un robot, une clé ou une boîte
                        is_free = True
                        if hasattr(self.game, 'agents'):
                            is_free &= not any(agent.x == x and agent.y == y for agent in self.game.agents)
                        if hasattr(self.game, 'keys'):
                            is_free &= not any(key.x == x and key.y == y for key in self.game.keys)
                        if hasattr(self.game, 'boxes'):
                            is_free &= not any(box.x == x and box.y == y for box in self.game.boxes)
                        
                        # Si la cellule est libre, affiche l'icône de l'obstacle
                        if is_free:
                            self.screen.blit(
                                self.obstacle[0],
                                self.obstacle[0].get_rect(topleft=(x * self.cell_size, y * self.cell_size))
                            )
        
        pygame.display.update()