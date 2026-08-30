# Shared Gradle convention cohort 9

This records the ninth artifact-parity adoption of the BlueMap Add-on Toolkit
Gradle convention. It changes development tooling only. It does not update the
ATMons 1.2.0 compatibility manifest, meta-repository gitlinks, add-on versions,
existing release tags, provenance, galleries, or renderer behavior.

## Scope

The cohort contains Crystalix and Powah. Both repositories pin toolkit
`v0.3.0-alpha.1` at commit
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` with a mode-160000 gitlink and the
same explicit trust pin in `settings.gradle`. The corresponding 20,585-byte
Python wheel has SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
Crystalix pins the hash-locked toolkit CLI/version check; Powah does not
acquire an unnecessary Python build dependency.

Each validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact inputs were:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Crystalix | Crystalix 3.0.0 | 817,004 | `42f97cf776cff8261bf671e64a333bbec65a8bf28e519d39cd958e0af9848e6c` |
| Crystalix | Fusion 1.3.12 | 923,270 | `17f5215648a98bcde4134577b013200dbf363273ae282449c51408ae8346f2fa` |
| Powah | Powah 6.2.10 | 2,737,991 | `0e604a7356111c1dd44a00ea42fc1aa960d9faeb978261349df1138fcee4d0b4` |

## Reviewed merges

| Add-on | Reviewed PR | Feature commit | Merge commit | Merge tree |
| --- | --- | --- | --- | --- |
| Crystalix | [#3](https://github.com/jan-guenter/bluemap-crystalix-addon/pull/3) | `e2daf51af1d31b1094584807543a42ad8f2d6b37` | `495dad97f787c92410dbc7be137b0093656e557b` | `955f74b0de0a0c4d68f80f07a6503bedf3cb3e24` |
| Powah | [#3](https://github.com/jan-guenter/bluemap-powah-addon/pull/3) | `25c04d0cc72ad0c5e711a732bbc39fb53fafe88b` | `7959b399ca57ea467eeabceed0fa30d3a165d2b1` | `b2b56b4ada86414157219cd0e462f5f2b3bb2d72` |

Crystalix was reviewed against base
`08353bef03d790ad20958dddf4de92b0ba748e69`; Powah was reviewed against base
`0631a9d07a6d6d6c00cdb299b29c997c24c6b014`. Every merge has its reviewed base
and feature commits as its two parents, its tree equals the reviewed feature
tree, and GitHub verifies the signatures.

The exact-head PR and post-merge `main` CI runs passed:

- [Crystalix PR CI](https://github.com/jan-guenter/bluemap-crystalix-addon/actions/runs/33281336679),
  job `99176901506`, artifact `9723098438`, and
  [main CI](https://github.com/jan-guenter/bluemap-crystalix-addon/actions/runs/33281574732),
  job `99177510590`, artifact `9723166492`; and
- [Powah PR CI](https://github.com/jan-guenter/bluemap-powah-addon/actions/runs/33281141999),
  job `99176404709`, artifact `9723032029`, and
  [main CI](https://github.com/jan-guenter/bluemap-powah-addon/actions/runs/33281226222),
  job `99176623696`, artifact `9723054532`.

No migration triggered a release workflow. Existing annotated release tags
remain on their publication commits:

| Add-on | Version | Tag object | Peeled release commit |
| --- | --- | --- | --- |
| Crystalix | `0.1.0-alpha.1` | `852bd08ca4df12cbb9b4091811a56703c98e541c` | `b60a3fecb809fbaefb3347500d75b5d453cfe14a` |
| Powah | `0.1.0-alpha.1` | `68151b88ce742ed0bad1dc026f8ce85f13022906` | `7ad05e80ed70152fcf48c92c6c32de3f6d815667` |

## Artifact, gallery, and acceptance parity

The complete consumer gates reproduced these files byte for byte before and
after each migration. Downloaded PR and post-merge CI outputs match the same
published bytes.

| Add-on | Output | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Crystalix | Production JAR | 47,389 | `512e02fda272a1c6809fb6c30ee3958cdf13fb87e531b23355069f177458721b` |
| Crystalix | Sources JAR | 20,119 | `fa853715534386d81ff40817efe70e0659975525eb0e19dddd6f5958d187d14d` |
| Crystalix | POM | 1,341 | `9a65c17ece50a7a846eb8fc9c0c7657600fefd4dbec5c87988a357245b26d2b1` |
| Crystalix | Module metadata | 2,831 | `0a629567fd9cf2b1dfc7d33d82c7b57ea2d02cc3f4422e757abc015261a5c6ef` |
| Powah | Production JAR | 36,572 | `0b370dfcd5d8c0a5844dd920d60a2cdb74ed441d87ff038382d8292c374686c8` |
| Powah | Sources JAR | 17,738 | `0bb0f1b4de0afa236239df2f17e61dd539417c4b8c40228ccd4ee433dffbd9b6` |
| Powah | POM | 1,371 | `be150f0dea9cf4a738ae946b33066fc7050b9a5cb15f1f86ab2e5fc9c36884c9` |
| Powah | Module metadata | 2,803 | `afc8631708e03d7df5b3841363270e95137e2654deaada498199232228a247b9` |

Crystalix has a manual source-only gallery whose unchanged tree is
`c753e3a41c62414946e19b6ebe8e902e5ba95a43`; there is no gallery ZIP identity.
Powah's unchanged gallery tree is
`1ae7525d2baf09e7e506de12853b1c68fbc4349d`, and its deterministic 3,171-byte
gallery ZIP retains SHA-256
`fa7c2a7f62765358bbf89375cc0ab1556aadb7cb445d0d207feebf0b5e81ddb2`.

Powah's first-party workspace ledger explicitly records owner visual
acceptance for the immutable published bytes. Crystalix's public publication
and provenance are independently verified, while owner acceptance is recorded
only in first-party workspace dossier, later release-ledger, and changelog
prose. Crystalix has no machine-readable acceptance record or retained staging
evidence, and an older stale implementation field still says pending. This
report therefore does not present Crystalix owner acceptance as
machine-verified or invent an acceptance seal.

## Build-contract parity

Dependency trees, outgoing variants, normalized consumer task surfaces, and
sorted release dry-run sets remained unchanged. Crystalix retains 21 release
tasks and Powah retains 29. Each full migrated build adds only four actionable
tasks from compiling the included convention plugin: Crystalix moved from 29
to 33 and Powah from 35 to 39.

Dirty toolkit worktrees, a checkout at toolkit v0.2, and wrong release tags
were rejected before promotion. After the probes, every toolkit checkout was
restored clean at the exact v0.3 gitlink.

The migration removes 56 repeated convention lines and adds two plugin
applications, a net reduction of 54 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Crystalix | 157 | 127 | 30 lines |
| Powah | 147 | 123 | 24 lines |

Consumer-owned dependency, publication, manifest, gallery, packaging, debug,
input-pin, and release configurations remain local. The consumer-owned
trust preflight remains repeated because an included plugin cannot authenticate
the source checkout from which it is loaded.

## Result

The ninth cohort confirms the v0.3 convention across one two-input exact-profile
consumer and one gallery-bearing consumer without changing published
artifacts, galleries, release identities, acceptance evidence, or renderer
behavior. Further adoption remains a repository-by-repository migration with
exact inputs, a frozen baseline, the complete local gate, artifact comparison,
reviewed PR CI, and post-merge `main` CI.
