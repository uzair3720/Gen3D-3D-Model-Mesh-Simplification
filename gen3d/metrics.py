"""Geometry metrics for comparing a simplified mesh against the original.

Points are sampled on one mesh and measured against the *exact surface* of the
other (point-to-triangle distance), in both directions. Comparing two
independent point samples instead would add a noise floor, so even identical
meshes would score a non-zero distance.

Normalise both meshes with `meshio.normalize_unit` first so the numbers are
comparable between objects.
"""
from __future__ import annotations

import numpy as np
import trimesh


def _one_way(src: trimesh.Trimesh, dst: trimesh.Trimesh, n: int, seed: int):
    """Distances and normal agreement from points on `src` to the surface of `dst`."""
    points, face_idx = trimesh.sample.sample_surface(src, n, seed=seed)
    closest, dist, tri_id = trimesh.proximity.closest_point(dst, points)
    cos = np.abs(np.einsum("ij,ij->i", src.face_normals[face_idx], dst.face_normals[tri_id]))
    return dist, cos


def surface_metrics(a: trimesh.Trimesh, b: trimesh.Trimesh, n: int = 5000, seed: int = 0) -> dict:
    """Chamfer distance, Hausdorff distance and normal consistency between a and b.

    - chamfer: mean of the two directional mean distances (lower is better).
    - hausdorff: worst-case distance, either direction (lower is better).
    - normal_consistency: mean |cos| between a sampled normal and the normal of
      the closest triangle on the other mesh (1.0 is best).
    """
    d_ab, c_ab = _one_way(a, b, n, seed)
    d_ba, c_ba = _one_way(b, a, n, seed + 1)
    return {
        "chamfer": float(0.5 * (d_ab.mean() + d_ba.mean())),
        "hausdorff": float(max(d_ab.max(), d_ba.max())),
        "normal_consistency": float(0.5 * (c_ab.mean() + c_ba.mean())),
    }
