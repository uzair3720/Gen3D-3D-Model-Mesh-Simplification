"""Per-edge features: the input to the learned collapse-cost model.

Every unique edge of the mesh gets one row of features. Nothing is collapsed
here, we only measure the mesh as it is.

Columns (see FEATURE_NAMES):
  length          edge length
  dihedral        angle in radians between the normals of the two faces that
                  share the edge (0 = flat, larger = sharper). 0 for boundary edges.
  is_boundary     1 if the edge belongs to only one face, else 0
  qem_cost        classical QEM cost of collapsing the edge to its midpoint
  valence_i/j     number of edges at each end vertex, as a rough local-density cue
"""
from __future__ import annotations

import numpy as np
import trimesh

FEATURE_NAMES = ["length", "dihedral", "is_boundary", "qem_cost", "valence_min", "valence_max"]


def vertex_quadrics(mesh: trimesh.Trimesh) -> np.ndarray:
    """One 4x4 quadric per vertex: the sum over its faces of area * (p p^T).

    p = (a, b, c, d) is the face plane a*x + b*y + c*z + d = 0 with unit normal.
    The quadric measures squared distance from a point to all those planes.
    """
    n = mesh.face_normals
    tri = mesh.triangles
    d = -np.einsum("ij,ij->i", n, tri[:, 0])
    p = np.concatenate([n, d[:, None]], axis=1)                  # (F, 4)
    face_q = mesh.area_faces[:, None, None] * p[:, :, None] * p[:, None, :]  # (F, 4, 4)

    q = np.zeros((len(mesh.vertices), 4, 4))
    for corner in range(3):
        np.add.at(q, mesh.faces[:, corner], face_q)
    return q


def edge_features(mesh: trimesh.Trimesh) -> tuple[np.ndarray, np.ndarray]:
    """Return (edges, features).

    edges    (E, 2) int array of vertex index pairs, one row per unique edge
    features (E, len(FEATURE_NAMES)) float array
    """
    edges = mesh.edges_unique                                    # (E, 2), sorted per row
    num_edges = len(edges)
    verts = mesh.vertices

    length = np.linalg.norm(verts[edges[:, 0]] - verts[edges[:, 1]], axis=1)

    # Number of faces per unique edge: 1 means boundary.
    faces_per_edge = np.bincount(mesh.edges_unique_inverse, minlength=num_edges)
    is_boundary = (faces_per_edge == 1).astype(float)

    # Dihedral angle for edges shared by exactly two faces.
    dihedral = np.zeros(num_edges)
    adj_edges = np.sort(mesh.face_adjacency_edges, axis=1)
    key = edges[:, 0].astype(np.int64) * len(verts) + edges[:, 1]
    adj_key = adj_edges[:, 0].astype(np.int64) * len(verts) + adj_edges[:, 1]
    order = np.argsort(key)
    pos = np.searchsorted(key[order], adj_key)
    dihedral[order[pos]] = mesh.face_adjacency_angles

    # QEM cost at the edge midpoint.
    q = vertex_quadrics(mesh)
    q_edge = q[edges[:, 0]] + q[edges[:, 1]]
    mid = 0.5 * (verts[edges[:, 0]] + verts[edges[:, 1]])
    mid_h = np.concatenate([mid, np.ones((num_edges, 1))], axis=1)
    qem_cost = np.einsum("ei,eij,ej->e", mid_h, q_edge, mid_h)

    valence = np.bincount(edges.ravel(), minlength=len(verts))
    v_a, v_b = valence[edges[:, 0]], valence[edges[:, 1]]

    features = np.stack(
        [length, dihedral, is_boundary, qem_cost, np.minimum(v_a, v_b), np.maximum(v_a, v_b)],
        axis=1,
    )
    return edges, features
