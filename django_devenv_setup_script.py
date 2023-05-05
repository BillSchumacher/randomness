import argparse
import json
import os
import subprocess
import sys

def run_command(command):
    subprocess.run(command, shell=True, check=True)

def install_python_packages():
    run_command("python -m pip install --upgrade pip")
    run_command("pip install pyyaml django")

parser = argparse.ArgumentParser(description="Configure the development environment.")
parser.add_argument("project_name", help="The name of your Django project.")
args = parser.parse_args()

# Install required Python packages
install_python_packages()

import yaml

# Check if Chocolatey is installed on Windows
if os.name == "nt":
    choco_check = subprocess.run("choco -v", shell=True, stderr=subprocess.DEVNULL)
    if choco_check.returncode != 0:
        print("Chocolatey not found. Installing Chocolatey...")
        run_command("powershell -Command \"Start-Process -Verb RunAs -FilePath 'powershell.exe' -ArgumentList 'Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))'\"")
        print("Chocolatey installed.")

# Check if Docker Desktop and GitHub CLI are installed, install if not
if os.name == "nt":
    docker_check = subprocess.run("docker -v", shell=True, stderr=subprocess.DEVNULL)
    gh_check = subprocess.run("gh --version", shell=True, stderr=subprocess.DEVNULL)
    if docker_check.returncode != 0 or gh_check.returncode != 0:
        print("Installing Docker Desktop and GitHub CLI...")
        run_command("powershell -Command \"Start-Process -Verb RunAs -FilePath 'powershell.exe' -ArgumentList 'choco install docker-desktop gh'\"")
        print("Docker Desktop and GitHub CLI installed.")
else:
    run_command("brew install docker docker-compose gh")

# Create Docker Compose configuration
docker_compose = {
    "version": "3.8",
    "services": {
        "web": {
            "build": ".",
            "command": "python manage.py runserver 0.0.0.0:8000",
            "ports": ["8000:8000"],
            "depends_on": ["db", "cache"],
            "volumes": ["./app:/app"],
        },
        "db": {
            "image": "postgres",
            "environment": {"POSTGRES_DB": args.project_name, "POSTGRES_USER": "postgres", "POSTGRES_PASSWORD": "postgres"},
            "volumes": ["./data/db:/var/lib/postgresql/data"],
        },
        "cache": {
            "image": "redis",
            "ports": ["6379:6379"],
            "volumes": ["./data/redis:/data"],
        },
    },
}

# Configure dev container settings
devcontainer_json = {
    "name": "Dev Container",
    "dockerComposeFile": "docker-compose.yml",
    "service": "web",
    "workspaceFolder": "/app",
    "extensions": ["ms-python.python", "ms-python.vscode-pylance", "redhat.vscode-yaml", "ms-azuretools.vscode-docker"],
}


# Set up the development environment in VSCode
vscode_settings = {
    "python.pythonPath": "venv/bin/python",
    "python.linting.pylintEnabled": True,
    "python.linting.flake8Enabled": True,
    "python.formatting.provider": "black",
    "editor.formatOnSave": True,
    "files.exclude": {
        "**/.git": True,
        "**/.svn": True,
        "**/.hg": True,
        "**/.DS_Store": True,
        "**/__pycache__": True,
        "**/*.pyc": True,
        "**/*.pyo": True,
        "**/*.pyd": True,
        "**/*.sqlite3": True,
        "**/*.log": True,
    },
}


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"Error executing command: {command}\n{stderr.decode('utf-8')}")
    else:
        print(stdout.decode('utf-8'))


# Create a new Django project
run_command(f"django-admin startproject {args.project_name}")

# Change to the project directory
os.chdir(args.project_name)

os.makedirs(".vscode", exist_ok=True)
with open(".vscode/settings.json", "w") as f:
    json.dump(vscode_settings, f, indent=2)


os.makedirs(".devcontainer", exist_ok=True)
with open(".devcontainer/devcontainer.json", "w") as f:
    json.dump(devcontainer_json, f, indent=2)

with open("docker-compose.yml", "w") as f:
    yaml.dump(docker_compose, f)

# Set up a virtual environment
run_command("python -m venv venv")

# Activate the virtual environment
venv_activate = ".\\venv\\Scripts\\activate" if os.name == "nt" else "source venv/bin/activate"
run_command(venv_activate)

# Install required packages
run_command("pip install django django-rest-framework Sphinx flake8 pytest pylint black")

# Create a requirements.txt file
run_command("pip freeze > requirements.txt")

# Set up Docker
with open("Dockerfile", "w") as f:
    f.write("FROM python:3\n")
    f.write("ENV PYTHONUNBUFFERED 1\n")
    f.write("RUN mkdir /code\n")
    f.write("WORKDIR /code\n")
    f.write("COPY requirements.txt /code/\n")
    f.write("RUN pip install -r requirements.txt\n")
    f.write("COPY . /code/\n")

# Set up GitHub Actions
os.makedirs(".github/workflows", exist_ok=True)
with open(".github/workflows/main.yml", "w") as f:
    f.write("name: CI\n")
    f.write("\n")
    f.write("on: [push, pull_request]\n")
    f.write("\n")
    f.write("jobs:\n")
    f.write("  build:\n")
    f.write("    runs-on: ubuntu-latest\n")
    f.write("    steps:\n")
    f.write("    - uses: actions/checkout@v2\n")
    f.write("    - name: Set up Python\n")
    f.write("      uses: actions/setup-python@v2\n")
    f.write("      with:\n")
    f.write("        python-version: 3.x\n")
    f.write("    - name: Install dependencies\n")
    f.write("      run: |\n")
    f.write("        python -m pip install --upgrade pip\n")
    f.write("        pip install -r requirements.txt\n")
    f.write("    - name: Lint with flake8\n")
    f.write("      run: |\n")
    f.write("        flake8 .\n")
    f.write("    - name: Test with pytest\n")
    f.write("      run: |\n")
    f.write("        pytest\n")

# Initialize Git repository
run_command("git init")

# Create .gitignore file
with open(".gitignore", "w") as f:
    f.write("venv/\n")
    f.write("__pycache__/\n")
    f.write("*.pyc\n")
    f.write("*.pyo\n")
    f.write("*.pyd\n")
    f.write("*.sqlite3\n")
    f.write("*.log\n")
    f.write("Dockerfile\n")
    f.write(".vscode/\n")
    f.write("db.sqlite3\n")
    f.write("*.pyc\n")

# Initial commit
run_command("git add .")

print("Docker Compose and Dev Container setup complete.")
