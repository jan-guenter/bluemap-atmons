# BlueMap add-on deduplication audit: ATMons 1.2.0

This is a deterministic source audit of the exact 51 add-on commits pinned by the meta-repository. It identifies extraction candidates; it does not assert behavioral equivalence or change any add-on.

## Scope and result

- Add-ons: **51** gitlinks; eligible tracked files: **2849** (29,294,829 bytes).
- Version manifest: `versions/1.2.0/manifest.json` (`69d6188596d73891af8e6dc8f959f12a77726275f5892421cedf02ca3ac5eb14`); all **51** add-on commits exactly match the index gitlinks.
- Inventory fingerprint: `06c9ed29c5cb843cb654fc19e51d7c3e87ffaa18f60a8e995c11294f24631ea5`.
- Exact file groups: **8** (99 occurrences).
- Whole-Java-file token groups: **43 exact**, **47 renamed**.
- Java method groups (minimum 36 tokens): **370 exact**, **203 renamed**.
- Parsed Python/Gradle/GitHub Actions/Bash groups (minimum 12 units): **366 exact**, **15 conservative local-renamed**.
- Structured inventory fingerprint: `057e065dc081a51fe400c37fadc5896f55ec73cb2824c1c27af4935430f8a806` (10185 parsed units; 9119 eligible).
- Exact method layers: behavioral 235, mixed 2, scaffolding 75, test_scaffolding 16, test_support 42; renamed method layers: behavioral 73, mixed 5, scaffolding 74, test_scaffolding 15, test_support 36.

The full JSON report records every qualifying occurrence with its add-on commit, path, line range where applicable, token count, and content fingerprint.

## Parsed non-Java duplication

| Language | Parsed units | Exact groups | Local-renamed groups |
| --- | ---: | ---: | ---: |
| github_actions | 1356 | 41 | 0 |
| gradle | 5970 | 222 | 8 |
| python | 2165 | 89 | 7 |
| shell | 694 | 14 | 0 |

## Strong exact-copy evidence

| Files | Add-ons | Layer | Evidence |
| --- | ---: | --- | --- |
| checkstyle.xml | 24 | scaffolding | `file-77fe7b6d9a70f527` |
| verify_staged_equivalence.py | 20 | scaffolding | `file-cc8fa6cb1e79b855` |
| verify_pinned_artifacts.py | 20 | scaffolding | `file-dc7c6d80796f9d57` |
| checkstyle.xml | 17 | scaffolding | `file-e04503e9acfe6b44` |
| checkstyle.xml | 9 | scaffolding | `file-43737c81b15d2ae7` |
| verify_staged_equivalence.py | 5 | scaffolding | `file-ecdecd142245f4d1` |
| clear.mcfunction | 2 | test_support | `file-78b6dd8bf0896769` |
| pose_south.mcfunction | 2 | test_support | `file-827d564197268833` |

## Repeated families

| Family | Add-ons | Files | Exact file groups | Exact / renamed methods | Exact / local structured |
| --- | ---: | ---: | ---: | ---: | ---: |
| Runtime activation and diagnostics | 51 | 161 | 0 | 8 / 18 | 0 / 0 |
| Artifact identity and profiles | 50 | 183 | 0 | 28 / 12 | 0 / 0 |
| BlueMap adapter bootstrap | 51 | 181 | 0 | 40 / 44 | 0 / 0 |
| Build, release, and quality configuration | 51 | 308 | 3 | 0 / 0 | 277 / 8 |
| Artifact verification tooling | 40 | 109 | 3 | 0 / 0 | 42 / 3 |
| Gallery generation and lifecycle harness | 51 | 431 | 1 | 0 / 0 | 47 / 5 |
| Rendering and geometry primitives | 26 | 36 | 0 | 32 / 4 | 0 / 0 |
| Installed model compilers | 13 | 28 | 0 | 46 / 14 | 0 / 0 |
| Connected-texture engine | 11 | 68 | 0 | 99 / 23 | 0 / 0 |
| Athena resource models | 4 | 10 | 0 | 16 / 1 | 0 / 0 |
| Fusion resource models | 5 | 18 | 0 | 56 / 5 | 0 / 0 |

## Recommended extraction order

### 1. `bluemap-addon-toolkit` — Development and release toolkit

Evidence: 848 family-matched files across 51 add-ons and 388 content clone groups.

Recommendation: Extract first as versioned CLI/Gradle conventions. Keep generated gallery data in each add-on.

Benefits:

- Removes the largest byte-identical script/config copies without adding a server runtime dependency.
- Makes gallery and release-policy fixes land once and gives all repositories the same deterministic checks.

Coupling/ABI risks:

- A shared tool version must remain pinned so an old add-on can still reproduce its release.
- Gallery generators have legitimate schema variants; keep extension hooks instead of forcing one data model.

### 2. `bluemap-addon-runtime` — Activation, artifact identity, and diagnostics runtime

Evidence: 344 family-matched files across 51 add-ons and 66 content clone groups.

Recommendation: Extract pure contracts and utilities after combined tests; retain each add-on's profile data locally.

Benefits:

- Centralizes exact-artifact gating, bounded diagnostics, and fail-closed activation behavior.
- Reduces the chance that one add-on drifts from the portfolio's compatibility policy.

Coupling/ABI risks:

- A shared runtime JAR creates ABI/version-skew and class-loader questions across independently released packs.
- Artifact profiles contain add-on-specific pins and must remain declarative inputs, not shared mutable state.

### 3. `athena-resource-models` — Athena resource-model source module

Evidence: 10 family-matched files across 4 add-ons and 17 content clone groups.

Recommendation: Extract after freezing the Chipped, Chisel, CobbleFurnies, and Factory Blocks fixtures.

Benefits:

- Shares the four-consumer Athena face and connection vocabulary behind conformance fixtures.
- Keeps exact resource interpretation in one source module without adding an installed dependency.

Coupling/ABI risks:

- The two emitter variants have real culling and top-only differences that need a tested strategy.
- Consumer allowlists, artifact profiles, and generated resource closures must remain local.

### 4. `fusion-resource-models` — Fusion resource-model source module

Evidence: 18 family-matched files across 5 add-ons and 61 content clone groups.

Recommendation: Extract the exact common contract; keep format versions, catalogs, and route allowlists local.

Benefits:

- Shares the proven four-consumer Fusion direction, orientation, texture, and emission contracts.
- Creates one fixture-backed home for connected-face and UV correctness.

Coupling/ABI risks:

- Format profiles and namespace routing differ and cannot be normalized mechanically.
- BlueMap-derived emitter mechanics require their existing notice and provenance boundary.

### 5. `bluemap-addon-render-core` — Neutral rendering primitives

Evidence: 36 family-matched files across 26 add-ons and 36 content clone groups.

Recommendation: Start only with exact multi-consumer APIs such as the seven-copy FaceLighting contract.

Benefits:

- Shares proven lighting, immutable geometry records, and transforms without owning block routes.
- Lets behavior-heavy add-ons focus on state and block-entity interpretation.

Coupling/ABI risks:

- Similar helper names do not prove identical UV, lighting, coordinate, or material semantics.
- BlueMap mesh emission must remain isolated in a version-specific adapter module.

### 6. `installed-geo-resource-models` — Installed Geo resource-model source module

Evidence: 28 family-matched files across 13 add-ons and 60 content clone groups.

Recommendation: Treat as provisional until Ars Nouveau, Ars Technica, and Ars Creo pass one parity suite.

Benefits:

- Shares the three-Ars-consumer installed Geo hierarchy, UV, and mesh compilation contract.
- Reduces repeated bounded parser and malformed-input behavior.

Coupling/ABI risks:

- Wavefront, OBJ, Blockbench/BBS, and Gecko-style formats are not one generic compiler.
- The three consumers need a common malformed-input and fallback fixture suite first.

### 7. `bluemap-addon-adapter-api` — BlueMap adapter bootstrap API

Evidence: 181 family-matched files across 51 add-ons and 84 content clone groups.

Recommendation: Design now, but publish only after the 5.23 integration branch has a stable combined runtime gate.

Benefits:

- Consolidates adapter compatibility probes and resource-extension registration used throughout the portfolio.
- Provides one migration seam for later BlueMap internal API changes.

Coupling/ABI risks:

- The code is coupled to BlueMap internals and currently names the 5.22 adapter generation.
- Extracting while the 5.23 backport is under integration could freeze the wrong ABI.

## Guardrails for consolidation

- Treat exact byte/token matches as mechanical evidence. Java alpha-renamed matches abstract identifiers and literal values, so review them before extraction.
- Parsed Python and Gradle local-renamed matches preserve literals and external/API names. GitHub Actions and Bash identifiers are never renamed. These are still review candidates, not proof of equivalent behavior.
- Keep profile pins, resource manifests, gallery case data, and mod-specific render decisions in their owning repositories.
- Do not introduce a shared server runtime JAR until class loading, dependency installation, independent add-on version skew, and removal behavior are tested together.
- Do not create one generic connected-texture engine. Athena, Fusion, and CTM keep separate format contracts and fixture suites.
- Put visual conformance fixtures around any geometry, UV, connected-texture, translucency, or block-entity helper before moving it.
- Re-run this audit and the full combined integration suite after each extraction slice; do not migrate all 51 repositories in one release wave.

## Reproduce

```bash
python tools/scan_duplicates.py --version 1.2.0 --write
python tools/scan_duplicates.py --version 1.2.0 --check
```

The scan includes only tracked first-party Java and meaningful build/config/gallery tooling from pinned git objects. It excludes generated/build trees, dependencies, third-party/vendor content, licenses, provenance, docs, binaries, and untracked files.
