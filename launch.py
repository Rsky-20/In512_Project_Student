import os
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Répertoire des logs
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
os.makedirs(LOG_DIR, exist_ok=True)

# Variables globales
number_of_agents = 0  # Nombre d'agents configuré
server_running = False  # Statut du serveur
agent_buttons = []  # Liste des boutons des agents

# Fonction pour exécuter une commande dans une console distincte
def run_in_console(command):
    subprocess.Popen(
        f'start cmd.exe /K "{command}"',
        shell=True
    )

# Fonction pour arrêter tous les processus
def close_all_processes(validate_button, agent_count_entry, server_button):
    global server_running
    if server_running:
        server_running = False
        messagebox.showinfo("Arrêt", "Tous les processus ont été arrêtés.")
    reset_ui(validate_button, agent_count_entry, server_button)

# Fonction pour réinitialiser l'interface utilisateur
def reset_ui(validate_button, agent_count_entry, server_button):
    validate_button.config(state=tk.NORMAL)
    agent_count_entry.config(state=tk.NORMAL)
    server_button.config(state=tk.DISABLED, text="Démarrer le Serveur", bg="gray")
    for button in agent_buttons:
        button.destroy()
    agent_buttons.clear()

# Interface principale
def create_gui():
    root = tk.Tk()
    root.title("Simulation Launcher")
    root.geometry("600x400")

    def validate_agents():
        global number_of_agents
        try:
            num_agents = int(agent_count_entry.get())
            if num_agents < 1:
                raise ValueError("Le nombre d'agents doit être supérieur ou égal à 1.")
            number_of_agents = num_agents
            validate_button.config(state=tk.DISABLED)
            agent_count_entry.config(state=tk.DISABLED)
            server_button.config(state=tk.NORMAL)
            add_agent_buttons()
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))

    def toggle_server():
        global server_running
        if server_running:
            messagebox.showinfo("Serveur", "Le serveur est déjà en cours d'exécution.")
            return
        command = f"python -u {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts/server.py')} -nb {number_of_agents}"
        run_in_console(command)
        server_button.config(text="Serveur Démarré", bg="green")
        server_running = True

    def toggle_agent(agent_index):
        if not server_running:
            messagebox.showerror("Erreur", "Le serveur doit être démarré avant de lancer les agents.")
            return

        # Change la couleur du bouton et lance la console
        agent_button = agent_buttons[agent_index]
        agent_button.config(bg="green", text=f"Agent {agent_index} Démarré")
        command = f"python -u {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts/agent.py')} --run autonomous --display_info true"
        run_in_console(command)
        

    def close_all():
        close_all_processes(validate_button, agent_count_entry, server_button)

    # Interface Tkinter
    ttk.Label(root, text="Nombre d'agents:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    agent_count_entry = ttk.Entry(root)
    agent_count_entry.grid(row=0, column=1, padx=5, pady=5)

    validate_button = ttk.Button(root, text="Valider le nombre d'agents", command=validate_agents)
    validate_button.grid(row=0, column=2, padx=5, pady=5)

    server_button = tk.Button(root, text="Démarrer le Serveur", command=toggle_server, bg="gray", state=tk.DISABLED)
    server_button.grid(row=1, column=0, padx=5, pady=5)

    ttk.Button(root, text="Arrêter Tous", command=close_all).grid(row=1, column=2, padx=5, pady=5)

    def add_agent_buttons():
        for i in range(number_of_agents):
            agent_button = tk.Button(root, text=f"Lancer Agent {i}", command=lambda idx=i: toggle_agent(idx), bg="gray")
            agent_button.grid(row=2 + i, column=0, padx=5, pady=5)
            agent_buttons.append(agent_button)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
