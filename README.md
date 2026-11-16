# Gen3D

Learned, appearance-aware mesh simplification built on QEM (quadric error metrics).
FYP-1, FAST-NUCES Peshawar.

**Research question:** does a small transformer that predicts a correction to the
QEM edge-collapse cost, trained on rendered-appearance error, simplify textured
meshes better than QEM / D-QEM / GNN-QEM at the same face budget, especially on
meshes produced by image-to-3D models such as SF3D?

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                          # should print: 5 passed
./run.sh                           # start the Inspector app, then open http://127.0.0.1:5000
python scripts/run_baseline.py     # QEM baseline on a built-in test sphere
python scripts/run_baseline.py path/to/mesh.obj
```

## Layout

| Path | Purpose |
|---|---|
| `gen3d/meshio.py` | load meshes, normalise scale, synthetic test mesh |
| `gen3d/baseline.py` | plain QEM baseline (geometry only, drops UVs) |
| `gen3d/metrics.py` | Chamfer, Hausdorff, normal consistency (point-to-surface, no sampling noise floor) |
| `gen3d/features.py` | per-edge features: length, dihedral angle, boundary flag, QEM cost, valence |
| `gen3d/analyze.py` | everything the Inspector page shows: counts, per-edge QEM cost, sample cup |
| `gen3d/image_to_3d.py` | photo to 3D with SF3D; needs the GPU machine and `SF3D_DIR` set; not tested yet |
| `app/server.py`, `app/static/` | the Inspector web app (Flask + three.js, works offline) |
| `scripts/run_baseline.py` | table of metrics at 50 / 25 / 10 / 5 % face budgets |
| `tests/` | unit tests |

## Status

Done: QEM baseline, geometry metrics, edge features (all tested).

Next, in order:
1. Run on real meshes: SF3D outputs and an Objaverse subset (on the university GPU machine).
2. Add D-QEM and GNN-QEM as baselines (both have public code).
3. Appearance metrics: render fixed views, PSNR / LPIPS, texture error.
4. Own edge-collapse loop that accepts an extra per-edge cost term.
5. Go/no-go experiment: label edges with measured appearance error, train a small
   transformer on mesh patches, check whether adding its prediction beats plain QEM.
6. App: login, upload, history, viewer.

## Known limits

- The baseline is geometry-only. `fast_simplification` ignores UVs and textures, so
  its output has no texture. It is the "plain QEM" row, not a textured baseline.
- Metrics measure geometry only. Appearance metrics are not written yet.
