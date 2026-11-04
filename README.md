# IndigoCS-webgl-tutorials — Interactive WebGL & GLSL Shader Tutorials

## Overview
`IndigoCS-webgl-tutorials` provides 6 self-contained WebGL and GLSL shader tutorials:
1. `01 - Simple Triangle` — Vertex buffers and minimal 2D triangle rendering.
2. `02 - Rotating Cube` — 3D perspective projection and world/view/projection matrices.
3. `03 - Textured Cube` — UV texture mapping (`crate.png`).
4. `04 - Loading External Files` — JSON mesh loading (`Susan.json`) and external GLSL shaders.
5. `05 - Phong Lighting Intro` — Ambient + diffuse + specular Phong illumination in GLSL.
6. `FragShader - Mandelbrot` & `Shadow Mapping` — Fragment shader Mandelbrot fractal and omnidirectional shadow mapping.

## Running Verification Tests
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
