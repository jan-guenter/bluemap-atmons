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
