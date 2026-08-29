# Semantic deduplication review: ATMons 1.2.0

This review turns the deterministic clone inventory into extraction decisions.
It covers the exact 51 add-on commits pinned by the ATMons 1.2.0 manifest. It
does not change a child repository, assert that similarly shaped renderers are
interchangeable, or authorize a child release.

The machine evidence remains the generated
[Markdown inventory](atmons-1.2.0.md) and
[JSON inventory](atmons-1.2.0.json). The scanner is
[`tools/scan_duplicates.py`](../../tools/scan_duplicates.py).

## Methodology and evidence boundary

The deterministic scan uses `versions/1.2.0/manifest.json` as its source of
truth and verifies that every manifest commit matches the corresponding
`addons/*` index gitlink. It reads those Git objects, not mutable submodule
working trees.

The scan includes tracked production and test Java, Gradle and quality
configuration, GitHub workflows, verification tools, gallery tools and
lifecycle data, and BlueMap add-on metadata. It excludes build output,
generated and vendored trees, dependencies, documentation, licenses,
provenance records, binary assets, and ordinary runtime resource data. Those
excluded inputs may be important to a later module's provenance or fixture
design, but they are not code-clone evidence.

The evidence classes are:

- Exact files: SHA-256 of complete file bytes.
- Exact Java files and methods: comments, whitespace, package declarations,
  and imports are removed; identifiers and literals remain exact.
- Renamed Java files and methods: identifiers are alpha-renamed by first
  occurrence and literals are reduced to their types. These matches are review
  candidates, not equivalence claims.
- Structured Python, Gradle, GitHub Actions, and shell units: syntax-aware
  fingerprints retain literals and external names. Only proven local Python
  and Gradle bindings may be normalized; workflow and shell identifiers are
  never renamed.
- The minimum qualifying sizes are 80 tokens for a Java file and 36 tokens for
  a Java method, and 12 syntax units for a structured record.

Scanner v2 parsed 9,479 structured units and admitted 8,508 to clone grouping.
It found 265 exact groups and 9 conservative local-renamed groups. Python
syntax errors, unbalanced Gradle blocks, unsupported workflow syntax, or Bash
parse failures stop the scan instead of silently dropping evidence.

The human review also performed a same-basename comparison to estimate the
size of broader tooling cohorts that are similar but not exact structured
clones. CI and release estimates use an 85 percent token-similarity floor and
one medoid per cohort. These are line-equivalent estimates, not byte-exact
savings.

The promotion rule applied here is:

1. Shared specifications and test contracts may be created immediately.
2. Shared production source requires two implementations with materially
   identical invariants and failure behavior plus a third concrete consumer.
3. A separately installed runtime provider requires three deployables that
   need one runtime ABI, a stable compatibility policy, a version handshake,
   load-order and version-skew tests, and operator acceptance.

## Non-additive result

The source inventory contains 2,887 eligible files and 29,115,561 bytes. It
includes 1,194 production Java files with 146,877 lines and 495 Java test files
with 65,872 lines.

- Byte-exact complete files: 7 groups, with 6,288 repeated scaffolding
  lines and 8 repeated test-support lines.
- Exact whole Java files: 45 groups, with 3,024 behavioral, 8,597
  scaffolding, and 3,422 test lines.
- Renamed whole Java files: 47 groups, with 632 behavioral, 9,561
  scaffolding, and 555 test candidate lines.
- Exact Java methods: 374 groups, with 7,593 behavioral, 10,047
  scaffolding, and 3,259 other lines.
- Renamed Java methods: 195 groups, with 2,349 behavioral, 5,295
  scaffolding, and 1,454 other candidate lines.

These rows must not be summed. A copied file also contributes copied methods.
A renamed group may contain members of an exact group. Repeated-family labels
also overlap primitive, format, and adapter classes. The line estimates count
all qualifying occurrences after the shortest representative; they are not a
prediction of the final module's size.

Small methods below the token floor, cross-language clones, generated runtime
profiles, and common fragments inside otherwise different methods are not in
the deterministic totals. This review treats small getters, stock fallback
idioms, vector products, and logging wrappers as low-value until they are part
of a larger proven contract.

## Tooling and repository boilerplate

The development and release layer is the largest low-risk target. The
generated family report records 852 build, release, verification, and gallery
files across all 51 add-ons. The structural review found about 35,259 repeated
line-equivalents:

| Cohort | Repositories represented | Repeated lines or line-equivalents |
| --- | ---: | ---: |
| `build.gradle` | 27 in 5 exact normalized cohorts | 10,341 |
| `settings.gradle` | 48 in 3 cohorts | 1,848 |
| `gradle.properties` | 51 in 2 high-similarity cohorts | 690 |
| `ci.yml` | 47 in 4 high-similarity cohorts | 4,599 |
| `release.yml` | 47 in 3 high-similarity cohorts | 8,593 |
| `bluemap.addon.json` | 50 in 3 exact normalized cohorts | 302 |
| `checkstyle.xml` | 46 in 2 byte-exact cohorts | 924 |
| `verify_pinned_artifacts.py` | 24 byte-exact copies | 2,346 |
| `verify_staged_equivalence.py` | 31 in 2 structural cohorts | 3,170 |
| `package.sh` | 40 in 6 structural cohorts | 1,371 |
| `generate.py` | 9 in 2 exact normalized cohorts | 1,075 |

The strongest complete-file evidence is:

- `file-77fe7b6d9a70f527`: 28 copies of `checkstyle.xml`.
- `file-43737c81b15d2ae7`: 18 copies of the other checkstyle generation.
- `file-cc8fa6cb1e79b855`: 24 copies of
  `verify_staged_equivalence.py`.
- `file-dc7c6d80796f9d57`: 24 copies of
  `verify_pinned_artifacts.py`.
- `file-ecdecd142245f4d1`: 5 copies of a second staged-equivalence
  generation.

The gallery generators are not one schema. A common CLI should own packaging,
build, clear, verify, deterministic serialization, and shared validation. Each
consumer should retain its case data and specialized generator hooks.

**Verdict:** create `bluemap-addon-toolkit` first. This is the name already
used by the portfolio architecture; it avoids creating a competing
`bluemap-addon-dev-toolkit` identity. Publish versioned Gradle conventions,
reusable pinned workflows, verification commands, gallery lifecycle helpers,
and the test kit. Repositories opt in to exact toolkit versions.

## Runtime activation and artifact identity

The runtime and profile framework is repeated across the whole portfolio.
Important whole-class groups include:

- `java-file-exact-06feb0c991a93502`: 24 `ArtifactPin` copies and 943
  repeated lines.
- `java-file-exact-8994b58dcbf88ed0`: the largest
  `ExactArtifactDetector` cohort, with 15 copies and 3,808 repeated lines.
  All four exact detector cohorts contain 22 files and 4,937 repeated lines.
- `java-file-exact-ce955695397ed9d0`: 24 `RegistryGuard` copies and 667
  repeated lines.
- `java-file-exact-17334c4a2524ec8e`: the largest
  `AdapterCompatibility` cohort, with 24 copies and 690 repeated lines.
  All three exact compatibility cohorts contain 43 files and 1,195 repeated
  lines.
- `java-file-renamed-0a97742394364a18`: 24 `AddonRuntime` copies and 1,817
  candidate lines.
- `java-file-exact-ff527b4976ce7dfe`: 9 `RouteActivation` copies and 552
  repeated lines.
- `java-file-renamed-4e9552fc1594517f`: 10 `ProfileDisablement` copies and
  489 candidate lines.
- `java-file-renamed-244b548d696b7f01`: 10 `BoundedDiagnostics` copies and
  245 candidate lines.

The detector conclusion is also supported by 21 exact copies of
`ExactArtifactDetectorTest` in
`java-file-exact-3448635fedbf8ba8`. The repeated-family view finds 8 exact and
18 renamed activation method groups, 28 exact and 12 renamed artifact/profile
method groups, and 41 exact and 43 renamed adapter-bootstrap method groups.

Exact mod coordinates, versions, sizes, hashes, resource manifests, and
profile data are not shared behavior. They remain declarative inputs in each
consumer. The shared source should contain parsing, duplicate rejection,
bounded diagnostics, terminal failure state, and compatibility contracts.

**Verdict:** the narrow production-source gate passes. Create
`bluemap-addon-runtime` as a source module compiled into each consumer. Do not
turn it into an installed provider. Keep BlueMap-internal adapter code out of
the first release so the stable contracts are not coupled to the current 5.22
package names while the 5.23 backport is still being integrated.

## Athena resource models

Chipped, Chisel, CobbleFurnies, and Factory Blocks contain four copies of the
same connection and face vocabulary and two closely related emitter variants.
Representative evidence is:

- `java-file-exact-10cb564c2dee90dd`: four `CtmConnections` copies.
- `java-file-exact-2fd1fe5786a2579f`: four `CtmSelector` copies.
- `java-file-exact-51ca07b556bffaeb`: four `CubeFace` copies.
- `java-file-exact-7c51b60c896dfa59`: Chipped and CobbleFurnies
  `AthenaQuadEmitter`.
- `java-file-exact-a0f46d7dbcd80eb9`: Chisel and Factory Blocks
  `AthenaQuadEmitter`.
- `java-file-exact-01813db117606962`: four exact
  `CtmConnectionsTest` copies.
- `java-file-exact-3f237c8634f60837` and
  `java-file-exact-42db445540ca848c`: the two exact emitter-test cohorts.

The eleven exact production/test file groups account for about 1,484 repeated
lines. Thirty-five exact method groups account for about 1,202 repeated method
lines, overlapping the file total. The two emitter variants differ mainly in
explicit top-only and culling hooks; that difference belongs behind a tested
strategy instead of being erased.

Representative sources are
[`Chipped AthenaQuadEmitter`](../../addons/chipped/src/main/java/io/github/janguenter/bluemap/chipped/adapter/bluemap522/AthenaQuadEmitter.java)
and
[`Chisel AthenaQuadEmitter`](../../addons/chisel/src/main/java/io/github/janguenter/bluemap/chisel/adapter/bluemap522/AthenaQuadEmitter.java).

**Verdict:** the production-source gate passes. Create
`athena-resource-models`, with no block registration and no consumer namespace
conditions. Keep consumer allowlists, exact artifact profiles, and generated
resource closure local.

## Fusion resource models

Connected Glass, Glassential, Rechiseled, and Rechiseled: Create contain the
strongest semantic renderer cluster. Rechiseled: Create is a bridge, but the
other three are independent consumers.

Representative whole-file evidence is:

- `java-file-exact-84327c9d00ef6240`: four `AxisVector` copies.
- `java-file-exact-8a8b6884c2e2cb9e`: four `TextureOrientation` copies.
- `java-file-exact-cb2f8e5960d5b8c1`: four `FusionDirection` copies.
- `java-file-exact-d521aec2eb3def81`: four exact orientation-test copies.
- `java-file-exact-b8ead46fd6d745d5f`: Rechiseled and bridge
  `FusionPredicate`.
- `java-file-exact-e9e14b5dc6d9d0a8`: Rechiseled and bridge
  `FusionTextureSelector`.

The exact helper and test files account for about 1,070 repeated lines. The
larger emitters are not whole-file clones, but 80 exact method groups cover
about 2,872 repeated method lines, plus 14 renamed groups covering about 327
candidate lines. Examples include `method-exact-19d60c4561024f93`
(`emitPolygon` in all four emitters), `method-exact-5bb873289cb6a425`
(`assignUvs`), and `method-renamed-f9947195dd05aafd` (`testAo`).

Representative sources are
[`Connected Glass FusionModelEmitter`](../../addons/connectedglass/src/main/java/io/github/janguenter/bluemap/connectedglass/adapter/bluemap522/FusionModelEmitter.java)
and
[`Rechiseled FusionModelEmitter`](../../addons/rechiseled/src/main/java/io/github/janguenter/bluemap/rechiseled/adapter/bluemap522/FusionModelEmitter.java).

**Verdict:** the production-source gate passes. Create
`fusion-resource-models`. Keep format-version profiles, namespace adapters,
resource catalogs, and route allowlists local. Preserve the BlueMap MIT notice
on emitter mechanics adapted from BlueMap.

## Installed Geo and general model compilers

Ars Nouveau, Ars Technica, and Ars Creo share an installed Geo model/compiler
contract. The scan finds 34 exact method groups covering about 910 repeated
lines and 11 renamed groups covering about 363 candidate lines. Notable
evidence includes:

- `java-file-exact-6ec0eab61a835405`: Ars Nouveau and Ars Technica
  `InstalledGeoModel`.
- `java-file-renamed-37491c155263a51f`: Ars Creo `WheelModel` plus the two
  `InstalledGeoModel` classes.
- `method-exact-d03c3d30cb0ce126`: identical compiler vertex-set logic in all
  three repositories.
- `method-exact-0a53f1a4d0aed86d`: identical `parseBones` behavior in all
  three repositories.

Oritech shares several vector, bone-chain, UV, and mesh-emission methods, but
not the complete compiler contract. CobbleFurnies and Cobblemon Stone Statues
share parser vocabulary while targeting different installed model formats.

**Verdict:** provisional pass for `installed-geo-resource-models`. Before code
moves, the three Ars consumers need one common fixture suite covering malformed
JSON, missing bones, UV mapping, hierarchy cycles, bounded input, and exact
fallback behavior. Do not fold Blockbench/BBS, Gecko-style, Wavefront, and OBJ
parsers into one generic model compiler.

## Neutral render primitives

The clearest neutral primitive is `FaceLighting`:

- `java-file-exact-7c6806712bf5d745` contains seven exact copies in Chipped,
  CobbleFurnies, Integrated Dynamics, LaserIO, Pipez, Powah, and
  Sophisticated. It accounts for 258 repeated lines.
- Ars Creo, Ars Nouveau, and Ars Technica form a separate three-copy lighting
  cohort.
- Chisel and Factory Blocks form another two-copy cohort.
- Nature's Aura and Tempad form a fourth cohort, with Productive Metalworks as
  a renamed candidate.

Only the seven-copy API is proven identical. Other useful exact method groups
include direction selection, transformed positions, stock fallback reset, and
atomic partial-geometry removal, but most are small and mix different renderer
invariants.

**Verdict:** create `bluemap-addon-render-core` only after the toolkit and
runtime modules. Start with the exact seven-copy lighting API and independently
tested JDK-only vectors or immutable geometry records. Keep BlueMap mesh
emission in a version-specific adapter module. Do not create repositories for
single helper classes.

## Mod-interplay clusters that stay private

Several bridge/base pairs explain real duplication but do not satisfy the
promotion rule:

- Immersive Engineering and Immersive Energistics wires:
  `java-file-exact-1ec249d3ae966447` (`WireEmitter`),
  `java-file-exact-2d6688f6749c5c5f` (`WireNetworkData`), and
  `java-file-exact-dc8f15f27acebb0e` (`WireRenderPass`) account for about
  402 repeated whole-file lines. Keep them private because there is no third
  proven consumer.
- Integrated Dynamics and Pipez JSON emitter:
  `java-file-exact-b20b004b24e9614a` is one 200-line copy. Keep it private
  because the third-consumer gate fails.
- Laser Bridges and Tempad tinted emitter:
  `java-file-renamed-bafd976b20c40314` covers about 218 candidate lines.
  Keep it private because the third-consumer gate fails.
- Wavefront parsers: `method-exact-cc3570c35117db82` matches Immersive
  Engineering and XNet, with related exact vertex parsing in Draconic
  Evolution. Keep only a specification and fixtures because the three
  repositories share fragments, not one proven failure contract.

Ars and Rechiseled bridge duplication is handled by the format-specific module
candidates above because third independent consumers and matching fixtures
exist. The Immersive Engineering bridge remains intentionally duplicated until
another wire consumer proves the same persisted topology, clipping, catenary,
and failure rules.

## No generic connected-texture engine

The generated family label `connected-texture-engine` contains 78 files across
11 add-ons, with 103 exact and 19 renamed method groups. That volume does not
justify a global selector.

Athena, Fusion, and CTM differ in resource schema, face-local neighborhood,
edge and diagonal rules, pane and pillar behavior, random or continuous
selection, texture-sheet layout, fallback policy, and format-version cadence.
A generalized selector would need consumer-specific conditionals and could
silently make distinct blocks fail in the same way.

The allowed common layer is limited to neutral face masks, neighborhood sample
records, coordinate transforms, deterministic mesh fixtures, and failure
contracts. Selection algorithms stay in `athena-resource-models`,
`fusion-resource-models`, and, once it has enough real consumers,
`ctm-resource-models`.

**Conclusion:** do not create `bluemap-addon-connected-textures` as a generic
production module.

## Recommended repository order

1. `bluemap-addon-toolkit`
   - Gradle conventions, test kit, verification CLI, gallery lifecycle, and
     reusable pinned workflows.
2. `bluemap-addon-runtime`
   - Pure activation, artifact identity, diagnostics, and profile-selection
     source compiled into consumers.
3. `athena-resource-models`
   - Exact Athena resource interpretation and strategy-tested mesh emission.
4. `fusion-resource-models`
   - Exact Fusion resource interpretation and format-specific mesh emission.
5. `bluemap-addon-render-core`
   - Only proven neutral lighting, records, transforms, and geometry helpers.
6. `installed-geo-resource-models`
   - After the three-consumer malformed-input and parity suite passes.
7. `bluemap-addon-adapter-api`
   - Design now, publish only after the 5.23 integration branch has a stable
     combined runtime gate.

`ctm-resource-models` remains specification/test-only until at least three
real consumers prove one format contract. A new shared source release is an
opt-in update for each add-on, not a reason to republish the whole portfolio.

## Classloader and packaging model

BlueMap loads add-on JARs through separate classloaders. Its add-on descriptor
can express required and soft add-on IDs but not dependency version ranges.
An ordinary companion library is therefore not automatically visible to a
consumer add-on, and a globally shared static cache would have ambiguous class
identity and lifecycle.

Use this initial packaging model:

1. Development tooling runs only during build and test. It is never installed
   beside BlueMap.
2. Production source modules are exact-version dependencies whose classes are
   compiled or merged directly into each consumer's production JAR. No nested
   JAR is shipped.
3. Each consumer retains its entrypoint, block-ID ownership, route allowlist,
   exact mod profile, and failure isolation.
4. Shared code keeps no cross-add-on singleton, registry, mutable cache, or
   class-identity assumption.
5. The JAR audit verifies the expected shared classes, notices, absence of
   nested dependencies, and unchanged server-only boundary.

A separately installed provider remains deferred. It would require a stable
ABI, explicit handshake, tests for both load orders, absent and incompatible
provider behavior, independent consumer version skew, reload, physical
removal, and combined failure isolation. The current 5.23 backport work makes
freezing that ABI premature.

## Licensing and provenance boundaries

The pinned repositories have 47 MIT top-level licenses. AE2, FramedBlocks, and
Powah use LGPL-3.0 variants; Botany Pots uses LGPL-2.1. Top-level license counts
do not replace file-level provenance.

Apply these boundaries to every extraction:

- Start a neutral module from the independently authored MIT origin. Do not
  copy an LGPL-marked downstream file into an MIT module and assume identical
  bytes authorize relicensing. An LGPL consumer may consume an MIT module.
- Keep FramedBlocks-derived geometry and AE2-derived or captured material out
  of a permissive neutral kernel.
- Preserve the full BlueMap MIT copyright and permission notice in Fusion and
  other emitters that adapt BlueMap renderer mechanics.
- Athena, Fusion, CTM, Geo, Wavefront, and OBJ interpreters may use installed
  resource formats and independently authored behavior, but may not
  redistribute upstream source, models, textures, archives, or generated
  resource closures.
- Keep candidate-specific algorithms in their own provenance boundary. A
  neutral module must not depend on a candidate mod or its client classes.
- Give every shared repository a top-level license, SPDX mapping, `NOTICE`,
  `THIRD_PARTY.md`, machine-readable provenance, source and binary JAR audits,
  and exact dependency pins.
- Re-run the relevant license review when moving code. Similarity is evidence
  of duplication, not evidence of origin or permission.

## Extraction validation sequence

For each module slice:

1. Freeze canonical fixtures and failure behavior in the existing consumers.
2. Extract the smallest passing clone cluster without consumer-specific
   conditionals.
3. Pin the exact module version and verify byte-reproducible consumer JARs.
4. Run every migrated child gate plus one untouched consumer as a control.
5. Run the full combined ATMons server suite with all add-ons present.
6. Render the affected galleries and compare geometry, UVs, lighting,
   translucency, connected faces, and stock fallback.
7. Test module absence where applicable and physical add-on removal.
8. Re-run the duplicate scan and record whether duplication fell without
   creating a broader ABI or licensing problem.

Migrate consumers in bounded cohorts. Do not update all 51 repositories in
one release wave.
