# BlueMap add-on portfolio consolidation: ATMons 1.2.0

This records the repository and source-style consolidation performed against
the exact 51 add-on commits pinned by `versions/1.2.0/manifest.json`. It does
not move the immutable `atmons-1.2.0` tag or change a released artifact.

## Baseline

The initial audit covered 4,001 tracked files, including 1,194 production Java
files and 495 Java test files. All 51 repositories already used Java 21,
UTF-8 compilation, `-Xlint:all`, `-Werror`, reproducible archives, LF source,
and full-SHA workflow action pins. All 102 workflows passed `actionlint`.

The material structural drift was:

- three Checkstyle rule generations across 47 repositories and no Checkstyle
  integration in Create, Crystalix, Mekanism, or Oritech;
- missing `AGENTS.md` in Oritech and Powah;
- missing `.gitattributes` in Logistics Networks and RFTools Builder;
- several missing release guides;
- repeated but legitimately specialized build, release, gallery, provenance,
  and exact-artifact gates.

The audit did not add meaningless placeholder tests to the four repositories
without Java tests, and it did not replace family-specific exact-input gates
with a weaker generic build.

## Common contract

The versioned `addon-v1` contract now owns:

- UTF-8 and LF source, no tabs or trailing whitespace, final newlines, and a
  120-character non-import Java line limit;
- four-space editor defaults without mass-reindenting sealed release source;
- one Checkstyle 10.18.2 ruleset;
- the required repository, documentation, gallery, provenance, workflow,
  Gradle, and add-on metadata shape;
- Java 21, compiler warning, reproducible archive, and full action-pin checks;
- a clean-worktree migration tool and a read-only portfolio checker.

Exact mod pins, artifact identities, add-on metadata, namespaces, activation
routes, renderers, galleries, licenses, and provenance remain family-owned.

## Source-preserving rollout

Each add-on received an independent `feature/addon-v1-conventions` pull
request. The rollout changed only managed repository files and the four
missing Checkstyle build hookups. It changed no Java source, add-on version,
release tag, compatibility manifest entry, or production resource.

The rollout gates were:

- 51 of 51 candidate worktrees passed the repository-contract checker;
- all 1,689 production and test Java files passed the canonical Checkstyle
  scan;
- all worktrees passed `git diff --check` and an explicit no-Java-diff gate;
- Create, Crystalix, Mekanism, and Oritech passed `clean check build` against
  the exact BlueMap 5.22 source and reproduced their accepted production-JAR
  seals after Checkstyle was added;
- the complete meta-repository validation, installer, integration tooling,
  scanner, convention tests, workflow lint, and Java 21 harness build passed.

Published tags and the compatibility manifest continue to identify the exact
accepted release commits and JARs. Tooling-only commits on child `main`
branches are not silently substituted for those release identities.

## Toolkit verifier extraction

The first extraction slice is complete. The public development-only toolkit
is pinned by exact gitlink and wheel identity, and all 24 members of the two
byte-exact verifier cohorts now consume it. Each tooling-only PR passed its
isolated release-candidate gate without changing renderer source, tests,
galleries, provenance, versions, accepted seals, or tags.

The [rollout record](toolkit-verifier-rollout.md) lists every reviewed PR and
merge commit. It records the removal of 48 duplicate scripts and 5,280
physical lines, with a net cohort reduction of 4,631 lines after adding the
immutable dependency pins and setup documentation.

Toolkit `v0.2.0-alpha.1` adds the narrowly scoped Java build convention. Its
first four-consumer [artifact-parity pilot](toolkit-gradle-convention-pilot.md)
passed both portfolio Gradle versions and reproduced every accepted JAR,
sources JAR, POM, module file, and Create gallery ZIP byte for byte.
The [second cohort](toolkit-gradle-convention-cohort-2.md) applies the same
gate to Chipped, Chisel, CobbleFurnies, and Glassential.
The [third cohort](toolkit-gradle-convention-cohort-3.md) applies the same gate
to Trophy Manager, Laser Bridges, More Red, and Lootr.
The [fourth cohort](toolkit-gradle-convention-cohort-4.md) applies it to XNet,
LaserIO, Little Big Redstone, and Nature's Aura.

Toolkit `v0.3.0-alpha.1` closes the v0.2 checker gap for migrated consumers.
The exact applied convention now satisfies only its eight owned build checks;
the three consumer-owned plugin checks remain mandatory. The
[v0.3 contract consolidation](toolkit-v0.3-contract-consolidation.md) makes
that pinned toolkit the meta repository's single source for the checker,
migrator, and managed templates.
The [fifth cohort](toolkit-gradle-convention-cohort-5.md) applies that v0.3
contract to Tempad, Productive Metalworks, Productive Bees, and Railcraft
Reborn with exact artifact, gallery, PR CI, and post-merge CI parity.
The [sixth cohort](toolkit-gradle-convention-cohort-6.md) applies the same
contract to Theurgy, Draconic Evolution, PneumaticCraft, and Ars Nouveau with
the same complete parity boundary.
The [seventh cohort](toolkit-gradle-convention-cohort-7.md) applies it to
Extreme Reactors, Ars Creo, Ars Energistique, and Ars Technica while retaining
their multi-artifact admission and installed-resource contracts.
The [eighth cohort](toolkit-gradle-convention-cohort-8.md) applies it to Camol,
Integrated Dynamics, Oritech, and Mekanism while preserving exact multi-input
admission, gallery behavior, and publication-versus-acceptance boundaries.
The [ninth cohort](toolkit-gradle-convention-cohort-9.md) applies it to
Crystalix and Powah while retaining their distinct gallery and owner-acceptance
evidence boundaries.
The [tenth cohort](toolkit-gradle-convention-cohort-10.md) updates the toolkit
trust identity for Pipez, Create, Supplementaries, and Connected Glass. Both
toolkit commits contain the same Gradle convention tree, so this cohort changes
checker and trust tooling without changing effective Gradle behavior.
The [eleventh cohort](toolkit-gradle-convention-cohort-11.md) applies the same
trust-only update to Chipped, Chisel, CobbleFurnies, and Glassential while
retaining their exact public artifacts and deterministic gallery packages.
The [twelfth cohort](toolkit-gradle-convention-cohort-12.md) moves Trophy
Manager, Laser Bridges & Doors, More Red, and Lootr to the v0.3 trust commit
and hash-locked wheel while preserving all release and gallery bytes.
The [thirteenth cohort](toolkit-gradle-convention-cohort-13.md) completes the
v0.3 trust migration for XNet, LaserIO, Little Big Redstone, and Nature's Aura;
XNet and Nature's Aura also adopt the corrected repository checker.
The [fourteenth cohort](toolkit-gradle-convention-cohort-14.md) begins the
remaining inline-consumer migration with Factory Blocks, Functional Storage,
Logistics Networks, and Rechiseled while preserving their exact outputs.
The [fifteenth cohort](toolkit-gradle-convention-cohort-15.md) continues that
migration with Modular Routers, Rechiseled Create, Cobblemon Stone Statues,
and Botany Pots under the same exact artifact and gallery parity boundary.
The [sixteenth cohort](toolkit-gradle-convention-cohort-16.md) covers
SecurityCraft, RFTools Utility, Immersive Engineering, and Immersive
Energistics. It retains their exact input matrices, publication files,
galleries, CI checkout identities, and release tags.
The [seventeenth cohort](toolkit-gradle-convention-cohort-17.md) closes the
rollout with Sophisticated, FramedBlocks, and AE2. AE2's repository policy
required a linear GitHub rebase. The reviewed feature is owner-signed, while
that migration's rebased main commit is unsigned but has exactly the reviewed
tree. A later workflow-only de-duplication squash is GitHub-signed and retains
the same release artifacts. The report keeps all of those identities
separate.

All 51 add-on repositories now use the v0.3 source-distributed Gradle
convention. Forty-nine are covered by the pilot and numbered cohort reports;
EnderIO and RFTools Builder completed equivalent standalone migrations. Every
adoption retained the consumer's exact inputs and accepted outputs. The
convention work changed no compatibility pin or released add-on.

## Deduplication result

Scanner v2 analyzed 2,887 eligible files and 29,115,561 bytes. Its Java pass
found 45 exact and 47 identifier-renamed whole-file groups, plus 374 exact and
195 renamed method groups. Its syntax-aware pass parsed 9,479 Python, Gradle,
GitHub Actions, and shell units, admitted 8,508 to grouping, and found 265
exact plus 9 conservative local-renamed groups.

The generated [clone inventory](../deduplication/atmons-1.2.0.md) and
[semantic review](../deduplication/atmons-1.2.0-review.md) establish this
extraction order:

1. `bluemap-addon-toolkit`, development-only and version-pinned;
2. `bluemap-addon-runtime`, bundled as source into each consumer rather than
   installed as a shared JAR;
3. separate `athena-resource-models` and `fusion-resource-models` modules;
4. the narrow `bluemap-addon-render-core`, whose completed first pilot moves
   the exact face-lighting API into Chipped, LaserIO, and Pipez;
5. `bluemap-installed-geo-resource-models`, whose three-consumer suite covers
   static models and sampled poses;
6. `bluemap-addon-adapter-api` only after BlueMap 5.23 has a stable combined
   runtime gate.

The scan rejects a generic connected-texture engine. Athena, Fusion, and CTM
have different formats and failure contracts. It also rejects an installed
shared runtime for now because BlueMap's separate add-on classloaders do not
provide a safe version-range or class-identity contract.

## Runtime module extraction

The first production-code extraction now has a published module. Public
[`bluemap-addon-runtime` `v0.1.0-alpha.1`](runtime-artifact-detection-module.md)
contains only the package-neutral, JDK-only artifact pin and exact detector.
Its release commit is
`6c062239f2669de9d20da32dc8b5372a5653b19d`. Consumers compile the pinned
module source into their own add-on JARs; server administrators do not install
the standalone module.

LaserIO, More Red, and Little Big Redstone passed their complete isolated
gates, archive accounting, unchanged galleries, trust probes, independent
final audit, two 51-add-on overlay reproductions, a controlled second server
restart, all 51 activation checks, and all 51 gallery assertions. Their signed
`0.1.0-alpha.2` candidates then passed PR CI and independent exact-main CI,
were merged with explicit two-parent commits, and were published as signed,
attested public prereleases. The exact identities are recorded in the
[runtime module report](runtime-artifact-detection-module.md).

## Athena and Fusion resource-model extraction

The next two production modules remain format-specific. Public
`bluemap-athena-resource-models` and `bluemap-fusion-resource-models`
`v0.1.0-alpha.1` releases contain only their proven neutral selection and
orientation types. Consumers pin the exact module commits and compile their
sources into each add-on; neither module is installed on the server.

Chipped, Chisel, CobbleFurnies, Connected Glass, and Rechiseled removed 20
consumer-local production sources while retaining every consumer-specific
profile, resource closure, route, fallback, emitter, and gallery. Their signed
`0.1.0-alpha.2` candidates passed exhaustive differential and archive gates,
one combined 51-add-on cold-restart run with 51 successful gallery assertions,
PR CI, exact-main CI, signed-tag publication, release checksum verification,
and JAR attestation verification. The exact evidence is recorded in the
[Athena and Fusion resource-model report](athena-fusion-resource-models.md).

## Render-core face-lighting extraction

Public `bluemap-addon-render-core` `v0.1.0-alpha.1` contains the proven
BlueMap 5.22 face-light sampler and no mesh emitter, resources, profiles, or
installed runtime. Its release commit is
`faf53c9586a2c876b5a91db5ae3c2650a98f19ba`. Consumers compile the exact
pinned source into their own add-on JARs.

Chipped, LaserIO, and Pipez removed their local copies while retaining their
renderer policy and accepted galleries. Their candidates passed isolated
build, archive, bytecode-parity, trust-probe, and independent audit gates. A
combined two-boot ATMons 1.2.0 run then verified all 51 activation markers and
all 51 gallery assertions. The three candidates passed PR CI and exact-main
CI and were published under signed, attested tags. The exact module, consumer,
artifact, and runtime identities are recorded in the
[render-core report](render-core-lighting-module.md).

## Installed GEO resource-model extraction

Public `bluemap-installed-geo-resource-models` `v0.1.0-alpha.1` contains the
bounded Bedrock GEO 1.12.0 compiler, immutable mesh model, and optional
per-bone pose input. It contains no installed assets, model names, resource
paths, add-on registration, or consumer policy. Consumers pin the exact
module commit and compile its source into their own add-on JARs.

Ars Technica and Ars Nouveau removed their local compiler and model copies.
Ars Creo exercises the sampled-pose path while retaining its animation parser
and wheel renderer. All three published signed, attested `0.1.0-alpha.2`
releases after exact ordered-mesh, archive, gallery, PR CI, and exact-main
gates. The exact module, consumer, artifact, and cumulative runtime identities
are recorded in the [installed GEO report](installed-geo-resource-models.md).

The immutable `atmons-1.2.0` tag, `versions/1.2.0/manifest.json`, installer
metadata, and pinned add-on gitlinks remain unchanged. These compatible later
releases are consolidation evidence for a future snapshot.
