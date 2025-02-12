import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import platform

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
    system_platform = platform.system()
    try:
        if system_platform == "Windows":
            # Commande pour Windows (ouvre dans cmd)
            process = subprocess.Popen(
                f'start cmd.exe /K "{command}"',
                stdin=subprocess.PIPE,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        elif system_platform == "Linux":
            # Commande pour Linux (ouvre dans un terminal gnome-terminal ou xterm)
            process = subprocess.Popen(
                ["gnome-terminal", "--", "bash", "-c", f"{command}; exec bash"]  # Pour GNOME Terminal
                if os.environ.get("XDG_CURRENT_DESKTOP") == "GNOME"
                else ["xterm", "-e", f"{command}; exec bash"],  # Alternative pour xterm
                stdin=subprocess.PIPE,
                shell=False
            )
        else:
            raise OSError(f"Système d'exploitation non pris en charge : {system_platform}")
        open_processes.append(process)
    except FileNotFoundError as e:
        print(f"Erreur : {e}")
        messagebox.showerror("Erreur", f"Terminal non trouvé pour le système {system_platform}. Vérifiez votre configuration.")

# Fonction pour arrêter tous les processus
def close_all_processes(validate_button, server_button):
    global server_running
    if open_processes:
        processes_to_remove = []
        for process in open_processes:
            try:
                # Vérifie si le processus est toujours actif
                if process.poll() is None:  # Si le processus est encore actif
                    process.terminate()  # Tente de terminer le processus proprement
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
    reset_ui(validate_button, server_button, agent_buttons)


# Fonction pour réinitialiser l'interface utilisateur
def reset_ui(validate_button, server_button, param_widgets):
    validate_button.config(state=tk.NORMAL)
    server_button.config(state=tk.DISABLED, text="Démarrer le Serveur", bg="gray")
    for widget in param_widgets:
        widget.config(state=tk.NORMAL)
    for button in agent_buttons:
        button.destroy()
    agent_buttons.clear()


# Interface principale
def create_gui():
    root = tk.Tk()
    root.title("Simulation Launcher")
    root.geometry("600x500")

    # Widgets pour les configurations
    ttk.Label(root, text="Mode de configuration:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    config_mode_var = tk.StringVar(value="Client-Server")
    config_combobox = ttk.Combobox(root, textvariable=config_mode_var, values=["Client Only", "Server Only", "Client-Server"], state="readonly")
    config_combobox.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(root, text="Adresse du serveur:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
    server_address_entry = ttk.Entry(root)
    server_address_entry.insert(0, "127.0.0.1")
    server_address_entry.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(root, text="Nombre d'agents:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
    agent_count_spinbox = ttk.Spinbox(root, from_=1, to=4, width=5)
    agent_count_spinbox.grid(row=2, column=1, padx=5, pady=5)

    ttk.Label(root, text="Carte à utiliser:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
    map_spinbox = ttk.Spinbox(root, from_=1, to=3, width=5)
    map_spinbox.grid(row=3, column=1, padx=5, pady=5)

    ttk.Label(root, text="Verbose:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
    verbose_var = tk.StringVar(value="true")
    verbose_combobox = ttk.Combobox(root, textvariable=verbose_var, values=["true", "false"], state="readonly")
    verbose_combobox.grid(row=4, column=1, padx=5, pady=5)

    ttk.Label(root, text="Mode:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
    mode_var = tk.StringVar(value="autonomous")
    mode_combobox = ttk.Combobox(root, textvariable=mode_var, values=["autonomous", "manual"], state="readonly")
    mode_combobox.grid(row=5, column=1, padx=5, pady=5)

    ttk.Label(root, text="Afficher infos agents:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
    display_info_var = tk.StringVar(value="true")
    display_info_combobox = ttk.Combobox(root, textvariable=display_info_var, values=["true", "false"], state="readonly")
    display_info_combobox.grid(row=6, column=1, padx=5, pady=5)

    param_widgets = [
        server_address_entry, agent_count_spinbox, map_spinbox,
        verbose_combobox, mode_combobox, display_info_combobox
    ]

    def validate_config():
        global number_of_agents
        mode = config_mode_var.get()
        try:
            number_of_agents = int(agent_count_spinbox.get())
            validate_button.config(state=tk.DISABLED)

            if mode == "Client Only":
                server_button.config(state=tk.DISABLED)
            elif mode == "Server Only" or mode == "Client-Server":
                server_button.config(state=tk.NORMAL)

            # Bloque les widgets après validation
            for widget in param_widgets:
                widget.config(state=tk.DISABLED)

            if mode != "Server Only":
                add_agent_buttons()
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide pour les agents.")

    def update_ui():
        mode = config_mode_var.get()
        if mode == "Client Only":
            server_address_entry.config(state="normal")
            server_button.grid_remove()
            agent_count_spinbox.config(state="normal")
            map_spinbox.config(state="disabled")
            verbose_combobox.config(state="normal")
            mode_combobox.config(state="normal")
            display_info_combobox.config(state="normal")

        elif mode == "Server Only":
            server_address_entry.config(state="normal")
            server_button.grid(row=7, column=1, padx=5, pady=5)
            agent_count_spinbox.config(state="normal")
            map_spinbox.config(state="normal")
            verbose_combobox.config(state="disabled")
            mode_combobox.config(state="disabled")
            display_info_combobox.config(state="disabled")

        elif mode == "Client-Server":
            server_address_entry.config(state="normal")
            server_button.grid(row=7, column=1, padx=5, pady=5)
            agent_count_spinbox.config(state="normal")
            map_spinbox.config(state="normal")
            verbose_combobox.config(state="normal")
            mode_combobox.config(state="normal")
            display_info_combobox.config(state="normal")

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
        if not server_running and config_mode_var.get() == 'Client-Server':
            messagebox.showerror("Erreur", "Le serveur doit être démarré avant de lancer les agents.")
            return
        agent_button = agent_buttons[agent_index]
        agent_button.config(bg="green", text=f"Agent {agent_index} Démarré")
        command = f"python -u scripts/agent.py --server_ip {server_address_entry.get()} --run {mode_var.get()} --display_info {display_info_var.get()} --verbose {verbose_var.get()}"
        run_in_console(command)

    def close_all():
        close_all_processes(validate_button, server_button)

    validate_button = ttk.Button(root, text="Valider Paramétrage", command=validate_config)
    validate_button.grid(row=7, column=0, padx=5, pady=5)

    server_button = tk.Button(root, text="Démarrer le Serveur", command=toggle_server, bg="gray", state=tk.DISABLED)
    server_button.grid(row=7, column=1, padx=5, pady=5)

    ttk.Button(root, text="Arrêter Tous", command=close_all).grid(row=8, column=0, padx=5, pady=5)

    def add_agent_buttons():
        for i in range(number_of_agents):
            agent_button = tk.Button(root, text=f"Lancer Agent {i}", command=lambda idx=i: toggle_agent(idx), bg="gray")
            agent_button.grid(row=9 + i, column=0, padx=5, pady=5)
            agent_buttons.append(agent_button)

    config_combobox.bind("<<ComboboxSelected>>", lambda _: update_ui())

    root.mainloop()


if __name__ == "__main__":
    create_gui()
