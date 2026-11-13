#!/usr/bin/env python3
"""Verification tests for IndigoCS-webgl-tutorials HTML, JS, and GLSL assets."""

import json
import os
import re
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


def extract_embedded_shaders(js_content):
    """Extract embedded vertex and fragment shaders defined as JS string arrays or variables."""
    shaders = []
    # Pattern for shaders joined via array of lines: var vertexShaderText = [ ... ].join('\n');
    array_pattern = re.compile(
        r"var\s+(vertexShaderText|fragmentShaderText)\s*=\s*\[(.*?)\]\.join\(['\"]\\n['\"]\);",
        re.DOTALL,
    )
    for match in array_pattern.finditer(js_content):
        name = match.group(1)
        raw_body = match.group(2)
        lines = []
        for line in raw_body.splitlines():
            line = line.strip()
            if line.startswith(("'","\"")) and (line.endswith("',") or line.endswith("\",") or line.endswith("'") or line.endswith("\"")):
                # Strip wrapping quotes and trailing comma
                unquoted = re.sub(r"^['\"]|['\"],?$", "", line)
                lines.append(unquoted)
        shader_src = "\n".join(lines)
        shaders.append((name, shader_src))
    return shaders


def validate_brackets(source, filename="shader"):
    """Verify balanced parentheses, brackets, and braces."""
    stack = []
    pairs = {")": "(", "}": "{", "]": "["}
    for idx, char in enumerate(source):
        if char in "({[":
            stack.append((char, idx))
        elif char in ")}]":
            if not stack:
                return False, f"Unopened closing bracket '{char}' at index {idx} in {filename}"
            last_char, last_idx = stack.pop()
            if pairs[char] != last_char:
                return False, (
                    f"Mismatched bracket: expected '{last_char}' closed, found '{char}' "
                    f"at index {idx} in {filename}"
                )
    if stack:
        unclosed, idx = stack[-1]
        return False, f"Unclosed bracket '{unclosed}' at index {idx} in {filename}"
    return True, "Balanced"


class TestWebGLTutorials(unittest.TestCase):
    def test_all_tutorial_directories_and_entrypoints_exist(self):
        """Verify each tutorial directory contains index.html and app.js."""
        for d in TUTORIAL_DIRS:
            tdir = os.path.join(ROOT, d)
            self.assertTrue(os.path.isdir(tdir), f"Missing directory: {tdir}")
            self.assertTrue(os.path.isfile(os.path.join(tdir, "index.html")), f"Missing index.html in {d}")
            self.assertTrue(os.path.isfile(os.path.join(tdir, "app.js")), f"Missing app.js in {d}")

    def test_root_index_portal_and_links(self):
        """Verify repository root index.html exists and links to all tutorials."""
        root_index = os.path.join(ROOT, "index.html")
        self.assertTrue(os.path.isfile(root_index), "Missing root index.html portal")
        with open(root_index, "r", encoding="utf-8") as f:
            content = f.read()

        for d in TUTORIAL_DIRS:
            encoded_dir = d.replace(" ", "%20")
            expected_href = f"{encoded_dir}/index.html"
            self.assertIn(
                expected_href,
                content,
                f"Root index.html missing link to {d} (expected {expected_href})",
            )

    def test_glsl_shader_syntax_and_bracket_matching(self):
        """Validate standalone and embedded GLSL shaders for bracket balance and required symbols."""
        glsl_files = []
        for dirpath, _, filenames in os.walk(ROOT):
            if ".git" in dirpath:
                continue
            for f in filenames:
                if f.endswith(".glsl"):
                    glsl_files.append(os.path.join(dirpath, f))

        self.assertGreaterEqual(len(glsl_files), 10, "Expected at least 10 standalone .glsl files")

        for glsl_path in glsl_files:
            rel_path = os.path.relpath(glsl_path, ROOT)
            with open(glsl_path, "r", encoding="utf-8") as f:
                source = f.read()

            self.assertIn("void main()", source, f"Shader {rel_path} lacks 'void main()'")

            # Check balanced brackets
            balanced, msg = validate_brackets(source, rel_path)
            self.assertTrue(balanced, msg)

            # Vertex shader must assign to gl_Position
            if glsl_path.endswith(".vs.glsl"):
                self.assertIn("gl_Position", source, f"Vertex shader {rel_path} does not assign gl_Position")

            # Fragment shader must assign to gl_FragColor or use discard
            if glsl_path.endswith(".fs.glsl"):
                has_color = ("gl_FragColor" in source) or ("gl_FragData" in source) or ("discard" in source)
                self.assertTrue(has_color, f"Fragment shader {rel_path} does not write color or discard")

        # Also validate embedded shaders inside JS files (01, 02, 03)
        for d in ["01 - Simple Triangle", "02 - Rotating Cube", "03 - Textured Cube"]:
            app_js_path = os.path.join(ROOT, d, "app.js")
            with open(app_js_path, "r", encoding="utf-8") as f:
                js_src = f.read()
            embedded = extract_embedded_shaders(js_src)
            self.assertGreaterEqual(len(embedded), 2, f"Expected vertex and fragment shaders in {d}/app.js")
            for name, shader_src in embedded:
                self.assertIn("void main()", shader_src, f"Embedded shader {name} in {d} lacks 'void main()'")
                balanced, msg = validate_brackets(shader_src, f"{d}:{name}")
                self.assertTrue(balanced, msg)
                if "vertex" in name.lower():
                    self.assertIn("gl_Position", shader_src, f"Embedded {name} in {d} lacks gl_Position")
                if "fragment" in name.lower():
                    self.assertIn("gl_FragColor", shader_src, f"Embedded {name} in {d} lacks gl_FragColor")

    def test_asset_link_integrity_html(self):
        """Verify HTML script and image tags reference valid files."""
        script_pattern = re.compile(r'<script\s+[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)
        img_pattern = re.compile(r'<img\s+[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)

        for d in TUTORIAL_DIRS:
            html_path = os.path.join(ROOT, d, "index.html")
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()

            script_srcs = script_pattern.findall(content)
            for src in script_srcs:
                if src.startswith("http://") or src.startswith("https://"):
                    continue
                # Normalize leading slash for relative test check
                target_path = os.path.join(ROOT, d, src.lstrip("/"))
                self.assertTrue(
                    os.path.isfile(target_path),
                    f"Broken script reference '{src}' in {d}/index.html (target: {target_path})",
                )

            img_srcs = img_pattern.findall(content)
            for src in img_srcs:
                if src.startswith("http://") or src.startswith("https://"):
                    continue
                target_path = os.path.join(ROOT, d, src.lstrip("/"))
                self.assertTrue(
                    os.path.isfile(target_path),
                    f"Broken image reference '{src}' in {d}/index.html (target: {target_path})",
                )

    def test_asset_link_integrity_models_and_textures(self):
        """Verify 3D JSON models and textures exist and are structurally valid."""
        # Susan model in 04 and 05
        for d in ["04 - Loading External Files", "05 - Phong Lighting Intro"]:
            susan_json = os.path.join(ROOT, d, "Susan.json")
            susan_tex = os.path.join(ROOT, d, "SusanTexture.png")
            self.assertTrue(os.path.isfile(susan_json), f"Missing Susan.json in {d}")
            self.assertTrue(os.path.isfile(susan_tex), f"Missing SusanTexture.png in {d}")

            with open(susan_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("meshes", data)
            mesh = data["meshes"][0]
            self.assertIn("vertices", mesh)
            self.assertIn("normals", mesh)
            self.assertIn("faces", mesh)
            self.assertGreater(len(mesh["vertices"]), 0)
            self.assertGreater(len(mesh["faces"]), 0)

        # Crate texture in 03
        crate_tex = os.path.join(ROOT, "03 - Textured Cube", "crate.png")
        self.assertTrue(os.path.isfile(crate_tex), "Missing crate.png in 03 - Textured Cube")

        # Room model in Shadow Mapping
        room_json = os.path.join(ROOT, "Shadow Mapping", "Room.json")
        self.assertTrue(os.path.isfile(room_json), "Missing Room.json in Shadow Mapping")
        with open(room_json, "r", encoding="utf-8") as f:
            room_data = json.load(f)
        self.assertIn("meshes", room_data)
        self.assertGreater(len(room_data["meshes"]), 0)

    def test_canvas_elements_and_ids(self):
        """Verify each tutorial has a canvas element with an explicit id."""
        canvas_pattern = re.compile(r'<canvas\s+[^>]*id=["\']([^"\']+)["\']', re.IGNORECASE)
        for d in TUTORIAL_DIRS:
            html_path = os.path.join(ROOT, d, "index.html")
            with open(html_path, "r", encoding="utf-8") as f:
                content = f.read()
            match = canvas_pattern.search(content)
            self.assertIsNotNone(match, f"Missing canvas with id in {d}/index.html")
            canvas_id = match.group(1)
            self.assertIn(canvas_id, ["game-surface", "gl-surface"])

    def test_invariant_zero_emojis(self):
        """Strict invariant check: zero emojis across all code, documentation, and tickets."""
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]")
        violations = []
        for dirpath, _, filenames in os.walk(ROOT):
            if ".git" in dirpath:
                continue
            for f in filenames:
                if f.endswith((".png", ".fbx", ".blend", ".blend1", ".pyc")):
                    continue
                p = os.path.join(dirpath, f)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                        content = fp.read()
                        if emoji_pattern.search(content):
                            violations.append(os.path.relpath(p, ROOT))
                except Exception:
                    pass
        self.assertEqual(violations, [], f"Emoji violations found in files: {violations}")

    def test_invariant_no_arrows_in_titles_and_links(self):
        """Strict invariant check: no arrows (->, <-, unicode arrows) in titles, headers, or links."""
        arrow_pattern = re.compile(r"->|<-|[→←↓↑]|&rarr;|&larr;|&darr;|&uarr;")
        tag_pattern = re.compile(r"<(title|h[1-6]|a)\b[^>]*>(.*?)</\1>", re.IGNORECASE | re.DOTALL)
        violations = []
        for dirpath, _, filenames in os.walk(ROOT):
            if ".git" in dirpath:
                continue
            for f in filenames:
                if not f.endswith(".html"):
                    continue
                p = os.path.join(dirpath, f)
                with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                    content = fp.read()
                for match in tag_pattern.finditer(content):
                    tag_text = match.group(2)
                    if arrow_pattern.search(tag_text):
                        violations.append(f"{os.path.relpath(p, ROOT)}: {tag_text.strip()}")

        self.assertEqual(violations, [], f"Arrow violations found in HTML titles or links: {violations}")

    def test_tickets_directory_soundness(self):
        """Verify ticket directory contains valid markdown tickets with actionable tasks."""
        tickets_dir = os.path.join(ROOT, "tickets")
        self.assertTrue(os.path.isdir(tickets_dir), "Missing tickets directory")
        ticket_files = [f for f in os.listdir(tickets_dir) if f.endswith(".md")]
        self.assertGreaterEqual(len(ticket_files), 10, "Expected at least 10 tickets in tickets/")
        for tf in ticket_files:
            tpath = os.path.join(tickets_dir, tf)
            with open(tpath, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(content.startswith("# [INDIGOCS-WEBGL-TUTORIALS]"), f"Invalid ticket header in {tf}")
            self.assertIn("Task Description", content, f"Missing Task Description in {tf}")


if __name__ == "__main__":
    unittest.main()
