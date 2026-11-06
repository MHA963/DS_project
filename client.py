"""Tiny REST client used by tests and benchmarks (and usable from the shell)."""
import sys, time, requests
from common import throttled, LEAD_PORT

class Client:
    def __init__(self, port=LEAD_PORT, rate_bps=None):
        self.base = f"http://127.0.0.1:{port}"; self.s = requests.Session(); self.rate = rate_bps
    def store(self, name, data):
        r = self.s.put(f"{self.base}/files/{name}", data=throttled(data, self.rate) if self.rate else data, timeout=120)
        return r
    def retrieve(self, name, version=None):
        r = self.s.get(f"{self.base}/files/{name}", params={"version": version} if version else None, timeout=120)
        return r
    def delete(self, name): return self.s.delete(f"{self.base}/files/{name}")

if __name__ == "__main__":      # python client.py store|get <name> [localfile]
    c = Client(); cmd, name = sys.argv[1], sys.argv[2]
    if cmd == "store": print(c.store(name, open(sys.argv[3], "rb").read()).json())
    else:
        r = c.retrieve(name); open(sys.argv[3] if len(sys.argv) > 3 else name, "wb").write(r.content); print("version", r.headers.get("X-Version"))
