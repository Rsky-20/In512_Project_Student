# IN512_Project - Unlock Boxes - Intelligent Distributed Systems

|                       | **Details**                                                           |
|-----------------------|-----------------------------------------------------------------------|
| **Date of Creation**  | 18.11.2024                                                            |
| **Team**              | Emma CADOT, Valentin DESFORGES, Sylvain LAGARENNE, Pierre VAUDRY      |
| **Version**           | v7.01.2025                                                            |
| **Python Version**    | Python 3.12.2                                                         |          

![Description of the image](resources/img/wall-e.png)

# Table of Contents

1. [IN512_Project - Unlock Boxes - Intelligent Distributed Systems](#in512_project---unlock-boxes---intelligent-distributed-systems)
    - [Project Details](#project-details)
    - [Team and Version Information](#team-and-version-information)

2. [Overview](#overview)

3. [Features](#features)
    - [Navigation](#navigation)
    - [Detection](#detection)
    - [Communication](#communication)
    - [Obstacle Avoidance](#obstacle-avoidance)
    - [Collaboration](#collaboration)

4. [Key Components](#key-components)
    - [Random Point Generation](#random-point-generation)
    - [Hot/Cold Search Algorithm](#hotcold-search-algorithm)
    - [Message Broadcasting](#message-broadcasting)

5. [Install Python Environment and Libraries](#install-python-environment-and-library)
    - [Installation Steps](#installation-steps)

6. [Git](#git)
    - [Install Git](#install-git)
    - [Configure Git for GitHub](#configure-git-for-github)

7. [Clone the Repository](#clone-the-repository)

8. [Instructions to Run the Scripts](#instructions-to-run-the-scripts)
    - [Run the Application Locally with 2 Agents](#run-the-application-with-2-agents-locally)
    - [Run the Application on Several Computers](#run-the-application-with-2-agents-on-several-computers)
    - [Run the Application with GUI](#run-the-application-with-gui)

---

## Overview
This project is part of the IN512 course and focuses on implementing a system of collaborative robots navigating a grid to complete their missions. Each robot is tasked with locating its unique key and corresponding box while navigating efficiently, avoiding obstacles, and communicating with other robots.

## Features
- **Navigation**: Robots navigate by targeting the furthest randomly generated points near the grid's border using Euclidean distance.
- **Detection**: Robots detect objects such as keys, boxes, and obstacles by interpreting cell values in the grid.
- **Communication**: Robots communicate discoveries (keys, boxes) using a broadcast message protocol to assist other agents.
- **Obstacle Avoidance**: Robots adapt their path to avoid obstacles by stepping back and recalculating their route.
- **Collaboration**: Robots share information to optimize their search and minimize redundant paths.

## Key Components
- **Random Point Generation**: Robots generate points of interest to explore the map effectively.
- **Hot/Cold Search Algorithm**: Robots use a gradient-based approach to locate keys and boxes.
- **Message Broadcasting**: Robots broadcast discoveries to the server, which relays them to other agents.


## Install python env and library
If not yet installed, open a terminal and run the following instruction:

```bash
python -m env .venv

source .\.venv\Scripts\activate # macOS/Linux
.\.venv\Scripts\activate        # Windows

pip install -r requirements.txt # Windows/Linux
pip3 install -r requirements.txt # macOS
```

If you have any difficulty with the installation, please call your teacher.

## Git
### Install Git
Git is a tool used for source code management. You can use it to create your own version of the project and share it with your group members. GitHub will be used to host your repository.</br>
To check if git is already installed on your computer, open a terminal and enter: **git**. If an error appears, you have to install it using [this link](https://git-scm.com/downloads).

### Configure git for GitHub
If you planned to create your own GitHub repository for this project, [create a GitHub account](https://github.com/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F&source=header-home) if you don't already have one.</br>
Once the account is created, open a terminal to enter details about your GitHub account so that git will be able to manipulate your future projects:
```bash
git config --global user.name "Your GitHub username"
git config --global user.email "The email address used when you created your GitHub account"
```

## Clone the repository
To have a local version of this GitHub repository, you have to clone it. Run the following instructions in a terminal:
<!-- ### Clone it with VS Code
1. Copy the url of the repository
2. On VS Code, press **Ctrl + Shift + P** (on Windows) or **Cmd + Shift + P** (on MAC OS) to open the command palette.
3. Press **clone** then click on **Gt:clone**.
4. Paste the url copied from step 1 then press 'Enter'.
5. In the pop-up window, specify where you want to clone the project.

### Clone it with command lines
Another solution is to open a terminal and run: -->
```bash
cd your_desired_path
git clone https://github.com/AybukeOzturk/In512_Project_Student
```

## Instructions to run the scripts
### Run the application with 2 agents, locally
1. Run the server
```bash
python scripts/server.py -nb 2 #On windows
python3 scripts/server.py -nb 2 #On MAC OS
```

2. Open two other terminals and run, **for each of them**, the following instruction:
(Default: 127.0.0.1)
```bash
python scripts/agent.py #On windows
python3 scripts/agent.py #On MAC OS
```

Once both terminals run the agent script, the environment should appear.


### Run the application with 2 agents on several computers
1. Run the server on one of the computers by specifing its ip address (for instance if the computer's ip address is X.X.X.X):
```bash
python scripts/server.py -nb 2 -i X.X.X.X #On windows
python3 scripts/server.py -nb 2 -i X.X.X.X #On MAC OS
```

2. On each computer, run one of the agents as follow:
```bash
python scripts/agent.py -i X.X.X.X #On windows
python3 scripts/agent.py -i X.X.X.X #On MAC OS
```

### Run the application with 2 agents on several computers
```bash
python scripts/server.py -nb 2 -i X.X.X.X #On windows
python3 scripts/server.py -nb 2 -i X.X.X.X #On MAC OS
```

Once both terminals run the agent script, the environment should appear on the computer that hosts the server.

### Run the application with GUI
```bash
python scripts/launch.py #On windows
python3 scripts/launch.py #On MAC OS
```
