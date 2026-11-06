"""Benchmark: upload & download latency per file, >=100 repetitions, for a given cluster config.
python bench.py --nodes 6 --mode parallel --rate 0 --reps 100 --files all --out results/x.json"""
import argparse, glob, json, os, statistics as st, time
from cluster import Cluster
from client import Client

def summarize(xs):
    xs = sorted(xs); return dict(avg=st.fmean(xs), median=st.median(xs), min=xs[0], max=xs[-1],
                                 stdev=st.pstdev(xs), p95=xs[int(0.95 * (len(xs) - 1))])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes", type=int, default=6); ap.add_argument("--mode", default="parallel")
    ap.add_argument("--rate", type=float, default=0, help="link rate R in bit/s (0 = unthrottled loopback)")
    ap.add_argument("--reps", type=int, default=100); ap.add_argument("--data", default="dataset")
    ap.add_argument("--files", default="all", help="'all' or comma list of stems e.g. notes,archive")
    ap.add_argument("--placement", default="random"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    paths = sorted(glob.glob(f"{a.data}/*_v1.*"))
    if a.files != "all": paths = [p for p in paths if os.path.basename(p).split("_v1")[0] in a.files.split(",")]
    res = dict(config=vars(a), files={}); retries = 0
    with Cluster(a.nodes, "/tmp/mp_bench", a.mode, a.rate, a.placement) as cl:
        c = Client(rate_bps=a.rate or None); c_dl = Client()
        for p in paths:
            data = open(p, "rb").read(); stem, ext = os.path.basename(p).split("_v1")
            up, down = [], []
            for rep in range(-3, a.reps):                      # 3 warm-up rounds, not recorded
                name = f"b{rep + 3}_{stem}_v1{ext}"
                for attempt in range(4):                        # a dropped keep-alive connection is retried, the failed round is discarded
                    try:
                        t0 = time.perf_counter(); r = c.store(name, data); t1 = time.perf_counter()
                        assert r.status_code == 201, r.text
                        t2 = time.perf_counter(); g = c_dl.retrieve(name); t3 = time.perf_counter()
                        assert g.content == data
                        break
                    except Exception as e:
                        retries += 1; print("  retry after", repr(e)[:300], "| procs:", len(os.popen("pgrep -f 'node.py|lead.py'").read().split()), flush=True)
                        c, c_dl = Client(rate_bps=a.rate or None), Client()
                        try: c.delete(name)
                        except Exception: pass
                        name = f"b{rep + 3}r{attempt}_{stem}_v1{ext}"
                else: raise RuntimeError("repeated failure")
                c.delete(name)                                  # untimed cleanup
                if rep >= 0: up.append(t1 - t0); down.append(t3 - t2)
            res["files"][os.path.basename(p)] = dict(size=len(data), up_raw=up, down_raw=down,
                                                    up=summarize(up), down=summarize(down))
            print(f"N={a.nodes} {a.mode} R={a.rate:g} {stem+ext:12s} {len(data):>8d} B  up avg {st.fmean(up)*1e3:8.2f} ms  down avg {st.fmean(down)*1e3:8.2f} ms", flush=True)
    res["retries"] = retries
    json.dump(res, open(a.out, "w"))
if __name__ == "__main__": main()
