"""Mesh loading helpers and small synthetic test meshes."""
from __future__ import annotations

import numpy as np
import trimesh


def load_mesh(path: str) -> trimesh.Trimesh:
    """Load a mesh file (obj/glb/ply/...) as a single Trimesh.

    A scene (for example a .glb with several parts) is merged into one mesh.
    Vertices are not merged or cleaned, so the file's UVs stay valid.
    """
    loaded = trimesh.load(path, process=False)
    if isinstance(loaded, trimesh.Scene):
        loaded = trimesh.util.concatenate(list(loaded.geometry.values()))
    return loaded


def normalize_unit(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Return a copy centred at the origin and scaled to fit a unit-diagonal box.

    Metrics such as Chamfer distance are only comparable between meshes if
    they are measured at the same scale.
    """
    out = mesh.copy()
    lo, hi = out.bounds
    out.vertices = (out.vertices - (lo + hi) / 2.0) / np.linalg.norm(hi - lo)
    return out


def make_test_mesh(subdivisions: int = 4, noise: float = 0.0, seed: int = 0) -> trimesh.Trimesh:
    """A bumpy icosphere used for tests and for trying the pipeline without data.

    `subdivisions=4` gives 5120 faces, `5` gives 20480.
    """
    mesh = trimesh.creation.icosphere(subdivisions=subdivisions)
    if noise > 0:
        rng = np.random.default_rng(seed)
        mesh.vertices = mesh.vertices * (1.0 + noise * rng.standard_normal((len(mesh.vertices), 1)))
    return mesh
