# Project Overview: Interactive WebGL and GLSL Shader Tutorials (`IndigoCS-webgl-tutorials`)

## Purpose and Scope

`IndigoCS-webgl-tutorials` (`/botworkspace/IndigoCS-webgl-tutorials`) is a progressive 3D graphics, WebGL 1.0, and GLSL shader programming repository covering vertex/index buffer management, 4x4 homogeneous matrix transformations (`gl-matrix`), UV texture mapping, external JSON/Blender mesh loading, Phong ambient/diffuse/specular illumination, complex-plane Mandelbrot fragment shaders, omnidirectional point-light shadow mapping with depth cubemaps, and a reusable 3D camera and frustum-culling library (`common/`).

## Repository Structure

- [index.html](file:///botworkspace/IndigoCS-webgl-tutorials/index.html), [README.md](file:///botworkspace/IndigoCS-webgl-tutorials/README.md), and [REPOSITORY_CATALOG_AND_NOTES.md](file:///botworkspace/IndigoCS-webgl-tutorials/REPOSITORY_CATALOG_AND_NOTES.md): Interactive tutorial portal and module catalog.
- `01 - Simple Triangle/`: Clip-space 2D triangle rendering, vertex buffer objects (VBOs), and attribute pointers.
- `02 - Rotating Cube/`: 3D perspective projection, depth buffering (`gl.DEPTH_TEST`), back-face culling (`gl.CULL_FACE`), and world/view/projection matrix uniforms.
- `03 - Textured Cube/`: 2D texture binding, mipmap filtering, and UV coordinate interpolation (`crate.png`).
- `04 - Loading External Files/`: Asynchronous HTTP fetching (`util.js`) of external `.vs.glsl` / `.fs.glsl` shader files and JSON mesh geometry (`Susan.json`).
- `05 - Phong Lighting Intro/`: Per-fragment Phong lighting model computing ambient, diffuse Lambertian, and specular reflectance in world space.
- `FragShader - Mandelbrot/`: GPU-accelerated complex-plane fractal rendering (`z = z^2 + c`) with interactive zoom and pan uniforms.
- `Shadow Mapping/`: Two-pass omnidirectional shadow mapping using an off-screen framebuffer object (`gl.FRAMEBUFFER`) and 6-face point-light depth cubemap (`gl.TEXTURE_CUBE_MAP`).
- `common/`: Shared `camera.js` and `frustum.js` utilities for 6-plane view-frustum culling and orbital/free-look camera controls.
- [tests/](file:///botworkspace/IndigoCS-webgl-tutorials/tests/): Automated verification suite validating HTML/JS/GLSL assets and camera/frustum math.

## Verification Command

```bash
python3 -m unittest discover -s /botworkspace/IndigoCS-webgl-tutorials/tests -p "test_*.py"
```
