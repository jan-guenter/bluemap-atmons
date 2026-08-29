# Shared Gradle convention pilot

This records the first artifact-parity adoption of the BlueMap Add-on Toolkit
Gradle convention. It changes development tooling only. It does not update the
ATMons 1.2.0 compatibility manifest, any add-on version, or an accepted release
tag.

## Toolkit release

The source-distributed convention is published in
[`v0.2.0-alpha.1`](https://github.com/jan-guenter/bluemap-addon-toolkit/releases/tag/v0.2.0-alpha.1).

| Identity | Value |
| --- | --- |
| Release commit | `f58da04567f10efe615c582797f3ab00b7a7343f` |
| Signed annotated tag | `v0.2.0-alpha.1` |
| Wheel | `bluemap_addon_toolkit-0.2.0a1-py3-none-any.whl` |
| Wheel size | 19,827 bytes |
| Wheel SHA-256 | `cbfbad7ea12ea631b9f36a5261482dde3ca4d8f270df1b5faf75310020b115f9` |

The release gate passed exact Gradle 9.4.0 and 9.6.1 fixtures, two clean
byte-reproducibility builds, Python 3.11/3.14 tests, source/wheel boundary
audits, clean-wheel installation, and build-provenance attestation. A real
nested-submodule test also proved that the consumer preflight accepts only the
committed gitlink and rejects a dirty toolkit, a different toolkit HEAD, or a
different declared pin before consumer tasks run.

The plugin owns only Java 21 toolchains and sources variants, compiler flags,
reproducible archive flags, JUnit Platform selection, and conditional
Checkstyle configuration. Repositories, dependencies, coordinates, manifests,
compression, debug metadata, publications, galleries, and release behavior
remain consumer-owned.

## Pilot merges

The cohort deliberately covers different accepted build shapes and both
portfolio Gradle versions.

| Add-on | Reviewed PR | Merge commit | Gate |
| --- | --- | --- | --- |
| Pipez | [#3](https://github.com/jan-guenter/bluemap-pipez-addon/pull/3) | `adafc5e683198edc025c001ef8b3dea270261880` | Gradle 9.4.0 full candidate gate |
| Create | [#3](https://github.com/jan-guenter/bluemap-create-addon/pull/3) | `aa9fe263faeaf3fc85d689a0c3e4b1ca0da08251` | Gradle 9.6.1 plus gallery ZIP |
| Supplementaries | [#4](https://github.com/jan-guenter/bluemap-supplementaries-addon/pull/4) | `cabfb0a740d4eb843a7e0389e6744acf1fa45b13` | Gradle 9.6.1 accepted-release gate |
| Connected Glass | [#3](https://github.com/jan-guenter/bluemap-connectedglass-addon/pull/3) | `4f36d14943b15d6e650f4ff4bd12037f9bb9e064` | Gradle 9.6.1 exact-artifact/profile gate |

Every merge is a two-parent merge whose tree equals its reviewed PR head. All
four GitHub CI builds passed. Each consumer pins the toolkit with a mode-160000
gitlink and the same explicit commit in `settings.gradle`; CI and release
checkouts initialize recursive submodules without stored credentials.

The four build files replaced 118 repeated convention lines with four plugin
applications. The consumer-owned trust preflight is intentionally repeated:
the included plugin cannot safely authorize its own source checkout.

## Artifact parity

The complete consumer gates reproduced these accepted files byte for byte.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Pipez | `e81dea280d08e19ea4602e5a0700f4ab7004ca74e3408bfba3a898cb745e67db` | `e15cd1e987fefb0433a8c3ab2b8bb5d7f8a3901f586c91a9a6dbfa76fbdf1ae1` | `83a20b47360cd35aef83fdee06567c2bae2a6587cd225c08b301e522bdfe5ce0` | `8b5504702e56f2ca0c324fe05a11dd60acaa219f297fa9a84266327e8c410d4a` |
| Create | `e9e860ff0a3cc3398090d03f36441a9df863ec96c0c5e6da408815a1f9c1cd05` | `c795af0a4082da8af8dc3e653836c6a8cba8b2825094cd6e1b2ab7926bed6bec` | `e747a3d8ce0b52e5621ec13ef69ac21bfad00ca74b02504a0c5ff3b9592eeb7f` | `a7fbf84d73c5c8941792f404dbab86d79849bf51eb8ed228ff4a5c6735fd4d08` |
| Supplementaries | `7559ec3eff162a279a1a3ba1ce4b061d0ed2ff6726e016614ed0973cc407e5da` | `bf0bcd6ae6edf884ac9ee70d71b8c8ad02fa8414a7223726d55598ab21d803ad` | `b664b59c2e04d60e1f6857ddb366e70e030c463b10b02d989aa022f80f03d795` | `63cc651c48816d2b5cb9c79ec3e4f6b4223e5e53c2909080cfca2040a10af381` |
| Connected Glass | `eb1dc07a6f9906f83a710e175cb8c119f0464bda73f651fa13a6e24900ffb70e` | `a2f65dd74c439ab6b1152db6e3255a7f4d282b4870b56c0c8e7f1ee65f2999f9` | `87489782df3acdad2046243d840bb4f1d81cf5cf685298f66072f6b883d0dc38` | `209c4f441d9e2e5a3eb0da13a136c955d54de7cc09875bb677317a2aed6c1c8b` |

Create's gallery ZIP also remained byte-identical at
`640863b2370550bd2cfd9ca867a49f3c46b5e12a8be8bf9a39fcdea0c3313332`.
The Connected Glass dependency graph and outgoing variants were unchanged;
its consumer task set was unchanged apart from the expected included-build
tasks that compile the convention plugin. Supplementaries retained its debug
metadata and STORED archive compression.

## Result

The pilot supports a bounded next cohort. It does not justify a blind
portfolio-wide rewrite: each consumer still needs its own exact inputs,
complete gate, and accepted-artifact comparison. Reusable workflows, gallery
schemas, and production Java remain separate future extraction decisions.
