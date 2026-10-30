import subprocess, sys, os
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v.strip('"\'')

procs = [
    subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000", "--reload"]),
    subprocess.Popen(["npm", "run", "dev", "--", "--port", "4321"], cwd="frontend", shell=(os.name == "nt")),
]
try:
    for p in procs: p.wait()
except KeyboardInterrupt:
    for p in procs: p.terminate()
