"""Start/stop N storage-node processes + the lead node."""
import os, sys, time, shutil, subprocess, requests
from common import *
HERE = os.path.dirname(os.path.abspath(__file__))

class Cluster:
    def __init__(self, n, root, mode="parallel", rate_bps=0, placement="random"):
        self.n, self.root, self.mode, self.rate, self.placement = n, root, mode, rate_bps, placement
        self.procs = []
    def start(self):
        shutil.rmtree(self.root, ignore_errors=True); os.makedirs(self.root)
        for i in range(self.n):
            self.procs.append(subprocess.Popen([sys.executable, "node.py", str(BASE_PORT + i), f"{self.root}/node{i}"],
                              cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        self.lead = subprocess.Popen([sys.executable, "lead.py", "--nodes", str(self.n), "--work", f"{self.root}/lead",
                              "--mode", self.mode, "--rate", str(self.rate), "--placement", self.placement],
                              cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for port in [BASE_PORT + i for i in range(self.n)] + [LEAD_PORT]:
            for _ in range(100):
                try:
                    requests.get(f"http://127.0.0.1:{port}/" + ("status" if port == LEAD_PORT else "health"), timeout=0.5); break
                except Exception: time.sleep(0.1)
            else: raise RuntimeError(f"port {port} did not come up")
        return self
    def kill_node(self, i): self.procs[i].terminate(); self.procs[i].wait()
    def stop(self):
        for p in self.procs + [self.lead]:
            p.terminate()
        for p in self.procs + [self.lead]:
            try: p.wait(timeout=5)
            except Exception: p.kill()
        self.procs = []
    def __enter__(self): return self.start()
    def __exit__(self, *a): self.stop()
