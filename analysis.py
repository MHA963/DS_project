"""Turn results/*.json into tables (results/summary.json) and figures (figs/*.png)."""
import json, glob, itertools, random, math, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from math import comb
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": .25})
C = {"6": "#2a6f97", "12": "#e07a1f", "24": "#2f9e44", "seq": "#c0392b"}
L = lambda f: json.load(open(f"results/{f}.json"))
out = {}

# ---- 1. load runs
import statistics as st
def summ(xs):
    xs = sorted(xs); return dict(avg=st.fmean(xs), median=st.median(xs), min=xs[0], max=xs[-1], stdev=st.pstdev(xs))
for key, f in [("par6", "real_par_N6"), ("par12", "real_par_N12"), ("par24", "real_par_N24"), ("seq6", "real_seq_N6")]:
    r = L(f)["files"]
    out.setdefault("real", {})[key] = {k: dict(size=v["size"], up=v["up"], down=v["down"]) for k, v in r.items()}
    out.setdefault("pooled", {})[key] = dict(up=summ([x for v in r.values() for x in v["up_raw"]]), down=summ([x for v in r.values() for x in v["down_raw"]]), n=sum(len(v["up_raw"]) for v in r.values()))
for key, f in [("par6", "sweep_par_N6"), ("par12", "sweep_par_N12"), ("par24", "sweep_par_N24"), ("seq6", "sweep_seq_N6")]:
    out.setdefault("sweep", {})[key] = {k: dict(size=v["size"], up=v["up"], down=v["down"]) for k, v in L(f)["files"].items()}
out["par6"] = out["sweep"]["par6"]; out["par12"] = out["sweep"]["par12"]; out["par24"] = out["sweep"]["par24"]; out["seq6"] = out["sweep"]["seq6"]
names = sorted(out["par6"], key=lambda k: out["par6"][k]["size"])
sizes = np.array([out["par6"][k]["size"] for k in names]) / 1e6

# ---- 2. linear fits T = t0 + s*size (size sweep)
def fit(key, what):
    y = np.array([out[key][k][what]["avg"] for k in names]) * 1e3
    s, t0 = np.polyfit(sizes, y, 1); r2 = 1 - ((y - (s * sizes + t0)) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return dict(ms_per_MB=s, t0_ms=t0, r2=r2)
out["fits"] = {f"{k}_{w}": fit(k, w) for k in ["par6", "par12", "par24", "seq6"] for w in ["up", "down"]}

# ---- 3. throttled runs vs model
thr = {}; rows = []
runs = [("par6", "R400_parallel_N6", 400e6), ("seq6", "R400_sequential_N6", 400e6), ("par24", "R400_parallel_N24", 400e6),
        ("par6", "R100_parallel_N6", 100e6), ("seq6", "R100_sequential_N6", 100e6)]
for key, f, R in runs:
    for k, v in sorted(L(f)["files"].items(), key=lambda kv: kv[1]["size"]):
        base = out[key if key != "par24" else "par24"][k]
        tx = 8 * v["size"] / R * 1e3
        kup = 4 if key == "seq6" else 2
        rows.append(dict(cfg=key, R=R / 1e6, file=k, size=v["size"], tx_ms=tx,
                         up_meas=v["up"]["avg"] * 1e3, up_model=base["up"]["avg"] * 1e3 + kup * tx,
                         down_meas=v["down"]["avg"] * 1e3, down_model=base["down"]["avg"] * 1e3 + tx,
                         up_med=v["up"]["median"] * 1e3, down_med=v["down"]["median"] * 1e3))
out["model_vs_meas"] = rows
for k in ("par6", "seq6", "par24"):
    rr = [r for r in rows if r["cfg"] == k and r["R"] == 400]; x = [r["tx_ms"] for r in rr]
    out[f"slope_up_{k}"] = float(np.polyfit(x, [r["up_meas"] for r in rr], 1)[0])
    out[f"slope_down_{k}"] = float(np.polyfit(x, [r["down_meas"] for r in rr], 1)[0])

# ---- 4. data-loss probability: random placement vs groups (MinCopysets-like), R=3
def p_random(N, F, nfiles):      # P(at least one of nfiles lost) when F nodes fail simultaneously
    p1 = comb(F, 3) / comb(N, 3); return 1 - (1 - p1) ** nfiles
def p_groups(N, F):              # a group is lost only if all 3 of its nodes fail
    G = N // 3; lost_all = 0; tot = comb(N, F)
    # count F-subsets that contain at least one full group (inclusion-exclusion)
    cnt = sum((-1) ** (j + 1) * comb(G, j) * comb(N - 3 * j, F - 3 * j) for j in range(1, G + 1) if F - 3 * j >= 0)
    return cnt / tot
loss = []
for N in (6, 12, 24):
    for F in (2, 3, 4, 6):
        if F >= N: continue
        loss.append(dict(N=N, F=F, p1=comb(F, 3) / comb(N, 3), rand50=p_random(N, F, 50), rand1000=p_random(N, F, 1000), groups=p_groups(N, F)))
# Monte-Carlo check of the random formula (50 files)
rnd = random.Random(1); mc = {}
for N, F in ((12, 3), (12, 4), (24, 4)):
    hit = 0; T = 20000
    for _ in range(T):
        place = [frozenset(rnd.sample(range(N), 3)) for _ in range(50)]; dead = set(rnd.sample(range(N), F))
        hit += any(p <= dead for p in place)
    mc[f"{N},{F}"] = hit / T
out["loss"] = loss; out["mc"] = mc
json.dump(out, open("results/summary.json", "w"), indent=1)

# ---------------- figures
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
for w, a, t in (("up", ax[0], "Upload (store, 3 replicas)"), ("down", ax[1], "Download (retrieve latest)")):
    for key, lab, col, ls in (("par6", "N=6", C["6"], "-"), ("par12", "N=12", C["12"], "-"), ("par24", "N=24", C["24"], "-"), ("seq6", "N=6 sequential fan-out", C["seq"], "--")):
        a.plot(sizes, [out[key][k][w]["avg"] * 1e3 for k in names], marker="o", ms=3.5, color=col, ls=ls, label=lab)
    a.set_title(t); a.set_xlabel("file size (MB)"); a.set_ylabel("mean time (ms)")
ax[0].legend(frameon=False, fontsize=8); plt.tight_layout(); plt.savefig("figs/fig_unthrottled.png", dpi=200); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(9, 3.6)); xs = np.arange(3); wd = .27
rows400 = [r for r in rows if r["R"] == 400]
for a, w, t in ((ax[0], "up", "Upload, R = 400 Mbit/s"), (ax[1], "down", "Download, R = 400 Mbit/s")):
    for i, (key, lab, col) in enumerate((("par6", "parallel fan-out", C["6"]), ("seq6", "sequential fan-out", C["seq"]))):
        rr = sorted([r for r in rows400 if r["cfg"] == key], key=lambda r: r["size"])
        a.bar(xs + (i - .5) * wd * 1.1 - wd * .0, [r[w + "_meas"] for r in rr], wd, color=col, label=lab + " (measured)")
        a.scatter(xs + (i - .5) * wd * 1.1, [r[w + "_model"] for r in rr], marker="_", s=400, color="k", zorder=5, label="model" if i == 0 else None)
    a.set_xticks(xs); a.set_xticklabels(["0.1 MB", "1 MB", "10 MB"]); a.set_title(t); a.set_ylabel("mean time (ms)")
ax[0].legend(frameon=False, fontsize=8); plt.tight_layout(); plt.savefig("figs/fig_model.png", dpi=200); plt.close()

fig, ax = plt.subplots(figsize=(5.2, 3.6))
for N, col in ((6, C["6"]), (12, C["12"]), (24, C["24"])):
    rr = [l for l in loss if l["N"] == N]
    ax.plot([l["F"] for l in rr], [l["rand1000"] for l in rr], "-o", ms=4, color=col, label=f"random, N={N}")
    ax.plot([l["F"] for l in rr], [l["groups"] for l in rr], "--s", ms=4, color=col, alpha=.7, label=f"groups, N={N}")
ax.set_xlabel("simultaneous node failures F"); ax.set_ylabel("P(lose ≥ 1 of 1000 files)"); ax.legend(frameon=False, fontsize=7, ncol=2)
plt.tight_layout(); plt.savefig("figs/fig_loss.png", dpi=200); plt.close()

# box plot of 3MB upload distribution (variance)
fig, ax = plt.subplots(figsize=(5.2, 3.4)); d = []; lab = []
for key, l in (("real_par_N6", "N=6"), ("real_par_N12", "N=12"), ("real_par_N24", "N=24")):
    d.append(np.array(L(key)["files"]["apple_v1.txt"]["up_raw"]) * 1e3); lab.append(l)
ax.boxplot(d, tick_labels=lab, showfliers=True, flierprops=dict(ms=3)); ax.set_ylabel("upload time of a 10 MB file (ms)"); plt.tight_layout(); plt.savefig("figs/fig_box.png", dpi=200); plt.close()
print(json.dumps({k: out[k] for k in ("fits", "slope_up_par6", "slope_up_seq6", "slope_up_par24", "slope_down_par6", "mc")}, indent=1))
for l in loss: print(l)
for r in rows: print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()})
