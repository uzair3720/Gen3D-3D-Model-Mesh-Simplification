"""Run the QEM baseline on one mesh at several face budgets and print a table.

    python scripts/run_baseline.py                  # built-in test sphere
    python scripts/run_baseline.py path/to/mesh.obj
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gen3d.baseline import qem_simplify
from gen3d.meshio import load_mesh, make_test_mesh, normalize_unit
from gen3d.metrics import surface_metrics

BUDGETS = [0.5, 0.25, 0.10, 0.05]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mesh", nargs="?", help="mesh file; omit to use a test sphere")
    args = parser.parse_args()

    mesh = load_mesh(args.mesh) if args.mesh else make_test_mesh(4, noise=0.02)
    ref = normalize_unit(mesh)
    print(f"original: {len(mesh.faces)} faces\n")
    print(f"{'budget':>7} {'faces':>7} {'chamfer':>10} {'hausdorff':>10} {'normal_c':>9}")
    for b in BUDGETS:
        out = qem_simplify(mesh, int(len(mesh.faces) * b))
        m = surface_metrics(ref, normalize_unit(out))
        print(f"{b:>7.0%} {len(out.faces):>7} {m['chamfer']:>10.5f} "
              f"{m['hausdorff']:>10.5f} {m['normal_consistency']:>9.4f}")


if __name__ == "__main__":
    main()
