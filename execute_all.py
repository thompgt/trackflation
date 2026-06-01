import subprocess
import os

notebooks = [
    "analysis", "200-metres_analysis", "400-metres_analysis", 
    "800-metres_analysis", "1500-metres_analysis", "5000-metres_analysis", 
    "10000-metres_analysis", "marathon_analysis", "3000-metres-steeplechase_analysis"
]

venv_jupyter = os.path.join("venv", "Scripts", "jupyter")

for nb in notebooks:
    path = os.path.join("notebooks", f"{nb}.ipynb")
    print(f"Executing {path}...")
    subprocess.run([
        venv_jupyter, "nbconvert", "--to", "notebook", "--execute", 
        path, "--output", f"{nb}.ipynb", "--inplace", "--allow-errors"
    ])
