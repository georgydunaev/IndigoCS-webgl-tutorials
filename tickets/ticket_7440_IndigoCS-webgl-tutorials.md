# [INDIGOCS-WEBGL-TUTORIALS] Ticket 7440 — IndigoCS-webgl-tutorials: Fix Shadow Map Framebuffer Texture Size Race Condition

**Repository:** `IndigoCS-webgl-tutorials`  
**Assigned AI Model:** `gemini-3.8-flash-medium`  
**Harness:** `botharness`  
**Status:** `OPEN` (Pending Autonomous Worker)  
**Created:** `2026-11-13T22:06:00Z`  

## Task Description
Ensure shadow map texture size is reliably initialized before cube map and depth renderbuffer memory allocation in LightMapDemoScene.

## Technical Details and Root Cause
In `Shadow Mapping/LightMapDemoScene.js`, the assignment:
`me.textureSize = getParameterByName('texSize') || 512;`
is located at line 331, outside and after the invocation of `async.parallel(...)` (lines 14 to 315).
Inside the async completion callback:
Lines 207 and 217 call `gl.texImage2D(..., me.textureSize, me.textureSize, ...)` to allocate all 6 cube map faces.
Line 231 calls `gl.renderbufferStorage(..., me.textureSize, me.textureSize)`.
While JavaScript asynchronous event loop dispatch currently delays the callback execution until after synchronous statements finish, relying on deferred property initialization outside the callback creates brittle ordering and breaks if asset loading completes synchronously (e.g., from cache or mock loaders). Furthermore, `this.textureSize` is undefined immediately after instantiation.

## Proposed Actionable Solution
1. In `Shadow Mapping/LightMapDemoScene.js`, initialize `this.textureSize = getParameterByName('texSize') || 512;` inside the `LightMapDemoScene` constructor function.
2. In `LightMapDemoScene.prototype.Load`, verify `this.textureSize` is a positive integer before binding and allocating textures and renderbuffers.

## Execution Guidelines
1. Work autonomously in `IndigoCS-webgl-tutorials/`.
2. Ensure existing tests continue to pass.
3. Keep modifications clean, sound, and adhering to WebGL/GLSL standards.
4. Run tests with local test runner before concluding.
