# Installed GEO resource-model extraction

This report records the fifth production-code extraction selected by the
ATMons 1.2.0 deduplication review. The module owns the shared bounded Bedrock
GEO 1.12.0 compiler, immutable mesh model, and optional sampled-pose input.
It does not own installed assets, resource paths, named model contracts,
animation parsing, BlueMap mesh emission, registration, or fallback policy.

Consumers pin the module as a Git submodule and compile its source into their
respective add-on JARs. The standalone module JAR is publication evidence, not
a server component.

## Released source module

The public
[`bluemap-installed-geo-resource-models`](https://github.com/jan-guenter/bluemap-installed-geo-resource-models)
repository released `v0.1.0-alpha.1` from merge commit
`c80a83eb6e2cb0bb05a69ace9716ef08b9db14f2`. Its signed annotated tag object
is `bb256abad13c917ecfee996ef29daab507c25060` and peels to that merge. The
exact production-source tree consumers pin is
`8db87f933557d54c5ede2db70d94f67eaf44c30b`.

Pull request [#1](https://github.com/jan-guenter/bluemap-installed-geo-resource-models/pull/1)
passed its complete CI and release gates. The module's 17 tests include a
192-quad raw-bit parity fixture. Its build gate also verifies the frozen source
oracles. The published release files match the reviewed bundle, and both JAR
attestations verify against the tagged commit:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Production JAR | 29,628 | `1f16dfa433ffd05f795eb3a3e96b70fdf5eafc5d3868cb73346bbe5c2b92af4d` |
| Sources JAR | 11,167 | `1b8074e4afca5c71b0a9333f636ca2456e22919d5af2b602dfa8da89cb7fbf23` |
| POM | 1,668 | `2a289036ec43e3b69bbe3e6e59fb4b42af4c60b1c121659e66d5d61140ed0f6c` |
| Gradle module metadata | 2,936 | `0939c97172d551aae3a86c43f32328d48abb8cac194349f1b49cbd37925de06b` |
| `SHA256SUMS` | 504 | `a8c045be652f6df4de7ee15eb2db2a7ac2fbc56f504d2bf5b53dd4a09d305175` |

Production source depends only on Gson 2.8.9 and Java 21. Gson remains a
consumer-pinned compile-only dependency and does not appear in the module's
publication metadata. The archive contains no BlueMap add-on descriptor,
entrypoint, nested JAR, Minecraft class, mod class, model asset, or texture.

## Extraction result

Ars Technica and Ars Nouveau each removed two local production sources and
compile the module's three production sources instead. Their complete ordered
mesh comparisons cover static installed resources, including 924 quads across
the ten Ars Nouveau cases. Ars Creo adds the independent non-identity-pose
control. Its aggregate parity locks 960 raw-bit-equal quads across the static
and sampled-pose fixtures.

The consumers retain their exact artifact admission, resource closures, model
contracts, animation data, mesh emitters, materials, routes, galleries,
diagnostics, and stock fallbacks. Each consumer's settings preflight rejects an
uninitialized, dirty, wrong-HEAD, wrong-index, or source-tree-mismatched
module checkout. Production and sources archive gates require one exact copy
of the shared classes and reject the displaced local paths and nested module
JARs.

## Consumer publications

The reviewed feature commits, final main merges, and signed tag objects are
separate identities:

| Add-on | Reviewed PR | Signed candidate | Final main merge | Signed tag object |
| --- | --- | --- | --- | --- |
| Ars Technica | [#6](https://github.com/jan-guenter/bluemap-ars-technica-addon/pull/6) | `b374dd2e1d24ea14850b766f797894b7f444c283` | `ce6ae6049522218a742acada1064e14ccf2c769e` | `35eddb3fbc8e2bbd424fe3b74cb1eeaa30e93d19` |
| Ars Nouveau | [#6](https://github.com/jan-guenter/bluemap-ars-nouveau-addon/pull/6) | `db60734f1f556311ceec404987451e77e5f853c3` | `3df77763803ef7c2cd228449bdfe2870d52e8fe1` | `298cf7a842c3c12c137c498b40b5edad4e1ad6ac` |
| Ars Creo | [#6](https://github.com/jan-guenter/bluemap-ars-creo-addon/pull/6) | `d5b1ff36105e483b400d3dd503f95c68b3a17670` | `0a5f536544b00068a061a88cc676f51459824bd8` | `b8b84e2c90964d38c174f14b958c7180f75de88c` |

| Add-on | PR CI | Exact-main CI | Release workflow |
| --- | --- | --- | --- |
| Ars Technica | `33310480707` | `33310636324` | `33310779905` |
| Ars Nouveau | `33312365321` | `33312530584` | `33312668833` |
| Ars Creo | `33313418771` | `33313606861` | `33313773305` |

All three consumers released signed, attested `v0.1.0-alpha.2` prereleases.
Their exact payloads are:

| Add-on | Production JAR | Sources JAR | POM | Gradle module metadata | `SHA256SUMS` |
| --- | --- | --- | --- | --- | --- |
| [Ars Technica](https://github.com/jan-guenter/bluemap-ars-technica-addon/releases/tag/v0.1.0-alpha.2) | 150,969 B `445239a893ea9027e4b2a0562d47d64fb0bdd5e5bb8c80156b79ee22502498f0` | 87,416 B `f3ab618e1c2af2acd274e5b029350f507a9ee05a80898092e4755cdfb997f708` | 1,347 B `5c794292b0f71c4a85085b88f9d8b4512e9f0c38a8f924de4c8913c14944fdd2` | 2,854 B `3f5a8de3f1d69738025345734ae04160d2606441024b96f818590bfd4d60bcc3` | 460 B `e5aaa4f5bfc98b4ffa1ac78a986515574a233f8e95ad312a79a3c7a299bcdd65` |
| [Ars Nouveau](https://github.com/jan-guenter/bluemap-ars-nouveau-addon/releases/tag/v0.1.0-alpha.2) | 164,317 B `5c5ae163f046ba28a48d28d03a2abc0b8eb6494eb8607dbb08e5f0a256bf1ce0` | 89,940 B `0b672c2e6637f599bf3aca3be1cfb1b34fad7861b3d548f23026b5b97785fd2c` | 1,341 B `fa830efa0bbbab0f6cac002fd2b946816349e486909e45fa219b8e8c57ba9b6e` | 2,847 B `aafc6c6e0662d7d273808f4e341212af60f5184a895200f831be4b3a88d86548` | 456 B `2baec1098510327c0bebfa67764625a982312b7a3f7a2053b7805603e40c9926` |
| [Ars Creo](https://github.com/jan-guenter/bluemap-ars-creo-addon/releases/tag/v0.1.0-alpha.2) | 173,649 B `b18fe7ba443e16c942a0a063b969f7acbf67c4451d08a974107b0e6c110b769c` | 96,149 B `e5eca13199133dabee79cb7758192987520ddde75b051fe23250e4d332bce8c4` | 1,323 B `be35a6b36a3cae2b0d435d3665c67e0e7ff7a2bd70689e69757731785fb96d49` | 2,826 B `4ebfa63992d6ae5890f5e04120feadbf27b205d07852d3656e6ad31537bfbab2` | 444 B `67bcf4fef77e62a6b80f863f67e7bfc100f8ace8bd9c345c0f0db071f91b3197` |

All completed release downloads are byte-identical to their reviewed bundles.
Their checksum manifests and tag-scoped JAR attestations pass, and their
workflows published the matching Maven versions.

## Combined integration gate

The first consumer gate bound the signed Ars Technica candidate without
changing the compatibility manifest. Its override lock hashes to
`4a39604c62359b0b8a5c98938520044ac0ba41c92f4a1707e346d6ce6b5691e4`.
The candidate manifest hashes to
`6d15de0f5f9977b6b0be4ce3e10a26da2a07ae77493d3f3f304c87f6e18121ee`,
the 51-row checksum manifest to
`2043bbc7143a4cd9e44c285d04285a17706b20305946340769e7a1b2bd3dea65`,
and the normalized pack inventory to
`b2eee4652faae3a362ebfa2fea5d672e090550f2bfd38e10757dc3498d0cf725`.

The disposable ATMons 1.2.0 server reported all 51 activation markers on both
boots and passed all 51 gallery builds and immediate assertions. None failed,
skipped, or ran without an assertion. The run began at
`2026-08-30T12:26:19Z` and finished at `2026-08-30T12:44:12Z`. Its retained
75,878-byte result hashes to
`736d1d325fa51861aab530a4f611d5446b7235c06d105c663ff11e439cf6037d`.

The final cumulative gate bound all three published consumers and repeated the
two-boot activation, exact overlay, and gallery assertions:

- override lock:
  `74dbc8dfe029400c281a89376c590693e3323e2fc69e4a99bde522dc0de20df3`;
- candidate manifest: 86,665 bytes, SHA-256
  `fc74a9e02a9d62ae58208685cfda3456ffa7d95dac79acf47670443920bd4212`;
- 51-row checksum manifest: 5,663 bytes, SHA-256
  `ab7a26c83fefb741298b8f0662cd8319f035c63b7de4b5831641148899217e40`;
- candidate JAR inventory: 51 JARs totalling 9,076,618 bytes; its 5,944-byte
  normalized inventory file has SHA-256
  `ff63ebb98ee86a7cbaacc1551564cb079037f2b5f32c6c2836f9871400238851`;
- run interval: `2026-08-30T13:31:10.621642Z` through
  `2026-08-30T13:47:38.558623Z`;
- retained result: 75,877 bytes, SHA-256
  `c9996bb13c9b2986a1c47afd5f8c932ff2750276ef1d47b4f023cd9e440947d4`;
- assertions: two distinct boots, 51 activation markers per boot, 51 passed
  galleries, zero failures, zero skips, and zero unasserted builds.

Raw results, container identities, logs, worlds, credentials, and staging
paths remain untracked.

## Compatibility boundary

The immutable `atmons-1.2.0` tag, `versions/1.2.0/manifest.json`, installer
metadata, tooling manifest, and pinned add-on gitlinks remain unchanged. The
module is not a direct meta-repository submodule because it reaches servers
only as source compiled into consumers. These later compatible releases may
be selected by a future compatibility snapshot. They do not rewrite the
published ATMons 1.2.0 snapshot.
