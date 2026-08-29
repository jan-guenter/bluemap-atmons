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
4. a narrow `bluemap-addon-render-core`, beginning with the exact seven-copy
   face-lighting API;
5. provisional `installed-geo-resource-models` after a three-consumer parity
   suite;
6. `bluemap-addon-adapter-api` only after BlueMap 5.23 has a stable combined
   runtime gate.

The scan rejects a generic connected-texture engine. Athena, Fusion, and CTM
have different formats and failure contracts. It also rejects an installed
shared runtime for now because BlueMap's separate add-on classloaders do not
provide a safe version-range or class-identity contract.
