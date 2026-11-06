"""Functional tests for Task 1: store/retrieve latest, versions, 3 distinct replicas, failure tolerance."""
import os, glob, json, sqlite3, time
from cluster import Cluster
from client import Client
from common import *

def run(data_dir="dataset", n=6):
    import sys; data_dir = sys.argv[1] if len(sys.argv) > 1 else data_dir
    files = sorted(glob.glob(f"{data_dir}/*_v*"))
    with Cluster(n, "/tmp/mp_test") as cl:
        c = Client(); results = []
        def check(name, ok): results.append((name, ok)); print(("PASS " if ok else "FAIL ") + name)
        # 1. store all 50 files (5 versions each, in order)
        placed = {}
        for f in files:
            r = c.store(os.path.basename(f), open(f, "rb").read()); assert r.status_code == 201, r.text
            placed[os.path.basename(f)] = r.json()
        NF = len(files)
        check(f"all {NF} files stored (HTTP 201)", len(placed) == NF)
        check("each file on exactly 3 distinct nodes", all(len(set(m["nodes"])) == 3 for m in placed.values()))
        # physical check: 3 copies on disk, byte-identical
        ok = True
        for name, m in placed.items():
            copies = [open(f"/tmp/mp_test/node{nd}/{blob_key(m['base'], m['version'])}", "rb").read() for nd in m["nodes"]]
            ok &= all(x == open(f"{data_dir}/{name}", "rb").read() for x in copies)
        check("3 byte-identical copies physically on disk", ok)
        total = sum(len(glob.glob(f"/tmp/mp_test/node{i}/*__v*")) for i in range(n))
        check(f"storage overhead = 3x ({3*NF} blobs for {NF} files)", total == 3 * NF)
        # 2. retrieve latest = v5
        ok = True
        for stem in sorted({parse_name(os.path.basename(f))[0] for f in files}):
            r = c.retrieve(stem); latest = max(glob.glob(f"{data_dir}/{stem.replace('.', '_v5.')}"))
            ok &= r.status_code == 200 and r.headers["X-Version"] == "5" and r.content == open(latest, "rb").read()
        check("retrieve without version returns latest (v5), byte-exact", ok)
        # 3. retrieve specific versions
        S0 = os.path.basename(files[0]).split("_v")[0]; E0 = os.path.splitext(files[0])[1]
        ok = all(c.retrieve(S0 + E0, v).content == open(f"{data_dir}/{S0}_v{v}{E0}", "rb").read() for v in range(1, 6))
        check("retrieve specific version (1..5) byte-exact", ok)
        check("retrieve by name with _vN suffix", c.retrieve(f"{S0}_v2{E0}").content == open(f"{data_dir}/{S0}_v2{E0}", "rb").read())
        # 4. auto-version + duplicate rejection
        r = c.store("new.txt", b"hello"); check("name without suffix gets version 1", r.json()["version"] == 1)
        r = c.store("new.txt", b"hello2"); check("second store without suffix gets version 2", r.json()["version"] == 2)
        check("duplicate explicit version rejected (409)", c.store("new_v2.txt", b"x").status_code == 409)
        check("unknown file -> 404", c.retrieve("nope.txt").status_code == 404)
        # 5. node failures: kill 2 nodes -> every file still readable (3-way replication tolerates 2 losses)
        cl.kill_node(0); cl.kill_node(1)
        ok = True
        for name, m in placed.items():
            r = c.retrieve(name)
            ok &= r.status_code == 200 and r.content == open(f"{data_dir}/{name}", "rb").read() if len(set(m["nodes"]) & {2,3,4,5}) >= 1 else True
        check("kill 2 nodes: every file with a surviving replica still retrievable", ok)
        lost = [n for n, m in placed.items() if set(m["nodes"]) <= {0, 1}]
        check("a file can never lose all 3 copies with only 2 nodes down", len(lost) == 0)
    bad = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} tests passed"); return not bad
if __name__ == "__main__": raise SystemExit(0 if run() else 1)
