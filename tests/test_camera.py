#!/usr/bin/env python3
"""Comprehensive unit tests for camera mathematics, controllers, and frustum culling.

Verifies quaternion operations, view matrix baselines, Euler pitch/yaw clamping,
inverse view-projection calculation, and Gribb-Hartmann frustum plane extraction.
"""

import math
import unittest

from tests.camera_math import (
    Frustum,
    FirstPersonCamera,
    OrbitCamera,
    clamp_pitch,
    mat4_identity,
    mat4_invert,
    mat4_look_at,
    mat4_multiply,
    mat4_perspective,
    mat4_transform_vec4,
    quat_conjugate,
    quat_from_axis_angle,
    quat_identity,
    quat_invert,
    quat_length,
    quat_multiply,
    quat_normalize,
    quat_rotate_vec3,
    quat_slerp,
    quat_to_mat4,
    vec3_add,
    vec3_cross,
    vec3_distance,
    vec3_dot,
    vec3_length,
    vec3_normalize,
    vec3_sub,
)


class TestQuaternionMath(unittest.TestCase):
    def test_quaternion_identity_and_normalization(self):
        q = quat_identity()
        self.assertEqual(q, [0.0, 0.0, 0.0, 1.0])
        self.assertAlmostEqual(quat_length(q), 1.0, places=7)

        # Normalization of non-unit quaternion
        q_raw = [0.0, 3.0, 4.0, 0.0]
        q_norm = quat_normalize(q_raw)
        self.assertAlmostEqual(q_norm[0], 0.0, places=7)
        self.assertAlmostEqual(q_norm[1], 0.6, places=7)
        self.assertAlmostEqual(q_norm[2], 0.8, places=7)
        self.assertAlmostEqual(q_norm[3], 0.0, places=7)
        self.assertAlmostEqual(quat_length(q_norm), 1.0, places=7)

        # Degenerate zero quaternion returns identity
        q_zero = quat_normalize([0.0, 0.0, 0.0, 0.0])
        self.assertEqual(q_zero, [0.0, 0.0, 0.0, 1.0])

    def test_quaternion_conjugate_and_inverse(self):
        q = quat_from_axis_angle([1.0, 2.0, 3.0], math.radians(60.0))
        q_inv = quat_invert(q)
        q_conj = quat_conjugate(q)

        # For unit quaternion, inverse equals conjugate
        for i in range(4):
            self.assertAlmostEqual(q_inv[i], q_conj[i], places=6)

        # q * q^-1 == identity
        prod = quat_multiply(q, q_inv)
        self.assertAlmostEqual(prod[0], 0.0, places=6)
        self.assertAlmostEqual(prod[1], 0.0, places=6)
        self.assertAlmostEqual(prod[2], 0.0, places=6)
        self.assertAlmostEqual(prod[3], 1.0, places=6)

    def test_quaternion_multiplication_properties(self):
        qi = [1.0, 0.0, 0.0, 0.0]
        qj = [0.0, 1.0, 0.0, 0.0]
        qk = [0.0, 0.0, 1.0, 0.0]

        # Hamilton relations: i * j = k
        ij = quat_multiply(qi, qj)
        self.assertAlmostEqual(ij[0], qk[0], places=6)
        self.assertAlmostEqual(ij[1], qk[1], places=6)
        self.assertAlmostEqual(ij[2], qk[2], places=6)
        self.assertAlmostEqual(ij[3], qk[3], places=6)

        # j * k = i
        jk = quat_multiply(qj, qk)
        self.assertAlmostEqual(jk[0], qi[0], places=6)
        self.assertAlmostEqual(jk[1], qi[1], places=6)
        self.assertAlmostEqual(jk[2], qi[2], places=6)
        self.assertAlmostEqual(jk[3], qi[3], places=6)

        # Anti-commutativity: j * i = -k
        ji = quat_multiply(qj, qi)
        self.assertAlmostEqual(ji[0], -qk[0], places=6)
        self.assertAlmostEqual(ji[1], -qk[1], places=6)
        self.assertAlmostEqual(ji[2], -qk[2], places=6)
        self.assertAlmostEqual(ji[3], -qk[3], places=6)

    def test_quaternion_slerp_interpolation(self):
        q0 = quat_from_axis_angle([0.0, 1.0, 0.0], 0.0)
        q1 = quat_from_axis_angle([0.0, 1.0, 0.0], math.radians(90.0))

        # t = 0 yields q0
        res0 = quat_slerp(q0, q1, 0.0)
        for i in range(4):
            self.assertAlmostEqual(res0[i], q0[i], places=6)

        # t = 1 yields q1
        res1 = quat_slerp(q0, q1, 1.0)
        for i in range(4):
            self.assertAlmostEqual(res1[i], q1[i], places=6)

        # t = 0.5 yields 45 deg rotation
        res_half = quat_slerp(q0, q1, 0.5)
        expected = quat_from_axis_angle([0.0, 1.0, 0.0], math.radians(45.0))
        for i in range(4):
            self.assertAlmostEqual(res_half[i], expected[i], places=6)

        # Slerp with negative dot product takes shortest path
        q1_neg = [-x for x in q1]
        res_neg = quat_slerp(q0, q1_neg, 0.5)
        for i in range(4):
            self.assertAlmostEqual(res_neg[i], expected[i], places=6)

    def test_quaternion_to_matrix_and_vector_rotation(self):
        angle = math.radians(90.0)
        q = quat_from_axis_angle([0.0, 1.0, 0.0], angle)
        m = quat_to_mat4(q)

        # Rotate vector [1, 0, 0] by 90 deg around Y:
        # Expect [0, 0, -1] in right-handed system
        v = [1.0, 0.0, 0.0]
        v_rot = quat_rotate_vec3(q, v)
        self.assertAlmostEqual(v_rot[0], 0.0, places=6)
        self.assertAlmostEqual(v_rot[1], 0.0, places=6)
        self.assertAlmostEqual(v_rot[2], -1.0, places=6)

        # Transforming with matrix matches
        v4 = [1.0, 0.0, 0.0, 1.0]
        v4_rot = mat4_transform_vec4(m, v4)
        self.assertAlmostEqual(v4_rot[0], 0.0, places=6)
        self.assertAlmostEqual(v4_rot[1], 0.0, places=6)
        self.assertAlmostEqual(v4_rot[2], -1.0, places=6)


class TestViewMatrixLookAt(unittest.TestCase):
    def test_look_at_standard_baseline(self):
        eye = [0.0, 0.0, 5.0]
        center = [0.0, 0.0, 0.0]
        up = [0.0, 1.0, 0.0]

        v_mat = mat4_look_at(eye, center, up)

        # World eye point transforms to origin in camera space
        p_eye = mat4_transform_vec4(v_mat, [0.0, 0.0, 5.0, 1.0])
        self.assertAlmostEqual(p_eye[0], 0.0, places=6)
        self.assertAlmostEqual(p_eye[1], 0.0, places=6)
        self.assertAlmostEqual(p_eye[2], 0.0, places=6)

        # World center transforms to -Z in camera space at distance 5
        p_center = mat4_transform_vec4(v_mat, [0.0, 0.0, 0.0, 1.0])
        self.assertAlmostEqual(p_center[0], 0.0, places=6)
        self.assertAlmostEqual(p_center[1], 0.0, places=6)
        self.assertAlmostEqual(p_center[2], -5.0, places=6)

        # Point to the right transforms to +X in camera space
        p_right = mat4_transform_vec4(v_mat, [2.0, 0.0, 5.0, 1.0])
        self.assertAlmostEqual(p_right[0], 2.0, places=6)
        self.assertAlmostEqual(p_right[1], 0.0, places=6)
        self.assertAlmostEqual(p_right[2], 0.0, places=6)

        # Point upwards transforms to +Y in camera space
        p_up = mat4_transform_vec4(v_mat, [0.0, 3.0, 5.0, 1.0])
        self.assertAlmostEqual(p_up[0], 0.0, places=6)
        self.assertAlmostEqual(p_up[1], 3.0, places=6)
        self.assertAlmostEqual(p_up[2], 0.0, places=6)

    def test_look_at_orthogonal_side_and_top_baselines(self):
        # Looking from +X towards origin
        eye_x = [10.0, 0.0, 0.0]
        center = [0.0, 0.0, 0.0]
        up = [0.0, 1.0, 0.0]
        v_side = mat4_look_at(eye_x, center, up)

        p_center = mat4_transform_vec4(v_side, [0.0, 0.0, 0.0, 1.0])
        self.assertAlmostEqual(p_center[0], 0.0, places=6)
        self.assertAlmostEqual(p_center[1], 0.0, places=6)
        self.assertAlmostEqual(p_center[2], -10.0, places=6)

        # Looking from +Y downwards towards origin with up along -Z
        eye_y = [0.0, 10.0, 0.0]
        up_top = [0.0, 0.0, -1.0]
        v_top = mat4_look_at(eye_y, center, up_top)

        p_top_center = mat4_transform_vec4(v_top, [0.0, 0.0, 0.0, 1.0])
        self.assertAlmostEqual(p_top_center[0], 0.0, places=6)
        self.assertAlmostEqual(p_top_center[1], 0.0, places=6)
        self.assertAlmostEqual(p_top_center[2], -10.0, places=6)


class TestEulerPitchClamping(unittest.TestCase):
    def test_pitch_clamping_bounds(self):
        # Within range
        self.assertAlmostEqual(clamp_pitch(0.0), 0.0, places=6)
        self.assertAlmostEqual(clamp_pitch(math.radians(45.0)), math.radians(45.0), places=6)
        self.assertAlmostEqual(clamp_pitch(math.radians(-45.0)), math.radians(-45.0), places=6)

        # Clamping upper bound (+89 degrees)
        max_rad = math.radians(89.0)
        self.assertAlmostEqual(clamp_pitch(math.radians(89.0)), max_rad, places=6)
        self.assertAlmostEqual(clamp_pitch(math.radians(90.0)), max_rad, places=6)
        self.assertAlmostEqual(clamp_pitch(math.radians(120.0)), max_rad, places=6)

        # Clamping lower bound (-89 degrees)
        min_rad = math.radians(-89.0)
        self.assertAlmostEqual(clamp_pitch(math.radians(-89.0)), min_rad, places=6)
        self.assertAlmostEqual(clamp_pitch(math.radians(-90.0)), min_rad, places=6)
        self.assertAlmostEqual(clamp_pitch(math.radians(-150.0)), min_rad, places=6)

    def test_orbit_camera_pitch_clamping_prevents_gimbal_lock(self):
        cam = OrbitCamera(target=[0.0, 0.0, 0.0], distance=5.0)

        # Attempt to pitch past +89 degrees
        cam.set_pitch(math.radians(100.0))
        self.assertAlmostEqual(cam.pitch, math.radians(89.0), places=6)

        eye = cam.get_eye_position()
        # Horizontal distance must not collapse to 0
        horiz_dist = math.sqrt(eye[0] * eye[0] + eye[2] * eye[2])
        self.assertGreater(horiz_dist, 0.05)

        # Attempt to pitch below -89 degrees
        cam.set_pitch(math.radians(-110.0))
        self.assertAlmostEqual(cam.pitch, math.radians(-89.0), places=6)

    def test_first_person_camera_pitch_clamping(self):
        cam = FirstPersonCamera(position=[0.0, 1.0, 5.0])
        cam.rotate(0.0, math.radians(120.0))
        self.assertAlmostEqual(cam.pitch, math.radians(89.0), places=6)

        fwd = cam.get_forward()
        right = cam.get_right()
        # Right vector remains well-defined and orthogonal
        self.assertAlmostEqual(vec3_dot(fwd, right), 0.0, places=6)
        self.assertGreater(vec3_length(right), 0.99)


class TestGribbHartmannFrustumCulling(unittest.TestCase):
    def setUp(self):
        # Camera at [0, 0, 5], looking at [0, 0, 0], up [0, 1, 0]
        # Near = 1.0 (world Z = 4.0), Far = 10.0 (world Z = -5.0)
        # FOV = 90 deg, aspect = 1.0
        self.fovy = math.radians(90.0)
        self.aspect = 1.0
        self.near = 1.0
        self.far = 10.0

        p = mat4_perspective(self.fovy, self.aspect, self.near, self.far)
        v = mat4_look_at([0.0, 0.0, 5.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0])
        self.vp = mat4_multiply(p, v)
        self.frustum = Frustum.from_view_projection(self.vp)

    def test_frustum_planes_normalized(self):
        self.assertEqual(len(self.frustum.planes), 6)
        for i in range(6):
            plane = self.frustum.planes[i]
            normal_len = math.sqrt(plane[0] ** 2 + plane[1] ** 2 + plane[2] ** 2)
            self.assertAlmostEqual(normal_len, 1.0, places=6)

    def test_point_classification(self):
        # Center target [0, 0, 0] is at distance 5 from eye, within [near=1, far=10]
        self.assertTrue(self.frustum.contains_point([0.0, 0.0, 0.0]))

        # Point inside near plane boundary (distance 0.5 from eye, world Z = 4.5)
        self.assertFalse(self.frustum.contains_point([0.0, 0.0, 4.5]))

        # Point past far plane (distance 11 from eye, world Z = -6.0)
        self.assertFalse(self.frustum.contains_point([0.0, 0.0, -6.0]))

        # Point far to the right (outside left/right planes)
        self.assertFalse(self.frustum.contains_point([20.0, 0.0, 0.0]))
        self.assertFalse(self.frustum.contains_point([-20.0, 0.0, 0.0]))

        # Point far upwards/downwards
        self.assertFalse(self.frustum.contains_point([0.0, 20.0, 0.0]))
        self.assertFalse(self.frustum.contains_point([0.0, -20.0, 0.0]))

    def test_bounding_sphere_classification(self):
        # Sphere at center completely inside
        self.assertEqual(self.frustum.classify_sphere([0.0, 0.0, 0.0], 0.5), Frustum.INSIDE)
        self.assertTrue(self.frustum.contains_sphere([0.0, 0.0, 0.0], 0.5))

        # Sphere completely outside near plane
        self.assertEqual(self.frustum.classify_sphere([0.0, 0.0, 4.8], 0.1), Frustum.OUTSIDE)
        self.assertFalse(self.frustum.contains_sphere([0.0, 0.0, 4.8], 0.1))

        # Sphere intersecting near plane (center at 4.5, radius 1.0 straddles near plane at 4.0)
        self.assertEqual(self.frustum.classify_sphere([0.0, 0.0, 4.5], 1.0), Frustum.INTERSECTS)
        self.assertTrue(self.frustum.contains_sphere([0.0, 0.0, 4.5], 1.0))

        # Sphere completely outside far plane
        self.assertEqual(self.frustum.classify_sphere([0.0, 0.0, -6.0], 0.2), Frustum.OUTSIDE)
        self.assertFalse(self.frustum.contains_sphere([0.0, 0.0, -6.0], 0.2))

        # Sphere intersecting far plane (center at -5.5, radius 1.0 straddles far plane at -5.0)
        self.assertEqual(self.frustum.classify_sphere([0.0, 0.0, -5.5], 1.0), Frustum.INTERSECTS)
        self.assertTrue(self.frustum.contains_sphere([0.0, 0.0, -5.5], 1.0))

    def test_aabb_classification(self):
        # AABB centered at origin inside frustum
        min_box = [-0.5, -0.5, -0.5]
        max_box = [0.5, 0.5, 0.5]
        self.assertEqual(self.frustum.classify_aabb(min_box, max_box), Frustum.INSIDE)
        self.assertTrue(self.frustum.contains_aabb(min_box, max_box))

        # AABB behind camera
        min_behind = [-2.0, -2.0, 6.0]
        max_behind = [2.0, 2.0, 8.0]
        self.assertEqual(self.frustum.classify_aabb(min_behind, max_behind), Frustum.OUTSIDE)
        self.assertFalse(self.frustum.contains_aabb(min_behind, max_behind))

        # AABB straddling near plane (Z from 3.5 to 4.5 across near plane at Z = 4.0)
        min_straddle = [-0.5, -0.5, 3.5]
        max_straddle = [0.5, 0.5, 4.5]
        self.assertEqual(self.frustum.classify_aabb(min_straddle, max_straddle), Frustum.INTERSECTS)
        self.assertTrue(self.frustum.contains_aabb(min_straddle, max_straddle))

        # AABB far off to the right
        min_right = [15.0, -1.0, -1.0]
        max_right = [20.0, 1.0, 1.0]
        self.assertEqual(self.frustum.classify_aabb(min_right, max_right), Frustum.OUTSIDE)
        self.assertFalse(self.frustum.contains_aabb(min_right, max_right))


class TestInverseViewProjection(unittest.TestCase):
    def test_inverse_view_projection_matrix_and_unprojection(self):
        fovy = math.radians(60.0)
        aspect = 1.333333
        near = 0.5
        far = 100.0

        p = mat4_perspective(fovy, aspect, near, far)
        v = mat4_look_at([0.0, 2.0, 10.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0])
        vp = mat4_multiply(p, v)

        inv_vp = mat4_invert(vp)
        self.assertIsNotNone(inv_vp)

        # vp * inv_vp must equal identity
        prod = mat4_multiply(vp, inv_vp)
        ident = mat4_identity()
        for i in range(16):
            self.assertAlmostEqual(prod[i], ident[i], places=5)

        # Test unprojecting near plane center in NDC [0, 0, -1, 1]
        ndc_near = [0.0, 0.0, -1.0, 1.0]
        world_near = mat4_transform_vec4(inv_vp, ndc_near)
        wnx = world_near[0] / world_near[3]
        wny = world_near[1] / world_near[3]
        wnz = world_near[2] / world_near[3]

        # Distance from eye to unprojected near point must equal near plane distance
        eye = [0.0, 2.0, 10.0]
        dist_to_near = vec3_distance(eye, [wnx, wny, wnz])
        self.assertAlmostEqual(dist_to_near, near, places=5)


class TestJavaScriptParity(unittest.TestCase):
    def test_javascript_implementation_parity(self):
        """Execute common/camera.js in Node.js and assert mathematical parity with Python."""
        import json
        import os
        import subprocess

        js_script = """
        const Cam = require('./common/camera.js');
        const q0 = Cam.quat.create();
        const q1 = Cam.quat.fromAxisAngle(Cam.quat.create(), [0, 1, 0], Math.PI / 2);
        const qslerp = Cam.quat.slerp(Cam.quat.create(), q0, q1, 0.5);

        const oc = new Cam.OrbitCamera([0, 0, 0], 5, 0, 0.2);
        const vm = Array.from(oc.getViewMatrix());
        const f = oc.getFrustum(1.333333);

        const fpc = new Cam.FirstPersonCamera([0, 1, 5], 0, 0.1);
        const fpc_fwd = Array.from(fpc.getForward());

        console.log(JSON.stringify({
            qslerp: Array.from(qslerp),
            view_matrix: vm,
            contains_origin: f.containsPoint([0, 0, 0]),
            contains_far_off: f.containsPoint([100, 0, 0]),
            fpc_forward: fpc_fwd
        }));
        """

        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        proc = subprocess.run(
            ["node", "-e", js_script],
            cwd=root_dir,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, f"Node.js execution failed: {proc.stderr}")
        data = json.loads(proc.stdout.strip())

        # Verify quaternion slerp matches Python
        py_q0 = quat_identity()
        py_q1 = quat_from_axis_angle([0.0, 1.0, 0.0], math.pi * 0.5)
        py_qslerp = quat_slerp(py_q0, py_q1, 0.5)
        for i in range(4):
            self.assertAlmostEqual(data["qslerp"][i], py_qslerp[i], places=5)

        # Verify OrbitCamera view matrix matches Python
        py_oc = OrbitCamera(target=[0.0, 0.0, 0.0], distance=5.0, yaw=0.0, pitch=0.2)
        py_vm = py_oc.get_view_matrix()
        for i in range(16):
            self.assertAlmostEqual(data["view_matrix"][i], py_vm[i], places=5)

        # Verify frustum containment
        self.assertTrue(data["contains_origin"])
        self.assertFalse(data["contains_far_off"])

        # Verify FirstPersonCamera forward vector matches Python
        py_fpc = FirstPersonCamera(position=[0.0, 1.0, 5.0], yaw=0.0, pitch=0.1)
        py_fwd = py_fpc.get_forward()
        for i in range(3):
            self.assertAlmostEqual(data["fpc_forward"][i], py_fwd[i], places=5)


if __name__ == "__main__":
    unittest.main()
