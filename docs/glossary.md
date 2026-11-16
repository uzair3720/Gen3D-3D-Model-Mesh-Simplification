# Glossary

Terms used in the Gen3D app, in plain words.

| Term | Meaning |
|---|---|
| Mesh | A 3D model made of many small flat triangles joined together, like a paper model. |
| Vertex | A corner point in 3D space. Triangles are drawn between vertices. |
| Face | One flat triangle of the surface. More faces means more detail and a heavier file. |
| Edge | A line joining two vertices; the side of a triangle. |
| Sharp edge | An edge where the surface bends by more than 30 degrees, like a table corner. |
| Dihedral angle | How much the surface bends at an edge. 0 degrees is flat. |
| Boundary edge | An edge with a triangle on only one side: the rim of an opening. |
| Component | A separate piece of the model that is not connected to the rest. |
| Watertight | The surface is fully closed, with no openings. |
| Decimate / simplify | Make the model lighter by removing edges while trying to keep its shape. |
| Edge collapse | Removing one edge by merging its two end vertices into one. |
| QEM | Quadric error metrics: the standard way to score edges for removal. |
| Collapse cost (QEM cost) | A number per edge: how far the surface would move if that edge were collapsed. Low cost is safe to remove. |
| Chamfer distance | Average distance between the simplified and the original surface. Lower is better. |
| Hausdorff distance | The largest distance between the two surfaces: the worst spot. Lower is better. |
| Normal consistency | How well the surface directions of the two models agree. 1.0 is a perfect match. |
| Transformer | A type of AI model that looks at many items together and learns which ones matter. Not implemented yet in this project. |
| SF3D | A pretrained AI model that turns one photo into a 3D mesh. It needs a GPU. |
