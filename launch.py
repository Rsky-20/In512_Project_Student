import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# Répertoire des logs
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
os.makedirs(LOG_DIR, exist_ok=True)

# Variables globales
number_of_agents = 0  # Nombre d'agents configuré
server_running = False  # Statut du serveur
agent_buttons = []  # Liste des boutons des agents
open_processes = []  # Liste des processus ouverts


# Fonction pour exécuter une commande dans une console distincte et stocker le processus
def run_in_console(command):
    process = subprocess.Popen(
        f'start cmd.exe /K "{command}"',  # Ouvre directement CMD avec la commande
        stdin=subprocess.PIPE,
        shell=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP  # Crée un nouveau groupe de processus
    )
    open_processes.append(process.pid)

# Fonction pour arrêter tous les processus
def close_all_processes(validate_button, server_button, open_processes):
    global server_running
    if open_processes:
        processes_to_remove = []
        for process in open_processes:
            try:
                # Vérifie si le processus est toujours actif
                if process.poll() is None:  # Si le processus est encore actif
                    process.kill()  # Tente de terminer le processus proprement
                    process.wait(timeout=5)  # Attendre jusqu'à 5 secondes que le processus se termine
                processes_to_remove.append(process)
            except Exception as e:
                print(f"Erreur lors de la fermeture d'un processus : {e}")
        
        # Nettoie les processus terminés de la liste
        for process in processes_to_remove:
            open_processes.remove(process)

        if open_processes:
            print(f"Certains processus n'ont pas pu être fermés : {len(open_processes)} restant(s).")
        else:
            print("Tous les processus ont été arrêtés.")
            messagebox.showinfo("Arrêt", "Tous les processus ont été arrêtés.")
    else:
        messagebox.showinfo("Arrêt", "Aucun processus en cours.")
    
    # Réinitialise l'état du serveur
    server_running = False
    reset_ui(validate_button, server_button)


# Fonction pour réinitialiser l'interface utilisateur
def reset_ui(validate_button, server_button):
    validate_button.config(state=tk.NORMAL)
    server_button.config(state=tk.DISABLED, text="Démarrer le Serveur", bg="gray")
    for button in agent_buttons:
        button.destroy()
    agent_buttons.clear()


# Interface principale
def create_gui():
    root = tk.Tk()
    root.title("Simulation Launcher")
    root.geometry("600x500")

    # Widgets pour les configurations
    ttk.Label(root, text="Adresse du serveur:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    server_address_entry = ttk.Entry(root)
    server_address_entry.insert(0, "127.0.0.1")
    server_address_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(root, text="Nombre d'agents:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    agent_count_spinbox = ttk.Spinbox(root, from_=1, to=4, width=5)
    agent_count_spinbox.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(root, text="Carte à utiliser:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    map_spinbox = ttk.Spinbox(root, from_=1, to=3, width=5)
    map_spinbox.grid(row=2, column=1, padx=5, pady=5)

    # Remplacement des checkbuttons par des comboboxes
    ttk.Label(root, text="Verbose:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    verbose_var = tk.StringVar(value="true")
    verbose_combobox = ttk.Combobox(root, textvariable=verbose_var, values=["true", "false"], state="readonly")
    verbose_combobox.grid(row=3, column=1, padx=5, pady=5)

    ttk.Label(root, text="Mode:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    mode_var = tk.StringVar(value="autonomous")
    mode_combobox = ttk.Combobox(root, textvariable=mode_var, values=["autonomous", "manual"], state="readonly")
    mode_combobox.grid(row=4, column=1, padx=5, pady=5)

    ttk.Label(root, text="Afficher infos agents:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
    display_info_var = tk.StringVar(value="true")
    display_info_combobox = ttk.Combobox(root, textvariable=display_info_var, values=["true", "false"], state="readonly")
    display_info_combobox.grid(row=5, column=1, padx=5, pady=5)

    def validate_config():
        global number_of_agents
        try:
            number_of_agents = int(agent_count_spinbox.get())
            validate_button.config(state=tk.DISABLED)
            server_button.config(state=tk.NORMAL)
            add_agent_buttons()
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide pour les agents.")

    def toggle_server():
        global server_running
        if server_running:
            messagebox.showinfo("Serveur", "Le serveur est déjà en cours d'exécution.")
            return
        command = f"python -u scripts/server.py --nb_agents {number_of_agents} --map_id {map_spinbox.get()} --ip_server {server_address_entry.get()}"
        run_in_console(command)
        server_button.config(text="Serveur Démarré", bg="green")
        server_running = True

    def toggle_agent(agent_index):
        if not server_running:
            messagebox.showerror("Erreur", "Le serveur doit être démarré avant de lancer les agents.")
            return
        agent_button = agent_buttons[agent_index]
        agent_button.config(bg="green", text=f"Agent {agent_index} Démarré")
        command = f"python -u scripts/agent.py --server_ip {server_address_entry.get()} --run {mode_var.get()} --display_info {display_info_var.get()} --verbose {verbose_var.get()}"
        run_in_console(command)

    def close_all():
        close_all_processes(validate_button, server_button, open_processes)

    validate_button = ttk.Button(root, text="Valider Configuration", command=validate_config)
    validate_button.grid(row=6, column=0, padx=5, pady=5)

    server_button = tk.Button(root, text="Démarrer le Serveur", command=toggle_server, bg="gray", state=tk.DISABLED)
    server_button.grid(row=6, column=1, padx=5, pady=5)

    ttk.Button(root, text="Arrêter Tous", command=close_all).grid(row=7, column=0, padx=5, pady=5)

    def add_agent_buttons():
        for i in range(number_of_agents):
            agent_button = tk.Button(root, text=f"Lancer Agent {i}", command=lambda idx=i: toggle_agent(idx), bg="gray")
            agent_button.grid(row=8 + i, column=0, padx=5, pady=5)
            agent_buttons.append(agent_button)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
