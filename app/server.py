"""Gen3D Inspector: a small web app that shows what is inside a 3D model.

    python app/server.py        then open http://127.0.0.1:5000
"""
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, request, send_from_directory

from gen3d.analyze import MAX_FACES, analyze, make_sample_cup, prepare
from gen3d.baseline import qem_simplify
from gen3d.image_to_3d import Sf3dUnavailable, image_to_mesh, sf3d_available
from gen3d.meshio import load_mesh, normalize_unit
from gen3d.metrics import surface_metrics

UPLOADS = ROOT / "data" / "uploads"
MESH_TYPES = {".glb", ".gltf", ".obj", ".ply", ".stl", ".off"}
IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp"}

app = Flask(__name__, static_folder=str(Path(__file__).parent / "static"), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024
MESHES = {}  # mesh id -> prepared mesh, kept in memory while the app runs


def _register(mesh, source: str):
    mesh = prepare(mesh)
    if len(mesh.faces) == 0:
        return jsonify(error="This file has no triangles in it."), 400
    if len(mesh.faces) > MAX_FACES:
        return jsonify(error=f"This model has {len(mesh.faces):,} faces. The limit is {MAX_FACES:,}."), 400
    mesh_id = uuid.uuid4().hex
    MESHES[mesh_id] = mesh
    return jsonify(id=mesh_id, source=source, **analyze(mesh))


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/status")
def status():
    return jsonify(sf3d_available=sf3d_available())


@app.post("/api/sample")
def sample():
    return _register(make_sample_cup(), "Built-in sample cup")


@app.post("/api/upload")
def upload():
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify(error="No file was sent."), 400
    ext = Path(file.filename).suffix.lower()
    if ext not in MESH_TYPES | IMAGE_TYPES:
        return jsonify(error=f"'{ext}' files are not supported. Use an image (png, jpg) or a 3D model (glb, obj, ply, stl)."), 400

    UPLOADS.mkdir(parents=True, exist_ok=True)
    job = uuid.uuid4().hex
    saved = UPLOADS / f"{job}{ext}"
    file.save(saved)

    try:
        if ext in IMAGE_TYPES:
            mesh_path = image_to_mesh(saved, UPLOADS / job)
            source = f"Generated from image {file.filename} by SF3D"
        else:
            mesh_path = saved
            source = f"Uploaded model {file.filename}"
        mesh = load_mesh(str(mesh_path))
    except Sf3dUnavailable as err:
        return jsonify(error=str(err)), 400
    except Exception as err:  # a broken or unreadable file
        return jsonify(error=f"Could not read this file: {err}"), 400
    return _register(mesh, source)


@app.post("/api/simplify")
def simplify():
    body = request.get_json(force=True)
    mesh = MESHES.get(body.get("id"))
    if mesh is None:
        return jsonify(error="Model not found. Upload it again."), 404
    keep = min(max(float(body.get("keep", 0.25)), 0.01), 1.0)

    simplified = prepare(qem_simplify(mesh, max(4, int(len(mesh.faces) * keep))))
    if len(simplified.faces) == 0:
        return jsonify(error="Nothing was left at this setting. Keep more faces."), 400
    quality = surface_metrics(normalize_unit(mesh), _same_frame(mesh, simplified), n=3000)
    return jsonify(quality=quality, **analyze(simplified))


def _same_frame(reference, other):
    """Scale `other` exactly the way normalize_unit scales `reference`."""
    lo, hi = reference.bounds
    out = other.copy()
    out.vertices = (out.vertices - (lo + hi) / 2.0) / ((hi - lo) ** 2).sum() ** 0.5
    return out


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
