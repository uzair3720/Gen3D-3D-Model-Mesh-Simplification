"""Baseline simplifier: classical QEM (Garland & Heckbert, 1997).

This wraps the `fast_simplification` package. It is geometry-only. It does not
know about UVs or textures, so it is the "plain QEM" row in our comparison
tables. The texture-aware baselines (D-QEM, GNN-QEM) are added separately.
"""
from __future__ import annotations

import fast_simplification
import numpy as np
import trimesh


def qem_simplify(mesh: trimesh.Trimesh, target_faces: int) -> trimesh.Trimesh:
    """Simplify `mesh` to about `target_faces` triangles using classical QEM."""
    if target_faces >= len(mesh.faces):
        return mesh.copy()
    target_reduction = 1.0 - target_faces / len(mesh.faces)
    verts, faces = fast_simplification.simplify(
        np.asarray(mesh.vertices, dtype=np.float64),
        np.asarray(mesh.faces, dtype=np.int64),
        target_reduction=target_reduction,
    )
    return trimesh.Trimesh(vertices=verts, faces=faces, process=False)
