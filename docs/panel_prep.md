# Panel preparation: the code and the algorithms

For Mubashir, Hadi and Uzair. Read it with the code open. Every claim here matches
the code as of 16 Nov 2026; if the code changes, update this file.

## 1. The system in five sentences

1. The user opens a 3D model (or, on the GPU machine, a photo that SF3D turns into a 3D model).
2. The server loads the mesh and welds duplicate vertices.
3. It measures every edge: length, bend angle, whether it is on an opening, and a QEM cost.
4. The page draws the mesh and colours each edge by its cost.
5. On "Apply", the server simplifies the mesh with QEM and reports how far the result is from the original.

Not built yet: the transformer, texture preservation, login and history. Say so if asked.

## 2. What each file does

| File | What it does | Who explains it |
|---|---|---|
| `gen3d/meshio.py` | Loads a model file into one mesh. `normalize_unit` centres it and scales it so its bounding-box diagonal is 1. | |
| `gen3d/features.py` | Builds one quadric per vertex and one row of measurements per edge. | |
| `gen3d/analyze.py` | Welds vertices, counts everything, ranks edges by cost, packs it all for the page. | |
| `gen3d/baseline.py` | Calls the `fast_simplification` library to do the QEM simplification. | |
| `gen3d/metrics.py` | Chamfer distance, Hausdorff distance, normal consistency. | |
| `gen3d/image_to_3d.py` | Runs SF3D on a photo. Needs the GPU machine. Not tested yet. | |
| `app/server.py` | Flask web server with four routes: status, sample, upload, simplify. | |
| `app/static/app.js` | Draws the mesh with three.js and fills the side panel. | |
| `tests/test_core.py` | Five automatic checks. Run `pytest -q`. | |

Fill in the last column. Each person should own about three files and be able to open
any of them and explain it line by line.

## 3. The algorithms

### 3.1 QEM (quadric error metrics), Garland and Heckbert, 1997

**Idea.** Every vertex sits where several triangles meet. If we move the vertex, it leaves
the flat planes of those triangles. QEM measures "how far, squared, is a point from all
those planes". An edge is cheap to remove if the merged vertex stays close to the planes
of both end vertices.

**Step by step, as in `vertex_quadrics` in `features.py`:**

1. Each triangle lies in a plane `a*x + b*y + c*z + d = 0`, where `(a, b, c)` is the
   triangle's unit normal and `d = -(normal . any corner)`. Write `p = (a, b, c, d)`.
2. The squared distance from a point `v = (x, y, z, 1)` to that plane is `(p . v)^2`,
   which equals `v^T (p p^T) v`. The 4x4 matrix `p p^T` is the triangle's quadric.
3. We multiply each triangle's quadric by the triangle's area, so large triangles count
   more and the result does not depend on how finely a flat region is cut up.
4. A vertex's quadric `Q` is the sum of the quadrics of the triangles that touch it.
5. For an edge between vertices i and j, the cost is `m^T (Q_i + Q_j) m`, where `m` is
   the edge midpoint. This is the `qem_cost` column in `edge_features`.

**Tiny example.** A vertex in the middle of a flat floor (plane z = 0). All its triangles
give `p = (0, 0, 1, 0)`. Moving it sideways costs 0: it stays on the floor. Lifting it by
height h costs `area * h^2`. So QEM lets flat regions be simplified freely and protects
bumps and corners.

**The loop.** Give every edge a cost, collapse the cheapest, update the neighbours'
costs, repeat until the target face count is reached. With a priority queue this is
O(n log n) for n edges.

**Two honest points the panel may probe:**

- *We use the midpoint.* The original paper solves a small linear system for the best
  position of the merged vertex. That system has no unique answer on flat regions, so
  the midpoint is the simple, always-defined choice for our displayed cost.
- *The cost we display and the simplifier are separate code.* The displayed cost is
  computed by our own `features.py`. The actual simplification is done by the
  `fast_simplification` library (a wrapper around the open-source
  "Fast Quadric Mesh Simplification" C++ code), which computes its own costs and uses a
  threshold-based approximation instead of a strict priority queue. Writing our own
  collapse loop is the next piece of work: it is needed to add the transformer's score
  and to keep textures.

### 3.2 Edge measurements (`edge_features`)

| Column | How it is computed | Why it is there |
|---|---|---|
| length | distance between the two end vertices | short edges are usually safe to remove |
| dihedral | angle between the normals of the two triangles sharing the edge; 0 = flat | sharp edges carry the shape |
| is_boundary | 1 if only one triangle uses the edge | rims of openings must be treated carefully |
| qem_cost | section 3.1 | the classical score |
| valence min / max | number of edges at each end vertex | describes how dense the mesh is there |

These rows are what the transformer will read. An edge is called "sharp" when its
dihedral angle is over 30 degrees (`SHARP_ANGLE_DEG` in `analyze.py`).

### 3.3 Welding (`prepare` in `analyze.py`)

Model files store a vertex several times when it lies on a texture seam. Unwelded, those
seams look like holes and edge counts are wrong. `prepare` merges vertices at the same
position and drops triangles with zero area.

### 3.4 Error metrics (`metrics.py`)

All three compare the simplified mesh with the original. Both are first scaled by the
original's bounding box so numbers are comparable between models.

- **Chamfer distance.** Sample 3,000 random points on mesh A; for each, find the distance
  to the nearest point on the surface of mesh B. Do the same from B to A. Average. It is
  the typical error. Lower is better.
- **Hausdorff distance.** The largest of all those distances. It is the worst spot.
- **Normal consistency.** At each sampled point, compare the direction the surface faces
  with the direction of the nearest triangle on the other mesh (absolute cosine). 1.0
  means the surfaces face the same way everywhere.

We measure point-to-surface, not point-to-point. Comparing two random point samples
gives a non-zero distance even for identical meshes; the first test in `tests/` checks
that identical meshes score zero.

### 3.5 Collapse-cost colours

Edges are coloured by rank (their position when sorted by cost), not by raw cost. Raw
costs span many orders of magnitude, so colouring by value would make nearly every edge
the same colour.

## 4. Likely questions and short answers

**Why remove the photo-to-3D part from the focus?** The panel's own mid-term feedback:
SF3D is pretrained, so our contribution is the simplifier. SF3D stays as the source of
input meshes.

**What exactly is your contribution?** Testing whether a transformer trained on
appearance improves QEM's edge scores for textured meshes from image-to-3D models.
The transformer is FYP-2 work.

**Did you implement QEM yourselves?** The cost computation, yes (`features.py`). The
collapse loop is a library today; our own loop is the next task.

**Why QEM and not something newer?** It is still the standard: TriFlow (ECCV 2026) uses
a QEM step inside its pipeline, and in its results plain QEM is close to the learned
method on shape accuracy.

**What is the difference from GNN-QEM?** It uses a graph neural network and targets
structure. We plan a transformer trained on rendered appearance and texture.

**What is the difference from TriFlow / Meshy T2?** They generate a new mesh and ignore
texture; they need very large training (TriFlow: 8 H100 GPUs for 12 days). We simplify an
existing textured mesh with a small model.

**How will the transformer be trained?** Trial-collapse an edge, measure the real damage
to shape and rendered image, undo, and record it. The transformer learns to predict that
number from the edge measurements.

**How is the transformer's score combined with QEM?** Final cost = QEM cost + weight x
predicted damage. Weight 0 gives plain QEM, which makes the comparison fair.

**How will you keep the texture?** Each vertex stores a position on the texture image
(UV). When two vertices merge, blend their UVs; do not merge across texture seams. This
follows D-QEM. Not built yet.

**What dataset?** Planned: an Objaverse subset of one or two categories for training,
SF3D outputs for testing. Not downloaded yet.

**How do you know your metrics are right?** Unit tests: identical meshes score zero, and
heavier simplification gives larger error.

**Why does simplification of a flat box show zero error?** Flat regions can lose
triangles with no change in shape. That is QEM working correctly.

**Why Flask and three.js?** Small, well known, and the page works offline because
three.js is stored in the project.

**Where are uploaded meshes stored?** Files in `data/uploads`; loaded meshes are held in
memory while the server runs. A database comes with login and history.

**What is 40% here?** Mesh loading, edge analysis, QEM baseline, metrics and the viewer
work. Photo input (GPU machine), our own collapse loop, the transformer, texture and
login/history remain.

**What are the limits right now?** No texture in the output, no learned model, photo
input untested, models over 300,000 faces are refused, tested mainly on a synthetic cup.

## 5. Things to check before the day

- The rubric scores "reliance on built-in functions (the lesser the better)". Our
  simplifier is a library call. Writing our own collapse loop would help with this mark
  and is needed anyway.
- If asked whether AI tools were used to write code, answer truthfully and know your
  department's policy beforehand. What protects you is being able to explain every line.

## 6. How to practise

1. Each person takes their files and explains them aloud to the other two, line by line.
2. Each person makes one small change alone (for example: change the sharp-edge threshold
   to 45 degrees, or add "max edge length" to the Mesh table) and gets it working.
3. Run `pytest -q` and `python scripts/run_baseline.py` and explain every number printed.
4. Take turns asking the questions in section 4 without notes.
5. Rehearse the live demo: load sample, show Collapse cost, simplify to 10%, read the error numbers.
