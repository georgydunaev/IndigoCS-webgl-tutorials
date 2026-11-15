# IndigoCS-webgl-tutorials Repository Catalog and Notes

## 1. Repository Overview

The `IndigoCS-webgl-tutorials` repository contains interactive WebGL 1.0 and GLSL tutorial modules progressing from 2D clip-space triangle rendering to 3D matrix transformations, UV texture mapping, external JSON/Blender mesh loading, Phong illumination, Mandelbrot fragment shaders, omnidirectional shadow mapping with point-light cubemaps, and a reusable 3D camera and frustum math library (`common/camera.js` and `tests/camera_math.py`).

All binary 3D assets (`.blend`, `.blend1`, `.fbx`, `.png`) are preserved untouched.

## 2. Tutorial Modules and Shader Inventory

### 2.1 Root Gallery Shell (`index.html`)
- Provides a responsive navigation hub and overview cards linking all 7 WebGL tutorial scenes, shader pipeline notes, and camera math utilities.

### 2.2 Tutorial 01: `01 - Simple Triangle/`
- **Files**: `index.html`, `app.js` (3,356 bytes), `LICENSE`.
- **Topics Covered**: WebGL context initialization (`webgl` / `experimental-webgl`), inline vertex and fragment shader compilation, vertex buffer object (`ARRAY_BUFFER`) binding for 2D position (`vec2`) and per-vertex RGB color (`vec3`), and `gl.drawArrays(gl.TRIANGLES, 0, 3)`.

### 2.3 Tutorial 02: `02 - Rotating Cube/`
- **Files**: `index.html`, `app.js` (6,384 bytes), `gl-matrix.js`, `LICENSE`.
- **Topics Covered**: 3D indexed geometry (`ELEMENT_ARRAY_BUFFER` with 24 vertices and 36 indices), depth testing (`gl.DEPTH_TEST`) and back-face culling (`gl.CULL_FACE`), uniform transformation matrices (`mWorld`, `mView`, `mProj`) via `gl-matrix`, and dual-axis animation loop (`requestAnimationFrame`).

### 2.4 Tutorial 03: `03 - Textured Cube/`
- **Files**: `index.html`, `app.js` (6,835 bytes), `crate.png`, `gl-matrix.js`, `LICENSE`.
- **Topics Covered**: 2D UV texture coordinates (`vertTexCoord`), WebGL texture object creation (`gl.createTexture`, `gl.texImage2D`), `sampler2D` fragment sampling, and wrapping/filtering parameters (`gl.CLAMP_TO_EDGE`, `gl.LINEAR`).

### 2.5 Tutorial 04: `04 - Loading External Files/`
- **Files**: `index.html`, `app.js` (6,664 bytes), `util.js` (846 bytes), `shader.vs.glsl`, `shader.fs.glsl`, `Susan.json`, `SusanTexture.png`, `Susan.blend`, `Susan.fbx`, `gl-matrix.js`.
- **Topics Covered**: Asynchronous loading of external GLSL shader texts (`loadTextResource`), JSON 3D mesh parsing (`loadJSONResource` loading Blender monkey `Susan.json`), and image loading (`loadImage`) before starting the render loop.

### 2.6 Tutorial 05: `05 - Phong Lighting Intro/`
- **Files**: `index.html`, `app.js` (7,710 bytes), `util.js`, `shader.vs.glsl` (393 bytes), `shader.fs.glsl` (547 bytes), `Susan.json`, `SusanTexture.png`, `gl-matrix.js`.
- **Topics Covered**: Surface normal transformation into world space (`fragNormal`), ambient light intensity (`ambientLightIntensity`) plus directional sunlight (`sun.direction`, `sun.color`) diffuse Lambertian dot-product shading in `shader.fs.glsl`.

### 2.7 Special Module: `FragShader - Mandelbrot/`
- **Files**: `index.html`, `app.js` (6,154 bytes), `mandl.vs.glsl` (98 bytes), `mandl.fs.glsl` (891 bytes), `bower_components/async/`.
- **Topics Covered**: Full-screen quad rendering where all computation happens per-fragment in `mandl.fs.glsl`, evaluating complex iteration $z_{n+1} = z_n^2 + c$ with interactive zoom/pan uniforms (`viewportDimensions`, `minI`, `maxI`, `minR`, `maxR`).

### 2.8 Advanced Module: `Shadow Mapping/`
- **Files**: `index.html`, `app.js` (643 bytes), `LightMapDemoScene.js` (19,175 bytes), `Models.js` (3,283 bytes), `util.js` (2,293 bytes), `Room.json` (150,547 bytes), `Room.blend`, `shaders/NoShadow.vs.glsl`, `shaders/NoShadow.fs.glsl`, `shaders/Shadow.vs.glsl`, `shaders/Shadow.fs.glsl`, `shaders/ShadowMapGen.vs.glsl`, `shaders/ShadowMapGen.fs.glsl`.
- **Topics Covered**: Two-pass omnidirectional point-light shadow mapping using a floating-point or depth cubemap framebuffer (`TEXTURE_CUBE_MAP`), rendering point-to-light distance in `ShadowMapGen.fs.glsl` across 6 cubemap faces (+X, -X, +Y, -Y, +Z, -Z) and comparing fragment distance against biased shadow cubemap depth in `Shadow.fs.glsl`.

### 2.9 Shared 3D Camera and Math Library (`common/camera.js` and `tests/camera_math.py`)
- **`common/camera.js` (845 lines)**: Self-contained UMD JavaScript module providing `vec3`, `vec4`, `mat4`, `quat`, `Frustum` (6-plane Gribb-Hartmann extraction, sphere and AABB culling), `Ray` (screen-to-world unprojection, ray-plane, ray-sphere, ray-AABB slabs intersection), `OrbitCamera`, and `FirstPersonCamera`.
- **`tests/camera_math.py`, `tests/test_camera.py`, `tests/test_webgl_tutorials.py`**: Python reference implementation and verification suite for matrix/quaternion identities, frustum culling, ray casting, and GLSL shader syntax.

## 3. Notes on Unfinished Sections and Open Integration Opportunities

- **Tutorial 05 Specular Phong Term**: Note that `05 - Phong Lighting Intro/shader.fs.glsl` implements ambient plus diffuse directional lighting (`ambientLightIntensity + sun.color * max(dot(fragNormal, normSunDir), 0.0)`) as an introduction to Phong shading, leaving the camera-dependent specular reflection term ($R \cdot V)^\alpha$ as the natural follow-up exercise.
- **Interactive Camera Integration in Tutorials 02 to 05**: While `common/camera.js` implements complete `OrbitCamera` and `FirstPersonCamera` classes and `Shadow Mapping/LightMapDemoScene.js` uses keyboard camera controls, Tutorials 02 through 05 currently use fixed `mat4.lookAt` cameras with automatic object rotation and can optionally wire in `OrbitCamera` mouse/wheel handlers.
