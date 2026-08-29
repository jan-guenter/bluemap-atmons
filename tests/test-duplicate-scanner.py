#!/usr/bin/env python3
"""Focused tests for the deterministic cross-add-on duplicate scanner."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("scan_duplicates", REPOSITORY_ROOT / "tools" / "scan_duplicates.py")
if SPEC is None or SPEC.loader is None:  # pragma: no cover - fixed repository layout
    raise RuntimeError("could not load tools/scan_duplicates.py")
SCANNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SCANNER
SPEC.loader.exec_module(SCANNER)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


class DuplicateScannerTest(unittest.TestCase):
    def source(self, text: str, *, addon: str = "one", path: str = "src/main/java/example/One.java"):
        return SCANNER.SourceFile(
            addon=addon,
            commit="a" * 40,
            path=path,
            category="java_main",
            layer="behavioral",
            data=text.encode("utf-8"),
        )

    def write_manifest(self, root: Path, version: str, commits: dict[str, str]) -> Path:
        path = root / "versions" / version / "manifest.json"
        path.parent.mkdir(parents=True)
        manifest = {
            "schema_version": 1,
            "atmons": {
                "version": version,
                "tag": f"atmons-{version}",
                "pack_commit": "b" * 40,
            },
            "release": {
                "addon_count": len(commits),
                "component_count": len(commits),
            },
            "components": [
                {
                    "id": addon,
                    "kind": "addon",
                    "submodule_path": f"addons/{addon}",
                    "commit": commit,
                }
                for addon, commit in sorted(commits.items())
            ],
        }
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return path

    def test_java_lexer_and_alpha_renaming(self) -> None:
        left = SCANNER.lex_java("int calculate(int input) { /* ignored */ return input + 3; }")
        right = SCANNER.lex_java("int transform(int value) { // ignored\n return value + 7; }")
        self.assertNotEqual(SCANNER.exact_token_stream(left), SCANNER.exact_token_stream(right))
        self.assertEqual(SCANNER.renamed_token_stream(left), SCANNER.renamed_token_stream(right))
        self.assertNotIn("ignored", SCANNER.exact_token_stream(left))

    def test_java_text_blocks_are_single_literals_and_do_not_create_fake_methods(self) -> None:
        left_source = '''
            final class One {
                String describe() {
                    return """
                        a } fakeMethod() { return "quoted";
                        line two
                        """;
                }
                int realMethod() { return 1; }
            }
        '''
        right_source = left_source.replace("line two", "different contents")
        left = SCANNER.lex_java(left_source)
        right = SCANNER.lex_java(right_source)
        text_blocks = [token for token in left if token.kind == "text_block"]
        self.assertEqual(1, len(text_blocks))
        self.assertIn("fakeMethod", text_blocks[0].text)
        self.assertNotEqual(SCANNER.exact_token_stream(left), SCANNER.exact_token_stream(right))
        self.assertEqual(SCANNER.renamed_token_stream(left), SCANNER.renamed_token_stream(right))

        methods = SCANNER.extract_methods(self.source(left_source), minimum_tokens=5)
        self.assertEqual(["describe", "realMethod"], [method.name for method in methods])

    def test_method_pass_finds_declarations_not_control_blocks(self) -> None:
        source = self.source(
            """
            package example;
            final class One {
                int calculate(int input) {
                    if (input > 0) {
                        return helper(input);
                    }
                    Runnable task = () -> { helper(input); };
                    return input;
                }
                int helper(int value) { return value + 1; }
            }
            """
        )
        methods = SCANNER.extract_methods(source, minimum_tokens=5)
        self.assertEqual(["calculate", "helper"], [method.name for method in methods])
        self.assertTrue(all(method.end_line >= method.start_line for method in methods))

    def test_path_scope_excludes_generated_and_third_party_content(self) -> None:
        self.assertEqual(("java_main", "behavioral"), SCANNER.classify_path("src/main/java/example/Renderer.java"))
        self.assertEqual(("verification_tool", "scaffolding"), SCANNER.classify_path("tools/verify_artifact.py"))
        self.assertIsNone(SCANNER.classify_path("build/generated/source/Copy.java"))
        self.assertIsNone(SCANNER.classify_path("third_party/Library.java"))
        self.assertIsNone(SCANNER.classify_path("LICENSE"))

    def test_dotted_version_is_preserved_in_report_names(self) -> None:
        json_path, markdown_path = SCANNER.default_report_paths(Path("/repo"), "1.2.0")
        self.assertEqual(Path("/repo/reports/deduplication/atmons-1.2.0.json"), json_path)
        self.assertEqual(Path("/repo/reports/deduplication/atmons-1.2.0.md"), markdown_path)

    def test_scan_uses_pinned_git_objects_and_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            git(root, "init", "-q")
            (root / "addons").mkdir()
            commits: dict[str, str] = {}
            for addon, class_name, method_name, literal in (
                ("one", "One", "calculate", "3"),
                ("two", "Two", "transform", "7"),
            ):
                repo = root / "addons" / addon
                repo.mkdir()
                git(repo, "init", "-q")
                git(repo, "config", "user.name", "Scanner Test")
                git(repo, "config", "user.email", "scanner@example.invalid")
                java = repo / "src" / "main" / "java" / "example" / f"{class_name}.java"
                java.parent.mkdir(parents=True)
                java.write_text(
                    f"package example; final class {class_name} {{ int {method_name}(int value) {{ return value + {literal}; }} }}\n",
                    encoding="utf-8",
                )
                tool = repo / "tools" / "verify_artifact.py"
                tool.parent.mkdir()
                tool.write_text("#!/usr/bin/env python3\nprint('same')\n", encoding="utf-8")
                git(repo, "add", ".")
                git(repo, "commit", "-qm", "fixture")
                commits[addon] = git(repo, "rev-parse", "HEAD")
                git(root, "update-index", "--add", "--cacheinfo", f"160000,{commits[addon]},addons/{addon}")

            manifest_path = self.write_manifest(root, "fixture", commits)

            first = SCANNER.build_report(root, "fixture", expected_addons=2, minimum_method_tokens=5, minimum_file_tokens=5)
            fixture_java = root / "addons" / "one" / "src" / "main" / "java" / "example" / "One.java"
            fixture_java.write_text("this mutable working-tree file must be ignored\n", encoding="utf-8")
            second = SCANNER.build_report(root, "fixture", expected_addons=2, minimum_method_tokens=5, minimum_file_tokens=5)

            self.assertEqual(first, second)
            self.assertEqual(2, first["scope"]["addon_count"])
            self.assertTrue(any(group["addon_count"] == 2 for group in first["exact_file_clones"]))
            self.assertTrue(first["java_file_token_clones"]["renamed"])
            self.assertEqual("versions/fixture/manifest.json", first["target"]["manifest"]["path"])
            self.assertEqual(hashlib.sha256(manifest_path.read_bytes()).hexdigest(), first["target"]["manifest"]["sha256"])
            self.assertTrue(first["target"]["gitlink_comparison"]["exact"])
            self.assertTrue(all(item["matches_manifest"] for item in first["scope"]["addons"]))
            self.assertIn("Inventory fingerprint", SCANNER.render_markdown(first))

    def test_scan_rejects_index_gitlink_commit_not_pinned_by_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            git(root, "init", "-q")
            repo = root / "addons" / "one"
            repo.mkdir(parents=True)
            git(repo, "init", "-q")
            git(repo, "config", "user.name", "Scanner Test")
            git(repo, "config", "user.email", "scanner@example.invalid")
            source = repo / "src" / "main" / "java" / "example" / "One.java"
            source.parent.mkdir(parents=True)
            source.write_text("final class One { int value() { return 1; } }\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "manifest pin")
            manifest_commit = git(repo, "rev-parse", "HEAD")
            self.write_manifest(root, "fixture", {"one": manifest_commit})

            source.write_text("final class One { int value() { return 2; } }\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-qm", "different index pin")
            index_commit = git(repo, "rev-parse", "HEAD")
            git(root, "update-index", "--add", "--cacheinfo", f"160000,{index_commit},addons/one")

            with self.assertRaisesRegex(RuntimeError, r"commit mismatches: one manifest="):
                SCANNER.build_report(
                    root,
                    "fixture",
                    expected_addons=1,
                    minimum_method_tokens=5,
                    minimum_file_tokens=5,
                )


if __name__ == "__main__":
    unittest.main()
