# Shared Gradle convention cohort 17

This report records the seventeenth and final artifact-parity adoption of the
BlueMap Add-on Toolkit Gradle convention. The migrations changed development
tooling only. They did not change the ATMons 1.2.0 manifest, meta-repository
gitlinks, renderer sources, resources, profiles, provenance, galleries,
acceptance records, add-on versions, tags, or published releases.

## Scope

The cohort contains Sophisticated, FramedBlocks, and AE2. Each repository pins
toolkit `v0.3.0-alpha.1` at commit
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` with a mode-160000 gitlink and a
consumer-owned trust preflight in `settings.gradle`.

All three consume only the toolkit's source-distributed Gradle convention.
They do not adopt the toolkit wheel or repository checker. The source checkout
is development-only and adds no installed dependency or packaged add-on file.

Every validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. Sophisticated and FramedBlocks
used these exact inputs:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Sophisticated | Sophisticated Core 1.4.80.2194 | 1,673,669 | `58a35e74642de9a7ffd39604f06903df39c166d332551c5770ca2e21685defc0` |
| Sophisticated | Sophisticated Storage 1.5.83.2017 | 1,828,640 | `354f62ef885b3219fb0787d211582d7ea733800ff31787cc85b9af68d260b600` |
| Sophisticated | Sophisticated Backpacks 3.25.73.2027 | 1,144,235 | `ded30f9269a92cc295ab0a735a86770ca097c30198b8f3f2288ecaac6542b93e` |
| FramedBlocks | FramedBlocks 10.6.1 | 4,306,703 | `3337f29e1fa3331e8740eef9c20b0750d81fd86d1057fb81012a5c4792aa3369` |

AE2 retained its larger validation matrix. It combines the ten current ATMons
1.2.0 artifacts with the historical Extended AE 2.2.33 input required by its
accepted Ex Drive gate:

| Input | Version | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Applied Energistics 2 | 19.2.17 | 8,230,896 | `460d779a0609b81409907d9956de8f6f70a1b0912257e3e5c3c7e75ac9630e95` |
| Applied Flux | 1.21-2.1.5-neoforge | 345,117 | `57e6a2c0f38e660c9e8416f9081d8c515f5ad096d6793d7b7f039e8e210d245b` |
| ME Requester | 1.21.1-1.4.3 | 184,517 | `68f3c861a802d48afeb6e3a48e8ee4f8633904340ac3f89f17493dc84490e385` |
| Expanded AE | 2.1.1 | 496,713 | `f39c0eb9c6271f54a44ffee092a29520f53000d1005849e6afada3ad9dffba14` |
| MEGA Cells | 4.11.0 | 1,137,276 | `a386bbf12afb11729b0dcf77f64221893d250f22e6185a4d728b9799b230bc55` |
| Advanced AE | 1.6.12-1.21.1 | 4,791,255 | `a01d9718667ac13899013e91c5b0b7708b9b9db1da9b8e380772dde54bbe8f41` |
| Athena | 4.0.6 | 99,944 | `43699885bbce3343916d4c5c4940cf0e3f9f6f02fdeb46e8655e121b42282ec5` |
| Extended AE | 1.21-2.2.35-neoforge | 5,578,031 | `14a2860fa2c747e9dda2279b8933fac6311fecfee166c765171022b902591c65` |
| Extended AE, historical Ex Drive gate | 1.21-2.2.33-neoforge | 5,573,972 | `6652ed1ea4b71f585d48c05a195a77594a7a2bd1ecea0fc805db2122aafad734` |
| Applied Mekanistics | 1.6.3 | 149,709 | `8946fea39451dbce8e709dedbef40a52ba337bdf7a25ac0c4b503800b1bf0773` |
| Mekanism | 10.7.19.85 | 11,976,009 | `004dbc9f3106f4d192aeaa1ee1190dd16ec9ca8059ed3d093b80034f4c574f43` |

## Reviewed integrations

| Add-on | Reviewed PR | Base commit | Owner-signed feature commit | Main integration | Integration form | Reviewed tree |
| --- | --- | --- | --- | --- | --- | --- |
| Sophisticated | [#3](https://github.com/jan-guenter/bluemap-sophisticated-addon/pull/3) | `3827a50c272004c07f3f3a1d8c4e1eef191a2ca6` | `7838d066b9f9312aa89579ce24f18e8b25e900cb` | `3ee7d6e0797e036755096727b813d2ffdf68ae03` | two-parent true merge | `cd7f1f3f5d20043d771989f31d3bfa944e1f4c69` |
| FramedBlocks | [#8](https://github.com/jan-guenter/bluemap-framedblocks-addon/pull/8) | `b9662d55a38fc0e6256afd19e01badd12f305d34` | `94c22820a9a4a185640dff5fc13757dac987ec2c` | `63ea8bc195b3a7787aa7030229906bc026291383` | one-parent squash | `1775355ed986f2f32687f3792c36cef539f28745` |
| AE2 | [#8](https://github.com/jan-guenter/bluemap-ae2-addon/pull/8) | `a0d09384030aa0f78b25f623075bc247f02204c5` | `ebf780d15bff13388ada5e705bddffe1c7cae2b6` | `cb8a0a33bfe919a5ad5db297e45350a47e1dbee6` | one-parent GitHub rebase | `3e48584de8d89d616b9ab78b62efadb69074fdb8` |

All three feature commits have valid owner signatures. Sophisticated's main
integration has the reviewed base and feature as its two parents and uses the
feature tree. FramedBlocks was integrated with GitHub's squash method, so its
main commit has only the reviewed base as a parent. Its tree nevertheless
equals the signed feature tree. The GitHub API reports both commits as
verified with reason `valid`.

AE2's repository requires linear history. GitHub rebased the signed feature
to the one-parent main commit named above. That rewrite is unsigned. It has
the reviewed base as its parent and exactly the signed feature tree, but this
report does not describe it as a signed or verified integration commit.

GitHub Actions reported each signed feature as the pull-request run's
`headSha`, while the workflow checked out and packaged the synthetic checkout
shown below. Each synthetic commit has the reviewed base and feature as its
parents, uses the feature tree, and has a valid GitHub signature. The main runs
then checked the integration commits named above.

| Add-on | Synthetic PR checkout | Pull-request CI / job / artifact | Exact-main CI / job / artifact |
| --- | --- | --- | --- |
| Sophisticated | `80dd36c277bd3df6b4a48b661fffa0237e568c20` | [33288889341](https://github.com/jan-guenter/bluemap-sophisticated-addon/actions/runs/33288889341) / `99196893822` / `9725342618` | [33289002986](https://github.com/jan-guenter/bluemap-sophisticated-addon/actions/runs/33289002986) / `99197187865` / `9725374491` |
| FramedBlocks | `b4292d0fa4f04bff0e7c0c90df21d131541ee7cb` | [33288811438](https://github.com/jan-guenter/bluemap-framedblocks-addon/actions/runs/33288811438) / `99196683804` / `9725331637` | [33289177573](https://github.com/jan-guenter/bluemap-framedblocks-addon/actions/runs/33289177573) / `99197660857` / `9725439978` |
| AE2 | `09329abd560914a06c17fd408182296d3d47def6` | [33291294020](https://github.com/jan-guenter/bluemap-ae2-addon/actions/runs/33291294020) / `99203253402` / `9726476433` | [33292912664](https://github.com/jan-guenter/bluemap-ae2-addon/actions/runs/33292912664) / `99207557932` / `9726945431` |

All six runs and jobs completed successfully. Downloaded artifacts from the
actual synthetic checkouts and exact main commits reproduced their expected
files. No migration triggered a release workflow.

AE2 then completed a separate workflow de-duplication follow-up in
[#10](https://github.com/jan-guenter/bluemap-ae2-addon/pull/10). It removes
the redundant direct Python-suite invocation from CI and release workflows;
Gradle `check` remains the single owner of that 194-test oracle. The
owner-signed feature `eebee9f036caab2ab007677da83add1f19aea37d` produced
GitHub-signed synthetic checkout
`dff6fb8d27a918079c860b4fb19197655cb225a8`. Both use tree
`f0079905b4f6babbf43103f7fb7a988ea56196ce`.

PR CI `33294529528` / job `99211809500` / artifact `9727199528` passed. The
GitHub-signed one-parent squash
`da88f2e3281153e7dba9b9b1bfadff846edb99d6` has the preceding AE2 main commit
as its parent and the reviewed tree. Its exact-main CI `33295349138` / job
`99213944999` / artifact `9727428261` also passed. Both logs contain exactly
one `Ran 194 tests` result and no direct workflow unittest command; both
artifacts reproduce the same four files recorded below. Tags, releases, and
release-workflow history remain unchanged.

The existing annotated release tags and GitHub releases remain unchanged:

| Add-on | Version | Tag object | Peeled release commit | Tag verification |
| --- | --- | --- | --- | --- |
| Sophisticated | `0.1.0-alpha.1` | `5342ae0942a0c04863e82eb7effdf49df30214b8` | `a75b1d82c3987fa9360a1e8a5910eedf90aca7cb` | unsigned |
| FramedBlocks | `0.1.0-alpha.2` | `b81370c746e7041d70b7dba5e7cc1813cd0b778c` | `0c20019d570356044526faea964caf10a13a82f3` | verified, valid owner signature |
| AE2 | `0.1.0-alpha.3` | `8980ab2b1359f98d6bd92a85d6cc375c1ef01261` | `575c05222c7322421c30cb1158a2054dc04aa564` | verified, valid owner signature |

## Artifact and gallery parity

Complete local gates and downloaded pull-request and exact-main CI artifacts
reproduced all four published files byte for byte in every repository.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Sophisticated | 114,309 B `d466d6b40fc1f51a8e045ba34631354fd181681aa8363b4f0649ec1c83227036` | 72,951 B `7c99607ecd26033de08814cf10dd298623cc3c919893e5e1a6efc83180cedbdc` | 1,375 B `8219774bae3cdba98cd30f2d0de379048e1ddf9fb5d865985648622cd215be9d` | 2,861 B `110ed34f47341944e1ee14091f58187137d412a3a4ee64630081cbd80eae6e9d` |
| FramedBlocks | 1,327,387 B `a7c4922777e6912d726da14d246c92c75b7fc1d1db8ec2f862a07b25bc9e9ebb` | 1,255,995 B `3be761a76ef9f05049eb7744b78c6db9ee758d5f1f1b8c890812cf456c4d425f` | 1,671 B `88a77f3ef637bade23776c94e1ee2dbfc563e5d0a24db5a3c305aa617e871f04` | 2,858 B `8bf248f4e47fa1ae9903c209c8e0574e84b5ecfb4592772e216399dbfafc65dc` |
| AE2 | 1,252,649 B `f7014e1c60bdf02fa22583a7b5b5cbf6f3076a0b2371601360775507d473a12d` | 555,054 B `3b2e75ca384f80c21315b4a78ad56739dd9d7661e07481b821892f7c58b11b51` | 1,619 B `05747080d86e9a01bddb8a0fd2a35c37dfb08bca25d7720ada7fce3d251d7ef4` | 2,794 B `8b4130658e3c2064976cc74176d81f23432b3fec93aa5fd64231148423195de7` |

Sophisticated's baseline and migrated deterministic gallery packages are
both 24,071 bytes with SHA-256
`cac6b0142ecc1dbbe2d800dde4398ee0727d5f4fbc3cac774798837d9dfebe2f`.
Its accepted 594-anchor gallery and acceptance record did not change. The
gallery tree remains `94b2a26224ebee7a204854075356f180716340e4`.

FramedBlocks does not produce the same gallery ZIP artifact. Its generator
check and tracked `SHA256SUMS` verification passed before and after the
migration. The unchanged gallery tree is
`e4fc8ef86b2e1ad488c211b2a813d42cb44b51ef`; it retains the 234-case roster,
15-case renderer-path matrix, and accepted controls.

AE2's two baseline packages and the migrated package are 102,465 bytes with
SHA-256
`6dca0be9198a4f099af8c8ee4c9decec05b8a15c5dcfc7d9576b9a9bc6dbc0eb`.
Its gallery sources, exact input matrix, generated data, acceptance records,
and release candidate remained unchanged.

## Build-contract parity

Normalized consumer task sets, compile dependencies, outgoing variants, and
release dry-run task sets remained exact in all three repositories. Each root
gate added only the four actions that compile the source-distributed
convention. Sophisticated moved from 38 to 42 actions and FramedBlocks from 42
to 46. AE2's migrated full gate completed 58 actions, including the four
convention actions. FramedBlocks' two independent release reproductions each
completed 47 actions and produced the same four published files.

The three `build.gradle` files have a net reduction of 90 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Sophisticated | 221 | 190 | 31 lines |
| FramedBlocks | 529 | 498 | 31 lines |
| AE2 | 4,178 | 4,150 | 28 lines |

Applicable exact-input, profile, gallery, Java, Python, Checkstyle,
repository, workflow, publication, and release-dry-run gates passed. The
retained results contain 10 Java tests for Sophisticated, 52 Java tests across
11 suites for FramedBlocks, and 590 Java plus 194 Python tests for AE2. AE2's
Java suite retains two intentional skips. All executed tests passed.

The common settings preflight rejected an uninitialized toolkit, a wrong
head, a dirty checkout, and a gitlink-index mismatch in all three
repositories. Consumer-owned dependency, packaging, exact-input, gallery,
provenance, and release rules remain local.

## Result

Cohort 17 moves the final three inline consumers to the v0.3 source
convention and trust identity. Their published files, galleries, build
contracts, release identities, and renderer behavior remain exact. The
portfolio-wide Gradle convention rollout is now complete in all 51 add-on
repositories.
