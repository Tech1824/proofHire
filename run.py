import subprocess, sys, os
procs = [
    subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--reload"]),
    subprocess.Popen(["npm", "run", "dev", "--", "--port", "4321"], cwd="frontend", shell=(os.name == "nt")),
]
try:
    for p in procs: p.wait()
except KeyboardInterrupt:
    for p in procs: p.terminate()
