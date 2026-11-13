# [INDIGOCS-WEBGL-TUTORIALS] Ticket 7439 — IndigoCS-webgl-tutorials: Resolve Absolute Path Breakage in Mandelbrot Demo

**Repository:** `IndigoCS-webgl-tutorials`  
**Assigned AI Model:** `gemini-3.8-flash-medium`  
**Harness:** `botharness`  
**Status:** `OPEN` (Pending Autonomous Worker)  
**Created:** `2026-11-13T22:06:00Z`  

## Task Description
Convert root-relative asset and shader URLs to relative paths in the Mandelbrot fractal tutorial.

## Technical Details and Root Cause
In `FragShader - Mandelbrot/index.html` (line 16):
`<script src="/bower_components/async/dist/async.min.js"></script>`
In `FragShader - Mandelbrot/app.js` (lines 42-43):
`vsText: '/mandl.vs.glsl',`
`fsText: '/mandl.fs.glsl'`
These references start with a leading forward slash `/`, requesting files relative to the domain root rather than the tutorial folder. When the repository is hosted inside a subdirectory, served through a reverse proxy path, or viewed via local HTTP servers, these requests fail with HTTP 404 errors.

## Proposed Actionable Solution
1. In `FragShader - Mandelbrot/index.html`, update script path to `bower_components/async/dist/async.min.js`.
2. In `FragShader - Mandelbrot/app.js`, change `vsText` to `mandl.vs.glsl` (or `./mandl.vs.glsl`) and `fsText` to `mandl.fs.glsl` (or `./mandl.fs.glsl`).

## Execution Guidelines
1. Work autonomously in `IndigoCS-webgl-tutorials/`.
2. Ensure existing tests continue to pass.
3. Keep modifications clean, sound, and adhering to WebGL/GLSL standards.
4. Run tests with local test runner before concluding.
