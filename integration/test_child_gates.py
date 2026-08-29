#!/usr/bin/env python3
"""Focused unit/integration checks for the sequential child-gate runner."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("run_child_gates.py")
SPEC = importlib.util.spec_from_file_location("run_child_gates", MODULE_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - fixed repository layout
    raise RuntimeError("could not load integration/run_child_gates.py")
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


class Fixture:
    def __init__(
        self,
        root: Path,
        *,
        addon_count: int = 2,
        mutating_addon: str | None = None,
        artifact_required: bool = False,
        gradle_artifact_property: bool = False,
    ) -> None:
        self.root = root
        self.components: list[dict[str, object]] = []
        git(root, "init", "-q")
        (root / "addons").mkdir()
        bluemap = root / "bluemap"
        bluemap.mkdir()
        git(bluemap, "init", "-q")
        git(bluemap, "config", "user.name", "Child Gate Test")
        git(bluemap, "config", "user.email", "child-gate@example.invalid")
        (bluemap / "README.md").write_text("fixture BlueMap source\n", encoding="utf-8")
        api = bluemap / "api"
        api.mkdir()
        git(api, "init", "-q")
        git(api, "config", "user.name", "Child Gate Test")
        git(api, "config", "user.email", "child-gate@example.invalid")
        (api / "README.md").write_text("fixture BlueMap API\n", encoding="utf-8")
        git(api, "add", "README.md")
        git(api, "commit", "-qm", "fixture BlueMap API")
        api_commit = git(api, "rev-parse", "HEAD")
        git(bluemap, "update-index", "--add", "--cacheinfo", f"160000,{api_commit},api")
        git(bluemap, "add", "README.md")
        git(bluemap, "commit", "-qm", "fixture BlueMap")
        bluemap_commit = git(bluemap, "rev-parse", "HEAD")
        self.bluemap = bluemap
        self.bluemap_api = api
        self.bluemap_commit = bluemap_commit
        git(root, "update-index", "--add", "--cacheinfo", f"160000,{bluemap_commit},bluemap")
        for index in range(addon_count):
            identifier = f"addon-{index + 1}"
            repository = root / "addons" / identifier
            repository.mkdir()
            git(repository, "init", "-q")
            git(repository, "config", "user.name", "Child Gate Test")
            git(repository, "config", "user.email", "child-gate@example.invalid")
            artifact_declaration = (
                "def fixtureJar = providers.gradleProperty('fixtureJar')\n"
                if gradle_artifact_property
                else ""
            )
            (repository / "build.gradle").write_text(
                "plugins { id 'maven-publish' }\n"
                + artifact_declaration
                + "publishing { publications { addon(MavenPublication) { } } }\n",
                encoding="utf-8",
            )
            marker = repository / "marker.txt"
            marker.write_text("clean\n", encoding="utf-8")
            wrapper = repository / "gradlew"
            mutation = "printf 'changed\\n' >> marker.txt\n" if identifier == mutating_addon else ""
            wrapper.write_text(
                "#!/bin/sh\nset -eu\n"
                + mutation
                + "printf 'fake Gradle gate: %s\\n' \"$*\"\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            gallery = repository / "gallery"
            gallery.mkdir()
            if artifact_required:
                (gallery / "generate.py").write_text(
                    "#!/usr/bin/env python3\nimport argparse\n"
                    "p=argparse.ArgumentParser(); p.add_argument('--artifact-dir', required=True); "
                    "p.add_argument('--check', action='store_true'); p.parse_args()\n",
                    encoding="utf-8",
                )
                (gallery / "lint.py").write_text(
                    "#!/usr/bin/env python3\nimport argparse\n"
                    "p=argparse.ArgumentParser(); p.add_argument('--artifact-dir', required=True); p.parse_args()\n",
                    encoding="utf-8",
                )
            else:
                (gallery / "generate.py").write_text(
                    "#!/usr/bin/env python3\nimport sys\n"
                    "assert '--check' in sys.argv\nprint('generator check passed')\n",
                    encoding="utf-8",
                )
                (gallery / "lint.py").write_text(
                    "#!/usr/bin/env python3\nprint('gallery lint passed')\n", encoding="utf-8"
                )
            tests = gallery / "tests"
            tests.mkdir()
            (tests / "test_fixture.py").write_text(
                "#!/usr/bin/env python3\nprint('gallery test passed')\n", encoding="utf-8"
            )
            git(repository, "add", ".")
            git(repository, "commit", "-qm", "fixture")
            commit = git(repository, "rev-parse", "HEAD")
            git(root, "update-index", "--add", "--cacheinfo", f"160000,{commit},addons/{identifier}")
            self.components.append(
                {
                    "id": identifier,
                    "kind": "addon",
                    "submodule_path": f"addons/{identifier}",
                    "commit": commit,
                }
            )
        versions = root / "versions" / "fixture"
        versions.mkdir(parents=True)
        self.manifest_path = versions / "manifest.json"
        self.manifest_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "atmons": {"version": "fixture", "pack_commit": "f" * 40},
                    "release": {"addon_count": addon_count},
                    "components": [
                        *self.components,
                        {
                            "id": "bluemap",
                            "kind": "bluemap",
                            "submodule_path": "bluemap",
                            "commit": bluemap_commit,
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


class ChildGateRunnerTest(unittest.TestCase):
    def build_fixture_plan(self, fixture: Fixture):
        return RUNNER.build_plan(
            fixture.root,
            fixture.manifest_path,
            expected_addons=len(fixture.components),
            bluemap_source=fixture.root / "bluemap",
            gallery_artifact_dirs={},
            python_command=sys.executable,
            gradle_command="gradle",
        )

    def test_plan_is_sorted_and_discovers_only_safe_tracked_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary))
            untracked = fixture.root / "addons" / "addon-1" / "gallery" / "tests" / "test_untracked.py"
            untracked.write_text("raise RuntimeError('must never execute')\n", encoding="utf-8")
            component = RUNNER.Component(**{
                "identifier": fixture.components[0]["id"],
                "submodule_path": fixture.components[0]["submodule_path"],
                "commit": fixture.components[0]["commit"],
            })
            discovered = RUNNER.discover_commands(
                fixture.root,
                component,
                bluemap_source=fixture.root / "bluemap",
                gallery_artifact_dirs={},
                gradle_artifacts={},
                python_command=sys.executable,
                gradle_command="gradle",
            )
            identifiers = [command.identifier for command in discovered.commands]
            self.assertEqual(
                [
                    "gallery-generate-check",
                    "gallery-lint",
                    "gallery-test-01",
                    "gradle-clean-check-build",
                    "gradle-generate-pom",
                ],
                identifiers,
            )
            self.assertNotIn("test_untracked.py", " ".join(" ".join(command.argv) for command in discovered.commands))

    def test_clean_fixture_suite_passes_and_records_output_and_duration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), addon_count=1)
            plan_report, plans = self.build_fixture_plan(fixture)
            self.assertEqual("ready", plan_report["summary"]["status"])
            self.assertEqual(5, plan_report["summary"]["command_count"])
            report = RUNNER.execute_suite(
                fixture.root,
                plan_report,
                plans,
                bluemap_source=fixture.root / "bluemap",
                timeout_seconds=30,
                tail_lines=10,
                fail_fast=False,
            )
            self.assertEqual("passed", report["summary"]["status"])
            self.assertEqual(1, report["summary"]["passed_addons"])
            self.assertEqual(5, report["summary"]["passed_commands"])
            self.assertTrue(report["summary"]["final_integrity_ok"])
            self.assertTrue(report["summary"]["final_bluemap_source_integrity_ok"])
            gradle = report["addons"][0]["commands"][-2]
            self.assertEqual("passed", gradle["status"])
            self.assertGreaterEqual(gradle["duration_seconds"], 0)
            self.assertIn("fake Gradle gate", gradle["output_tail"])
            self.assertNotIn(str(fixture.root), gradle["output_tail"])

    def test_tracked_mutation_fails_immediately_and_leaves_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), addon_count=1, mutating_addon="addon-1")
            plan_report, plans = self.build_fixture_plan(fixture)
            report = RUNNER.execute_suite(
                fixture.root,
                plan_report,
                plans,
                bluemap_source=fixture.root / "bluemap",
                timeout_seconds=30,
                tail_lines=10,
                fail_fast=False,
            )
            self.assertEqual("failed", report["summary"]["status"])
            commands = report["addons"][0]["commands"]
            self.assertEqual("integrity_failed", commands[-2]["status"])
            self.assertEqual("not_run_after_failure", commands[-1]["status"])
            self.assertIn("marker.txt", commands[-2]["integrity_after"]["status_porcelain"])
            self.assertFalse(report["summary"]["final_integrity_ok"])

    def test_head_pin_drift_blocks_global_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), addon_count=1)
            repository = fixture.root / "addons" / "addon-1"
            (repository / "later.txt").write_text("later\n", encoding="utf-8")
            git(repository, "add", "later.txt")
            git(repository, "commit", "-qm", "later")
            plan_report, _plans = self.build_fixture_plan(fixture)
            self.assertEqual("blocked", plan_report["summary"]["status"])
            self.assertEqual(["addon-1"], plan_report["summary"]["preflight_failed_addons"])

    def test_ignored_source_input_blocks_preflight_but_bounded_build_outputs_do_not(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), addon_count=1)
            repository = fixture.root / "addons" / "addon-1"
            exclude = Path(git(repository, "rev-parse", "--absolute-git-dir")) / "info" / "exclude"
            exclude.write_text("/build/\n/.gradle/\n/hidden-source.jar\n", encoding="utf-8")
            (repository / "build").mkdir()
            (repository / "build" / "fixture.class").write_bytes(b"output")
            (repository / ".gradle").mkdir()
            (repository / ".gradle" / "cache.bin").write_bytes(b"cache")

            allowed, _plans = self.build_fixture_plan(fixture)
            self.assertEqual("ready", allowed["summary"]["status"])
            attestation = allowed["addons"][0]["preflight"]["source_input_attestation"]
            self.assertTrue(attestation["ok"])
            self.assertEqual([".gradle/", "build/"], attestation["allowed_ignored_output_entries"])

            (repository / "hidden-source.jar").write_bytes(b"injected")
            blocked, _plans = self.build_fixture_plan(fixture)
            self.assertEqual("blocked", blocked["summary"]["status"])
            attestation = blocked["addons"][0]["preflight"]["source_input_attestation"]
            self.assertFalse(attestation["ok"])
            self.assertEqual(["hidden-source.jar"], attestation["unexpected_ignored_entries"])

    def test_ignored_input_in_nested_bluemap_api_blocks_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), addon_count=1)
            exclude = (
                Path(git(fixture.bluemap_api, "rev-parse", "--absolute-git-dir"))
                / "info"
                / "exclude"
            )
            exclude.write_text("/injected.jar\n", encoding="utf-8")
            (fixture.bluemap_api / "injected.jar").write_bytes(b"injected")
            blocked, _plans = self.build_fixture_plan(fixture)
            self.assertEqual("blocked", blocked["summary"]["status"])
            api = blocked["target"]["active_bluemap_source"]["api"]
            self.assertFalse(api["ok"])
            self.assertEqual(
                ["injected.jar"],
                api["source_input_attestation"]["unexpected_ignored_entries"],
            )

    def test_explicit_bluemap_commit_allows_review_branch_to_differ_from_manifest_gitlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), addon_count=1)
            (fixture.bluemap / "branch.txt").write_text("integration branch\n", encoding="utf-8")
            git(fixture.bluemap, "add", "branch.txt")
            git(fixture.bluemap, "commit", "-qm", "integration branch")
            branch_commit = git(fixture.bluemap, "rev-parse", "HEAD")

            blocked, _plans = self.build_fixture_plan(fixture)
            self.assertEqual("blocked", blocked["summary"]["status"])
            overridden, _plans = RUNNER.build_plan(
                fixture.root,
                fixture.manifest_path,
                expected_addons=1,
                bluemap_source=fixture.bluemap,
                expected_bluemap_commit=branch_commit,
                gallery_artifact_dirs={},
                python_command=sys.executable,
                gradle_command="gradle",
            )
            source = overridden["target"]["active_bluemap_source"]
            self.assertEqual("ready", overridden["summary"]["status"])
            self.assertTrue(overridden["target"]["bluemap_integration_override"])
            self.assertEqual(branch_commit, source["head_commit"])
            self.assertEqual(fixture.bluemap_commit, source["gitlink_commit"])
            self.assertFalse(source["gitlink_matches_head"])
            self.assertTrue(source["ok"])

    def test_output_tail_is_bounded_and_path_sanitized(self) -> None:
        root = Path("/tmp/private-root")
        output = "first\n/tmp/private-root/addons/a\nthird\nfourth\n"
        self.assertEqual(
            "<repo>/addons/a\nthird\nfourth",
            RUNNER.sanitized_output(output, root, tail_lines=3),
        )

    def test_explicit_gradle_command_takes_precedence(self) -> None:
        self.assertEqual(
            "/opt/gradle/bin/gradle",
            RUNNER.resolve_gradle_command(Path("/missing"), "/opt/gradle/bin/gradle"),
        )

    def test_required_gallery_artifact_directory_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), addon_count=1, artifact_required=True)
            blocked, _plans = self.build_fixture_plan(fixture)
            self.assertEqual("blocked", blocked["summary"]["status"])
            self.assertIn("requires --artifact-dir", blocked["summary"]["discovery_errors"][0])
            artifacts = fixture.root / "exact-artifacts"
            artifacts.mkdir()
            (artifacts / "fixture.jar").write_bytes(b"gallery fixture artifact")
            ready, plans = RUNNER.build_plan(
                fixture.root,
                fixture.manifest_path,
                expected_addons=1,
                bluemap_source=fixture.bluemap,
                gallery_artifact_dirs={"addon-1": artifacts},
                python_command=sys.executable,
                gradle_command="gradle",
            )
            self.assertEqual("ready", ready["summary"]["status"])
            self.assertIn("--artifact-dir", plans[0].commands[0].argv)
            self.assertIn("<gallery-artifacts:addon-1>", plans[0].commands[0].display_argv)
            evidence = ready["settings"]["gallery_artifact_inputs"]
            self.assertEqual(1, evidence[0]["file_count"])
            self.assertNotIn(str(artifacts), json.dumps(ready))
            self.assertTrue(RUNNER.external_input_state(plans[0])["ok"])
            (artifacts / "fixture.jar").write_bytes(b"changed gallery input")
            self.assertFalse(RUNNER.external_input_state(plans[0])["ok"])

    def test_manifest_selection_requires_tracked_canonical_bytes_and_shared_validator(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(Path(temporary), addon_count=1)
            tools = fixture.root / "tools"
            tools.mkdir()
            validator = tools / "validate.py"
            validator.write_text(
                "import argparse\n"
                "p=argparse.ArgumentParser(); p.add_argument('--version', required=True); a=p.parse_args()\n"
                "print('validated', a.version)\n",
                encoding="utf-8",
            )
            git(
                fixture.root,
                "add",
                "tools/validate.py",
                "versions/fixture/manifest.json",
            )
            evidence = RUNNER.validate_manifest_selection(
                fixture.root,
                fixture.manifest_path,
                "fixture",
            )
            self.assertTrue(evidence["ok"])
            self.assertTrue(evidence["canonical_matches_tracked_index"])
            self.assertEqual("validated fixture", evidence["shared_validator"]["output_tail"])

            override = fixture.root / "versions" / "fixture" / "override.json"
            override.write_bytes(fixture.manifest_path.read_bytes() + b" \n")
            with self.assertRaisesRegex(RUNNER.GateError, "differs byte-for-byte"):
                RUNNER.validate_manifest_selection(fixture.root, override, "fixture")

    def test_gradle_artifacts_are_hashed_validated_and_path_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Fixture(
                Path(temporary),
                addon_count=1,
                gradle_artifact_property=True,
            )
            jar = fixture.root / "exact pack artifact.jar"
            payload = b"exact fixture jar bytes"
            jar.write_bytes(payload)
            parsed = RUNNER.parse_gradle_artifacts(
                fixture.root,
                [f"addon-1:fixtureJar={jar}"],
            )
            report, plans = RUNNER.build_plan(
                fixture.root,
                fixture.manifest_path,
                expected_addons=1,
                bluemap_source=fixture.bluemap,
                gallery_artifact_dirs={},
                gradle_artifacts=parsed,
                python_command=sys.executable,
                gradle_command="gradle",
            )
            self.assertEqual("ready", report["summary"]["status"])
            evidence = report["settings"]["gradle_artifact_inputs"]
            self.assertEqual(1, len(evidence))
            self.assertEqual(hashlib.sha256(payload).hexdigest(), evidence[0]["sha256"])
            self.assertEqual(len(payload), evidence[0]["size_bytes"])
            gradle = plans[0].commands[-2]
            self.assertIn(f"-PfixtureJar={jar}", gradle.argv)
            self.assertIn(
                "-PfixtureJar=<artifact:addon-1:fixtureJar>",
                gradle.display_argv,
            )
            self.assertNotIn(str(jar), json.dumps(report))
            self.assertTrue(RUNNER.external_input_state(plans[0])["ok"])

            mutating = RUNNER.CommandSpec(
                "mutate-external-input",
                "fixture command mutates an external input",
                (
                    sys.executable,
                    "-c",
                    f"from pathlib import Path; Path({str(jar)!r}).write_bytes(b'changed')",
                ),
                ("<python>", "<fixture-mutate-external-input>"),
            )
            result = RUNNER.execute_command(
                fixture.root,
                plans[0],
                mutating,
                bluemap_source=fixture.bluemap,
                expected_bluemap_commit=fixture.bluemap_commit,
                require_bluemap_gitlink_match=True,
                timeout_seconds=30,
                tail_lines=10,
            )
            self.assertTrue(result["external_input_integrity_before"]["ok"])
            self.assertFalse(result["external_input_integrity_after"]["ok"])
            self.assertEqual("integrity_failed", result["status"])

    def test_expected_rejection_accepts_only_the_pinned_compatibility_failure(self) -> None:
        manifest_commit = "1" * 40
        active_commit = "2" * 40
        report = {
            "mode": "run",
            "target": {
                "active_bluemap_expected_commit": active_commit,
                "manifest_bluemap_commit": manifest_commit,
                "bluemap_integration_override": True,
            },
            "addons": [
                {
                    "id": "addon-1",
                    "status": "failed",
                    "commands": [
                        {
                            "id": "gradle-clean-check-build",
                            "status": "failed",
                            "exit_code": 1,
                            "output_tail": (
                                f"Refusing BlueMap {active_commit}; expected {manifest_commit}"
                            ),
                        },
                        {"id": "gradle-generate-pom", "status": "not_run_after_failure"},
                    ],
                }
            ],
            "summary": {
                "status": "failed",
                "final_integrity_ok": True,
                "final_bluemap_source_integrity_ok": True,
                "duration_seconds": 1.25,
            },
        }
        evaluated = RUNNER.evaluate_expected_rejection(report)
        self.assertEqual("expected-rejection", evaluated["mode"])
        self.assertEqual("passed", evaluated["summary"]["status"])
        self.assertEqual(1, evaluated["summary"]["expected_rejection_addons"])
        self.assertEqual("expected_rejection", evaluated["addons"][0]["status"])

    def test_expected_rejection_rejects_unrelated_build_failure(self) -> None:
        manifest_commit = "1" * 40
        active_commit = "2" * 40
        report = {
            "mode": "run",
            "target": {
                "active_bluemap_expected_commit": active_commit,
                "manifest_bluemap_commit": manifest_commit,
                "bluemap_integration_override": True,
            },
            "addons": [
                {
                    "id": "addon-1",
                    "status": "failed",
                    "commands": [
                        {
                            "id": "gradle-clean-check-build",
                            "status": "failed",
                            "exit_code": 1,
                            "output_tail": "missing exact mod artifact",
                        }
                    ],
                }
            ],
            "summary": {
                "status": "failed",
                "final_integrity_ok": True,
                "final_bluemap_source_integrity_ok": True,
                "duration_seconds": 0.5,
            },
        }
        evaluated = RUNNER.evaluate_expected_rejection(report)
        self.assertEqual("failed", evaluated["summary"]["status"])
        self.assertEqual(1, evaluated["summary"]["unexpected_addons"])

    def test_expected_rejection_allows_only_explicit_reviewed_passes(self) -> None:
        manifest_commit = "1" * 40
        active_commit = "2" * 40
        report = {
            "mode": "run",
            "runner": {},
            "target": {
                "active_bluemap_expected_commit": active_commit,
                "manifest_bluemap_commit": manifest_commit,
                "bluemap_integration_override": True,
            },
            "addons": [
                {
                    "id": "source-compatible",
                    "status": "passed",
                    "commands": [{"id": "gradle-clean-check-build", "status": "passed"}],
                }
            ],
            "summary": {
                "status": "passed",
                "final_integrity_ok": True,
                "final_bluemap_source_integrity_ok": True,
                "duration_seconds": 0.1,
            },
        }
        evaluated = RUNNER.evaluate_expected_rejection(
            report,
            expected_pass_addons={"source-compatible"},
        )
        self.assertEqual("passed", evaluated["summary"]["status"])
        self.assertEqual(1, evaluated["summary"]["expected_pass_addons"])
        self.assertEqual("expected_pass", evaluated["addons"][0]["status"])
        self.assertIn("expected_rejection_evaluator", evaluated["runner"])


if __name__ == "__main__":
    unittest.main()
