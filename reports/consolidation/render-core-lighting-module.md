# Render-core face-lighting extraction

This report records the fourth production-code extraction selected by the
ATMons 1.2.0 deduplication review. The module contains one proven seven-copy
face-lighting operation. It does not contain mesh emission, materials,
resources, profiles, registration, activation, or mod-specific policy.

Consumers pin the module as a Git submodule and compile its source into their
own add-on JAR. The standalone module JAR is publication evidence, not a server
component.

## Released module

The public
[`bluemap-addon-render-core`](https://github.com/jan-guenter/bluemap-addon-render-core)
repository released `v0.1.0-alpha.1` from merge commit
`faf53c9586a2c876b5a91db5ae3c2650a98f19ba`. Its signed annotated tag object
is `571b8986a34a38c751a25eadfdea739f2566bd40` and peels to that merge. The
main tree is `01dd0792b5402de3e4e3db02fb729c9095d376e2`; the exact production-source
tree consumers pin is `73870b3976ad3a17bf4bf350d9531b66d3d4a3af`.

Pull request [#1](https://github.com/jan-guenter/bluemap-addon-render-core/pull/1)
contains three owner-signed commits:

| Change | Commit |
| --- | --- |
| Initial extraction | `6fbba451a07170a4e60248123e91b8f6cc2a674a` |
| Release validation hardening | `20e22d25aec2e7b1d9d6919a4e794081cc9ee568` |
| Maven lookup correction and final feature head | `1ef73ea71bcf6a84ed062b566ab90ea7e7701596` |

PR CI run `33303484172` tested synthetic checkout
`ce5b3a85cd623e5b697ded9aedc73de65069ee3b`; its three jobs were
`99235775509`, `99235775601`, and `99235775639`. Artifact `9729722160` is
13,462 bytes with digest
`e14aed275eb8d7d9c857dea8db1aed4a1cc4a42b5d4b90de8cc3e027daf1b76a`.
Exact-main run `33303774474` used jobs `99236574890`, `99236574953`, and
`99236574956`; its 13,462-byte artifact `9729815005` has digest
`a898ccc35821508bbcf6993d863f867ac675cda4c81556654f19a42e49029343`.
Release run `33303785361` passed.

The published files reproduce the reviewed release bundle:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Production JAR | 8,404 | `84ba3cead60069889c2c70f96c8fdd40206f4e1db8dae4a2efdd9f6467b39f01` |
| Sources JAR | 6,813 | `d049fdc78d90ad16694a479079d708e4931910b6b34881b40f047d112da6ecaf` |
| POM | 1,603 | `cfdcb1850ad1e9da642b36c9ad1b6b4c7d01641ad31301e89040c902148f8a21` |
| Gradle module metadata | 2,849 | `9cee0a97c2b4bb928b5f3471fc51c0132edd802bcdb31da954c3cc5c146d7c6f` |
| `SHA256SUMS` | 456 | `cbaaad1adf4ee48ccf4cbbda67181495dcf093920f95586a09bed0ef0486eaa6` |

The Java 21 publication metadata declares no production dependency. Its source
compiles against the exact pinned BlueMap 5.22 internals. Its package is
`io.github.janguenter.bluemap.addon.render.core.adapter.bluemap522`, which
makes the BlueMap adapter version explicit. The production archive has no
BlueMap add-on descriptor, service entrypoint, nested JAR, module descriptor,
or server-loadable component.

## Extraction result

The pilot moves the exact `FaceLighting` source from Chipped, LaserIO, and
Pipez. The consumers remove three files containing 127 lines and 4,244 bytes.
The module owns one 43-line, 1,455-byte file. The repository-source reduction
is two files, 84 lines, and 2,789 bytes.

The API samples four adjacent blocks around a face and returns the exact
four-corner light values used by the existing emitters. Consumer-specific
positions, materials, culling, geometry, routing, and fallback remain local.
Package-normalized source and bytecode comparisons proved the relocated class
and affected callers equivalent. Each consumer also retained its exact gallery
archive and rejected an uninitialized, dirty, wrong-HEAD, wrong-index, or
source-tree-mismatched module checkout.

## Signed consumer candidates

| Add-on | Baseline main | Signed candidate | Candidate tree | Version |
| --- | --- | --- | --- | --- |
| Chipped | `cc5ab1b2af6e447db775f12e659d3dea980350cb` | `28f22a0c5417514fa27be47595a19a9c8bc7e45d` | `15d6b82dd5c3945bc06e34caba84e6826621f696` | `0.1.0-alpha.3` |
| LaserIO | `e18f93588eacd3a188190a0318b32f11a038f798` | `050d62ed92ea030b4baf947cf9b95a8c4f22fcf1` | `984a8b0393c993d8d239941364138e694750d9a5` | `0.1.0-alpha.3` |
| Pipez | `e1ffb394cec4e9860433f7c187b3d09afb6e30b3` | `03350a757e5337264c60242376bf34669ed1a538` | `f07b9bb5cbdb468ca1f51c29e4e9e1e1ee884a75` | `0.1.0-alpha.2` |

Each candidate pins module commit
`faf53c9586a2c876b5a91db5ae3c2650a98f19ba` and source tree
`73870b3976ad3a17bf4bf350d9531b66d3d4a3af`. Complete Java 21 candidate
gates, archive accounting, deterministic galleries, trust probes, and an
independent audit passed before combined testing.

## Combined integration gate

The local override lock has SHA-256
`2ee21fca06964440fc0b9737ecefd0dc52a02ef0239f5266acb1f4b8a75ae41a`.
It bound the three signed candidates without changing the immutable
`atmons-1.2.0` compatibility manifest. The resulting 51-add-on evidence was:

- candidate manifest: 86,678 bytes, SHA-256
  `6b03bf5d9f466a5a197666bffd5072bd2c1ad1aa195bf917300ca0bb423059d0`;
- 51-row checksum manifest: 5,663 bytes, SHA-256
  `9c14111c2fdf83f96f178a806d348d6dfedb6bf7a15e847dd29ec8995492f948`;
- candidate JAR inventory: 51 JARs and 9,050,979 bytes, normalized SHA-256
  `7080ad5ea6fcc4c94f2737687a858a2685a6776ba025cb0341b3e4177d578d46`.

The disposable ATMons 1.2.0 server reported all 51 activation markers on both
boots. The controlled restart changed the retained `7bdf...` container
identity to `5588...`, then repeated the runtime, pack, activation, overlay,
and gallery-composition attestations. All 51 gallery builds and immediate
assertions passed. None failed, skipped, or ran without an assertion.

The run began at `2026-08-30T09:52:17Z` and finished at
`2026-08-30T10:11:46Z`. Its 75,748-byte result has SHA-256
`d029450aaef444e6f9f9dacee90f0ad7a330d95780f4ccb530795d00e746d943`.
Raw logs, container identities, the world, and credentials remain untracked.

## Consumer publications

The feature, synthetic pull-request checkout, final main merge, and signed tag
are distinct identities:

| Add-on | Reviewed PR | Synthetic PR checkout | Final main merge | Signed tag object |
| --- | --- | --- | --- | --- |
| Chipped | [#6](https://github.com/jan-guenter/bluemap-chipped-addon/pull/6) | `8b27e244cd8de0d8cc3208f14b36d27f70f2c49b` | `81d0b48dc1043136176caa78affeeab0fd3511b4` | `cdb6a0c308f2e892f13fb3380bc99f568c79a261` |
| LaserIO | [#7](https://github.com/jan-guenter/bluemap-laserio-addon/pull/7) | `92fc4c3e30a02e6c875820ead3123083ac3ef84c` | `72e2855e96aa759212ce381b8c05c437487ba9ae` | `a71d12abf7bd22ef80e4a8c670feb5962efcd077` |
| Pipez | [#5](https://github.com/jan-guenter/bluemap-pipez-addon/pull/5) | `b78de6b13ae6fdf4023d8e2b471b4e16e211f1b` | `8b14c6ff8fff48ebf74dc87430184d522f37bf96` | `f8e6bd664401b189bc85aa349713579593a9ab93` |

| Add-on | PR CI / artifact | Exact-main CI / artifact | Release workflow |
| --- | --- | --- | --- |
| Chipped | `33304810740` / `9730122281` | `33305922117` / `9730465680` | `33306044303` |
| LaserIO | `33304229733` / `9729960562` | `33305921981` / `9730479245` | `33306043888` |
| Pipez | `33304443028` / `9730007041` | `33305921932` / `9730465244` | `33306044022` |

The signed Chipped and LaserIO `v0.1.0-alpha.3` tags and Pipez
`v0.1.0-alpha.2` tag peel to the final merges above. All release assets passed
their checksum manifests and tag-scoped provenance checks:

| Add-on | Production JAR | Sources JAR | POM | Gradle module metadata |
| --- | --- | --- | --- | --- |
| [Chipped](https://github.com/jan-guenter/bluemap-chipped-addon/releases/tag/v0.1.0-alpha.3) | 601,011 B `b5a1e7184f98ebea44fc085fcc5dfcd54096fafae9ae158915476b33df1f9cac` | 559,912 B `02e43090ca15ef9f48b58a306b186e9976b55cd64ed7a8ee6109398b6a2e267b` | 1,341 B `cd27953c5fe1b3d184fc6d1d07226cbdc826e7bfb95d887f084517d57c2a2b9b` | 2,820 B `52b856089a9e4d6ac0287c8f3e31d3cfeb44a75aa05b91fd831504e9a9240d09` |
| [LaserIO](https://github.com/jan-guenter/bluemap-laserio-addon/releases/tag/v0.1.0-alpha.3) | 113,607 B `0be9ddacdac5a11a15e608605562d8f49b142585d1ec605ad7278b14e89a17a2` | 76,502 B `9a181222cc2239f6be3db569cf45bb1d652811076b27dd1b8c5cd7cdf8b5150b` | 1,317 B `381e3b507c3e3887a7d22b61b80c3d36ce56f3ae8004fd138db38182cac5844c` | 2,819 B `436a6f849ca6ac6e393735ddf35be1b3299114900c0ee8c2a4017146cb1f9f5c` |
| [Pipez](https://github.com/jan-guenter/bluemap-pipez-addon/releases/tag/v0.1.0-alpha.2) | 55,373 B `73d27be8dac93b1cccd619ed0bc560847e636b175199ae1a8509b092228384c3` | 31,288 B `27ca39580b4dc84fe2215137db31e282449595456176c399f2efee89f9e679a9` | 1,339 B `8d970a81c7b811661707ad3ddd116cde4a814872cce505798e927d3f76ddf84a` | 2,803 B `cebe346c50698a0e4aa2b2a4126eb457bc2090cebf87b4763fd3178df847c287` |

Their `SHA256SUMS` identities are Chipped 448 bytes /
`fbf7218dcecacdca9636de0bc24a4753130a7949e7d1fb4cf8aecc7207e8537b`,
LaserIO 440 bytes /
`4fd65329f81bdc14ee654b360a95bf844f4032303586ab388ea1cad9c7bf6c2b`,
and Pipez 440 bytes /
`6a5c3edb86142b05d64033e19932e89d47c650aeb9d593dd8f57ad0c1a5d6985`.
All three workflows published public Maven versions. The Chipped and Pipez
workflows re-read the exact Maven bytes and sidecars. LaserIO's publish step
passed and public package metadata confirms `0.1.0-alpha.3`, but the local
token received HTTP 401 when reading its package bytes. This report therefore
does not claim a separate byte comparison for that Maven version.

## Remaining boundary

CobbleFurnies, Integrated Dynamics, Powah, and Sophisticated are the remaining
members of the original seven-copy cohort. They need independent migration and
archive gates before they pin the module. The Ars, Chisel and Factory Blocks,
and Nature's Aura and Tempad lighting cohorts remain separate. The module still
does not justify shared mesh emission or a general rendering engine.

The immutable `atmons-1.2.0` compatibility tag and manifest remain unchanged.
These later compatible releases can be selected by a future compatibility
snapshot; they do not rewrite the published 1.2.0 snapshot.
