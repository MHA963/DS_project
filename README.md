# Distributed Storage Mini-Project

Task 1: a replicated, versioned file store. Each file is stored as 3 full copies on 3 different nodes out of N = 6, 12 or 24. The lead node offers a Flask REST interface and keeps its metadata in SQLite.

## Setup
python -m venv env
env\Scripts\activate
pip install flask requests waitress numpy matplotlib

## Run
python test_correctness.py dataset_real
python bench.py --data dataset_real --nodes 6 --reps 10 --files apple --out test.json
./run_all.sh dataset_real

The course dataset (50 files, 10 MB each) is in the dataset_real folder.

## Files
- common.py, node.py, lead.py, cluster.py, client.py: the system
- test_correctness.py: functional tests
- bench.py, run_all.sh, analysis.py: benchmarks and figures
- results/, figs/: measurements from the report
