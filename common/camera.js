/**
 * Mathematical Orbit and First-Person Camera Controller and Frustum Plane Culling Utility.
 *
 * Implements:
 * 1. Unit Quaternion algebra (identity, normalize, multiply, conjugate, invert, slerp, rotation matrix).
 * 2. Vector3 and Matrix4 column-major mathematical operations.
 * 3. Euler pitch and yaw clamping (preventing gimbal lock).
 * 4. OrbitCamera with spherical coordinates, zoom, and panning.
 * 5. FirstPersonCamera (FPS free-look) with quaternion orientation and directional translation.
 * 6. Gribb-Hartmann 6-plane frustum extraction from View-Projection matrix.
 * 7. Point, bounding sphere, and AABB visibility classification and culling.
 */

(function (global, factory) {
	if (typeof exports === 'object' && typeof module !== 'undefined') {
		module.exports = factory();
	} else if (typeof define === 'function' && define.amd) {
		define(factory);
	} else {
		global.CameraMath = factory();
	}
}(typeof self !== 'undefined' ? self : this, function () {
	'use strict';

	var MAX_PITCH_DEG = 89.0;
	var MAX_PITCH_RAD = (MAX_PITCH_DEG * Math.PI) / 180.0;

	// Clamping helper
	function clamp(val, minVal, maxVal) {
		return Math.max(minVal, Math.min(maxVal, val));
	}

	function clampPitch(pitchRad, minDeg, maxDeg) {
		var minRad = (typeof minDeg === 'number' ? minDeg : -MAX_PITCH_DEG) * Math.PI / 180.0;
		var maxRad = (typeof maxDeg === 'number' ? maxDeg : MAX_PITCH_DEG) * Math.PI / 180.0;
		return clamp(pitchRad, minRad, maxRad);
	}

	// Vector3 operations
	var vec3 = {
		create: function (x, y, z) {
			var out = new Float32Array(3);
			out[0] = x || 0.0;
			out[1] = y || 0.0;
			out[2] = z || 0.0;
			return out;
		},
		clone: function (a) {
			var out = new Float32Array(3);
			out[0] = a[0];
			out[1] = a[1];
			out[2] = a[2];
			return out;
		},
		set: function (out, x, y, z) {
			out[0] = x;
			out[1] = y;
			out[2] = z;
			return out;
		},
		add: function (out, a, b) {
			out[0] = a[0] + b[0];
			out[1] = a[1] + b[1];
			out[2] = a[2] + b[2];
			return out;
		},
		subtract: function (out, a, b) {
			out[0] = a[0] - b[0];
			out[1] = a[1] - b[1];
			out[2] = a[2] - b[2];
			return out;
		},
		scale: function (out, a, s) {
			out[0] = a[0] * s;
			out[1] = a[1] * s;
			out[2] = a[2] * s;
			return out;
		},
		scaleAndAdd: function (out, a, b, s) {
			out[0] = a[0] + b[0] * s;
			out[1] = a[1] + b[1] * s;
			out[2] = a[2] + b[2] * s;
			return out;
		},
		dot: function (a, b) {
			return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
		},
		cross: function (out, a, b) {
			var ax = a[0], ay = a[1], az = a[2];
			var bx = b[0], by = b[1], bz = b[2];
			out[0] = ay * bz - az * by;
			out[1] = az * bx - ax * bz;
			out[2] = ax * by - ay * bx;
			return out;
		},
		length: function (a) {
			var x = a[0], y = a[1], z = a[2];
			return Math.sqrt(x * x + y * y + z * z);
		},
		distance: function (a, b) {
			var x = a[0] - b[0];
			var y = a[1] - b[1];
			var z = a[2] - b[2];
			return Math.sqrt(x * x + y * y + z * z);
		},
		normalize: function (out, a) {
			var x = a[0], y = a[1], z = a[2];
			var len = Math.sqrt(x * x + y * y + z * z);
			if (len > 0.000001) {
				var inv = 1.0 / len;
				out[0] = x * inv;
				out[1] = y * inv;
				out[2] = z * inv;
			} else {
				out[0] = 0.0;
				out[1] = 0.0;
				out[2] = 0.0;
			}
			return out;
		}
	};

	// Quaternion operations [x, y, z, w]
	var quat = {
		create: function () {
			var out = new Float32Array(4);
			out[3] = 1.0;
			return out;
		},
		identity: function (out) {
			out[0] = 0.0;
			out[1] = 0.0;
			out[2] = 0.0;
			out[3] = 1.0;
			return out;
		},
		clone: function (q) {
			var out = new Float32Array(4);
			out[0] = q[0];
			out[1] = q[1];
			out[2] = q[2];
			out[3] = q[3];
			return out;
		},
		dot: function (a, b) {
			return a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3];
		},
		length: function (q) {
			return Math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3]);
		},
		normalize: function (out, q) {
			var x = q[0], y = q[1], z = q[2], w = q[3];
			var len = Math.sqrt(x * x + y * y + z * z + w * w);
			if (len > 0.000001) {
				var inv = 1.0 / len;
				out[0] = x * inv;
				out[1] = y * inv;
				out[2] = z * inv;
				out[3] = w * inv;
			} else {
				out[0] = 0.0;
				out[1] = 0.0;
				out[2] = 0.0;
				out[3] = 1.0;
			}
			return out;
		},
		conjugate: function (out, q) {
			out[0] = -q[0];
			out[1] = -q[1];
			out[2] = -q[2];
			out[3] = q[3];
			return out;
		},
		invert: function (out, q) {
			var a0 = q[0], a1 = q[1], a2 = q[2], a3 = q[3];
			var dot = a0 * a0 + a1 * a1 + a2 * a2 + a3 * a3;
			if (dot > 0.000001) {
				var invDot = 1.0 / dot;
				out[0] = -a0 * invDot;
				out[1] = -a1 * invDot;
				out[2] = -a2 * invDot;
				out[3] = a3 * invDot;
			} else {
				out[0] = 0.0;
				out[1] = 0.0;
				out[2] = 0.0;
				out[3] = 1.0;
			}
			return out;
		},
		multiply: function (out, a, b) {
			var ax = a[0], ay = a[1], az = a[2], aw = a[3];
			var bx = b[0], by = b[1], bz = b[2], bw = b[3];
			out[0] = ax * bw + aw * bx + ay * bz - az * by;
			out[1] = ay * bw + aw * by + az * bx - ax * bz;
			out[2] = az * bw + aw * bz + ax * by - ay * bx;
			out[3] = aw * bw - ax * bx - ay * by - az * bz;
			return out;
		},
		fromAxisAngle: function (out, axis, rad) {
			var halfRad = rad * 0.5;
			var s = Math.sin(halfRad);
			var ax = axis[0], ay = axis[1], az = axis[2];
			var len = Math.sqrt(ax * ax + ay * ay + az * az);
			if (len > 0.000001) {
				var inv = 1.0 / len;
				ax *= inv;
				ay *= inv;
				az *= inv;
			}
			out[0] = ax * s;
			out[1] = ay * s;
			out[2] = az * s;
			out[3] = Math.cos(halfRad);
			return out;
		},
		slerp: function (out, a, b, t) {
			var ax = a[0], ay = a[1], az = a[2], aw = a[3];
			var bx = b[0], by = b[1], bz = b[2], bw = b[3];
			var cosHalfTheta = ax * bx + ay * by + az * bz + aw * bw;

			if (cosHalfTheta < 0.0) {
				bx = -bx;
				by = -by;
				bz = -bz;
				bw = -bw;
				cosHalfTheta = -cosHalfTheta;
			}

			if (cosHalfTheta > 0.9995) {
				out[0] = ax + t * (bx - ax);
				out[1] = ay + t * (by - ay);
				out[2] = az + t * (bz - az);
				out[3] = aw + t * (bw - aw);
				return quat.normalize(out, out);
			}

			var halfTheta = Math.acos(cosHalfTheta);
			var sinHalfTheta = Math.sqrt(1.0 - cosHalfTheta * cosHalfTheta);
			if (Math.abs(sinHalfTheta) < 0.000001) {
				out[0] = ax;
				out[1] = ay;
				out[2] = az;
				out[3] = aw;
				return out;
			}

			var ratioA = Math.sin((1.0 - t) * halfTheta) / sinHalfTheta;
			var ratioB = Math.sin(t * halfTheta) / sinHalfTheta;

			out[0] = ax * ratioA + bx * ratioB;
			out[1] = ay * ratioA + by * ratioB;
			out[2] = az * ratioA + bz * ratioB;
			out[3] = aw * ratioA + bw * ratioB;
			return out;
		},
		toMat4: function (out, q) {
			var x = q[0], y = q[1], z = q[2], w = q[3];
			var x2 = x + x, y2 = y + y, z2 = z + z;
			var xx = x * x2, xy = x * y2, xz = x * z2;
			var yy = y * y2, yz = y * z2, zz = z * z2;
			var wx = w * x2, wy = w * y2, wz = w * z2;

			out[0] = 1.0 - (yy + zz);
			out[1] = xy + wz;
			out[2] = xz - wy;
			out[3] = 0.0;

			out[4] = xy - wz;
			out[5] = 1.0 - (xx + zz);
			out[6] = yz + wx;
			out[7] = 0.0;

			out[8] = xz + wy;
			out[9] = yz - wx;
			out[10] = 1.0 - (xx + yy);
			out[11] = 0.0;

			out[12] = 0.0;
			out[13] = 0.0;
			out[14] = 0.0;
			out[15] = 1.0;
			return out;
		},
		rotateVec3: function (out, q, v) {
			var qx = q[0], qy = q[1], qz = q[2], qw = q[3];
			var vx = v[0], vy = v[1], vz = v[2];

			// t = 2 * cross(q.xyz, v)
			var tx = 2.0 * (qy * vz - qz * vy);
			var ty = 2.0 * (qz * vx - qx * vz);
			var tz = 2.0 * (qx * vy - qy * vx);

			// out = v + qw * t + cross(q.xyz, t)
			out[0] = vx + qw * tx + (qy * tz - qz * ty);
			out[1] = vy + qw * ty + (qz * tx - qx * tz);
			out[2] = vz + qw * tz + (qx * ty - qy * tx);
			return out;
		}
	};

	// Matrix4 operations (column-major 16-element Float32Array)
	var mat4 = {
		create: function () {
			var out = new Float32Array(16);
			out[0] = 1.0;
			out[5] = 1.0;
			out[10] = 1.0;
			out[15] = 1.0;
			return out;
		},
		identity: function (out) {
			out[0] = 1.0; out[1] = 0.0; out[2] = 0.0; out[3] = 0.0;
			out[4] = 0.0; out[5] = 1.0; out[6] = 0.0; out[7] = 0.0;
			out[8] = 0.0; out[9] = 0.0; out[10] = 1.0; out[11] = 0.0;
			out[12] = 0.0; out[13] = 0.0; out[14] = 0.0; out[15] = 1.0;
			return out;
		},
		clone: function (m) {
			var out = new Float32Array(16);
			out.set(m);
			return out;
		},
		multiply: function (out, a, b) {
			var b0, b1, b2, b3;
			for (var c = 0; c < 4; c++) {
				b0 = b[c * 4 + 0];
				b1 = b[c * 4 + 1];
				b2 = b[c * 4 + 2];
				b3 = b[c * 4 + 3];
				out[c * 4 + 0] = b0 * a[0] + b1 * a[4] + b2 * a[8] + b3 * a[12];
				out[c * 4 + 1] = b0 * a[1] + b1 * a[5] + b2 * a[9] + b3 * a[13];
				out[c * 4 + 2] = b0 * a[2] + b1 * a[6] + b2 * a[10] + b3 * a[14];
				out[c * 4 + 3] = b0 * a[3] + b1 * a[7] + b2 * a[11] + b3 * a[15];
			}
			return out;
		},
		lookAt: function (out, eye, center, up) {
			var eyex = eye[0], eyey = eye[1], eyez = eye[2];
			var zx = eyex - center[0], zy = eyey - center[1], zz = eyez - center[2];
			var lenZ = Math.sqrt(zx * zx + zy * zy + zz * zz);
			if (lenZ > 0.000001) {
				var invZ = 1.0 / lenZ;
				zx *= invZ; zy *= invZ; zz *= invZ;
			} else {
				zx = 0.0; zy = 0.0; zz = 1.0;
			}

			var xx = up[1] * zz - up[2] * zy;
			var xy = up[2] * zx - up[0] * zz;
			var xz = up[0] * zy - up[1] * zx;
			var lenX = Math.sqrt(xx * xx + xy * xy + xz * xz);
			if (lenX > 0.000001) {
				var invX = 1.0 / lenX;
				xx *= invX; xy *= invX; xz *= invX;
			} else {
				if (Math.abs(zy) > 0.999) {
					xx = 1.0; xy = 0.0; xz = 0.0;
				} else {
					xx = 0.0; xy = 1.0; xz = 0.0;
				}
			}

			var yx = zy * xz - zz * xy;
			var yy = zz * xx - zx * xz;
			var yz = zx * xy - zy * xx;

			out[0] = xx;
			out[1] = yx;
			out[2] = zx;
			out[3] = 0.0;

			out[4] = xy;
			out[5] = yy;
			out[6] = zy;
			out[7] = 0.0;

			out[8] = xz;
			out[9] = yz;
			out[10] = zz;
			out[11] = 0.0;

			out[12] = -(xx * eyex + xy * eyey + xz * eyez);
			out[13] = -(yx * eyex + yy * eyey + yz * eyez);
			out[14] = -(zx * eyex + zy * eyey + zz * eyez);
			out[15] = 1.0;
			return out;
		},
		perspective: function (out, fovy, aspect, near, far) {
			var f = 1.0 / Math.tan(fovy * 0.5);
			var nf = 1.0 / (near - far);

			out[0] = f / aspect;
			out[1] = 0.0;
			out[2] = 0.0;
			out[3] = 0.0;

			out[4] = 0.0;
			out[5] = f;
			out[6] = 0.0;
			out[7] = 0.0;

			out[8] = 0.0;
			out[9] = 0.0;
			out[10] = (far + near) * nf;
			out[11] = -1.0;

			out[12] = 0.0;
			out[13] = 0.0;
			out[14] = (2.0 * far * near) * nf;
			out[15] = 0.0;
			return out;
		},
		invert: function (out, m) {
			var a00 = m[0], a10 = m[1], a20 = m[2], a30 = m[3];
			var a01 = m[4], a11 = m[5], a21 = m[6], a31 = m[7];
			var a02 = m[8], a12 = m[9], a22 = m[10], a32 = m[11];
			var a03 = m[12], a13 = m[13], a23 = m[14], a33 = m[15];

			var b00 = a00 * a11 - a01 * a10;
			var b01 = a00 * a12 - a02 * a10;
			var b02 = a00 * a13 - a03 * a10;
			var b03 = a01 * a12 - a02 * a11;
			var b04 = a01 * a13 - a03 * a11;
			var b05 = a02 * a13 - a03 * a12;
			var b06 = a20 * a31 - a21 * a30;
			var b07 = a20 * a32 - a22 * a30;
			var b08 = a20 * a33 - a23 * a30;
			var b09 = a21 * a32 - a22 * a31;
			var b10 = a21 * a33 - a23 * a31;
			var b11 = a22 * a33 - a23 * a32;

			var det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06;
			if (!det || Math.abs(det) < 0.000000000001) {
				return null;
			}
			var invDet = 1.0 / det;

			out[0] = (a11 * b11 - a12 * b10 + a13 * b09) * invDet;
			out[1] = (-a10 * b11 + a12 * b08 - a13 * b07) * invDet;
			out[2] = (a10 * b10 - a11 * b08 + a13 * b06) * invDet;
			out[3] = (-a10 * b09 + a11 * b07 - a12 * b06) * invDet;

			out[4] = (-a01 * b11 + a02 * b10 - a03 * b09) * invDet;
			out[5] = (a00 * b11 - a02 * b08 + a03 * b07) * invDet;
			out[6] = (-a00 * b10 + a01 * b08 - a03 * b06) * invDet;
			out[7] = (a00 * b09 - a01 * b07 + a02 * b06) * invDet;

			out[8] = (a31 * b05 - a32 * b04 + a33 * b03) * invDet;
			out[9] = (-a30 * b05 + a32 * b02 - a33 * b01) * invDet;
			out[10] = (a30 * b04 - a31 * b02 + a33 * b00) * invDet;
			out[11] = (-a30 * b03 + a31 * b01 - a32 * b00) * invDet;

			out[12] = (-a21 * b05 + a22 * b04 - a23 * b03) * invDet;
			out[13] = (a20 * b05 - a22 * b02 + a23 * b01) * invDet;
			out[14] = (-a20 * b04 + a21 * b02 - a23 * b00) * invDet;
			out[15] = (a20 * b03 - a21 * b01 + a22 * b00) * invDet;
			return out;
		},
		transpose: function (out, m) {
			out[0] = m[0]; out[1] = m[4]; out[2] = m[8]; out[3] = m[12];
			out[4] = m[1]; out[5] = m[5]; out[6] = m[9]; out[7] = m[13];
			out[8] = m[2]; out[9] = m[6]; out[10] = m[10]; out[11] = m[14];
			out[12] = m[3]; out[13] = m[7]; out[14] = m[11]; out[15] = m[15];
			return out;
		},
		transformVec4: function (out, m, v) {
			var x = v[0], y = v[1], z = v[2], w = v[3];
			out[0] = m[0] * x + m[4] * y + m[8] * z + m[12] * w;
			out[1] = m[1] * x + m[5] * y + m[9] * z + m[13] * w;
			out[2] = m[2] * x + m[6] * y + m[10] * z + m[14] * w;
			out[3] = m[3] * x + m[7] * y + m[11] * z + m[15] * w;
			return out;
		}
	};

	// Frustum Plane Classification constants
	var OUTSIDE = -1;
	var INTERSECTS = 0;
	var INSIDE = 1;

	// Gribb-Hartmann Frustum
	function Frustum(planes) {
		this.planes = planes; // Array of 6 planes: [A, B, C, D]
	}

	Frustum.OUTSIDE = OUTSIDE;
	Frustum.INTERSECTS = INTERSECTS;
	Frustum.INSIDE = INSIDE;

	Frustum.fromViewProjection = function (vp, normalize) {
		if (typeof normalize === 'undefined') {
			normalize = true;
		}
		var planes = new Array(6);

		// Left plane: row3 + row0
		planes[0] = new Float32Array([
			vp[3] + vp[0],
			vp[7] + vp[4],
			vp[11] + vp[8],
			vp[15] + vp[12]
		]);

		// Right plane: row3 - row0
		planes[1] = new Float32Array([
			vp[3] - vp[0],
			vp[7] - vp[4],
			vp[11] - vp[8],
			vp[15] - vp[12]
		]);

		// Bottom plane: row3 + row1
		planes[2] = new Float32Array([
			vp[3] + vp[1],
			vp[7] + vp[5],
			vp[11] + vp[9],
			vp[15] + vp[13]
		]);

		// Top plane: row3 - row1
		planes[3] = new Float32Array([
			vp[3] - vp[1],
			vp[7] - vp[5],
			vp[11] - vp[9],
			vp[15] - vp[13]
		]);

		// Near plane: row3 + row2
		planes[4] = new Float32Array([
			vp[3] + vp[2],
			vp[7] + vp[6],
			vp[11] + vp[10],
			vp[15] + vp[14]
		]);

		// Far plane: row3 - row2
		planes[5] = new Float32Array([
			vp[3] - vp[2],
			vp[7] - vp[6],
			vp[11] - vp[10],
			vp[15] - vp[14]
		]);

		if (normalize) {
			for (var i = 0; i < 6; i++) {
				var p = planes[i];
				var len = Math.sqrt(p[0] * p[0] + p[1] * p[1] + p[2] * p[2]);
				if (len > 0.000001) {
					var inv = 1.0 / len;
					p[0] *= inv;
					p[1] *= inv;
					p[2] *= inv;
					p[3] *= inv;
				}
			}
		}

		return new Frustum(planes);
	};

	Frustum.prototype.distanceToPlane = function (planeIdx, point) {
		var p = this.planes[planeIdx];
		return p[0] * point[0] + p[1] * point[1] + p[2] * point[2] + p[3];
	};

	Frustum.prototype.containsPoint = function (point) {
		for (var i = 0; i < 6; i++) {
			if (this.distanceToPlane(i, point) < 0.0) {
				return false;
			}
		}
		return true;
	};

	Frustum.prototype.classifySphere = function (center, radius) {
		var allInside = true;
		for (var i = 0; i < 6; i++) {
			var dist = this.distanceToPlane(i, center);
			if (dist < -radius) {
				return OUTSIDE;
			}
			if (dist < radius) {
				allInside = false;
			}
		}
		return allInside ? INSIDE : INTERSECTS;
	};

	Frustum.prototype.containsSphere = function (center, radius) {
		return this.classifySphere(center, radius) !== OUTSIDE;
	};

	Frustum.prototype.classifyAABB = function (minPoint, maxPoint) {
		var allInside = true;
		for (var i = 0; i < 6; i++) {
			var p = this.planes[i];
			var px = p[0] >= 0.0 ? maxPoint[0] : minPoint[0];
			var py = p[1] >= 0.0 ? maxPoint[1] : minPoint[1];
			var pz = p[2] >= 0.0 ? maxPoint[2] : minPoint[2];

			if (p[0] * px + p[1] * py + p[2] * pz + p[3] < 0.0) {
				return OUTSIDE;
			}

			var nx = p[0] >= 0.0 ? minPoint[0] : maxPoint[0];
			var ny = p[1] >= 0.0 ? minPoint[1] : maxPoint[1];
			var nz = p[2] >= 0.0 ? minPoint[2] : maxPoint[2];

			if (p[0] * nx + p[1] * ny + p[2] * nz + p[3] < 0.0) {
				allInside = false;
			}
		}
		return allInside ? INSIDE : INTERSECTS;
	};

	Frustum.prototype.containsAABB = function (minPoint, maxPoint) {
		return this.classifyAABB(minPoint, maxPoint) !== OUTSIDE;
	};

	// OrbitCamera
	function OrbitCamera(target, distance, yaw, pitch, options) {
		options = options || {};
		this.target = target ? vec3.clone(target) : vec3.create(0.0, 0.0, 0.0);
		this.distance = typeof distance === 'number' ? distance : 5.0;
		this.yaw = typeof yaw === 'number' ? yaw : 0.0;
		this.pitch = clampPitch(typeof pitch === 'number' ? pitch : 0.0);
		this.up = options.up ? vec3.clone(options.up) : vec3.create(0.0, 1.0, 0.0);
		vec3.normalize(this.up, this.up);
		this.fovy = typeof options.fovy === 'number' ? options.fovy : (45.0 * Math.PI) / 180.0;
		this.near = typeof options.near === 'number' ? options.near : 0.1;
		this.far = typeof options.far === 'number' ? options.far : 100.0;
	}

	OrbitCamera.prototype.setTarget = function (target) {
		this.target[0] = target[0];
		this.target[1] = target[1];
		this.target[2] = target[2];
	};

	OrbitCamera.prototype.setDistance = function (dist, minDist, maxDist) {
		var minD = typeof minDist === 'number' ? minDist : 0.01;
		var maxD = typeof maxDist === 'number' ? maxDist : 10000.0;
		this.distance = clamp(dist, minD, maxD);
	};

	OrbitCamera.prototype.setYaw = function (yaw) {
		this.yaw = yaw;
	};

	OrbitCamera.prototype.setPitch = function (pitch) {
		this.pitch = clampPitch(pitch);
	};

	OrbitCamera.prototype.orbit = function (deltaYaw, deltaPitch) {
		this.yaw += deltaYaw;
		this.pitch = clampPitch(this.pitch + deltaPitch);
	};

	OrbitCamera.prototype.zoom = function (deltaDistance, minDist, maxDist) {
		this.setDistance(this.distance + deltaDistance, minDist, maxDist);
	};

	OrbitCamera.prototype.pan = function (dx, dy) {
		var eye = this.getEyePosition();
		var forward = vec3.create();
		vec3.subtract(forward, this.target, eye);
		vec3.normalize(forward, forward);

		var right = vec3.create();
		vec3.cross(right, forward, this.up);
		vec3.normalize(right, right);

		var camUp = vec3.create();
		vec3.cross(camUp, right, forward);
		vec3.normalize(camUp, camUp);

		var shift = vec3.create();
		vec3.scaleAndAdd(shift, shift, right, dx);
		vec3.scaleAndAdd(shift, shift, camUp, dy);
		vec3.add(this.target, this.target, shift);
	};

	OrbitCamera.prototype.getEyePosition = function (out) {
		out = out || vec3.create();
		var cp = Math.cos(this.pitch);
		var sp = Math.sin(this.pitch);
		var cy = Math.cos(this.yaw);
		var sy = Math.sin(this.yaw);

		out[0] = this.target[0] + this.distance * cp * sy;
		out[1] = this.target[1] + this.distance * sp;
		out[2] = this.target[2] + this.distance * cp * cy;
		return out;
	};

	OrbitCamera.prototype.getViewMatrix = function (out) {
		out = out || mat4.create();
		var eye = this.getEyePosition();
		return mat4.lookAt(out, eye, this.target, this.up);
	};

	OrbitCamera.prototype.getProjectionMatrix = function (out, aspect) {
		out = out || mat4.create();
		return mat4.perspective(out, this.fovy, aspect, this.near, this.far);
	};

	OrbitCamera.prototype.getViewProjectionMatrix = function (out, aspect) {
		out = out || mat4.create();
		var p = this.getProjectionMatrix(null, aspect);
		var v = this.getViewMatrix();
		return mat4.multiply(out, p, v);
	};

	OrbitCamera.prototype.getInverseViewProjectionMatrix = function (out, aspect) {
		out = out || mat4.create();
		var vp = this.getViewProjectionMatrix(null, aspect);
		return mat4.invert(out, vp);
	};

	OrbitCamera.prototype.getFrustum = function (aspect) {
		var vp = this.getViewProjectionMatrix(null, aspect);
		return Frustum.fromViewProjection(vp, true);
	};

	// FirstPersonCamera
	function FirstPersonCamera(position, yaw, pitch, options) {
		options = options || {};
		this.position = position ? vec3.clone(position) : vec3.create(0.0, 0.0, 0.0);
		this.yaw = typeof yaw === 'number' ? yaw : 0.0;
		this.pitch = clampPitch(typeof pitch === 'number' ? pitch : 0.0);
		this.up = options.up ? vec3.clone(options.up) : vec3.create(0.0, 1.0, 0.0);
		vec3.normalize(this.up, this.up);
		this.fovy = typeof options.fovy === 'number' ? options.fovy : (45.0 * Math.PI) / 180.0;
		this.near = typeof options.near === 'number' ? options.near : 0.1;
		this.far = typeof options.far === 'number' ? options.far : 100.0;
		this.orientation = quat.create();
		this._updateOrientationFromEuler();
	}

	FirstPersonCamera.prototype._updateOrientationFromEuler = function () {
		var qy = quat.create();
		var qx = quat.create();
		quat.fromAxisAngle(qy, [0.0, 1.0, 0.0], this.yaw);
		quat.fromAxisAngle(qx, [1.0, 0.0, 0.0], this.pitch);
		quat.multiply(this.orientation, qy, qx);
		quat.normalize(this.orientation, this.orientation);
	};

	FirstPersonCamera.prototype.setPosition = function (pos) {
		this.position[0] = pos[0];
		this.position[1] = pos[1];
		this.position[2] = pos[2];
	};

	FirstPersonCamera.prototype.setYaw = function (yaw) {
		this.yaw = yaw;
		this._updateOrientationFromEuler();
	};

	FirstPersonCamera.prototype.setPitch = function (pitch) {
		this.pitch = clampPitch(pitch);
		this._updateOrientationFromEuler();
	};

	FirstPersonCamera.prototype.rotate = function (deltaYaw, deltaPitch) {
		this.yaw += deltaYaw;
		this.pitch = clampPitch(this.pitch + deltaPitch);
		this._updateOrientationFromEuler();
	};

	FirstPersonCamera.prototype.rotateByQuat = function (q) {
		quat.multiply(this.orientation, q, this.orientation);
		quat.normalize(this.orientation, this.orientation);
	};

	FirstPersonCamera.prototype.getForward = function (out) {
		out = out || vec3.create();
		quat.rotateVec3(out, this.orientation, [0.0, 0.0, -1.0]);
		return vec3.normalize(out, out);
	};

	FirstPersonCamera.prototype.getRight = function (out) {
		out = out || vec3.create();
		quat.rotateVec3(out, this.orientation, [1.0, 0.0, 0.0]);
		return vec3.normalize(out, out);
	};

	FirstPersonCamera.prototype.getUp = function (out) {
		out = out || vec3.create();
		quat.rotateVec3(out, this.orientation, [0.0, 1.0, 0.0]);
		return vec3.normalize(out, out);
	};

	FirstPersonCamera.prototype.moveForward = function (dist) {
		var fwd = this.getForward();
		vec3.scaleAndAdd(this.position, this.position, fwd, dist);
	};

	FirstPersonCamera.prototype.moveRight = function (dist) {
		var right = this.getRight();
		vec3.scaleAndAdd(this.position, this.position, right, dist);
	};

	FirstPersonCamera.prototype.moveUp = function (dist) {
		var up = this.getUp();
		vec3.scaleAndAdd(this.position, this.position, up, dist);
	};

	FirstPersonCamera.prototype.getViewMatrix = function (out) {
		out = out || mat4.create();
		var forward = this.getForward();
		var target = vec3.create();
		vec3.add(target, this.position, forward);
		return mat4.lookAt(out, this.position, target, this.up);
	};

	FirstPersonCamera.prototype.getProjectionMatrix = function (out, aspect) {
		out = out || mat4.create();
		return mat4.perspective(out, this.fovy, aspect, this.near, this.far);
	};

	FirstPersonCamera.prototype.getViewProjectionMatrix = function (out, aspect) {
		out = out || mat4.create();
		var p = this.getProjectionMatrix(null, aspect);
		var v = this.getViewMatrix();
		return mat4.multiply(out, p, v);
	};

	FirstPersonCamera.prototype.getInverseViewProjectionMatrix = function (out, aspect) {
		out = out || mat4.create();
		var vp = this.getViewProjectionMatrix(null, aspect);
		return mat4.invert(out, vp);
	};

	FirstPersonCamera.prototype.getFrustum = function (aspect) {
		var vp = this.getViewProjectionMatrix(null, aspect);
		return Frustum.fromViewProjection(vp, true);
	};

	return {
		vec3: vec3,
		quat: quat,
		mat4: mat4,
		clamp: clamp,
		clampPitch: clampPitch,
		Frustum: Frustum,
		OrbitCamera: OrbitCamera,
		FirstPersonCamera: FirstPersonCamera
	};
}));
