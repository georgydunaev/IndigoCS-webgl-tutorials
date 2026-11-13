# [INDIGOCS-WEBGL-TUTORIALS] Ticket 7436 — IndigoCS-webgl-tutorials: Fix Unnormalized Normal Vectors in Phong and Shadow Mapping Shaders

**Repository:** `IndigoCS-webgl-tutorials`  
**Assigned AI Model:** `gemini-3.8-flash-medium`  
**Harness:** `botharness`  
**Status:** `OPEN` (Pending Autonomous Worker)  
**Created:** `2026-11-13T22:06:00Z`  

## Task Description
Normalize interpolated normal vectors within fragment shaders prior to computing diffuse dot products in Phong Lighting and Shadow Mapping tutorials.

## Technical Details and Root Cause
1. In `05 - Phong Lighting Intro/shader.fs.glsl`, line 18 calculates `vec3 surfaceNormal = normalize(fragNormal);` but line 23 performs `dot(fragNormal, normSunDir)` using unnormalized `fragNormal`. Because vertex normals interpolated across triangle surfaces do not retain unit length, calculating dot products with raw interpolated normals introduces diffuse intensity distortion. Furthermore, `surfaceNormal` remains unused dead code.
2. In `Shadow Mapping/shaders/NoShadow.fs.glsl` (line 13) and `Shadow Mapping/shaders/Shadow.fs.glsl` (line 27), lighting intensity computes `max(dot(fNorm, toLightNormal), 0.0)` directly with varying `fNorm`. The varying normal must be normalized per fragment to ensure correct cosine shading.

## Proposed Actionable Solution
1. In `05 - Phong Lighting Intro/shader.fs.glsl`, update line 23 to evaluate `dot(surfaceNormal, normSunDir)` instead of `dot(fragNormal, normSunDir)`.
2. In `Shadow Mapping/shaders/NoShadow.fs.glsl`, define `vec3 normal = normalize(fNorm);` and use `dot(normal, toLightNormal)`.
3. In `Shadow Mapping/shaders/Shadow.fs.glsl`, define `vec3 normal = normalize(fNorm);` and use `dot(normal, toLightNormal)`.

## Execution Guidelines
1. Work autonomously in `IndigoCS-webgl-tutorials/`.
2. Ensure existing tests continue to pass.
3. Keep modifications clean, sound, and adhering to WebGL/GLSL standards.
4. Run tests with local test runner before concluding.
