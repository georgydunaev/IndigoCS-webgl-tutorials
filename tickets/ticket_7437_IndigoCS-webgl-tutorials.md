# [INDIGOCS-WEBGL-TUTORIALS] Ticket 7437 — IndigoCS-webgl-tutorials: Implement Specular Reflection Term in Phong Lighting Tutorial

**Repository:** `IndigoCS-webgl-tutorials`  
**Assigned AI Model:** `gemini-3.8-flash-medium`  
**Harness:** `botharness`  
**Status:** `OPEN` (Pending Autonomous Worker)  
**Created:** `2026-11-13T22:06:00Z`  

## Task Description
Implement the specular highlight reflection term in tutorial 05 to complete the classical Phong illumination model.

## Technical Details and Root Cause
Tutorial 05 is titled `05 - Phong Lighting Intro` and its documentation states it demonstrates ambient plus diffuse plus specular Phong illumination. However, inspection of `05 - Phong Lighting Intro/shader.fs.glsl` reveals only ambient and diffuse (Lambertian) calculations:
`vec3 lightIntensity = ambientLightIntensity + sun.color * max(dot(fragNormal, normSunDir), 0.0);`
The specular component (measuring reflection towards the camera viewpoint) is absent. A true Phong lighting model requires ambient, diffuse, and specular terms:
`I = I_a * k_a + I_d * k_d * (N . L) + I_s * k_s * (R . V)^shininess`

## Proposed Actionable Solution
1. In `05 - Phong Lighting Intro/shader.vs.glsl`, compute and pass world-space fragment position `fragPosition` as a varying to the fragment shader.
2. Add a camera position uniform (e.g., `uniform vec3 viewPosition;` or `cameraPosition`) to `shader.fs.glsl`.
3. Compute view direction `vec3 viewDir = normalize(viewPosition - fragPosition);`.
4. Compute light reflection direction `vec3 reflectDir = reflect(-normSunDir, surfaceNormal);`.
5. Compute specular intensity `float spec = pow(max(dot(viewDir, reflectDir), 0.0), 32.0);` and add specular light contribution to `lightIntensity`.
6. Update `05 - Phong Lighting Intro/app.js` to bind and provide the camera view position uniform.

## Execution Guidelines
1. Work autonomously in `IndigoCS-webgl-tutorials/`.
2. Ensure existing tests continue to pass.
3. Keep modifications clean, sound, and adhering to WebGL/GLSL standards.
4. Run tests with local test runner before concluding.
