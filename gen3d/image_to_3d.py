"""Image -> 3D mesh using SF3D (Stable Fast 3D), a pretrained model.

SF3D needs a GPU and several GB of downloads, so it is not installed on the
laptop. On the university machine: clone the SF3D repository, install it, and
set the environment variable SF3D_DIR to that folder before starting the app.

NOT YET TESTED: this follows the command in the SF3D README. Run it once on the
GPU machine and fix the output path below if SF3D writes somewhere else.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class Sf3dUnavailable(RuntimeError):
    """Raised when SF3D is not installed on this machine."""


def sf3d_available() -> bool:
    folder = os.environ.get("SF3D_DIR", "")
    return bool(folder) and (Path(folder) / "run.py").is_file()


def image_to_mesh(image_path: Path, out_dir: Path) -> Path:
    """Run SF3D on one image and return the path of the generated .glb mesh."""
    if not sf3d_available():
        raise Sf3dUnavailable(
            "Image-to-3D needs the SF3D model, which needs a GPU. It is not installed on "
            "this computer. Upload a 3D model file (.glb / .obj) instead, or run the app "
            "on the university GPU machine with SF3D_DIR set."
        )
    sf3d_dir = Path(os.environ["SF3D_DIR"])
    python = os.environ.get("SF3D_PYTHON", sys.executable)
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [python, "run.py", str(image_path.resolve()), "--output-dir", str(out_dir.resolve())],
        cwd=sf3d_dir, check=True, timeout=600,
    )
    mesh_path = out_dir / "0" / "mesh.glb"
    if not mesh_path.is_file():
        raise RuntimeError(f"SF3D finished but {mesh_path} was not created")
    return mesh_path
