# Shared Gradle convention cohort 16

This report records the sixteenth artifact-parity adoption of the BlueMap
Add-on Toolkit Gradle convention. The migrations changed development tooling
and, for Immersive Engineering, the matching build instructions. They did not
change the ATMons 1.2.0 manifest, meta-repository gitlinks, renderer sources,
resources, profiles, provenance, galleries, acceptance records, add-on
versions, or published releases.

## Scope

The cohort contains SecurityCraft, RFTools Utility, Immersive Engineering, and
Immersive Energistics. Each repository pins toolkit `v0.3.0-alpha.1` at commit
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` with a mode-160000 gitlink and the
same consumer-owned trust preflight in `settings.gradle`.

SecurityCraft consumes the source-distributed Gradle convention directly.
The other three repositories also replace their development-only toolkit
`v0.1.0-alpha.1` wheel with the 20,585-byte `v0.3.0-alpha.1` wheel, SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
No toolkit file becomes an installed dependency or packaged add-on entry.

Every validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact candidate inputs were:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| SecurityCraft | SecurityCraft 1.10.2.1 | 5,193,371 | `75ac9e73c60caf58df7069f167dbacc00a640e1418207dff654f56a5fdb5f229` |
| RFTools Utility | RFTools Utility 1.21-7.0.12 | 1,434,987 | `1fdbf7505c6d6f4ef93b8b15961c9c1a6a4d35a5d676297f8f647916238f4d2a` |
| RFTools Utility | McJtyLib 1.21-9.0.21 | 699,982 | `b8eca900d4fe77a495c74137bd6be79c67281e5d7ae67ca55f59980c64960a0e` |
| RFTools Utility | RFTools Base 1.21-6.0.11 | 463,973 | `5195ba530e6cf9ba61c9954a3297679e6d29aa1b6182e27ae14ea43463dd4b00` |
| Immersive Engineering | Immersive Engineering 12.4.2-194 | 14,232,121 | `45942985a4a4aebf265b8e22a0c54a96208637471f36f2532ff5d4911322debc` |
| Immersive Energistics | Immersive Energistics 1.1.0-beta | 40,560 | `389b6671058915761d5e897a624055adc78e4680180c521994e39a0ef4e7c79b` |
| Immersive Energistics | Immersive Engineering 12.4.2-194 | 14,232,121 | `45942985a4a4aebf265b8e22a0c54a96208637471f36f2532ff5d4911322debc` |
| Immersive Energistics | Applied Energistics 2 19.2.17 | 8,230,896 | `460d779a0609b81409907d9956de8f6f70a1b0912257e3e5c3c7e75ac9630e95` |

## Reviewed merges

| Add-on | Reviewed PR | Base commit | Owner-signed feature commit | True verified merge | Merge tree |
| --- | --- | --- | --- | --- | --- |
| SecurityCraft | [#6](https://github.com/jan-guenter/bluemap-securitycraft-addon/pull/6) | `618b4dbfdfe6847f4e3e7c6847cb234b36c6efca` | `b93154ebe8e8b25c20ce7d0178be09556ddbbb54` | `498c7cfff60b032d89e807b57a092d06fd3596e5` | `fba5f06da7fcd03390a728cc8910cad76e599d01` |
| RFTools Utility | [#4](https://github.com/jan-guenter/bluemap-rftools-utility-addon/pull/4) | `18fdf86841e07b9f310bdd8c7360642fb652dd95` | `15da982cc221b65c77a5f6db63440cdfe12e8c32` | `801bffba22bcc287fe55d91c6baa7b6f03085bcd` | `c8828f4d6a503e36976d6e294bdc2820128c85b6` |
| Immersive Engineering | [#4](https://github.com/jan-guenter/bluemap-immersive-engineering-addon/pull/4) | `eab8786558ededb1720f8533af23b333c295d533` | `38857d506a0f58ee069280bed4fe93885d687474` | `0ea2c011f7a59615f45f423d5fe867b28982159e` | `0f72ca03e23bec05914ba93473ab8d8bec83db9a` |
| Immersive Energistics | [#4](https://github.com/jan-guenter/bluemap-immersive-energistics-addon/pull/4) | `cf6f576781bafcf977b4aa1fbc594545d762d80d` | `760ec15402ba72ad524621cabe1a1727e6e47ffb` | `227844d592fe42d431129f081fabe1b2b4b1de24` | `874f7fe605610f21cb42bb8b1f43195ab27a73fb` |

Every feature commit has a valid owner signature. Each true merge has the
reviewed base and feature as its two parents, and its tree equals the feature
tree. The GitHub API reports every true merge as verified with reason `valid`.

GitHub Actions reported each signed feature as the pull-request run's
`headSha`, but the workflow checked out and packaged the synthetic merge shown
below. Each synthetic commit has the reviewed base and feature as its parents,
uses the feature tree, and has a valid GitHub signature. The post-merge run
then checked the true merge commit.

| Add-on | Synthetic PR checkout | Pull-request CI / job / artifact | Exact-main CI / job / artifact |
| --- | --- | --- | --- |
| SecurityCraft | `e7f795d3a4fb38b703ca44536b9fa44b4f91c600` | [33288131166](https://github.com/jan-guenter/bluemap-securitycraft-addon/actions/runs/33288131166) / `99194856777` / `9725118929` | [33288256088](https://github.com/jan-guenter/bluemap-securitycraft-addon/actions/runs/33288256088) / `99195204677` / `9725160983` |
| RFTools Utility | `3077b7b845c51eeb0c11201aaad39f810bc09f50` | [33288061715](https://github.com/jan-guenter/bluemap-rftools-utility-addon/actions/runs/33288061715) / `99194671562` / `9725095365` | [33288200465](https://github.com/jan-guenter/bluemap-rftools-utility-addon/actions/runs/33288200465) / `99195043345` / `9725139341` |
| Immersive Engineering | `ea932c10c50e258d38628ba6758b6f26cea4309f` | [33288798629](https://github.com/jan-guenter/bluemap-immersive-engineering-addon/actions/runs/33288798629) / `99196648568` / `9725328358` | [33288936011](https://github.com/jan-guenter/bluemap-immersive-engineering-addon/actions/runs/33288936011) / `99197013933` / `9725369145` |
| Immersive Energistics | `5270ed577b6f8ae33f5ce23e42bbaad85e41bdb4` | [33288838537](https://github.com/jan-guenter/bluemap-immersive-energistics-addon/actions/runs/33288838537) / `99196754588` / `9725341912` | [33288972113](https://github.com/jan-guenter/bluemap-immersive-energistics-addon/actions/runs/33288972113) / `99197109376` / `9725378102` |

All eight runs and jobs completed successfully. The pull-request artifact
names contain the synthetic checkout identities, while the main artifact
names contain the true merge identities. No migration triggered a release
workflow.

The existing annotated release tags and GitHub releases remain unchanged:

| Add-on | Version | Tag object | Peeled release commit | Tag verification |
| --- | --- | --- | --- | --- |
| SecurityCraft | `0.1.0-alpha.1` | `1540d814c5d5e18b57dc5a8d933962fa31596e69` | `a99e816581b62c71dae3975e1e677a1ff93aec64` | unsigned |
| RFTools Utility | `0.1.0-alpha.1` | `645550501961e1c2d04d65e57ef63626f9fa65b4` | `cf3f4c714aafd49be097d391d077158f0cc1fb60` | verified, valid owner signature |
| Immersive Engineering | `0.1.0-alpha.1` | `1daeb73d6252a2a677ae6777428d065498214a65` | `a08b7fd0267103d0a3d1722bed171ef7b4487a57` | unsigned |
| Immersive Energistics | `0.1.0-alpha.1` | `9e93f1b1084ae53d11928b07018a402398f1de2e` | `4632af465a9991cc1f81ea4d12239d5a1376c6df` | unsigned |

## Artifact and gallery parity

Complete local gates and downloaded pull-request and exact-main CI artifacts
reproduced all four published files byte for byte in every repository.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| SecurityCraft | 33,345 B `4caccbbfaf9d413ae7d60e926069812e09da182adeb907ec2475083904d096e4` | 18,804 B `71ba8c65532c6640b28f484aa1ef2d7900e563e7f37474d855ae01db21372694` | 1,370 B `68bcd52d29167f03065d94a11f4aa2ee2530acfe2e7572df2ed8ca88b098223e` | 2,859 B `2d705130f94b9d5a2ce1a63577d3907f71ec0d225745df957e4398e3e7547ab9` |
| RFTools Utility | 71,184 B `a9adfd5d2773b9b7ed2a7757b520ea513b5dedeaa0e57eb8349afdb9ebd6dd25` | 50,658 B `8b34f2f5762cc1c591078f605a1c488c09380ee92f656298c807463dc364fb8f` | 1,365 B `b51c383c34ee37e92bd1fbb48023f1ac06ac106ed2d50ba34040dedfde370350` | 2,873 B `e1995a9747e35ed988389e4abe483457109657ee173929085173459caab3bec3` |
| Immersive Engineering | 321,202 B `eec9bbd5b1c27ffa3e9c57d7a730f5a2212ebeebc600cafc7498fa0a15580fb4` | 181,013 B `d3b88f65d9f292f03ef2aa99a06ec16a1e541c58b04fa41cf85c274de654be8f` | 1,401 B `1d497453dc2419e7bc3079ff0a2d39787f1bad22bddffd9a3ade2a8e6b893949` | 2,918 B `06c5b87cc73c7977b9a17cd556f0edd45ddac57f430106b3136697abd42cbd59` |
| Immersive Energistics | 91,505 B `e61ae9c0fd9c8cfd36698a13a03124ff3536e8e93419fca22c47d4e29eb9bc76` | 60,289 B `b30e5160f1a49cf107af1567bafdb32c5fd58429facc73cbeb8d30859a062146` | 1,401 B `f582b5a01955d4101aaef639d11a6ef1b81cf9b66d4d7d5cb0e1de743594444f` | 2,915 B `418ba70d6964fcd7c9ede0258a2a47f635d5af5ea4eece2856156b22d73ff183` |

Baseline and migrated gallery packages also match exactly. SecurityCraft is
4,130 bytes with SHA-256
`b14c2a650aaa0302c48d918f23d854e92dc520f2cc944498c30c5912a13f84d5`.
RFTools Utility is 2,942 bytes with SHA-256
`63393b50de6684e925cec0ddbee6d3818dfa8cf7f8d90f8de9fdb46ca85c4767`.
Immersive Engineering is 10,927 bytes with SHA-256
`81f519133f0fb481984b41bd3db778573a2aa67eb8dbe8bc052c4ea36449e5e1`.
Immersive Energistics is 3,370 bytes with SHA-256
`abf6b4b926d1fc8b4bdce774b7c57af3911bb5f9fbac7f6d0e67e0a27c577b8f`.
The existing owner-accepted freezes and gallery controls remain unchanged.

## Build-contract parity

Normalized task sets, compile dependencies, outgoing variants, and release
dry-run task sets remained exact. The root full gates gained only the four
actions that compile the source-distributed convention: SecurityCraft 43 to
47, RFTools Utility 47 to 51, Immersive Engineering 47 to 51, and Immersive
Energistics 47 to 51.

The four `build.gradle` files have a net reduction of 103 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| SecurityCraft | 325 | 297 | 28 lines |
| RFTools Utility | 506 | 481 | 25 lines |
| Immersive Engineering | 504 | 479 | 25 lines |
| Immersive Energistics | 506 | 481 | 25 lines |

Applicable exact-input, profile, gallery, Python, Java, Checkstyle, repository,
workflow, publication, and release-dry-run gates passed. The retained Java
results contain 11 tests for SecurityCraft, five for RFTools Utility, 30 for
Immersive Engineering, and 11 for Immersive Energistics. All passed.

The common settings preflight rejected uninitialized, dirty, wrong toolkit
heads, and mismatched gitlink-index states in all four repositories. Immersive
Engineering also retained fail-closed checks for a wrong toolkit wheel hash
and wrong release tag. Consumer-owned dependency, packaging, exact-input,
gallery, and release rules remain local.

## Result

The sixteenth cohort moves four more inline consumers to the v0.3 convention
and trust identity. Their published files, deterministic galleries, build
contracts, release identities, and renderer behavior remain exact. At this
point 48 of the 51 add-on repositories used the shared convention; cohort 17
contains the final three.
