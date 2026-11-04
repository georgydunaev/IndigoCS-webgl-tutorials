#!/usr/bin/env python3
"""Verification tests for IndigoCS-webgl-tutorials HTML/JS/GLSL assets."""

import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TUTORIAL_DIRS = [
    "01 - Simple Triangle",
    "02 - Rotating Cube",
    "03 - Textured Cube",
    "04 - Loading External Files",
    "05 - Phong Lighting Intro",
    "FragShader - Mandelbrot",
    "Shadow Mapping",
]


class TestWebGLTutorials(unittest.TestCase):
    def test_all_tutorial_directories_and_entrypoints_exist(self):
        for d in TUTORIAL_DIRS:
            tdir = os.path.join(ROOT, d)
            self.assertTrue(os.path.isdir(tdir), f"Missing directory: {tdir}")
            self.assertTrue(os.path.isfile(os.path.join(tdir, "index.html")), f"Missing index.html in {d}")
            self.assertTrue(os.path.isfile(os.path.join(tdir, "app.js")), f"Missing app.js in {d}")


if __name__ == "__main__":
    unittest.main()
