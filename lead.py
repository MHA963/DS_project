"""Lead node: REST front end, metadata (SQLite), placement, replication fan-out, read failover.

POST/PUT /files/<name>          store (name may carry _vN; otherwise next version is assigned)
GET      /files/<name>[?version=N]   latest (or given / _vN) version
GET      /files/<name>/info     metadata
DELETE   /files/<name>          remove all versions (used by benchmark cleanup)
GET      /status                node liveness
"""
import os, sys, json, random, sqlite3, threading, itertools
import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, Response, jsonify
from common import *

class Lead:
    def __init__(self, n_nodes, workdir, mode="parallel", rate_bps=None,
                 placement="random", base_port=BASE_PORT, seed=None):
        self.n, self.mode, self.rate, self.placement = n_nodes, mode, rate_bps, placement
        self.base_port = base_port
        self.rng = random.Random(seed)
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=REPLICAS * 4)
        self.sess = threading.local()
        os.makedirs(workdir, exist_ok=True)
        self.db = sqlite3.connect(os.path.join(workdir, "meta.db"), check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS files(
            base TEXT, version INT, size INT, sha TEXT, nodes TEXT, PRIMARY KEY(base, version))""")
        self.db.commit()
        # MinCopysets-style groups: split nodes into disjoint groups of REPLICAS (N divisible by 3)
        self.groups = [list(range(i, i + REPLICAS)) for i in range(0, n_nodes - n_nodes % REPLICAS, REPLICAS)]

    def url(self, node, key): return f"http://127.0.0.1:{self.base_port + node}/blob/{key}"

    def session(self):
        if not hasattr(self.sess, "s"): self.sess.s = requests.Session()
        return self.sess.s

    def alive(self):
        out = []
        for i in range(self.n):
            try:
                requests.get(f"http://127.0.0.1:{self.base_port + i}/health", timeout=0.5); out.append(i)
            except Exception: pass
        return out

    def choose_nodes(self):
        if self.placement == "groups":                      # all replicas of a file in one fixed group
            return list(self.rng.choice(self.groups))
        return self.rng.sample(range(self.n), REPLICAS)     # random replication, 3 distinct nodes

    def _send(self, node, key, data, digest):
        r = self.session().put(self.url(node, key), data=throttled(data, self.rate) if self.rate else data,
                               headers={"X-Sha256": digest}, timeout=60)
        r.raise_for_status()
        return node

    def store(self, filename, data):
        base, ver = parse_name(filename)
        with self.lock:
            cur = self.db.execute("SELECT MAX(version) FROM files WHERE base=?", (base,)).fetchone()[0]
            if ver is None: ver = (cur or 0) + 1
            elif self.db.execute("SELECT 1 FROM files WHERE base=? AND version=?", (base, ver)).fetchone():
                return None, f"version {ver} of {base} already exists"
        nodes, digest, key = self.choose_nodes(), sha256(data), blob_key(base, ver)
        if self.mode == "sequential":
            for nd in nodes: self._send(nd, key, data, digest)
        else:                                                # lead sends directly to each node, in parallel
            for f in [self.pool.submit(self._send, nd, key, data, digest) for nd in nodes]: f.result()
        with self.lock:                                      # commit metadata only after all 3 acks
            self.db.execute("INSERT INTO files VALUES(?,?,?,?,?)", (base, ver, len(data), digest, json.dumps(nodes)))
            self.db.commit()
        return dict(base=base, version=ver, size=len(data), sha256=digest, nodes=nodes), None

    def lookup(self, name, version=None):
        base, v = parse_name(name)
        v = version if version is not None else v
        q = "SELECT version,size,sha,nodes FROM files WHERE base=? " + ("AND version=?" if v is not None else "ORDER BY version DESC LIMIT 1")
        row = self.db.execute(q, (base, v) if v is not None else (base,)).fetchone()
        if not row: return None
        return dict(base=base, version=row[0], size=row[1], sha256=row[2], nodes=json.loads(row[3]))

    def fetch(self, meta):
        order = meta["nodes"][:]; random.shuffle(order)      # spread read load over the replicas
        for nd in order:                                     # failover: try next replica on error
            try:
                r = self.session().get(self.url(nd, blob_key(meta["base"], meta["version"])), timeout=30)
                if r.status_code == 200 and sha256(r.content) == meta["sha256"]:
                    return r.content, nd
            except requests.RequestException:
                continue
        return None, None

    def delete(self, name):
        base, _ = parse_name(name)
        rows = self.db.execute("SELECT version,nodes FROM files WHERE base=?", (base,)).fetchall()
        for v, nodes in rows:
            for nd in json.loads(nodes):
                try: requests.delete(self.url(nd, blob_key(base, v)), timeout=5)
                except requests.RequestException: pass
        with self.lock:
            self.db.execute("DELETE FROM files WHERE base=?", (base,)); self.db.commit()
        return len(rows)

def make_app(lead):
    app = Flask(__name__)

    @app.route("/files/<path:name>", methods=["POST", "PUT"])
    def store(name):
        meta, err = lead.store(name, request.get_data())
        if err: return jsonify(error=err), 409
        return jsonify(meta), 201

    @app.get("/files/<path:name>")
    def get(name):
        if name.endswith("/info"):
            m = lead.lookup(name[:-5]); return (jsonify(m), 200) if m else (jsonify(error="not found"), 404)
        v = request.args.get("version", type=int)
        meta = lead.lookup(name, v)
        if not meta: return jsonify(error="not found"), 404
        data, nd = lead.fetch(meta)
        if data is None: return jsonify(error="all replicas unavailable"), 503
        return Response(throttled(data, lead.rate) if lead.rate else data, mimetype="application/octet-stream",
                        headers={"X-Version": str(meta["version"]), "X-Served-By": str(nd)})

    @app.delete("/files/<path:name>")
    def delete(name): return jsonify(deleted=lead.delete(name))

    @app.get("/status")
    def status(): return jsonify(alive=lead.alive(), n=lead.n, mode=lead.mode, rate_bps=lead.rate)
    return app

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", type=int, default=6); ap.add_argument("--work", default="lead_data")
    ap.add_argument("--mode", default="parallel"); ap.add_argument("--rate", type=float, default=0)
    ap.add_argument("--placement", default="random"); ap.add_argument("--port", type=int, default=LEAD_PORT)
    a = ap.parse_args()
    from waitress import serve
    serve(make_app(Lead(a.nodes, a.work, a.mode, a.rate or None, a.placement)), host="127.0.0.1", port=a.port, threads=16)
