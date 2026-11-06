#!/bin/bash
# Reproduces every measurement.  Usage: ./run_all.sh <dataset_dir>
# The dataset folder holds the real files; 'sweep' (prefixes of apple_v1 of 0.1..10 MB) is created from it.
D=${1:-dataset_real}; mkdir -p results sweep
python3 - "$D" <<'PY'
import sys,os,glob
src=open(sorted(glob.glob(sys.argv[1]+"/*_v1.*"))[0],"rb").read()
for stem,sz in [("s0100k",100_000),("s0500k",500_000),("s1000k",1_000_000),("s2000k",2_000_000),("s5000k",5_000_000),("s10000k",10_000_000)]:
    if sz<=len(src): open(f"sweep/{stem}_v1.txt","wb").write(src[:sz])
PY
# A. real files (10 base files, v1), unthrottled
for N in 6 12 24; do python3 bench.py --data $D --nodes $N --mode parallel --reps 100 --out results/real_par_N$N.json; done
python3 bench.py --data $D --nodes 6 --mode sequential --reps 100 --out results/real_seq_N6.json
# B. size sweep, unthrottled
for N in 6 12 24; do python3 bench.py --data sweep --nodes $N --mode parallel --reps 100 --out results/sweep_par_N$N.json; done
python3 bench.py --data sweep --nodes 6 --mode sequential --reps 100 --out results/sweep_seq_N6.json
# C. emulated link rate
F=s0100k,s1000k,s10000k
for M in parallel sequential; do python3 bench.py --data sweep --nodes 6 --mode $M --rate 400e6 --reps 100 --files $F --out results/R400_${M}_N6.json; done
python3 bench.py --data sweep --nodes 24 --mode parallel --rate 400e6 --reps 100 --files $F --out results/R400_parallel_N24.json
for M in parallel sequential; do python3 bench.py --data sweep --nodes 6 --mode $M --rate 100e6 --reps 100 --files s10000k --out results/R100_${M}_N6.json; done
echo DONE
