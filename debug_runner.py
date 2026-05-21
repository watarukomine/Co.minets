import subprocess
import os

print("--- Check Missing Script Executing ---")
result = subprocess.run(["python", "check_missing.py"], capture_output=True, text=True)
print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
