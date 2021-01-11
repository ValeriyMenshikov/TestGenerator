import os
from tkinter import filedialog, Tk
import subprocess
import sys


root = Tk()
root.withdraw()
requirements_path = r'C:\Users\vmenshikov\PycharmProjects\TestGenerator\requirements.txt'
env_path = filedialog.askdirectory() + '/venv'

if not os.path.exists(env_path):
    subprocess.call([sys.executable, '-m', 'venv', env_path])
    python_interpreter = os.path.join(env_path, 'Scripts', 'python.exe')
    subprocess.call([python_interpreter, '-m', 'pip', 'install', '--upgrade', 'pip'])
    for package in open(requirements_path):
        subprocess.call([python_interpreter, '-m', 'pip', 'install', package])
else:
    print("INFO: %s exists." % (env_path))


