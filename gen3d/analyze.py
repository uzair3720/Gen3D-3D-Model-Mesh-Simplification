"""Turn a mesh into everything the inspector page shows.

`analyze(mesh)` returns a plain dictionary (numbers and lists only) holding the
geometry, a summary of counts, and a QEM cost for every edge.
"""
from __future__ import annotations

import numpy as np
import trimesh

from .features import FEATURE_NAMES, edge_features

SHARP_ANGLE_DEG = 30.0   # an edge whose two faces meet at more than this is "sharp"
MAX_FACES = 300_000      # larger meshes are refused so the page stays responsive


def prepare(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Weld vertices that sit at the same position.

    Model files store a vertex several times when it lies on a texture seam.
    Unwelded, those seams look like holes and the edge counts are wrong.
    """
    out = trimesh.Trimesh(vertices=np.asarray(mesh.vertices), faces=np.asarray(mesh.faces), process=False)
    out.merge_vertices()
    out.update_faces(out.nondegenerate_faces())
    out.remove_unreferenced_vertices()
    return out


def make_sample_cup() -> trimesh.Trimesh:
    """A cup made by spinning a curved outline around an axis.

    Used when no file is uploaded. It has curved sides, a sharp base edge and an
    open rim, so every view of the inspector has something to show.
    """
    height = np.linspace(0.0, 1.0, 40)
    radius = 0.32 + 0.10 * np.sin(height * 5.0) + 0.12 * height
    outline = np.column_stack([radius, height])
    outline = np.vstack([[0.0, 0.0], outline])          # closed flat base
    cup = trimesh.creation.revolve(outline, sections=96)
    cup.apply_transform(trimesh.transformations.rotation_matrix(-np.pi / 2, [1, 0, 0]))  # stand upright (y up)
    return cup


def _rank01(values: np.ndarray) -> np.ndarray:
    """Position of each value in sorted order, scaled to 0..1 (0 = smallest)."""
    if len(values) < 2:
        return np.zeros(len(values))
    order = np.argsort(values, kind="stable")
    rank = np.empty(len(values))
    rank[order] = np.arange(len(values))
    return rank / (len(values) - 1)


def analyze(mesh: trimesh.Trimesh) -> dict:
    """Summary numbers, geometry and per-edge data for one (prepared) mesh."""
    edges, feats = edge_features(mesh)
    col = {name: feats[:, i] for i, name in enumerate(FEATURE_NAMES)}
    col["qem_cost"] = np.maximum(col["qem_cost"], 0.0)   # remove tiny negative rounding errors
    sharp = np.degrees(col["dihedral"]) > SHARP_ANGLE_DEG

    def edge_row(i: int) -> dict:
        return {
            "edge": [int(edges[i, 0]), int(edges[i, 1])],
            "length": float(col["length"][i]),
            "angle_deg": float(np.degrees(col["dihedral"][i])),
            "is_boundary": bool(col["is_boundary"][i]),
            "qem_cost": float(col["qem_cost"][i]),
        }

    order = np.argsort(col["qem_cost"], kind="stable")
    return {
        "stats": {
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "edges": int(len(edges)),
            "boundary_edges": int(col["is_boundary"].sum()),
            "sharp_edges": int(sharp.sum()),
            "watertight": bool(mesh.is_watertight),
            "parts": int(mesh.body_count),
            "surface_area": float(mesh.area),
            "edge_length_min": float(col["length"].min()),
            "edge_length_mean": float(col["length"].mean()),
            "edge_length_max": float(col["length"].max()),
            "qem_cost_median": float(np.median(col["qem_cost"])),
            "qem_cost_max": float(col["qem_cost"].max()),
        },
        "positions": np.asarray(mesh.vertices, dtype=np.float32).ravel().tolist(),
        "faces": np.asarray(mesh.faces, dtype=np.int32).ravel().tolist(),
        "edges": edges.astype(np.int32).ravel().tolist(),
        "edge_cost_rank": np.round(_rank01(col["qem_cost"]), 4).tolist(),
        "edge_sharp": sharp.astype(int).tolist(),
        "edge_boundary": col["is_boundary"].astype(int).tolist(),
        "cheapest_edges": [edge_row(i) for i in order[:8]],
        "costliest_edges": [edge_row(i) for i in order[::-1][:8]],
    }
