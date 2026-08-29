#!/usr/bin/env python3
"""Deterministic cross-add-on duplication audit for BlueMap ATMons.

The scanner reads the exact commits recorded by a version manifest and first
requires every ``addons/*`` index gitlink to match it. It deliberately does not
inspect mutable submodule working trees. Output is content-addressed and has no
wall-clock timestamp, so the same manifest and gitlinks produce byte-identical
reports.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Iterable, Sequence


SCHEMA_VERSION = 1
SCANNER_VERSION = "1.1.0"
DEFAULT_MIN_METHOD_TOKENS = 36
DEFAULT_MIN_FILE_TOKENS = 80

JAVA_KEYWORDS = frozenset(
    {
        "abstract",
        "assert",
        "boolean",
        "break",
        "byte",
        "case",
        "catch",
        "char",
        "class",
        "const",
        "continue",
        "default",
        "do",
        "double",
        "else",
        "enum",
        "exports",
        "extends",
        "false",
        "final",
        "finally",
        "float",
        "for",
        "goto",
        "if",
        "implements",
        "import",
        "instanceof",
        "int",
        "interface",
        "long",
        "module",
        "native",
        "new",
        "non-sealed",
        "null",
        "open",
        "opens",
        "package",
        "permits",
        "private",
        "protected",
        "provides",
        "public",
        "record",
        "requires",
        "return",
        "sealed",
        "short",
        "static",
        "strictfp",
        "super",
        "switch",
        "synchronized",
        "this",
        "throw",
        "throws",
        "to",
        "transient",
        "transitive",
        "true",
        "try",
        "uses",
        "var",
        "void",
        "volatile",
        "when",
        "while",
        "with",
        "yield",
    }
)

CONTROL_NAMES = frozenset(
    {"catch", "do", "else", "for", "if", "new", "return", "switch", "synchronized", "throw", "try", "while"}
)

TOKEN_RE = re.compile(
    r'''
    (?P<space>\s+)
  | (?P<line_comment>//[^\r\n]*)
  | (?P<block_comment>/\*.*?\*/)
  | (?P<text_block>\"\"\"(?:\\.|(?!\"\"\").)*\"\"\")
  | (?P<string>"(?:\\.|[^"\\])*")
  | (?P<char>'(?:\\.|[^'\\])*')
  | (?P<number>
        (?:0[xX][0-9a-fA-F](?:_?[0-9a-fA-F])*(?:\.[0-9a-fA-F](?:_?[0-9a-fA-F])*)?[pP][+-]?[0-9](?:_?[0-9])*[fFdD]?)
      | (?:0[bB][01](?:_?[01])*[lL]?)
      | (?:\d(?:_?\d)*(?:\.\d(?:_?\d)*)?(?:[eE][+-]?\d(?:_?\d)*)?[fFdDlL]?)
    )
  | (?P<identifier>[A-Za-z_$][A-Za-z0-9_$]*)
  | (?P<operator>>>>=|>>>=|<<=|>>=|->|::|\.\.\.|==|!=|<=|>=|&&|\|\||\+\+|--|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>>|>>|[{}()\[\];,.?:@~+\-*/%&|^!<>=])
  | (?P<other>.)
    ''',
    re.DOTALL | re.VERBOSE,
)

SCAFFOLD_BASENAME_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^AddonRuntime(?:Test)?\.java$",
        r"^AdapterCompatibility(?:Test)?\.java$",
        r"^ArtifactPin\.java$",
        r"^BlueMap.*Addon(?:Test)?\.java$",
        r"^BlueMap\d+Adapter(?:Test)?\.java$",
        r"^BoundedDiagnostics\.java$",
        r"^Exact.*ArtifactDetector(?:Test)?\.java$",
        r"^ProfileDisablement(?:Test)?\.java$",
        r"^.*Profile\.java$",
        r"^.*ResourceExtension(?:Type|Test)?\.java$",
        r"^.*Runtime(?:Test)?\.java$",
        r"^RegistryGuard\.java$",
        r"^RouteActivation(?:Test)?\.java$",
        r"^ActiveResource(?:Loader|SchemaValidator)(?:Test)?\.java$",
    )
)

EXCLUDED_PARTS = frozenset(
    {
        ".gradle",
        "build",
        "generated",
        "node_modules",
        "out",
        "third-party",
        "third_party",
        "vendor",
        "vendored",
    }
)


@dataclasses.dataclass(frozen=True)
class JavaToken:
    text: str
    kind: str
    line: int


@dataclasses.dataclass(frozen=True)
class SourceFile:
    addon: str
    commit: str
    path: str
    category: str
    layer: str
    data: bytes

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.data).hexdigest()

    @property
    def line_count(self) -> int:
        if not self.data:
            return 0
        return self.data.count(b"\n") + (0 if self.data.endswith(b"\n") else 1)

    @property
    def evidence_path(self) -> str:
        return f"addons/{self.addon}/{self.path}"


@dataclasses.dataclass(frozen=True)
class MethodRecord:
    addon: str
    path: str
    commit: str
    name: str
    start_line: int
    end_line: int
    token_count: int
    layer: str
    exact_hash: str
    renamed_hash: str


@dataclasses.dataclass(frozen=True)
class FamilyRule:
    identifier: str
    title: str
    description: str
    basenames: tuple[str, ...] = ()
    basename_regexes: tuple[str, ...] = ()
    categories: tuple[str, ...] = ()
    path_regexes: tuple[str, ...] = ()

    def matches(self, source: SourceFile) -> bool:
        basename = PurePosixPath(source.path).name
        if basename in self.basenames:
            return True
        if source.category in self.categories:
            return True
        return any(re.search(pattern, basename) for pattern in self.basename_regexes) or any(
            re.search(pattern, source.path) for pattern in self.path_regexes
        )


FAMILY_RULES = (
    FamilyRule(
        "runtime-activation",
        "Runtime activation and diagnostics",
        "Pack activation, registry guards, route disablement, and bounded diagnostics.",
        basenames=(
            "AddonRuntime.java",
            "BoundedDiagnostics.java",
            "ProfileDisablement.java",
            "RegistryGuard.java",
            "RouteActivation.java",
        ),
        basename_regexes=(r"^BlueMap.*Addon\.java$", r"^.*Runtime\.java$"),
    ),
    FamilyRule(
        "artifact-identity",
        "Artifact identity and profiles",
        "Exact mod-JAR identity, version pins, and selected compatibility profiles.",
        basenames=("ArtifactPin.java", "ExactArtifactDetector.java", "ExactModArtifactDetector.java"),
        basename_regexes=(r"^Exact.*ArtifactDetector(?:Test)?\.java$", r"Profile\.java$"),
    ),
    FamilyRule(
        "adapter-bootstrap",
        "BlueMap adapter bootstrap",
        "BlueMap compatibility checks, adapter entry points, and resource-extension registration.",
        basenames=("AdapterCompatibility.java", "ActiveResourceLoader.java", "ActiveResourceSchemaValidator.java"),
        basename_regexes=(r"^BlueMap\d+Adapter\.java$", r"ResourceExtension(?:Type)?\.java$"),
    ),
    FamilyRule(
        "build-release-quality",
        "Build, release, and quality configuration",
        "Gradle, CI/release workflows, and static-analysis configuration.",
        categories=("build_config", "ci_config", "quality_config"),
    ),
    FamilyRule(
        "artifact-verification-tools",
        "Artifact verification tooling",
        "Pinned-artifact, staged-equivalence, and generated-profile verification scripts.",
        categories=("verification_tool",),
    ),
    FamilyRule(
        "gallery-toolchain",
        "Gallery generation and lifecycle harness",
        "Gallery generators, packagers, linters, and the standard build/clear/verify lifecycle.",
        categories=("gallery_tool",),
        path_regexes=(r"^gallery/datapack/.*/function/(?:build|clear|load|release|verify[^/]*)\.mcfunction$",),
    ),
    FamilyRule(
        "render-primitives",
        "Rendering and geometry primitives",
        "Repeated face-lighting, primitive-emission, direction, and geometry helpers.",
        basenames=(
            "AffineTransform.java",
            "AxisVector.java",
            "CubeFace.java",
            "FaceLighting.java",
            "JsonModelEmitter.java",
            "PrimitiveEmitter.java",
            "TextureOrientation.java",
        ),
    ),
    FamilyRule(
        "installed-model-compilers",
        "Installed model compilers",
        "Wavefront/installed-model readers, manifests, mesh compilation, and emission.",
        basename_regexes=(r"^(?:Exact)?ResourceManifest\.java$", r"^InstalledGeo.*\.java$", r"^Wavefront.*\.java$"),
    ),
    FamilyRule(
        "connected-texture-engine",
        "Connected-texture engine",
        "CTM/fusion selectors, predicates, texture programs, and Athena-style quad emission.",
        basename_regexes=(
            r"^(?:Athena|Ctm|Fusion|GiantTexture).+\.java$",
            r"^(?:ShapeFamily|TextureLayout)\.java$",
        ),
    ),
)


CANDIDATE_SPECS = (
    {
        "order": 1,
        "id": "bluemap-addon-dev-toolkit",
        "title": "Development and release toolkit",
        "families": ("build-release-quality", "artifact-verification-tools", "gallery-toolchain"),
        "benefits": (
            "Removes the largest byte-identical script/config copies without adding a server runtime dependency.",
            "Makes gallery and release-policy fixes land once and gives all repositories the same deterministic checks.",
        ),
        "risks": (
            "A shared tool version must remain pinned so an old add-on can still reproduce its release.",
            "Gallery generators have legitimate schema variants; keep extension hooks instead of forcing one data model.",
        ),
        "recommendation": "Extract first as versioned CLI/Gradle conventions. Keep generated gallery data in each add-on.",
    },
    {
        "order": 2,
        "id": "bluemap-addon-runtime",
        "title": "Activation, artifact identity, and diagnostics runtime",
        "families": ("runtime-activation", "artifact-identity"),
        "benefits": (
            "Centralizes exact-artifact gating, bounded diagnostics, and fail-closed activation behavior.",
            "Reduces the chance that one add-on drifts from the portfolio's compatibility policy.",
        ),
        "risks": (
            "A shared runtime JAR creates ABI/version-skew and class-loader questions across independently released packs.",
            "Artifact profiles contain add-on-specific pins and must remain declarative inputs, not shared mutable state.",
        ),
        "recommendation": "Extract pure contracts and utilities after combined tests; retain each add-on's profile data locally.",
    },
    {
        "order": 3,
        "id": "bluemap-addon-adapter-api",
        "title": "BlueMap adapter bootstrap API",
        "families": ("adapter-bootstrap",),
        "benefits": (
            "Consolidates adapter compatibility probes and resource-extension registration used throughout the portfolio.",
            "Provides one migration seam for later BlueMap internal API changes.",
        ),
        "risks": (
            "The code is coupled to BlueMap internals and currently names the 5.22 adapter generation.",
            "Extracting while the 5.23 backport is under integration could freeze the wrong ABI.",
        ),
        "recommendation": "Design now, but publish only after the 5.23 integration branch has a stable combined runtime gate.",
    },
    {
        "order": 4,
        "id": "bluemap-addon-render-core",
        "title": "Pure rendering and installed-model core",
        "families": ("render-primitives", "installed-model-compilers"),
        "benefits": (
            "Shares tested geometry, face-lighting, model parsing, and mesh-emission primitives.",
            "Lets behavior-heavy add-ons focus on block-state and block-entity interpretation.",
        ),
        "risks": (
            "Similar class names do not prove identical UV, lighting, coordinate, or material semantics.",
            "Changes in a common renderer have a much larger visual regression radius.",
        ),
        "recommendation": "Extract only clone groups proven pure by fixture tests; preserve add-on-specific emitters.",
    },
    {
        "order": 5,
        "id": "bluemap-addon-connected-textures",
        "title": "Connected-texture/fusion module",
        "families": ("connected-texture-engine",),
        "benefits": (
            "Unifies the repeated CTM/fusion topology and texture-selection implementations.",
            "Creates one place for connected-face correctness and adjacency regression fixtures.",
        ),
        "risks": (
            "Mods use different CTM dialects, edge rules, fallback textures, and resource schemas.",
            "A false abstraction can silently make visually distinct blocks look uniformly wrong.",
        ),
        "recommendation": "Extract last, as a strategy-based module with per-mod conformance fixtures and visual gates.",
    },
)


def run_git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: {detail}")
    return result.stdout


def discover_addon_gitlinks(root: Path) -> list[tuple[str, str]]:
    raw = run_git(root, "ls-files", "--stage", "-z", "addons")
    gitlinks: list[tuple[str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_id, stage = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8")
        if mode != "160000" or stage != "0" or not re.fullmatch(r"addons/[^/]+", path):
            continue
        gitlinks.append((path.removeprefix("addons/"), object_id))
    return sorted(gitlinks)


def load_version_manifest(
    root: Path,
    pack_version: str,
    *,
    expected_addons: int,
) -> tuple[dict[str, object], list[tuple[str, str]]]:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", pack_version) or ".." in pack_version:
        raise RuntimeError(f"unsafe All the Mons version label: {pack_version!r}")
    relative_path = PurePosixPath("versions") / pack_version / "manifest.json"
    path = root / Path(relative_path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"cannot read version manifest {relative_path}: {exc}") from exc
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"version manifest is not valid UTF-8 JSON: {relative_path}: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise RuntimeError(f"version manifest must be a schema-1 object: {relative_path}")

    atmons = manifest.get("atmons")
    if not isinstance(atmons, dict) or atmons.get("version") != pack_version:
        actual = atmons.get("version") if isinstance(atmons, dict) else None
        raise RuntimeError(
            f"version manifest identity mismatch: requested {pack_version!r}, manifest records {actual!r}"
        )
    tag = atmons.get("tag")
    pack_commit = atmons.get("pack_commit")
    if not isinstance(tag, str) or not tag:
        raise RuntimeError(f"version manifest has no atmons.tag: {relative_path}")
    if not isinstance(pack_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", pack_commit):
        raise RuntimeError(f"version manifest has no full lowercase atmons.pack_commit: {relative_path}")

    release = manifest.get("release")
    declared_addons = release.get("addon_count") if isinstance(release, dict) else None
    if declared_addons != expected_addons:
        raise RuntimeError(
            f"version manifest declares {declared_addons!r} add-ons, expected {expected_addons}: {relative_path}"
        )
    components = manifest.get("components")
    if not isinstance(components, list):
        raise RuntimeError(f"version manifest components must be an array: {relative_path}")

    manifest_gitlinks: list[tuple[str, str]] = []
    for component in components:
        if not isinstance(component, dict) or component.get("kind") != "addon":
            continue
        identifier = component.get("id")
        submodule_path = component.get("submodule_path")
        commit = component.get("commit")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", identifier):
            raise RuntimeError(f"version manifest contains an invalid add-on id: {identifier!r}")
        expected_path = f"addons/{identifier}"
        if submodule_path != expected_path:
            raise RuntimeError(
                f"version manifest add-on {identifier!r} uses {submodule_path!r}, expected {expected_path!r}"
            )
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise RuntimeError(f"version manifest add-on {identifier!r} has no full lowercase commit")
        manifest_gitlinks.append((identifier, commit))
    manifest_gitlinks.sort()
    identifiers = [identifier for identifier, _commit in manifest_gitlinks]
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError(f"version manifest contains duplicate add-on ids: {relative_path}")
    if len(manifest_gitlinks) != expected_addons:
        raise RuntimeError(
            f"version manifest contains {len(manifest_gitlinks)} add-on components, expected {expected_addons}: {relative_path}"
        )

    identity: dict[str, object] = {
        "path": relative_path.as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "schema_version": 1,
        "atmons_version": pack_version,
        "tag": tag,
        "pack_commit": pack_commit,
        "addon_count": len(manifest_gitlinks),
    }
    return identity, manifest_gitlinks


def require_exact_manifest_gitlinks(
    manifest_identity: dict[str, object],
    manifest_gitlinks: Sequence[tuple[str, str]],
    index_gitlinks: Sequence[tuple[str, str]],
) -> None:
    manifest_by_id = dict(manifest_gitlinks)
    index_by_id = dict(index_gitlinks)
    missing = sorted(manifest_by_id.keys() - index_by_id.keys())
    unexpected = sorted(index_by_id.keys() - manifest_by_id.keys())
    changed = sorted(
        identifier
        for identifier in manifest_by_id.keys() & index_by_id.keys()
        if manifest_by_id[identifier] != index_by_id[identifier]
    )
    if not (missing or unexpected or changed):
        return
    details: list[str] = []
    if missing:
        details.append(f"missing index gitlinks: {', '.join(missing)}")
    if unexpected:
        details.append(f"unexpected index gitlinks: {', '.join(unexpected)}")
    if changed:
        details.append(
            "commit mismatches: "
            + ", ".join(
                f"{identifier} manifest={manifest_by_id[identifier]} index={index_by_id[identifier]}"
                for identifier in changed
            )
        )
    raise RuntimeError(
        f"add-on gitlinks do not exactly match {manifest_identity['path']} "
        f"({manifest_identity['sha256']}): {'; '.join(details)}"
    )


def classify_path(path: str) -> tuple[str, str] | None:
    posix = PurePosixPath(path)
    lowered_parts = {part.lower() for part in posix.parts}
    if lowered_parts & EXCLUDED_PARTS:
        return None
    suffix = posix.suffix.lower()
    basename = posix.name

    if path.startswith("src/main/java/") and suffix == ".java":
        return "java_main", classify_java_layer(path, is_test=False)
    if path.startswith("src/test/java/") and suffix == ".java":
        return "java_test", classify_java_layer(path, is_test=True)
    if path in {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradle.properties"}:
        return "build_config", "scaffolding"
    if path == "gradle/libs.versions.toml" or path == "gradle/wrapper/gradle-wrapper.properties":
        return "build_config", "scaffolding"
    if path.startswith(".github/workflows/") and suffix in {".yml", ".yaml"}:
        return "ci_config", "scaffolding"
    if path.startswith("config/") and suffix in {".json", ".properties", ".toml", ".xml", ".yaml", ".yml"}:
        return "quality_config", "scaffolding"
    if path.startswith("tools/") and suffix in {".json", ".py", ".sh", ".toml", ".yaml", ".yml"}:
        category = "verification_tool" if re.search(r"(?:verify|profile|release|audit|check)", basename, re.IGNORECASE) else "tooling"
        return category, "scaffolding"
    if path.startswith("gallery/"):
        if suffix in {".py", ".sh"}:
            return "gallery_tool", "scaffolding"
        if suffix in {".json", ".mcfunction", ".mcmeta", ".properties", ".toml", ".tsv", ".yaml", ".yml"}:
            return "gallery_data", "test_support"
    if path in {"src/main/resources/bluemap.addon.json", "src/main/resources/META-INF/neoforge.mods.toml"}:
        return "addon_metadata", "scaffolding"
    return None


def classify_java_layer(path: str, *, is_test: bool) -> str:
    basename = PurePosixPath(path).name
    infrastructure_directory = any(segment in {"activation", "diagnostics", "profile"} for segment in PurePosixPath(path).parts)
    is_scaffold = infrastructure_directory or any(pattern.search(basename) for pattern in SCAFFOLD_BASENAME_PATTERNS)
    if is_test:
        return "test_scaffolding" if is_scaffold else "test_support"
    return "scaffolding" if is_scaffold else "behavioral"


def list_tree_paths(repo: Path, commit: str) -> list[str]:
    raw = run_git(repo, "ls-tree", "-r", "--name-only", "-z", commit)
    return sorted(item.decode("utf-8") for item in raw.split(b"\0") if item)


def read_commit_files(repo: Path, commit: str, paths: Sequence[str]) -> dict[str, bytes]:
    if not paths:
        return {}
    archive = run_git(repo, "archive", "--format=tar", commit, "--", *paths)
    result: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"could not read archived member {member.name} from {repo}@{commit}")
            result[member.name] = extracted.read()
    missing = sorted(set(paths) - result.keys())
    if missing:
        raise RuntimeError(f"git archive omitted {len(missing)} selected files from {repo}@{commit}: {missing[:3]}")
    return result


def load_sources(root: Path, gitlinks: Sequence[tuple[str, str]]) -> list[SourceFile]:
    sources: list[SourceFile] = []
    for addon, commit in gitlinks:
        repo = root / "addons" / addon
        if not (repo / ".git").exists() and not (repo / ".git").is_file():
            raise RuntimeError(f"submodule worktree is not initialized: {repo}")
        selected: list[tuple[str, str, str]] = []
        for path in list_tree_paths(repo, commit):
            classification = classify_path(path)
            if classification is not None:
                selected.append((path, *classification))
        archived = read_commit_files(repo, commit, [item[0] for item in selected])
        for path, category, layer in selected:
            data = archived[path]
            try:
                data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise RuntimeError(f"selected first-party text file is not UTF-8: addons/{addon}/{path}") from exc
            sources.append(SourceFile(addon, commit, path, category, layer, data))
    return sorted(sources, key=lambda source: (source.addon, source.path))


def lex_java(text: str) -> list[JavaToken]:
    tokens: list[JavaToken] = []
    line = 1
    position = 0
    while position < len(text):
        match = TOKEN_RE.match(text, position)
        if match is None:  # pragma: no cover - TOKEN_RE has an all-character fallback
            raise ValueError(f"Java lexer stalled at character {position}")
        kind = match.lastgroup or "other"
        value = match.group(0)
        if kind not in {"space", "line_comment", "block_comment"}:
            tokens.append(JavaToken(value, kind, line))
        line += value.count("\n")
        position = match.end()
    return tokens


def strip_package_and_imports(tokens: Sequence[JavaToken]) -> list[JavaToken]:
    result: list[JavaToken] = []
    index = 0
    while index < len(tokens):
        if tokens[index].text in {"package", "import"}:
            index += 1
            while index < len(tokens) and tokens[index].text != ";":
                index += 1
            if index < len(tokens):
                index += 1
            continue
        result.extend(tokens[index:])
        break
    return result


def exact_token_stream(tokens: Sequence[JavaToken]) -> str:
    return "\x1f".join(token.text for token in tokens)


def renamed_token_stream(tokens: Sequence[JavaToken]) -> str:
    identifiers: dict[str, str] = {}
    result: list[str] = []
    for token in tokens:
        if token.kind == "identifier" and token.text not in JAVA_KEYWORDS:
            replacement = identifiers.setdefault(token.text, f"ID{len(identifiers)}")
            result.append(replacement)
        elif token.kind in {"string", "text_block"}:
            result.append("STRING_LITERAL")
        elif token.kind == "char":
            result.append("CHAR_LITERAL")
        elif token.kind == "number":
            result.append("NUMBER_LITERAL")
        else:
            result.append(token.text)
    return "\x1f".join(result)


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def matching_pairs(tokens: Sequence[JavaToken], opening: str, closing: str) -> dict[int, int]:
    stack: list[int] = []
    pairs: dict[int, int] = {}
    for index, token in enumerate(tokens):
        if token.text == opening:
            stack.append(index)
        elif token.text == closing and stack:
            start = stack.pop()
            pairs[start] = index
            pairs[index] = start
    return pairs


def extract_methods(source: SourceFile, minimum_tokens: int) -> list[MethodRecord]:
    text = source.data.decode("utf-8")
    tokens = lex_java(text)
    parens = matching_pairs(tokens, "(", ")")
    braces = matching_pairs(tokens, "{", "}")
    methods: list[MethodRecord] = []

    for body_start, body_end in sorted((left, right) for left, right in braces.items() if left < right):
        cursor = body_start - 1
        while cursor >= 0 and tokens[cursor].text not in {"}", "{", ";"}:
            if tokens[cursor].text == ")":
                break
            cursor -= 1
        if cursor < 0 or tokens[cursor].text != ")" or cursor not in parens:
            continue
        params_start = parens[cursor]
        name_index = params_start - 1
        if name_index < 0 or tokens[name_index].kind != "identifier":
            continue
        name = tokens[name_index].text
        if name in CONTROL_NAMES:
            continue
        between = {token.text for token in tokens[cursor + 1 : body_start]}
        if between & {"->", "=", ";"}:
            continue
        if name_index > 0 and tokens[name_index - 1].text in {".", "::", "new"}:
            continue

        delimiter = name_index - 1
        while delimiter >= 0 and tokens[delimiter].text not in {";", "{", "}"}:
            delimiter -= 1
        prefix = {token.text for token in tokens[delimiter + 1 : name_index]}
        if prefix & {"=", "new", "return", "throw", "->"}:
            continue

        method_tokens = tokens[name_index : body_end + 1]
        if len(method_tokens) < minimum_tokens:
            continue
        exact_stream = exact_token_stream(method_tokens)
        renamed_stream = renamed_token_stream(method_tokens)
        methods.append(
            MethodRecord(
                addon=source.addon,
                path=source.path,
                commit=source.commit,
                name=name,
                start_line=tokens[name_index].line,
                end_line=tokens[body_end].line,
                token_count=len(method_tokens),
                layer=source.layer,
                exact_hash=digest_text(exact_stream),
                renamed_hash=digest_text(renamed_stream),
            )
        )
    return methods


def group_layer(layers: Iterable[str]) -> str:
    values = set(layers)
    production = values & {"behavioral", "scaffolding"}
    if len(production) > 1:
        return "mixed"
    if production:
        return next(iter(production))
    if values == {"test_scaffolding"}:
        return "test_scaffolding"
    if values <= {"test_scaffolding", "test_support"}:
        return "test_support" if "test_support" in values else "test_scaffolding"
    return "mixed"


def cross_addon_groups(items: Iterable[object], fingerprint_getter) -> list[list[object]]:
    grouped: dict[str, list[object]] = collections.defaultdict(list)
    for item in items:
        grouped[fingerprint_getter(item)].append(item)
    result = [group for group in grouped.values() if len({getattr(item, "addon") for item in group}) >= 2]
    return sorted(
        result,
        key=lambda group: (
            -len({getattr(item, "addon") for item in group}),
            -len(group),
            fingerprint_getter(group[0]),
        ),
    )


def source_occurrence(source: SourceFile) -> dict[str, object]:
    return {
        "addon": source.addon,
        "path": source.evidence_path,
        "commit": source.commit,
        "category": source.category,
        "layer": source.layer,
    }


def method_occurrence(method: MethodRecord) -> dict[str, object]:
    return {
        "addon": method.addon,
        "path": f"addons/{method.addon}/{method.path}",
        "commit": method.commit,
        "method": method.name,
        "start_line": method.start_line,
        "end_line": method.end_line,
        "token_count": method.token_count,
        "layer": method.layer,
        "exact_token_sha256": method.exact_hash,
    }


def exact_file_groups(sources: Sequence[SourceFile]) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    for group in cross_addon_groups(sources, lambda source: source.sha256):
        ordered = sorted(group, key=lambda source: (source.addon, source.path))
        fingerprint = ordered[0].sha256
        groups.append(
            {
                "id": f"file-{fingerprint[:16]}",
                "sha256": fingerprint,
                "byte_size": len(ordered[0].data),
                "line_count": ordered[0].line_count,
                "addon_count": len({source.addon for source in ordered}),
                "occurrence_count": len(ordered),
                "layer": group_layer(source.layer for source in ordered),
                "categories": sorted({source.category for source in ordered}),
                "occurrences": [source_occurrence(source) for source in ordered],
            }
        )
    return groups


def method_clone_groups(methods: Sequence[MethodRecord]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    exact_groups: list[dict[str, object]] = []
    for group in cross_addon_groups(methods, lambda method: method.exact_hash):
        ordered = sorted(group, key=lambda method: (method.addon, method.path, method.start_line, method.name))
        fingerprint = ordered[0].exact_hash
        exact_groups.append(
            {
                "id": f"method-exact-{fingerprint[:16]}",
                "token_sha256": fingerprint,
                "addon_count": len({method.addon for method in ordered}),
                "occurrence_count": len(ordered),
                "minimum_token_count": min(method.token_count for method in ordered),
                "layer": group_layer(method.layer for method in ordered),
                "occurrences": [method_occurrence(method) for method in ordered],
            }
        )

    renamed_groups: list[dict[str, object]] = []
    for group in cross_addon_groups(methods, lambda method: method.renamed_hash):
        if len({method.exact_hash for method in group}) < 2:
            continue
        ordered = sorted(group, key=lambda method: (method.addon, method.path, method.start_line, method.name))
        fingerprint = ordered[0].renamed_hash
        renamed_groups.append(
            {
                "id": f"method-renamed-{fingerprint[:16]}",
                "renamed_token_sha256": fingerprint,
                "distinct_exact_token_fingerprints": len({method.exact_hash for method in ordered}),
                "addon_count": len({method.addon for method in ordered}),
                "occurrence_count": len(ordered),
                "minimum_token_count": min(method.token_count for method in ordered),
                "layer": group_layer(method.layer for method in ordered),
                "occurrences": [method_occurrence(method) for method in ordered],
            }
        )
    return exact_groups, renamed_groups


def java_file_clone_groups(
    java_sources: Sequence[SourceFile], minimum_tokens: int
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[tuple[str, str], tuple[str, str, int]]]:
    fingerprints: dict[tuple[str, str], tuple[str, str, int]] = {}
    for source in java_sources:
        tokens = strip_package_and_imports(lex_java(source.data.decode("utf-8")))
        if len(tokens) < minimum_tokens:
            continue
        fingerprints[(source.addon, source.path)] = (
            digest_text(exact_token_stream(tokens)),
            digest_text(renamed_token_stream(tokens)),
            len(tokens),
        )

    selected = [source for source in java_sources if (source.addon, source.path) in fingerprints]
    exact: list[dict[str, object]] = []
    for group in cross_addon_groups(selected, lambda source: fingerprints[(source.addon, source.path)][0]):
        ordered = sorted(group, key=lambda source: (source.addon, source.path))
        fingerprint = fingerprints[(ordered[0].addon, ordered[0].path)][0]
        exact.append(
            {
                "id": f"java-file-exact-{fingerprint[:16]}",
                "token_sha256": fingerprint,
                "addon_count": len({source.addon for source in ordered}),
                "occurrence_count": len(ordered),
                "minimum_token_count": min(fingerprints[(source.addon, source.path)][2] for source in ordered),
                "layer": group_layer(source.layer for source in ordered),
                "occurrences": [source_occurrence(source) for source in ordered],
            }
        )

    renamed: list[dict[str, object]] = []
    for group in cross_addon_groups(selected, lambda source: fingerprints[(source.addon, source.path)][1]):
        exact_fingerprints = {fingerprints[(source.addon, source.path)][0] for source in group}
        if len(exact_fingerprints) < 2:
            continue
        ordered = sorted(group, key=lambda source: (source.addon, source.path))
        fingerprint = fingerprints[(ordered[0].addon, ordered[0].path)][1]
        renamed.append(
            {
                "id": f"java-file-renamed-{fingerprint[:16]}",
                "renamed_token_sha256": fingerprint,
                "distinct_exact_token_fingerprints": len(exact_fingerprints),
                "addon_count": len({source.addon for source in ordered}),
                "occurrence_count": len(ordered),
                "minimum_token_count": min(fingerprints[(source.addon, source.path)][2] for source in ordered),
                "layer": group_layer(source.layer for source in ordered),
                "occurrences": [source_occurrence(source) for source in ordered],
            }
        )
    return exact, renamed, fingerprints


def scaffold_families(
    sources: Sequence[SourceFile],
    exact_files: Sequence[dict[str, object]],
    exact_methods: Sequence[dict[str, object]],
    renamed_methods: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for rule in FAMILY_RULES:
        matched = sorted((source for source in sources if rule.matches(source)), key=lambda source: (source.addon, source.path))
        if len({source.addon for source in matched}) < 2:
            continue
        evidence_paths = {source.evidence_path for source in matched}
        exact_file_ids = sorted(
            group["id"]
            for group in exact_files
            if any(occurrence["path"] in evidence_paths for occurrence in group["occurrences"])
        )
        exact_method_ids = sorted(
            group["id"]
            for group in exact_methods
            if any(occurrence["path"] in evidence_paths for occurrence in group["occurrences"])
        )
        renamed_method_ids = sorted(
            group["id"]
            for group in renamed_methods
            if any(occurrence["path"] in evidence_paths for occurrence in group["occurrences"])
        )
        result.append(
            {
                "id": rule.identifier,
                "title": rule.title,
                "description": rule.description,
                "addon_count": len({source.addon for source in matched}),
                "file_count": len(matched),
                "production_file_count": sum(source.category == "java_main" for source in matched),
                "test_file_count": sum(source.category == "java_test" or source.category == "gallery_data" for source in matched),
                "tooling_file_count": sum(source.category not in {"java_main", "java_test", "gallery_data"} for source in matched),
                "addons": sorted({source.addon for source in matched}),
                "exact_file_clone_group_ids": exact_file_ids,
                "exact_method_clone_group_ids": exact_method_ids,
                "renamed_method_clone_group_ids": renamed_method_ids,
                "occurrences": [source_occurrence(source) for source in matched],
            }
        )
    return result


def candidate_modules(families: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    by_id = {family["id"]: family for family in families}
    candidates: list[dict[str, object]] = []
    for spec in CANDIDATE_SPECS:
        present = [by_id[identifier] for identifier in spec["families"] if identifier in by_id]
        addons = sorted({addon for family in present for addon in family["addons"]})
        clone_ids = sorted(
            {
                clone_id
                for family in present
                for key in (
                    "exact_file_clone_group_ids",
                    "exact_method_clone_group_ids",
                    "renamed_method_clone_group_ids",
                )
                for clone_id in family[key]
            }
        )
        candidates.append(
            {
                "extraction_order": spec["order"],
                "id": spec["id"],
                "title": spec["title"],
                "evidence": {
                    "family_ids": [family["id"] for family in present],
                    "addon_count": len(addons),
                    "file_count": sum(int(family["file_count"]) for family in present),
                    "clone_group_count": len(clone_ids),
                    "clone_group_ids": clone_ids,
                    "addons": addons,
                },
                "benefits": list(spec["benefits"]),
                "coupling_and_abi_risks": list(spec["risks"]),
                "recommendation": spec["recommendation"],
            }
        )
    return candidates


def make_inventory_digest(sources: Sequence[SourceFile]) -> str:
    digest = hashlib.sha256()
    for source in sources:
        for field in (source.addon, source.commit, source.path, source.sha256):
            digest.update(field.encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def layer_counts(groups: Sequence[dict[str, object]]) -> dict[str, int]:
    counter = collections.Counter(str(group["layer"]) for group in groups)
    return dict(sorted(counter.items()))


def build_report(
    root: Path,
    pack_version: str,
    *,
    minimum_method_tokens: int = DEFAULT_MIN_METHOD_TOKENS,
    minimum_file_tokens: int = DEFAULT_MIN_FILE_TOKENS,
    expected_addons: int = 51,
) -> dict[str, object]:
    manifest_identity, manifest_gitlinks = load_version_manifest(
        root,
        pack_version,
        expected_addons=expected_addons,
    )
    index_gitlinks = discover_addon_gitlinks(root)
    if len(index_gitlinks) != expected_addons:
        raise RuntimeError(f"expected {expected_addons} addon gitlinks, found {len(index_gitlinks)}")
    require_exact_manifest_gitlinks(manifest_identity, manifest_gitlinks, index_gitlinks)
    sources = load_sources(root, manifest_gitlinks)
    java_sources = [source for source in sources if source.category in {"java_main", "java_test"}]
    methods = [
        method
        for source in java_sources
        for method in extract_methods(source, minimum_tokens=minimum_method_tokens)
    ]

    files_exact = exact_file_groups(sources)
    methods_exact, methods_renamed = method_clone_groups(methods)
    java_files_exact, java_files_renamed, file_fingerprints = java_file_clone_groups(
        java_sources, minimum_tokens=minimum_file_tokens
    )
    families = scaffold_families(sources, files_exact, methods_exact, methods_renamed)

    category_counts = collections.Counter(source.category for source in sources)
    layer_file_counts = collections.Counter(source.layer for source in sources)
    report: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "scanner": {
            "name": "tools/scan_duplicates.py",
            "version": SCANNER_VERSION,
            "deterministic": True,
        },
        "target": {
            "pack": "All the Mons",
            "pack_version": pack_version,
            "source": "version-manifest commits verified against addons/* index gitlinks",
            "manifest": manifest_identity,
            "gitlink_comparison": {
                "exact": True,
                "manifest_addon_count": len(manifest_gitlinks),
                "index_addon_count": len(index_gitlinks),
            },
        },
        "scope": {
            "addon_count": len(manifest_gitlinks),
            "addons": [
                {
                    "id": addon,
                    "manifest_commit": commit,
                    "gitlink_commit": commit,
                    "matches_manifest": True,
                }
                for addon, commit in manifest_gitlinks
            ],
            "eligible_file_count": len(sources),
            "eligible_byte_count": sum(len(source.data) for source in sources),
            "eligible_file_inventory_sha256": make_inventory_digest(sources),
            "category_file_counts": dict(sorted(category_counts.items())),
            "layer_file_counts": dict(sorted(layer_file_counts.items())),
            "java_file_count_eligible_for_token_clones": len(file_fingerprints),
            "java_method_count_eligible_for_clones": len(methods),
            "included": [
                "tracked src/main/java and src/test/java sources",
                "tracked Gradle, CI/release, and quality configuration",
                "tracked UTF-8 tools and gallery generator/lifecycle data",
                "tracked BlueMap add-on and NeoForge metadata",
            ],
            "excluded": [
                "build output and generated trees",
                "third-party, vendored, and dependency content",
                "licenses, notices, provenance records, documentation, binary assets, and Gradle wrapper binaries/scripts",
                "untracked files and mutable submodule working-tree content",
            ],
        },
        "methodology": {
            "minimum_java_method_tokens": minimum_method_tokens,
            "minimum_java_file_tokens": minimum_file_tokens,
            "exact_files": "SHA-256 of complete tracked file bytes; cross-add-on groups only.",
            "exact_java_tokens": "Comments/whitespace and package/import declarations are removed; identifiers and literals, including complete Java text blocks, are preserved.",
            "renamed_java_tokens": "Each identifier is alpha-renamed by first occurrence and literal values, including text blocks, are typed; groups must contain at least two exact-token fingerprints.",
            "method_boundary_note": "Method declarations are recognized with a deterministic lexical brace/parenthesis pass. Whole-file token fingerprints cover Java constructs the method pass does not recognize.",
            "interpretation_note": "Renamed clones are candidates for review, not proof of equivalent behavior. Layer labels keep infrastructure/test repetition separate from behavior-heavy rendering code.",
        },
        "summary": {
            "exact_file_clone_groups": len(files_exact),
            "exact_file_clone_occurrences": sum(int(group["occurrence_count"]) for group in files_exact),
            "exact_java_file_token_clone_groups": len(java_files_exact),
            "renamed_java_file_token_clone_groups": len(java_files_renamed),
            "exact_java_method_clone_groups": len(methods_exact),
            "renamed_java_method_clone_groups": len(methods_renamed),
            "exact_method_groups_by_layer": layer_counts(methods_exact),
            "renamed_method_groups_by_layer": layer_counts(methods_renamed),
            "scaffold_family_count": len(families),
        },
        "exact_file_clones": files_exact,
        "java_file_token_clones": {"exact": java_files_exact, "renamed": java_files_renamed},
        "java_method_clones": {"exact": methods_exact, "renamed": methods_renamed},
        "repeated_families": families,
        "reusable_module_candidates": candidate_modules(families),
    }
    return report


def format_count_by_layer(counts: dict[str, int]) -> str:
    return ", ".join(f"{layer} {count}" for layer, count in sorted(counts.items())) or "none"


def top_group_label(group: dict[str, object]) -> str:
    occurrences = group["occurrences"]
    names = sorted({PurePosixPath(str(item["path"])).name for item in occurrences})
    return ", ".join(names[:3]) + (" …" if len(names) > 3 else "")


def render_markdown(report: dict[str, object]) -> str:
    scope = report["scope"]
    summary = report["summary"]
    methodology = report["methodology"]
    manifest = report["target"]["manifest"]
    lines = [
        f"# BlueMap add-on deduplication audit: ATMons {report['target']['pack_version']}",
        "",
        "This is a deterministic source audit of the exact 51 add-on commits pinned by the meta-repository. "
        "It identifies extraction candidates; it does not assert behavioral equivalence or change any add-on.",
        "",
        "## Scope and result",
        "",
        f"- Add-ons: **{scope['addon_count']}** gitlinks; eligible tracked files: **{scope['eligible_file_count']}** "
        f"({scope['eligible_byte_count']:,} bytes).",
        f"- Version manifest: `{manifest['path']}` (`{manifest['sha256']}`); all "
        f"**{manifest['addon_count']}** add-on commits exactly match the index gitlinks.",
        f"- Inventory fingerprint: `{scope['eligible_file_inventory_sha256']}`.",
        f"- Exact file groups: **{summary['exact_file_clone_groups']}** "
        f"({summary['exact_file_clone_occurrences']} occurrences).",
        f"- Whole-Java-file token groups: **{summary['exact_java_file_token_clone_groups']} exact**, "
        f"**{summary['renamed_java_file_token_clone_groups']} renamed**.",
        f"- Java method groups (minimum {methodology['minimum_java_method_tokens']} tokens): "
        f"**{summary['exact_java_method_clone_groups']} exact**, "
        f"**{summary['renamed_java_method_clone_groups']} renamed**.",
        f"- Exact method layers: {format_count_by_layer(summary['exact_method_groups_by_layer'])}; "
        f"renamed method layers: {format_count_by_layer(summary['renamed_method_groups_by_layer'])}.",
        "",
        "The full JSON report records every qualifying occurrence with its add-on commit, path, line range where applicable, "
        "token count, and content fingerprint.",
        "",
        "## Strong exact-copy evidence",
        "",
        "| Files | Add-ons | Layer | Evidence |",
        "| --- | ---: | --- | --- |",
    ]
    exact_groups = report["exact_file_clones"]
    for group in exact_groups[:12]:
        lines.append(
            f"| {top_group_label(group)} | {group['addon_count']} | {group['layer']} | `{group['id']}` |"
        )
    if not exact_groups:
        lines.append("| None | 0 | — | — |")

    lines.extend(
        [
            "",
            "## Repeated families",
            "",
            "| Family | Add-ons | Files | Exact file groups | Exact / renamed method groups |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for family in report["repeated_families"]:
        lines.append(
            f"| {family['title']} | {family['addon_count']} | {family['file_count']} | "
            f"{len(family['exact_file_clone_group_ids'])} | "
            f"{len(family['exact_method_clone_group_ids'])} / {len(family['renamed_method_clone_group_ids'])} |"
        )

    lines.extend(
        [
            "",
            "## Recommended extraction order",
            "",
        ]
    )
    for candidate in report["reusable_module_candidates"]:
        evidence = candidate["evidence"]
        lines.extend(
            [
                f"### {candidate['extraction_order']}. `{candidate['id']}` — {candidate['title']}",
                "",
                f"Evidence: {evidence['file_count']} family-matched files across {evidence['addon_count']} add-ons and "
                f"{evidence['clone_group_count']} content clone groups.",
                "",
                f"Recommendation: {candidate['recommendation']}",
                "",
                "Benefits:",
                "",
                *[f"- {benefit}" for benefit in candidate["benefits"]],
                "",
                "Coupling/ABI risks:",
                "",
                *[f"- {risk}" for risk in candidate["coupling_and_abi_risks"]],
                "",
            ]
        )

    lines.extend(
        [
            "## Guardrails for consolidation",
            "",
            "- Treat exact byte/token matches as mechanical evidence. Review alpha-renamed matches before extraction; literals and identifiers are intentionally abstracted.",
            "- Keep profile pins, resource manifests, gallery case data, and mod-specific render decisions in their owning repositories.",
            "- Do not introduce a shared server runtime JAR until class loading, dependency installation, independent add-on version skew, and removal behavior are tested together.",
            "- Put visual conformance fixtures around any geometry, UV, connected-texture, translucency, or block-entity helper before moving it.",
            "- Re-run this audit and the full combined integration suite after each extraction slice; do not migrate all 51 repositories in one release wave.",
            "",
            "## Reproduce",
            "",
            "```bash",
            "python tools/scan_duplicates.py --version 1.2.0 --write",
            "python tools/scan_duplicates.py --version 1.2.0 --check",
            "```",
            "",
            "The scan includes only tracked first-party Java and meaningful build/config/gallery tooling from pinned git objects. "
            "It excludes generated/build trees, dependencies, third-party/vendor content, licenses, provenance, docs, binaries, and untracked files.",
            "",
        ]
    )
    return "\n".join(lines)


def serialize_json(report: dict[str, object]) -> str:
    return json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_or_check(path: Path, content: str, *, check: bool) -> bool:
    if check:
        if not path.exists():
            print(f"missing generated report: {path}", file=sys.stderr)
            return False
        existing = path.read_text(encoding="utf-8")
        if existing != content:
            print(f"generated report is stale: {path}", file=sys.stderr)
            return False
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1], help="BlueMap ATMons repository root")
    parser.add_argument("--version", required=True, help="All the Mons version label for the report")
    parser.add_argument("--expected-addons", type=int, default=51)
    parser.add_argument("--minimum-method-tokens", type=int, default=DEFAULT_MIN_METHOD_TOKENS)
    parser.add_argument("--minimum-file-tokens", type=int, default=DEFAULT_MIN_FILE_TOKENS)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the JSON and Markdown reports")
    mode.add_argument("--check", action="store_true", help="verify committed reports are current")
    parser.add_argument("--json-out", type=Path, help="JSON output path (relative paths resolve below the repository)")
    parser.add_argument("--markdown-out", type=Path, help="Markdown output path (relative paths resolve below the repository)")
    return parser.parse_args(argv)


def resolve_output(root: Path, explicit: Path | None, default: Path) -> Path:
    path = explicit or default
    return path if path.is_absolute() else root / path


def default_report_paths(root: Path, pack_version: str) -> tuple[Path, Path]:
    base = root / "reports" / "deduplication" / f"atmons-{pack_version}"
    return Path(f"{base}.json"), Path(f"{base}.md")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.repo.resolve()
    report = build_report(
        root,
        args.version,
        minimum_method_tokens=args.minimum_method_tokens,
        minimum_file_tokens=args.minimum_file_tokens,
        expected_addons=args.expected_addons,
    )
    default_json, default_markdown = default_report_paths(root, args.version)
    json_path = resolve_output(root, args.json_out, default_json)
    markdown_path = resolve_output(root, args.markdown_out, default_markdown)
    check = bool(args.check)
    ok_json = write_or_check(json_path, serialize_json(report), check=check)
    ok_markdown = write_or_check(markdown_path, render_markdown(report), check=check)
    if not (ok_json and ok_markdown):
        return 1
    verb = "validated" if check else "wrote"
    print(
        f"{verb} deduplication report for {report['scope']['addon_count']} add-ons: "
        f"{json_path} and {markdown_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
