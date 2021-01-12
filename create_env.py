import os
from tkinter import filedialog, Tk
from sys import platform
import subprocess
import sys

root = Tk()
root.withdraw()
requirements_path = r'C:\Users\vmenshikov\PycharmProjects\TestGenerator\requirements.txt'
env_path = os.path.join(filedialog.askdirectory(), 'venv')


def create_env(env_path, requirements_path):
    if not os.path.exists(env_path):
        subprocess.call([sys.executable, '-m', 'venv', env_path])
        if platform == "win32":
            python_interpreter = os.path.join(env_path, 'Scripts', 'python.exe')
        else:
            python_interpreter = os.path.join(env_path, 'bin', 'python')
        subprocess.call([python_interpreter, '-m', 'pip', 'install', '--upgrade', 'pip'])
        subprocess.call([python_interpreter, '-m', 'pip', 'install', '-r', requirements_path])
    else:
        print("INFO: %s exists." % (env_path))


create_env(env_path, requirements_path)
