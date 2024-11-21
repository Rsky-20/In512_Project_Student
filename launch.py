import subprocess
import os
import time
import psutil  # Bibliothèque pour gérer les processus

process = []

def launch_all():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(script_dir)
    
    commande_terminal1 = f"cd {script_dir} && python scripts/server.py -nb 2 -i 127.0.0.1"
    
    # Ouvrir un terminal et exécuter une commande
    subprocess.run(["start", "cmd", "/k", commande_terminal1], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    time.sleep(1)

    commande_terminal2 = f"cd {script_dir} && python scripts/agent.py -i 127.0.0.1"
    # Ouvrir un autre terminal et exécuter une commande différente
    subprocess.run(["start", "cmd", "/k", commande_terminal2], shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    time.sleep(2)
    # URL à ouvrir
    url = "http://127.0.0.1:5555/"
    # Chemin potentiel de l'exécutable Internet Explorer
    ie_path = "C:\\Program Files\\Internet Explorer\\iexplore.exe"

    # Vérifier si Internet Explorer est installé
    if os.path.exists(ie_path):
        # Lancer Internet Explorer
        subprocess.Popen([ie_path, url])
    else:
        print("Internet Explorer n'est pas installé ou n'est pas trouvé.")
    0

def close_all():
    # Fermer Internet Explorer en utilisant le PID
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'iexplore.exe':  # Vérifie les processus associés à Internet Explorer
            proc.kill()  # Terminer le processus
            print(f"Processus {proc.info['pid']} fermé.")
        if proc.info['name'] == 'cmd.exe':
            proc.kill()  # Terminer le processus
            print(f"Processus {proc.info['pid']} fermé.")

if __name__=='__main__':
    launch_all()
    loop=True
    while loop:
        user_input = input("Entrez quelque chose : ")
        print(f"Vous avez entré : {user_input}")
        if user_input == 'exit':
            close_all()
            time.sleep(3)
            loop=False
    print("Close app")
