/**
 * common/phong_specular_and_orbit.js
 *
 * Specular Phong Lighting Extension (Blinn-Phong and Classical Phong Reflection)
 * and Interactive OrbitCamera Controller Binding Helper for Tutorials 02 to 05.
 *
 * Compatible with Browser globals (window.WebGLPhongOrbit) and CommonJS/Node.js.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    var camLib = require('./camera.js');
    module.exports = factory(camLib);
  } else {
    root.WebGLPhongOrbit = factory(root.WebGLCamera);
  }
}(typeof self !== 'undefined' ? self : this, function (CameraLib) {
  'use strict';

  var vec3 = CameraLib && CameraLib.vec3 ? CameraLib.vec3 : null;
  var OrbitCamera = CameraLib && CameraLib.OrbitCamera ? CameraLib.OrbitCamera : null;

  /**
   * Upgraded GLSL Vertex Shader for Full Ambient + Diffuse + Specular Phong Shading.
   * Passes world-space fragment position (fragPosition), world-space normal (fragNormal),
   * and UV texture coordinate (fragTexCoord) to the fragment shader.
   */
  var PHONG_SPECULAR_VERTEX_SHADER_SRC = [
    'precision mediump float;',
    '',
    'attribute vec3 vertPosition;',
    'attribute vec2 vertTexCoord;',
    'attribute vec3 vertNormal;',
    '',
    'varying vec2 fragTexCoord;',
    'varying vec3 fragNormal;',
    'varying vec3 fragPosition;',
    '',
    'uniform mat4 mWorld;',
    'uniform mat4 mView;',
    'uniform mat4 mProj;',
    '',
    'void main()',
    '{',
    '  fragTexCoord = vertTexCoord;',
    '  vec4 worldPos = mWorld * vec4(vertPosition, 1.0);',
    '  fragPosition = worldPos.xyz;',
    '  fragNormal = (mWorld * vec4(vertNormal, 0.0)).xyz;',
    '  gl_Position = mProj * mView * worldPos;',
    '}'
  ].join('\n');

  /**
   * Upgraded GLSL Fragment Shader for Full Ambient + Diffuse + Specular Phong Shading.
   * Extends Tutorial 05 (05 - Phong Lighting Intro/shader.fs.glsl) with view-dependent
   * specular highlights controlled by cameraPosition, specularIntensity, and shininess.
   */
  var PHONG_SPECULAR_FRAGMENT_SHADER_SRC = [
    'precision mediump float;',
    '',
    'struct DirectionalLight',
    '{',
    '  vec3 direction;',
    '  vec3 color;',
    '};',
    '',
    'varying vec2 fragTexCoord;',
    'varying vec3 fragNormal;',
    'varying vec3 fragPosition;',
    '',
    'uniform vec3 ambientLightIntensity;',
    'uniform DirectionalLight sun;',
    'uniform vec3 cameraPosition;',
    'uniform float specularIntensity;',
    'uniform float shininess;',
    'uniform sampler2D sampler;',
    '',
    'void main()',
    '{',
    '  vec3 surfaceNormal = normalize(fragNormal);',
    '  vec3 normSunDir = normalize(sun.direction);',
    '  vec3 viewDir = normalize(cameraPosition - fragPosition);',
    '  vec3 reflectDir = reflect(-normSunDir, surfaceNormal);',
    '',
    '  float diffuseFactor = max(dot(surfaceNormal, normSunDir), 0.0);',
    '  float specAngle = max(dot(viewDir, reflectDir), 0.0);',
    '  float specularFactor = diffuseFactor > 0.0 ? pow(specAngle, max(shininess, 1.0)) : 0.0;',
    '',
    '  vec4 texel = texture2D(sampler, fragTexCoord);',
    '  vec3 lightIntensity = ambientLightIntensity + sun.color * diffuseFactor;',
    '  vec3 specularColor = sun.color * (specularIntensity * specularFactor);',
    '',
    '  gl_FragColor = vec4(texel.rgb * lightIntensity + specularColor, texel.a);',
    '}'
  ].join('\n');

  /**
   * CPU Reference Evaluator for Full Phong Illumination (Ambient + Diffuse + Specular).
   * Used both for unit verification and deterministic CPU/GPU parity checks.
   */
  function evaluatePhongIllumination(params) {
    if (!vec3) {
      throw new Error('WebGLCamera.vec3 is required to evaluate Phong illumination');
    }
    var normal = vec3.normalize(vec3.create(), params.normal || [0, 1, 0]);
    var lightDir = vec3.normalize(vec3.create(), params.lightDirection || [0, 1, 0]);
    var fragPos = params.fragPosition || [0, 0, 0];
    var camPos = params.cameraPosition || [0, 0, 5];
    var viewVec = vec3.subtract(vec3.create(), camPos, fragPos);
    var viewDir = vec3.normalize(vec3.create(), viewVec);

    var nDotL = vec3.dot(normal, lightDir);
    var diffuseFactor = Math.max(nDotL, 0.0);

    // reflect(-L, N) = -L - 2 * dot(-L, N) * N = 2 * dot(N, L) * N - L
    var reflectDir = vec3.create(
      2.0 * nDotL * normal[0] - lightDir[0],
      2.0 * nDotL * normal[1] - lightDir[1],
      2.0 * nDotL * normal[2] - lightDir[2]
    );
    vec3.normalize(reflectDir, reflectDir);

    var shininess = typeof params.shininess === 'number' ? Math.max(params.shininess, 1.0) : 32.0;
    var specIntensity = typeof params.specularIntensity === 'number' ? params.specularIntensity : 0.5;
    var vDotR = Math.max(vec3.dot(viewDir, reflectDir), 0.0);
    var specularFactor = diffuseFactor > 0.0 ? Math.pow(vDotR, shininess) : 0.0;

    var ambient = params.ambientColor || [0.2, 0.2, 0.2];
    var sunColor = params.lightColor || [0.9, 0.9, 0.9];
    var texel = params.texelRGB || [1.0, 1.0, 1.0];

    var lightR = ambient[0] + sunColor[0] * diffuseFactor;
    var lightG = ambient[1] + sunColor[1] * diffuseFactor;
    var lightB = ambient[2] + sunColor[2] * diffuseFactor;

    var specR = sunColor[0] * specIntensity * specularFactor;
    var specG = sunColor[1] * specIntensity * specularFactor;
    var specB = sunColor[2] * specIntensity * specularFactor;

    return {
      diffuseFactor: diffuseFactor,
      specularFactor: specularFactor,
      reflectDirection: reflectDir,
      colorRGB: vec3.create(
        texel[0] * lightR + specR,
        texel[1] * lightG + specG,
        texel[2] * lightB + specB
      )
    };
  }

  /**
   * Attaches interactive mouse drag (orbit + pan) and wheel zoom handlers from
   * an HTMLCanvasElement (or mock event target) to an OrbitCamera instance,
   * and provides a helper to upload view, projection, and cameraPosition uniforms.
   */
  function attachOrbitCameraController(canvas, camera, options) {
    var opts = options || {};
    var rotateSpeed = typeof opts.rotateSpeed === 'number' ? opts.rotateSpeed : 0.008;
    var zoomSpeed = typeof opts.zoomSpeed === 'number' ? opts.zoomSpeed : 0.002;
    var panSpeed = typeof opts.panSpeed === 'number' ? opts.panSpeed : 0.01;
    var minDistance = typeof opts.minDistance === 'number' ? opts.minDistance : 0.5;
    var maxDistance = typeof opts.maxDistance === 'number' ? opts.maxDistance : 100.0;

    var cam = camera || (OrbitCamera ? new OrbitCamera([0, 0, 0], 8.0, 0.0, 0.3) : null);
    var state = {
      dragging: false,
      mode: 'orbit',
      lastX: 0,
      lastY: 0
    };

    function onMouseDown(ev) {
      state.dragging = true;
      state.mode = (ev && (ev.shiftKey || ev.button === 2)) ? 'pan' : 'orbit';
      state.lastX = ev && typeof ev.clientX === 'number' ? ev.clientX : 0;
      state.lastY = ev && typeof ev.clientY === 'number' ? ev.clientY : 0;
    }

    function onMouseMove(ev) {
      if (!state.dragging || !cam) return;
      var cx = ev && typeof ev.clientX === 'number' ? ev.clientX : state.lastX;
      var cy = ev && typeof ev.clientY === 'number' ? ev.clientY : state.lastY;
      var dx = cx - state.lastX;
      var dy = cy - state.lastY;
      state.lastX = cx;
      state.lastY = cy;

      if (state.mode === 'pan') {
        cam.pan(-dx * panSpeed, dy * panSpeed);
      } else {
        cam.orbit(-dx * rotateSpeed, dy * rotateSpeed);
      }
    }

    function onMouseUp() {
      state.dragging = false;
    }

    function onWheel(ev) {
      if (!cam) return;
      if (ev && typeof ev.preventDefault === 'function') {
        ev.preventDefault();
      }
      var deltaY = ev && typeof ev.deltaY === 'number' ? ev.deltaY : 0;
      cam.zoom(deltaY * zoomSpeed, minDistance, maxDistance);
    }

    if (canvas && typeof canvas.addEventListener === 'function') {
      canvas.addEventListener('mousedown', onMouseDown);
      canvas.addEventListener('mousemove', onMouseMove);
      canvas.addEventListener('mouseup', onMouseUp);
      canvas.addEventListener('mouseleave', onMouseUp);
      canvas.addEventListener('wheel', onWheel);
    }

    return {
      camera: cam,
      state: state,
      onMouseDown: onMouseDown,
      onMouseMove: onMouseMove,
      onMouseUp: onMouseUp,
      onWheel: onWheel,
      applyUniforms: function (gl, program, uniformLocations, aspect) {
        if (!gl || !cam || !uniformLocations) return;
        var viewMat = cam.getViewMatrix();
        var projMat = cam.getProjectionMatrix(null, aspect);
        var eyePos = cam.getEyePosition();
        if (uniformLocations.mView) {
          gl.uniformMatrix4fv(uniformLocations.mView, gl.FALSE, viewMat);
        }
        if (uniformLocations.mProj) {
          gl.uniformMatrix4fv(uniformLocations.mProj, gl.FALSE, projMat);
        }
        if (uniformLocations.cameraPosition) {
          gl.uniform3f(uniformLocations.cameraPosition, eyePos[0], eyePos[1], eyePos[2]);
        }
      },
      detach: function () {
        if (canvas && typeof canvas.removeEventListener === 'function') {
          canvas.removeEventListener('mousedown', onMouseDown);
          canvas.removeEventListener('mousemove', onMouseMove);
          canvas.removeEventListener('mouseup', onMouseUp);
          canvas.removeEventListener('mouseleave', onMouseUp);
          canvas.removeEventListener('wheel', onWheel);
        }
      }
    };
  }

  return {
    PHONG_SPECULAR_VERTEX_SHADER_SRC: PHONG_SPECULAR_VERTEX_SHADER_SRC,
    PHONG_SPECULAR_FRAGMENT_SHADER_SRC: PHONG_SPECULAR_FRAGMENT_SHADER_SRC,
    evaluatePhongIllumination: evaluatePhongIllumination,
    attachOrbitCameraController: attachOrbitCameraController
  };
}));
