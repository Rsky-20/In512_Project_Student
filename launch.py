import subprocess
import os
import time
import threading
import psutil  # Bibliothèque pour gérer les processus
from colorama import Fore, Style  # Pour les couleurs dans la console
import requests

processes = []  # Liste pour suivre les processus ouverts

def stream_output(process, name, color):
    """
    Redirige les sorties d'un processus vers la console principale.
    """
    for line in iter(process.stdout.readline, b''):
        print(f"{color}[{name}]{Style.RESET_ALL} {line.decode().strip()}")

def launch_all():
    """
    Lance les processus nécessaires pour le projet :
    - Serveur
    - Agent
    - Navigateur
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")

    # Commande pour le serveur
    server_command = f"cd {script_dir} && python scripts/server.py -nb 2 -i 127.0.0.1"
    server_process = subprocess.Popen(
        ["cmd", "/k", server_command],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    processes.append(server_process)
    threading.Thread(target=stream_output, args=(server_process, "server", Fore.BLUE), daemon=True).start()
    time.sleep(1)

    # Commande pour l'agent 1
    agent_command_1 = f"cd {script_dir} && python scripts/agent.py -i 127.0.0.1"
    agent_process_1 = subprocess.Popen(
        ["cmd", "/k", agent_command_1],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    processes.append(agent_process_1)
    threading.Thread(target=stream_output, args=(agent_process_1, "agent_1", Fore.GREEN), daemon=True).start()
    time.sleep(1)
    
    # Commande pour l'agent 2
    agent_command_2 = f"cd {script_dir} && python scripts/agent.py -i 127.0.0.1"
    agent_process_2 = subprocess.Popen(
        ["cmd", "/k", agent_command_2],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    processes.append(agent_process_2)
    threading.Thread(target=stream_output, args=(agent_process_2, "agent_2", Fore.GREEN), daemon=True).start()
    time.sleep(1)

    # Utiliser `requests` pour vérifier que le serveur est accessible
    url = "http://127.0.0.1:5555/"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"{Fore.CYAN}Serveur accessible à {url}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Erreur : Serveur inaccessible (Code {response.status_code}){Style.RESET_ALL}")
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}Erreur lors de la connexion au serveur : {e}{Style.RESET_ALL}")


def close_all():
    """
    Ferme tous les processus ouverts :
    - Fenêtres cmd spécifiques
    - Navigateur Internet Explorer
    """
    print("Fermeture de tous les processus...")

    for proc in processes:
        try:
            # Terminer le processus suivi dans la liste
            proc.terminate()
            proc.wait(timeout=5)
            print(f"Processus {proc.pid} terminé.")
        except Exception as e:
            print(f"Erreur lors de la fermeture du processus {proc.pid}: {e}")

    # Supplément : Fermer tous les processus `cmd.exe` et `iexplore.exe` associés
    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline"]):
        try:
            if proc.info["name"] == "cmd.exe":
                # Vérifie si la commande appartient à ce projet
                if "scripts/server.py" in " ".join(proc.info["cmdline"]) or "scripts/agent.py" in " ".join(proc.info["cmdline"]):
                    proc.kill()
                    print(f"Fenêtre cmd (PID {proc.info['pid']}) fermée.")
            elif proc.info["name"] == "iexplore.exe":
                proc.kill()
                print(f"Internet Explorer (PID {proc.info['pid']}) fermé.")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

if __name__ == '__main__':
    launch_all()
    loop = True
    while loop:
        user_input = input("Entrez une commande ('exit' pour quitter) : ")
        if user_input == 'exit':
            close_all()
            time.sleep(3)
            loop = False
    print("Fermeture complète.")
