import numpy as np

from gen3d.baseline import qem_simplify
from gen3d.features import FEATURE_NAMES, edge_features
from gen3d.meshio import make_test_mesh, normalize_unit
from gen3d.metrics import surface_metrics


def test_identical_meshes_have_near_zero_error():
    m = normalize_unit(make_test_mesh(3))
    r = surface_metrics(m, m, n=5000)
    assert r["chamfer"] < 1e-6
    assert r["hausdorff"] < 1e-6
    assert r["normal_consistency"] > 0.999


def test_qem_reaches_requested_face_count():
    m = make_test_mesh(4)  # 5120 faces
    out = qem_simplify(m, 1000)
    assert 800 <= len(out.faces) <= 1200


def test_more_simplification_gives_more_error():
    m = normalize_unit(make_test_mesh(4, noise=0.02))
    mild = surface_metrics(m, normalize_unit(qem_simplify(m, 2500)), n=5000)
    harsh = surface_metrics(m, normalize_unit(qem_simplify(m, 200)), n=5000)
    assert harsh["chamfer"] > mild["chamfer"]


def test_edge_features_shape_and_sanity():
    m = make_test_mesh(3)
    edges, feats = edge_features(m)
    assert feats.shape == (len(edges), len(FEATURE_NAMES))
    assert np.isfinite(feats).all()
    assert (feats[:, 0] > 0).all()          # lengths positive
    assert feats[:, 2].sum() == 0           # a closed sphere has no boundary edges
    assert (feats[:, 3] >= -1e-9).all()     # QEM cost is non-negative


def test_flat_edge_has_zero_dihedral_and_sharp_edge_does_not():
    import trimesh
    box = trimesh.creation.box()
    _, feats = edge_features(box)
    # a box has both flat (diagonal of a face) and sharp (90 degree) edges
    assert feats[:, 1].min() < 1e-6
    assert feats[:, 1].max() > 1.0
