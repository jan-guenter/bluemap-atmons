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
    def source(
        self,
        text: str,
        *,
        addon: str = "one",
        path: str = "src/main/java/example/One.java",
        category: str = "java_main",
        layer: str = "behavioral",
    ):
        return SCANNER.SourceFile(
            addon=addon,
            commit="a" * 40,
            path=path,
            category=category,
            layer=layer,
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

    def test_python_ast_normalizes_only_local_names(self) -> None:
        left = self.source(
            """import hashlib\n\ndef verify(source):\n    digest = hashlib.sha256(source.encode()).hexdigest()\n    return 'https://example.invalid/' + digest\n""",
            path="tools/verify.py",
            category="verification_tool",
            layer="scaffolding",
        )
        right = self.source(
            """import hashlib\n\ndef verify(value):\n    result = hashlib.sha256(value.encode()).hexdigest()\n    return 'https://example.invalid/' + result\n""",
            addon="two",
            path="tools/verify.py",
            category="verification_tool",
            layer="scaffolding",
        )
        changed_literal = self.source(
            right.data.decode("utf-8").replace("example.invalid", "other.invalid"),
            addon="three",
            path="tools/verify.py",
            category="verification_tool",
            layer="scaffolding",
        )
        changed_external = self.source(
            right.data.decode("utf-8").replace("sha256", "sha1"),
            addon="four",
            path="tools/verify.py",
            category="verification_tool",
            layer="scaffolding",
        )
        left_record = SCANNER.extract_python_records(left)[0]
        right_record = SCANNER.extract_python_records(right)[0]
        self.assertNotEqual(left_record.exact_hash, right_record.exact_hash)
        self.assertEqual(left_record.normalized_hash, right_record.normalized_hash)
        self.assertNotEqual(right_record.normalized_hash, SCANNER.extract_python_records(changed_literal)[0].normalized_hash)
        self.assertNotEqual(right_record.normalized_hash, SCANNER.extract_python_records(changed_external)[0].normalized_hash)
        self.assertEqual((3, 5), (left_record.start_line, left_record.end_line))

    def test_python_ast_fails_closed_on_syntax_error(self) -> None:
        source = self.source(
            "def broken(:\n    pass\n",
            path="tools/broken.py",
            category="tooling",
            layer="scaffolding",
        )
        with self.assertRaisesRegex(RuntimeError, r"Python parse failed closed: addons/one/tools/broken.py:1"):
            SCANNER.extract_python_records(source)

    def test_gradle_structures_preserve_coordinates_and_literals(self) -> None:
        left_text = """
            plugins { id 'java' }
            tasks.register('verifyPinned') {
                def inputPath = 'inputs/artifact.jar'
                def pattern = ~/[0-9a-f]{64}/
                def helper = '''print({"key": "value"})'''
                doLast { println inputPath }
            }
        """
        right_text = left_text.replace("inputPath", "artifactPath").replace("# marker", "")
        left = self.source(left_text, path="build.gradle", category="build_config", layer="scaffolding")
        right = self.source(right_text, addon="two", path="build.gradle", category="build_config", layer="scaffolding")
        commented = self.source(
            "// comment only\n" + left_text,
            addon="three",
            path="build.gradle",
            category="build_config",
            layer="scaffolding",
        )
        left_records = SCANNER.extract_gradle_records(left)
        right_records = SCANNER.extract_gradle_records(right)
        commented_records = SCANNER.extract_gradle_records(commented)
        left_task = next(record for record in left_records if record.kind == "gradle_task")
        right_task = next(record for record in right_records if record.kind == "gradle_task")
        commented_task = next(record for record in commented_records if record.kind == "gradle_task")
        self.assertEqual(left_task.exact_hash, commented_task.exact_hash)
        self.assertNotEqual(left_task.exact_hash, right_task.exact_hash)
        self.assertEqual(left_task.normalized_hash, right_task.normalized_hash)
        changed = self.source(
            left_text.replace("inputs/artifact.jar", "inputs/other.jar"),
            addon="four",
            path="build.gradle",
            category="build_config",
            layer="scaffolding",
        )
        changed_task = next(record for record in SCANNER.extract_gradle_records(changed) if record.kind == "gradle_task")
        self.assertNotEqual(left_task.normalized_hash, changed_task.normalized_hash)
        self.assertTrue({"gradle_block", "gradle_task", "gradle_closure"} <= {record.kind for record in left_records})
        self.assertGreaterEqual(left_task.end_line, left_task.start_line)

    def test_gradle_fails_closed_on_unbalanced_delimiter(self) -> None:
        source = self.source(
            "tasks.register('broken') { doLast { println 'x' }\n",
            path="build.gradle",
            category="build_config",
            layer="scaffolding",
        )
        with self.assertRaisesRegex(RuntimeError, r"Gradle parse failed closed: .*unmatched \{"):
            SCANNER.extract_gradle_records(source)

    def test_workflow_jobs_steps_and_bash_runs_preserve_external_values(self) -> None:
        workflow = """name: CI
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout
        uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # pinned
      - name: Verify
        shell: bash
        run: |
          verify() {
            curl --fail https://example.invalid/artifact
          }
          verify
"""
        source = self.source(workflow, path=".github/workflows/ci.yml", category="ci_config", layer="scaffolding")
        records = SCANNER.extract_workflow_records(source)
        self.assertEqual(1, sum(record.kind == "workflow_job" for record in records))
        self.assertEqual(2, sum(record.kind == "workflow_step" for record in records))
        self.assertEqual(1, sum(record.kind == "workflow_run" for record in records))
        self.assertEqual(1, sum(record.kind == "shell_function" for record in records))
        checkout = next(record for record in records if record.kind == "workflow_step" and record.name == "Checkout")
        job = next(record for record in records if record.kind == "workflow_job")
        commented = self.source(
            workflow.replace("# pinned", "# another comment"),
            addon="two",
            path=".github/workflows/ci.yml",
            category="ci_config",
            layer="scaffolding",
        )
        commented_records = SCANNER.extract_workflow_records(commented)
        self.assertEqual(checkout.exact_hash, next(record for record in commented_records if record.kind == "workflow_step" and record.name == "Checkout").exact_hash)
        changed_sha = self.source(
            workflow.replace("a" * 40, "b" * 40),
            addon="three",
            path=".github/workflows/ci.yml",
            category="ci_config",
            layer="scaffolding",
        )
        self.assertNotEqual(checkout.exact_hash, next(record for record in SCANNER.extract_workflow_records(changed_sha) if record.kind == "workflow_step" and record.name == "Checkout").exact_hash)
        changed_context = self.source(
            workflow.replace("branches: [main]", "branches: [release]").replace("contents: read", "contents: write"),
            addon="four",
            path=".github/workflows/ci.yml",
            category="ci_config",
            layer="scaffolding",
        )
        self.assertNotEqual(job.exact_hash, next(record for record in SCANNER.extract_workflow_records(changed_context) if record.kind == "workflow_job").exact_hash)

    def test_workflow_parser_rejects_duplicate_jobs_and_tab_indentation(self) -> None:
        duplicate = self.source(
            "jobs:\n  build:\n    runs-on: ubuntu\n  build:\n    runs-on: ubuntu\n",
            path=".github/workflows/ci.yml",
            category="ci_config",
            layer="scaffolding",
        )
        with self.assertRaisesRegex(RuntimeError, "duplicate job id"):
            SCANNER.extract_workflow_records(duplicate)
        tabbed = self.source(
            "jobs:\n\tbuild:\n    runs-on: ubuntu\n",
            path=".github/workflows/ci.yml",
            category="ci_config",
            layer="scaffolding",
        )
        with self.assertRaisesRegex(RuntimeError, "tab indentation"):
            SCANNER.extract_workflow_records(tabbed)

    def test_shell_functions_preserve_commands_literals_and_heredocs(self) -> None:
        script = """#!/usr/bin/env bash
verify() {
  curl --fail https://example.invalid/artifact
  sha256sum --check <<'SUMS'
aaaaaaaa  artifact.jar
SUMS
}
verify
"""
        source = self.source(script, path="tools/verify.sh", category="verification_tool", layer="scaffolding")
        record = SCANNER.extract_shell_records(source)[0]
        changed_body = self.source(
            script.replace("aaaaaaaa", "bbbbbbbb"),
            addon="two",
            path="tools/verify.sh",
            category="verification_tool",
            layer="scaffolding",
        )
        changed_flag = self.source(
            script.replace("--fail", "--silent"),
            addon="three",
            path="tools/verify.sh",
            category="verification_tool",
            layer="scaffolding",
        )
        self.assertNotEqual(record.exact_hash, SCANNER.extract_shell_records(changed_body)[0].exact_hash)
        self.assertNotEqual(record.exact_hash, SCANNER.extract_shell_records(changed_flag)[0].exact_hash)
        broken = self.source(
            "#!/usr/bin/env bash\nif true; then\n",
            path="tools/broken.sh",
            category="tooling",
            layer="scaffolding",
        )
        with self.assertRaisesRegex(RuntimeError, "Bash parse failed closed"):
            SCANNER.extract_shell_records(broken)

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
                tool.write_text(
                    "#!/usr/bin/env python3\ndef verify(value):\n    result = value.strip()\n    return 'same:' + result\n",
                    encoding="utf-8",
                )
                (repo / "build.gradle").write_text(
                    "plugins { id 'java' }\ntasks.register('verify') { doLast { println 'same' } }\n",
                    encoding="utf-8",
                )
                workflow = repo / ".github" / "workflows" / "ci.yml"
                workflow.parent.mkdir(parents=True)
                workflow.write_text(
                    "jobs:\n  build:\n    runs-on: ubuntu-24.04\n    steps:\n      - name: Verify\n        run: |\n          verify() {\n            echo same\n          }\n          verify\n",
                    encoding="utf-8",
                )
                shell = repo / "tools" / "verify.sh"
                shell.write_text("#!/usr/bin/env bash\nverify() { echo same; }\nverify\n", encoding="utf-8")
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
            self.assertTrue(first["structured_unit_clones"]["exact"])
            self.assertEqual(first["scope"]["structured_unit_inventory_sha256"], second["scope"]["structured_unit_inventory_sha256"])
            self.assertGreater(first["scope"]["structured_unit_count"], 0)
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
