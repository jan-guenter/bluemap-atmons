# BlueMap add-on deduplication audit: ATMons 1.2.0

This is a deterministic source audit of the exact 51 add-on commits pinned by the meta-repository. It identifies extraction candidates; it does not assert behavioral equivalence or change any add-on.

## Scope and result

- Add-ons: **51** gitlinks; eligible tracked files: **2887** (29,115,561 bytes).
- Version manifest: `versions/1.2.0/manifest.json` (`c181203ddaf4ad353cecf7975af21acb1f55011b5a8c8f1b25bf79a8202db138`); all **51** add-on commits exactly match the index gitlinks.
- Inventory fingerprint: `60dc3e2a985b213c7c929e649d55d5154e3e520708e7c1a1549215bdd303a51e`.
- Exact file groups: **7** (103 occurrences).
- Whole-Java-file token groups: **45 exact**, **47 renamed**.
- Java method groups (minimum 36 tokens): **374 exact**, **195 renamed**.
- Parsed Python/Gradle/GitHub Actions/Bash groups (minimum 12 units): **265 exact**, **9 conservative local-renamed**.
- Structured inventory fingerprint: `79a0753f11aaec87fac5ec422ef8c55172630ac2fe9002aaa9587382bc479910` (9479 parsed units; 8508 eligible).
- Exact method layers: behavioral 239, mixed 2, scaffolding 76, test_scaffolding 16, test_support 41; renamed method layers: behavioral 73, mixed 5, scaffolding 73, test_scaffolding 15, test_support 29.

The full JSON report records every qualifying occurrence with its add-on commit, path, line range where applicable, token count, and content fingerprint.

## Parsed non-Java duplication

| Language | Parsed units | Exact groups | Local-renamed groups |
| --- | ---: | ---: | ---: |
| github_actions | 1322 | 33 | 0 |
| gradle | 5289 | 131 | 2 |
| python | 2200 | 89 | 7 |
| shell | 668 | 12 | 0 |

## Strong exact-copy evidence

| Files | Add-ons | Layer | Evidence |
| --- | ---: | --- | --- |
| checkstyle.xml | 28 | scaffolding | `file-77fe7b6d9a70f527` |
| verify_staged_equivalence.py | 24 | scaffolding | `file-cc8fa6cb1e79b855` |
| verify_pinned_artifacts.py | 24 | scaffolding | `file-dc7c6d80796f9d57` |
| checkstyle.xml | 18 | scaffolding | `file-43737c81b15d2ae7` |
| verify_staged_equivalence.py | 5 | scaffolding | `file-ecdecd142245f4d1` |
| clear.mcfunction | 2 | test_support | `file-78b6dd8bf0896769` |
| pose_south.mcfunction | 2 | test_support | `file-827d564197268833` |

## Repeated families

| Family | Add-ons | Files | Exact file groups | Exact / renamed methods | Exact / local structured |
| --- | ---: | ---: | ---: | ---: | ---: |
| Runtime activation and diagnostics | 51 | 165 | 0 | 8 / 18 | 0 / 0 |
| Artifact identity and profiles | 50 | 186 | 0 | 28 / 12 | 0 / 0 |
| BlueMap adapter bootstrap | 51 | 215 | 0 | 41 / 43 | 0 / 0 |
| Build, release, and quality configuration | 51 | 304 | 2 | 0 / 0 | 176 / 2 |
| Artifact verification tooling | 44 | 117 | 3 | 0 / 0 | 42 / 3 |
| Gallery generation and lifecycle harness | 51 | 431 | 1 | 0 / 0 | 47 / 5 |
| Rendering and geometry primitives | 27 | 43 | 0 | 32 / 4 | 0 / 0 |
| Installed model compilers | 13 | 28 | 0 | 46 / 14 | 0 / 0 |
| Connected-texture engine | 11 | 78 | 0 | 103 / 19 | 0 / 0 |

## Recommended extraction order

### 1. `bluemap-addon-dev-toolkit` — Development and release toolkit

Evidence: 852 family-matched files across 51 add-ons and 280 content clone groups.

Recommendation: Extract first as versioned CLI/Gradle conventions. Keep generated gallery data in each add-on.

Benefits:

- Removes the largest byte-identical script/config copies without adding a server runtime dependency.
- Makes gallery and release-policy fixes land once and gives all repositories the same deterministic checks.

Coupling/ABI risks:

- A shared tool version must remain pinned so an old add-on can still reproduce its release.
- Gallery generators have legitimate schema variants; keep extension hooks instead of forcing one data model.

### 2. `bluemap-addon-runtime` — Activation, artifact identity, and diagnostics runtime

Evidence: 351 family-matched files across 51 add-ons and 66 content clone groups.

Recommendation: Extract pure contracts and utilities after combined tests; retain each add-on's profile data locally.

Benefits:

- Centralizes exact-artifact gating, bounded diagnostics, and fail-closed activation behavior.
- Reduces the chance that one add-on drifts from the portfolio's compatibility policy.

Coupling/ABI risks:

- A shared runtime JAR creates ABI/version-skew and class-loader questions across independently released packs.
- Artifact profiles contain add-on-specific pins and must remain declarative inputs, not shared mutable state.

### 3. `bluemap-addon-adapter-api` — BlueMap adapter bootstrap API

Evidence: 215 family-matched files across 51 add-ons and 84 content clone groups.

Recommendation: Design now, but publish only after the 5.23 integration branch has a stable combined runtime gate.

Benefits:

- Consolidates adapter compatibility probes and resource-extension registration used throughout the portfolio.
- Provides one migration seam for later BlueMap internal API changes.

Coupling/ABI risks:

- The code is coupled to BlueMap internals and currently names the 5.22 adapter generation.
- Extracting while the 5.23 backport is under integration could freeze the wrong ABI.

### 4. `bluemap-addon-render-core` — Pure rendering and installed-model core

Evidence: 71 family-matched files across 32 add-ons and 96 content clone groups.

Recommendation: Extract only clone groups proven pure by fixture tests; preserve add-on-specific emitters.

Benefits:

- Shares tested geometry, face-lighting, model parsing, and mesh-emission primitives.
- Lets behavior-heavy add-ons focus on block-state and block-entity interpretation.

Coupling/ABI risks:

- Similar class names do not prove identical UV, lighting, coordinate, or material semantics.
- Changes in a common renderer have a much larger visual regression radius.

### 5. `bluemap-addon-connected-textures` — Connected-texture/fusion module

Evidence: 78 family-matched files across 11 add-ons and 122 content clone groups.

Recommendation: Extract last, as a strategy-based module with per-mod conformance fixtures and visual gates.

Benefits:

- Unifies the repeated CTM/fusion topology and texture-selection implementations.
- Creates one place for connected-face correctness and adjacency regression fixtures.

Coupling/ABI risks:

- Mods use different CTM dialects, edge rules, fallback textures, and resource schemas.
- A false abstraction can silently make visually distinct blocks look uniformly wrong.

## Guardrails for consolidation

- Treat exact byte/token matches as mechanical evidence. Java alpha-renamed matches abstract identifiers and literal values, so review them before extraction.
- Parsed Python and Gradle local-renamed matches preserve literals and external/API names. GitHub Actions and Bash identifiers are never renamed. These are still review candidates, not proof of equivalent behavior.
- Keep profile pins, resource manifests, gallery case data, and mod-specific render decisions in their owning repositories.
- Do not introduce a shared server runtime JAR until class loading, dependency installation, independent add-on version skew, and removal behavior are tested together.
- Put visual conformance fixtures around any geometry, UV, connected-texture, translucency, or block-entity helper before moving it.
- Re-run this audit and the full combined integration suite after each extraction slice; do not migrate all 51 repositories in one release wave.

## Reproduce

```bash
python tools/scan_duplicates.py --version 1.2.0 --write
python tools/scan_duplicates.py --version 1.2.0 --check
```

The scan includes only tracked first-party Java and meaningful build/config/gallery tooling from pinned git objects. It excludes generated/build trees, dependencies, third-party/vendor content, licenses, provenance, docs, binaries, and untracked files.
