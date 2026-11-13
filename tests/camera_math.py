#!/usr/bin/env python3
"""Mathematical camera controller and frustum plane culling reference implementation.

Provides quaternion operations, Euler pitch and yaw clamping, look-at view
matrices, perspective projection, inverse view-projection, and Gribb-Hartmann
6-plane view frustum extraction for spatial containment and bounding box culling.
"""

import math

# Vector3 mathematical utilities
def vec3_create(x=0.0, y=0.0, z=0.0):
    return [float(x), float(y), float(z)]


def vec3_clone(v):
    return [float(v[0]), float(v[1]), float(v[2])]


def vec3_add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def vec3_sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def vec3_scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]


def vec3_scale_and_add(a, b, s):
    return [a[0] + b[0] * s, a[1] + b[1] * s, a[2] + b[2] * s]


def vec3_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec3_cross(a, b):
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def vec3_length_sq(v):
    return v[0] * v[0] + v[1] * v[1] + v[2] * v[2]


def vec3_length(v):
    return math.sqrt(vec3_length_sq(v))


def vec3_distance(a, b):
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    dz = a[2] - b[2]
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def vec3_normalize(v):
    l = vec3_length(v)
    if l > 1e-12:
        inv = 1.0 / l
        return [v[0] * inv, v[1] * inv, v[2] * inv]
    return [0.0, 0.0, 0.0]


# Quaternion mathematical utilities [x, y, z, w]
def quat_identity():
    return [0.0, 0.0, 0.0, 1.0]


def quat_clone(q):
    return [float(q[0]), float(q[1]), float(q[2]), float(q[3])]


def quat_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]


def quat_length_sq(q):
    return quat_dot(q, q)


def quat_length(q):
    return math.sqrt(quat_length_sq(q))


def quat_normalize(q):
    l = quat_length(q)
    if l > 1e-12:
        inv = 1.0 / l
        return [q[0] * inv, q[1] * inv, q[2] * inv, q[3] * inv]
    return quat_identity()


def quat_conjugate(q):
    return [-q[0], -q[1], -q[2], q[3]]


def quat_invert(q):
    ls = quat_length_sq(q)
    if ls > 1e-12:
        inv = 1.0 / ls
        return [-q[0] * inv, -q[1] * inv, -q[2] * inv, q[3] * inv]
    return quat_identity()


def quat_multiply(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return [
        ax * bw + aw * bx + ay * bz - az * by,
        ay * bw + aw * by + az * bx - ax * bz,
        az * bw + aw * bz + ax * by - ay * bx,
        aw * bw - ax * bx - ay * by - az * bz,
    ]


def quat_from_axis_angle(axis, angle_rad):
    norm_axis = vec3_normalize(axis)
    half_angle = angle_rad * 0.5
    s = math.sin(half_angle)
    return [
        norm_axis[0] * s,
        norm_axis[1] * s,
        norm_axis[2] * s,
        math.cos(half_angle),
    ]


def quat_slerp(a, b, t):
    t = max(0.0, min(1.0, float(t)))
    cos_half_theta = quat_dot(a, b)
    b_copy = [b[0], b[1], b[2], b[3]]

    # Ensure shortest path across 4D hypersphere
    if cos_half_theta < 0.0:
        b_copy = [-b_copy[0], -b_copy[1], -b_copy[2], -b_copy[3]]
        cos_half_theta = -cos_half_theta

    if cos_half_theta > 0.9995:
        # Collinear: use normalized linear interpolation (nlerp)
        res = [
            a[0] + t * (b_copy[0] - a[0]),
            a[1] + t * (b_copy[1] - a[1]),
            a[2] + t * (b_copy[2] - a[2]),
            a[3] + t * (b_copy[3] - a[3]),
        ]
        return quat_normalize(res)

    half_theta = math.acos(cos_half_theta)
    sin_half_theta = math.sqrt(1.0 - cos_half_theta * cos_half_theta)
    if abs(sin_half_theta) < 1e-12:
        return quat_clone(a)

    ratio_a = math.sin((1.0 - t) * half_theta) / sin_half_theta
    ratio_b = math.sin(t * half_theta) / sin_half_theta

    return [
        a[0] * ratio_a + b_copy[0] * ratio_b,
        a[1] * ratio_a + b_copy[1] * ratio_b,
        a[2] * ratio_a + b_copy[2] * ratio_b,
        a[3] * ratio_a + b_copy[3] * ratio_b,
    ]


def quat_to_mat4(q):
    x, y, z, w = q
    x2, y2, z2 = x + x, y + y, z + z
    xx, xy, xz = x * x2, x * y2, x * z2
    yy, yz, zz = y * y2, y * z2, z * z2
    wx, wy, wz = w * x2, w * y2, w * z2

    # Column-major 4x4 matrix
    return [
        1.0 - (yy + zz), xy + wz, xz - wy, 0.0,
        xy - wz, 1.0 - (xx + zz), yz + wx, 0.0,
        xz + wy, yz - wx, 1.0 - (xx + yy), 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def quat_rotate_vec3(q, v):
    # v_rot = v + 2 * cross(q.xyz, cross(q.xyz, v) + q.w * v)
    qx, qy, qz, qw = q
    q_vec = [qx, qy, qz]
    uv = vec3_cross(q_vec, v)
    uuv = vec3_cross(q_vec, uv)
    scaled_uv = vec3_scale(uv, 2.0 * qw)
    scaled_uuv = vec3_scale(uuv, 2.0)
    return vec3_add(v, vec3_add(scaled_uv, scaled_uuv))


# Matrix4 column-major 16-element array utilities
def mat4_identity():
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def mat4_clone(m):
    return [float(x) for x in m]


def mat4_multiply(a, b):
    # Column-major out = a * b
    out = [0.0] * 16
    for col in range(4):
        b0 = b[col * 4 + 0]
        b1 = b[col * 4 + 1]
        b2 = b[col * 4 + 2]
        b3 = b[col * 4 + 3]
        out[col * 4 + 0] = b0 * a[0] + b1 * a[4] + b2 * a[8] + b3 * a[12]
        out[col * 4 + 1] = b0 * a[1] + b1 * a[5] + b2 * a[9] + b3 * a[13]
        out[col * 4 + 2] = b0 * a[2] + b1 * a[6] + b2 * a[10] + b3 * a[14]
        out[col * 4 + 3] = b0 * a[3] + b1 * a[7] + b2 * a[11] + b3 * a[15]
    return out


def mat4_look_at(eye, center, up):
    # Right-handed view matrix (camera looks towards negative Z)
    eyex, eyey, eyez = eye
    z = vec3_sub(eye, center)
    z = vec3_normalize(z)

    # If eye equals center, default to +Z
    if vec3_length_sq(z) < 1e-12:
        z = [0.0, 0.0, 1.0]

    x = vec3_cross(up, z)
    x = vec3_normalize(x)
    if vec3_length_sq(x) < 1e-12:
        # Degenerate up vector: fallback to orthogonal axis
        if abs(z[1]) > 0.999:
            x = vec3_normalize(vec3_cross([0.0, 0.0, 1.0], z))
        else:
            x = vec3_normalize(vec3_cross([0.0, 1.0, 0.0], z))

    y = vec3_cross(z, x)

    # Column-major rotation and translation
    return [
        x[0], y[0], z[0], 0.0,
        x[1], y[1], z[1], 0.0,
        x[2], y[2], z[2], 0.0,
        -(x[0] * eyex + x[1] * eyey + x[2] * eyez),
        -(y[0] * eyex + y[1] * eyey + y[2] * eyez),
        -(z[0] * eyex + z[1] * eyey + z[2] * eyez),
        1.0,
    ]


def mat4_perspective(fovy_rad, aspect, near, far):
    f = 1.0 / math.tan(fovy_rad * 0.5)
    nf = 1.0 / (near - far)

    return [
        f / aspect, 0.0, 0.0, 0.0,
        0.0, f, 0.0, 0.0,
        0.0, 0.0, (far + near) * nf, -1.0,
        0.0, 0.0, (2.0 * far * near) * nf, 0.0,
    ]


def mat4_invert(m):
    a00, a10, a20, a30 = m[0], m[1], m[2], m[3]
    a01, a11, a21, a31 = m[4], m[5], m[6], m[7]
    a02, a12, a22, a32 = m[8], m[9], m[10], m[11]
    a03, a13, a23, a33 = m[12], m[13], m[14], m[15]

    b00 = a00 * a11 - a01 * a10
    b01 = a00 * a12 - a02 * a10
    b02 = a00 * a13 - a03 * a10
    b03 = a01 * a12 - a02 * a11
    b04 = a01 * a13 - a03 * a11
    b05 = a02 * a13 - a03 * a12
    b06 = a20 * a31 - a21 * a30
    b07 = a20 * a32 - a22 * a30
    b08 = a20 * a33 - a23 * a30
    b09 = a21 * a32 - a22 * a31
    b10 = a21 * a33 - a23 * a31
    b11 = a22 * a33 - a23 * a32

    det = b00 * b11 - b01 * b10 + b02 * b09 + b03 * b08 - b04 * b07 + b05 * b06
    if abs(det) < 1e-12:
        return None

    inv_det = 1.0 / det

    return [
        (a11 * b11 - a12 * b10 + a13 * b09) * inv_det,
        (-a10 * b11 + a12 * b08 - a13 * b07) * inv_det,
        (a10 * b10 - a11 * b08 + a13 * b06) * inv_det,
        (-a10 * b09 + a11 * b07 - a12 * b06) * inv_det,

        (-a01 * b11 + a02 * b10 - a03 * b09) * inv_det,
        (a00 * b11 - a02 * b08 + a03 * b07) * inv_det,
        (-a00 * b10 + a01 * b08 - a03 * b06) * inv_det,
        (a00 * b09 - a01 * b07 + a02 * b06) * inv_det,

        (a31 * b05 - a32 * b04 + a33 * b03) * inv_det,
        (-a30 * b05 + a32 * b02 - a33 * b01) * inv_det,
        (a30 * b04 - a31 * b02 + a33 * b00) * inv_det,
        (-a30 * b03 + a31 * b01 - a32 * b00) * inv_det,

        (-a21 * b05 + a22 * b04 - a23 * b03) * inv_det,
        (a20 * b05 - a22 * b02 + a23 * b01) * inv_det,
        (-a20 * b04 + a21 * b02 - a23 * b00) * inv_det,
        (a20 * b03 - a21 * b01 + a22 * b00) * inv_det,
    ]


def mat4_transpose(m):
    return [
        m[0], m[4], m[8], m[12],
        m[1], m[5], m[9], m[13],
        m[2], m[6], m[10], m[14],
        m[3], m[7], m[11], m[15],
    ]


def mat4_transform_vec4(m, v):
    x, y, z, w = v
    return [
        m[0] * x + m[4] * y + m[8] * z + m[12] * w,
        m[1] * x + m[5] * y + m[9] * z + m[13] * w,
        m[2] * x + m[6] * y + m[10] * z + m[14] * w,
        m[3] * x + m[7] * y + m[11] * z + m[15] * w,
    ]


# Euler pitch and yaw clamping
MAX_PITCH_DEG = 89.0
MAX_PITCH_RAD = math.radians(MAX_PITCH_DEG)


def clamp(val, min_val, max_val):
    return max(min_val, min(max_val, val))


def clamp_pitch(pitch_rad, min_deg=-MAX_PITCH_DEG, max_deg=MAX_PITCH_DEG):
    min_rad = math.radians(min_deg)
    max_rad = math.radians(max_deg)
    return clamp(pitch_rad, min_rad, max_rad)


# Gribb-Hartmann Frustum Plane Extraction and Culling Utility
class Frustum:
    PLANE_LEFT = 0
    PLANE_RIGHT = 1
    PLANE_BOTTOM = 2
    PLANE_TOP = 3
    PLANE_NEAR = 4
    PLANE_FAR = 5

    OUTSIDE = -1
    INTERSECTS = 0
    INSIDE = 1

    def __init__(self, planes):
        # planes is a list of 6 planes: [A, B, C, D] where Ax + By + Cz + D >= 0 is inside
        self.planes = planes

    @classmethod
    def from_view_projection(cls, vp, normalize=True):
        """Extract the 6 view frustum planes from a column-major 4x4 View-Projection matrix.

        Using the Gribb-Hartmann algorithm:
        Row 0: vp[0], vp[4], vp[8],  vp[12]
        Row 1: vp[1], vp[5], vp[9],  vp[13]
        Row 2: vp[2], vp[6], vp[10], vp[14]
        Row 3: vp[3], vp[7], vp[11], vp[15]
        """
        planes = [None] * 6

        # Left plane: row3 + row0
        planes[cls.PLANE_LEFT] = [
            vp[3] + vp[0],
            vp[7] + vp[4],
            vp[11] + vp[8],
            vp[15] + vp[12],
        ]

        # Right plane: row3 - row0
        planes[cls.PLANE_RIGHT] = [
            vp[3] - vp[0],
            vp[7] - vp[4],
            vp[11] - vp[8],
            vp[15] - vp[12],
        ]

        # Bottom plane: row3 + row1
        planes[cls.PLANE_BOTTOM] = [
            vp[3] + vp[1],
            vp[7] + vp[5],
            vp[11] + vp[9],
            vp[15] + vp[13],
        ]

        # Top plane: row3 - row1
        planes[cls.PLANE_TOP] = [
            vp[3] - vp[1],
            vp[7] - vp[5],
            vp[11] - vp[9],
            vp[15] - vp[13],
        ]

        # Near plane (OpenGL/WebGL [-1, 1]): row3 + row2
        planes[cls.PLANE_NEAR] = [
            vp[3] + vp[2],
            vp[7] + vp[6],
            vp[11] + vp[10],
            vp[15] + vp[14],
        ]

        # Far plane: row3 - row2
        planes[cls.PLANE_FAR] = [
            vp[3] - vp[2],
            vp[7] - vp[6],
            vp[11] - vp[10],
            vp[15] - vp[14],
        ]

        if normalize:
            for i in range(6):
                p = planes[i]
                length = math.sqrt(p[0] * p[0] + p[1] * p[1] + p[2] * p[2])
                if length > 1e-12:
                    inv = 1.0 / length
                    planes[i] = [p[0] * inv, p[1] * inv, p[2] * inv, p[3] * inv]

        return cls(planes)

    def distance_to_plane(self, plane_idx, point):
        p = self.planes[plane_idx]
        return p[0] * point[0] + p[1] * point[1] + p[2] * point[2] + p[3]

    def contains_point(self, point):
        """Check if point is inside or on the boundary of the frustum."""
        for i in range(6):
            if self.distance_to_plane(i, point) < 0.0:
                return False
        return True

    def classify_sphere(self, center, radius):
        """Classify a bounding sphere: OUTSIDE (-1), INTERSECTS (0), or INSIDE (1)."""
        all_inside = True
        for i in range(6):
            dist = self.distance_to_plane(i, center)
            if dist < -radius:
                return self.OUTSIDE
            if dist < radius:
                all_inside = False
        return self.INSIDE if all_inside else self.INTERSECTS

    def contains_sphere(self, center, radius):
        """Returns True if the sphere is inside or intersecting the frustum (visible)."""
        return self.classify_sphere(center, radius) != self.OUTSIDE

    def classify_aabb(self, min_point, max_point):
        """Classify an Axis-Aligned Bounding Box: OUTSIDE (-1), INTERSECTS (0), or INSIDE (1)."""
        all_inside = True
        for i in range(6):
            p = self.planes[i]
            # Positive vertex (furthest in direction of normal)
            px = max_point[0] if p[0] >= 0.0 else min_point[0]
            py = max_point[1] if p[1] >= 0.0 else min_point[1]
            pz = max_point[2] if p[2] >= 0.0 else min_point[2]

            if (p[0] * px + p[1] * py + p[2] * pz + p[3]) < 0.0:
                return self.OUTSIDE

            # Negative vertex (furthest opposite direction of normal)
            nx = min_point[0] if p[0] >= 0.0 else max_point[0]
            ny = min_point[1] if p[1] >= 0.0 else max_point[1]
            nz = min_point[2] if p[2] >= 0.0 else max_point[2]

            if (p[0] * nx + p[1] * ny + p[2] * nz + p[3]) < 0.0:
                all_inside = False

        return self.INSIDE if all_inside else self.INTERSECTS

    def contains_aabb(self, min_point, max_point):
        """Returns True if the AABB is inside or intersecting the frustum (visible)."""
        return self.classify_aabb(min_point, max_point) != self.OUTSIDE


# Orbit Camera Controller
class OrbitCamera:
    """Mathematical Orbit Camera revolving around a target in spherical coordinates."""

    def __init__(
        self,
        target=(0.0, 0.0, 0.0),
        distance=5.0,
        yaw=0.0,
        pitch=0.0,
        up=(0.0, 1.0, 0.0),
        fovy=math.radians(45.0),
        near=0.1,
        far=100.0,
    ):
        self.target = vec3_clone(target)
        self.distance = float(distance)
        self.yaw = float(yaw)
        self.pitch = clamp_pitch(float(pitch))
        self.up = vec3_normalize(vec3_clone(up))
        self.fovy = float(fovy)
        self.near = float(near)
        self.far = float(far)

    def set_target(self, target):
        self.target = vec3_clone(target)

    def set_distance(self, distance, min_dist=0.01, max_dist=10000.0):
        self.distance = clamp(float(distance), min_dist, max_dist)

    def set_yaw(self, yaw):
        self.yaw = float(yaw)

    def set_pitch(self, pitch):
        self.pitch = clamp_pitch(float(pitch))

    def orbit(self, delta_yaw, delta_pitch):
        self.yaw += float(delta_yaw)
        self.pitch = clamp_pitch(self.pitch + float(delta_pitch))

    def zoom(self, delta_distance, min_dist=0.01, max_dist=10000.0):
        self.set_distance(self.distance + delta_distance, min_dist, max_dist)

    def get_eye_position(self):
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)
        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)

        # Standard spherical coordinates revolving around target
        offset = [
            self.distance * cp * sy,
            self.distance * sp,
            self.distance * cp * cy,
        ]
        return vec3_add(self.target, offset)

    def pan(self, dx, dy):
        """Pan target and camera position along right and up axes."""
        eye = self.get_eye_position()
        forward = vec3_normalize(vec3_sub(self.target, eye))
        right = vec3_normalize(vec3_cross(forward, self.up))
        cam_up = vec3_normalize(vec3_cross(right, forward))

        shift = vec3_add(vec3_scale(right, dx), vec3_scale(cam_up, dy))
        self.target = vec3_add(self.target, shift)

    def get_view_matrix(self):
        eye = self.get_eye_position()
        return mat4_look_at(eye, self.target, self.up)

    def get_projection_matrix(self, aspect):
        return mat4_perspective(self.fovy, aspect, self.near, self.far)

    def get_view_projection_matrix(self, aspect):
        p = self.get_projection_matrix(aspect)
        v = self.get_view_matrix()
        return mat4_multiply(p, v)

    def get_inverse_view_projection_matrix(self, aspect):
        vp = self.get_view_projection_matrix(aspect)
        return mat4_invert(vp)

    def get_frustum(self, aspect):
        vp = self.get_view_projection_matrix(aspect)
        return Frustum.from_view_projection(vp)


# First-Person Camera Controller
class FirstPersonCamera:
    """Mathematical First-Person (FPS / Free Look) Camera Controller."""

    def __init__(
        self,
        position=(0.0, 0.0, 0.0),
        yaw=0.0,
        pitch=0.0,
        up=(0.0, 1.0, 0.0),
        fovy=math.radians(45.0),
        near=0.1,
        far=100.0,
    ):
        self.position = vec3_clone(position)
        self.yaw = float(yaw)
        self.pitch = clamp_pitch(float(pitch))
        self.up = vec3_normalize(vec3_clone(up))
        self.fovy = float(fovy)
        self.near = float(near)
        self.far = float(far)
        self.orientation = quat_identity()
        self._update_orientation_from_euler()

    def _update_orientation_from_euler(self):
        # Create rotation quaternion: yaw around Y, pitch around X
        qy = quat_from_axis_angle([0.0, 1.0, 0.0], self.yaw)
        qx = quat_from_axis_angle([1.0, 0.0, 0.0], self.pitch)
        self.orientation = quat_normalize(quat_multiply(qy, qx))

    def set_position(self, pos):
        self.position = vec3_clone(pos)

    def set_yaw(self, yaw):
        self.yaw = float(yaw)
        self._update_orientation_from_euler()

    def set_pitch(self, pitch):
        self.pitch = clamp_pitch(float(pitch))
        self._update_orientation_from_euler()

    def rotate(self, delta_yaw, delta_pitch):
        self.yaw += float(delta_yaw)
        self.pitch = clamp_pitch(self.pitch + float(delta_pitch))
        self._update_orientation_from_euler()

    def rotate_by_quat(self, q):
        self.orientation = quat_normalize(quat_multiply(q, self.orientation))

    def get_forward(self):
        # Rotate default forward vector [0, 0, -1] by orientation quaternion
        return vec3_normalize(quat_rotate_vec3(self.orientation, [0.0, 0.0, -1.0]))

    def get_right(self):
        # Rotate default right vector [1, 0, 0] by orientation quaternion
        return vec3_normalize(quat_rotate_vec3(self.orientation, [1.0, 0.0, 0.0]))

    def get_up(self):
        # Rotate default up vector [0, 1, 0] by orientation quaternion
        return vec3_normalize(quat_rotate_vec3(self.orientation, [0.0, 1.0, 0.0]))

    def move_forward(self, distance):
        fwd = self.get_forward()
        self.position = vec3_scale_and_add(self.position, fwd, distance)

    def move_right(self, distance):
        right = self.get_right()
        self.position = vec3_scale_and_add(self.position, right, distance)

    def move_up(self, distance):
        up = self.get_up()
        self.position = vec3_scale_and_add(self.position, up, distance)

    def get_view_matrix(self):
        forward = self.get_forward()
        target = vec3_add(self.position, forward)
        return mat4_look_at(self.position, target, self.up)

    def get_projection_matrix(self, aspect):
        return mat4_perspective(self.fovy, aspect, self.near, self.far)

    def get_view_projection_matrix(self, aspect):
        p = self.get_projection_matrix(aspect)
        v = self.get_view_matrix()
        return mat4_multiply(p, v)

    def get_inverse_view_projection_matrix(self, aspect):
        vp = self.get_view_projection_matrix(aspect)
        return mat4_invert(vp)

    def get_frustum(self, aspect):
        vp = self.get_view_projection_matrix(aspect)
        return Frustum.from_view_projection(vp)
