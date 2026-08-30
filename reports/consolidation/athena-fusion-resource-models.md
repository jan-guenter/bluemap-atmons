# Athena and Fusion resource-model extraction

This report records the second and third production-code extractions selected
by the ATMons 1.2.0 deduplication review. They remain two independent source
modules: Athena and Fusion have different resource formats, selection rules,
and failure contracts. No generic connected-texture runtime was introduced.

Both modules are pinned as Git submodules and compiled from source into each
consumer. Their standalone JARs are publication evidence, not server
components. BlueMap's separate add-on classloaders still make an installed
shared library the wrong deployment model.

## Released source modules

The public
[`bluemap-athena-resource-models`](https://github.com/jan-guenter/bluemap-athena-resource-models)
and
[`bluemap-fusion-resource-models`](https://github.com/jan-guenter/bluemap-fusion-resource-models)
repositories released `v0.1.0-alpha.1` after reviewed pull requests, exact-main
CI, and signed-tag release workflows.

| Module | Reviewed PR | Signed feature | Synthetic PR checkout | Final merge | Signed tag object |
| --- | --- | --- | --- | --- | --- |
| Athena | [#1](https://github.com/jan-guenter/bluemap-athena-resource-models/pull/1) | `bcce9f68f82e4171b01f809e7540eef2da801fd5` | `ffb5d6320cc8fc31cba255b6b85e0dac717c2950` | `4a503a63f7f10b7c414c6c1228207a5ba00bfd54` | `c8714ddd9d08203cc3821df71bd174fb47ed8548` |
| Fusion | [#1](https://github.com/jan-guenter/bluemap-fusion-resource-models/pull/1) | `7684117bd0297a79d56f3d95d1455886decf26e4` | `0b57ba154cc3a2e40990bd1aceb73f1fb1516775` | `3ddd5d39bb7cc8664c242aedd849a636316075c2` | `635f72d0020b08d9a234c796fdeab683d8d9d901` |

The exact workflow and artifact boundaries are:

| Module | PR CI / artifact | Exact-main CI / artifact | Release workflow | Main-source tree |
| --- | --- | --- | --- | --- |
| Athena | `33297747807` / `9727949724` | `33297807061` / `9727967045` | `33297865130` | `882689c2f9a0875547f4e30aefd68659103d5046` |
| Fusion | `33297843005` / `9727997664` | `33297978106` / `9728037353` | `33298097590` | `6e85031ff2f0e7417a7a2fb0babbf7ed5a4f218a` |

Both release bundles passed their checksum manifests and publication gates:

| Module | Production JAR | Sources JAR | POM | Gradle module metadata | `SHA256SUMS` |
| --- | --- | --- | --- | --- | --- |
| Athena | 11,025 B `9fb3a571bf76e91774a03fdb6ae7a5609456e0f309b0cce701324c1611679e2e` | 7,487 B `3aa1126dab97c1f8ab4989a04325fe0d1ac10a3d395d532dcb38c4e1dfc17e44` | 1,638 B `e9a0294ae18a926ade26e350f247f72507ad7c826736f0f758c5e61c83ef0e0f` | 2,886 B `a4b742475884efb88773f83a0822a5903e8a020978477002699354efabcda189` | 476 B `ef41d1b0bf57eac167de5b87488c7afb1b3ad61f8ea3efbf91bffc9431a061b5` |
| Fusion | 20,041 B `d6a39b19ba406477d2e05790f53c6c852c2f99a010ec0e12bbe99147633599fb` | 11,697 B `791e4606d21c8ef43c72d140480c2d99588324e55893472f1eca2da02b796f80` | 1,633 B `4cffe10f32425e7cf6af5ad6a23113e50720e6b00e60091d9e00339c92874363` | 2,887 B `33ac7c94c799fc687d7aaf46268c63671df94ece9947863ffe0f5cf1d047b2a2` | 476 B `e0539f4907850c9efd3f3bda206bf9583272e5d793c93ae37d1bf6cd6dc7c8a4` |

Athena supplies four JDK-only types under
`io.github.janguenter.bluemap.resource.athena.model`: texture roles,
quadrant selection, the eight-bit connection mask, and cube-face basis.
Fusion supplies five types under
`io.github.janguenter.bluemap.resource.fusion.model`: axis arithmetic,
direction masks, six layout names, tile/PIECED-corner selection, and face
orientation. Fusion's BlueMap dependency is compile-only and absent from its
publication metadata.

## Extraction result

The five pilots deleted 20 consumer-local production sources and replaced
them with exact gitlink-pinned module sources:

| Family | Consumers | Deleted local sources | Module sources | Repository-source reduction |
| --- | --- | ---: | ---: | ---: |
| Athena | Chipped, Chisel, CobbleFurnies | 12 / 525 lines / 12,997 bytes | 4 / 175 lines / 4,349 bytes | 8 files / 350 lines / 8,648 bytes |
| Fusion | Connected Glass, Rechiseled | 8 / 634 lines / 20,706 bytes | 5 / 396 lines / 12,678 bytes | 3 files / 238 lines / 8,028 bytes |
| **Total** | **five consumers** | **20 / 1,159 lines / 33,703 bytes** | **9 / 571 lines / 17,027 bytes** | **11 files / 588 lines / 16,676 bytes** |

These are source-repository reductions, not installed-size claims. Each
consumer still compiles the exact shared classes into its own add-on JAR so it
has no runtime dependency on another add-on or library. The consumers retain
their own profiles, allowlists, resource admission, predicates, routes,
fallback, mesh emission, gallery, and diagnostics.

The Athena differential gates normalized all five resulting class files and
every unaffected consumer class. Fusion exhaustively covered every supported
mask/layout, PIECED corner, direction, and face orientation. All five settings
preflights rejected uninitialized, dirty, wrong-HEAD, wrong-index, or
source-tree-mismatched module checkouts. Their production and sources archive
gates require one exact shared roster and reject all displaced local paths and
nested module JARs.

## Signed consumer candidates

| Add-on | Baseline main | Signed candidate | Candidate tree | Shared module |
| --- | --- | --- | --- | --- |
| Chipped | `26df095af693d36c75b4d82738736157be3d1f9d` | `a927d23944bfd73b267448479dfb4f0222116b25` | `3f2af05b2789c583e2d9e63b499f353e61eca888` | Athena `4a503a63f7f10b7c414c6c1228207a5ba00bfd54` |
| Chisel | `6553da70621f6039db5f0fb961c2843a1c36988d` | `60d45972db71acbfb29689124f10e79a1952094a` | `c5f950492ac03a5954f2108759003ca67e3f06af` | Athena `4a503a63f7f10b7c414c6c1228207a5ba00bfd54` |
| CobbleFurnies | `90ca220d0fa4d4dfd258fd54b14b8b2606a0975d` | `6652258eff4093668f55024693f8183749a6a6f7` | `3d22019ef2258a395383cbdc836c208e2168cb78` | Athena `4a503a63f7f10b7c414c6c1228207a5ba00bfd54` |
| Connected Glass | `55dc1a0c5a12a02b204c95ab96d3bec044568abf` | `99241f5fd2e352e7b683a6b7c2d70e1df063fe2b` | `2f009f5eba5f14a5389859139ff66454fb597820` | Fusion `3ddd5d39bb7cc8664c242aedd849a636316075c2` |
| Rechiseled | `a8ab2d7070d8667fc73112b46977b15b819cef1a` | `2d98c6f1ab7eb7ce6ceaf0f364ce15aa8b2b9ad8` | `489f3305f07c685405de21fb7f11485bdc2fa3fd` | Fusion `3ddd5d39bb7cc8664c242aedd849a636316075c2` |

Rechiseled's repository policy forbids local packaging. Its first
authoritative PR-CI pass produced the four payload identities, a signed
follow-up commit sealed them in `provenance/release.json`, and final PR CI
reproduced those exact bytes. The other four candidates reproduced their four
payloads locally before admission. An independent final audit found no
actionable gap in the five-candidate boundary.

## Combined integration gate

The candidate override lock bound the five signed commits and exact production
JARs without changing `versions/1.2.0/manifest.json` or the immutable
`atmons-1.2.0` tag. The 51-add-on overlay builder admitted all candidates and
retained 46 released controls. Its exact identities were:

- candidate manifest: 88,642 bytes, SHA-256
  `991010c18a8977b60591df978405d15fea5012aecdf68605e948d34bc00347c6`;
- 51-row checksum manifest: 5,663 bytes, SHA-256
  `7a462637a2eab2bbba8e5f9ccbb4a58dd1eba45795232dc44b5f9262af7ec17a`;
- candidate JAR inventory: 9,052,767 bytes, normalized SHA-256
  `621583987e32dc8761cd4467edee928ff4920eb2da213edef5c8f1f157b54bbb`.

The disposable ATMons 1.2.0 server admitted the exact 375-JAR base inventory,
candidate BlueMap commit `7e07f4e74ec1e92a6ead9aa1e66054af3e133aac`, and all 51 add-ons. The gate
verified 51 activation markers, replaced the Minecraft pod, required a new
boot identity, and reverified the exact 377-JAR runtime inventory and 51
candidate checksums. It then rebuilt and asserted every gallery: 51 passed,
zero failed, zero skipped, and zero were performed without an assertion.

The retained 75,816-byte result hashes to
`a68e78a4f45c01482db0c5e92581b46346b9c58b70ae68c9e3c1ae3c291d491e`.
The raw result, world, logs, credentials, and staging paths remain untracked as
required by the meta-repository evidence boundary.

## Consumer publications

The signed feature heads, GitHub synthetic pull-request checkouts, and final
main merges are intentionally recorded as distinct identities:

| Add-on | Reviewed PR | Synthetic PR checkout | Final main merge | Signed tag object |
| --- | --- | --- | --- | --- |
| Chipped | [#5](https://github.com/jan-guenter/bluemap-chipped-addon/pull/5) | `57cae4a6dd66b546e0f63fdb937424709d37af4c` | `cc5ab1b2af6e447db775f12e659d3dea980350cb` | `2932b2f8794988c87857cf1bc18638d8a0658ba2` |
| Chisel | [#5](https://github.com/jan-guenter/bluemap-chisel-addon/pull/5) | `c049004ea17cf613bc545237c1f9a11e79cc3d21` | `5c9b600f5c20e27d2229ae204952f9229c118440` | `c70953583112013b58ca07e4d3546e066ebc5849` |
| CobbleFurnies | [#5](https://github.com/jan-guenter/bluemap-cobblefurnies-addon/pull/5) | `5c39b9a8798ea59e23a7e61fc0a2aec55bd6f52d` | `5f8aaf610b9cbc767ddadc94a22402f033999e5b` | `8df08b795b0b363dc29418225b5c7171174538d4` |
| Connected Glass | [#5](https://github.com/jan-guenter/bluemap-connectedglass-addon/pull/5) | `50ca3017c63260fb4e7f8a85786af9b14df04138` | `e81552b200b411a1551416ff3c181b94ee1b140e` | `56c78ee36d75d990bf044e7a2fbf04a902e4ff11` |
| Rechiseled | [#4](https://github.com/jan-guenter/bluemap-rechiseled-addon/pull/4) | `fa9046ef73a2fa462ce3b9762544f5f85bf5bb65` | `c4dd008dae139cf0b193dc3a759c09d1857c479a` | `ba216855089f379c3f5e1e67bb2236651b661554` |

| Add-on | PR CI / artifact | Exact-main CI / artifact | Release workflow |
| --- | --- | --- | --- |
| Chipped | `33300980284` / `9728937779` | `33301072677` / `9728962788` | `33301176037` |
| Chisel | `33300981201` / `9728933239` | `33301074965` / `9728966495` | `33301176923` |
| CobbleFurnies | `33300896539` / `9728909347` | `33300965625` / `9728929981` | `33301037017` |
| Connected Glass | `33300905608` / `9728914416` | `33300996961` / `9728940970` | `33301074015` |
| Rechiseled | `33299776772` / `9728554668` | `33300939893` / `9728922659` | `33301016423` |

All signed `v0.1.0-alpha.2` tags peel to the final main merges above. The five
public prereleases are not drafts. Their exact publication payloads are:

| Add-on | Production JAR | Sources JAR | POM | Gradle module metadata |
| --- | --- | --- | --- | --- |
| [Chipped](https://github.com/jan-guenter/bluemap-chipped-addon/releases/tag/v0.1.0-alpha.2) | 599,702 B `2bf02cecde1f74cbb3be528710823367db5e487aef709a0aef0f64aeb2ee4713` | 558,620 B `f039709ee4741c6f92c208a1a5934b2f3aebfed15e5328e50f785cd0bb206d1c` | 1,341 B `db6addec7b3c0e32c3b71ada5b670b6ad8e5fe60413e9b2a93b6199ed6d7b9c7` | 2,820 B `5b3642845ffa163a57355a3813055c6333d2b467138b6c5d68cbcc7e842e1db4` |
| [Chisel](https://github.com/jan-guenter/bluemap-chisel-addon/releases/tag/v0.1.0-alpha.2) | 251,223 B `0b4fcb7221d7d0bd103397ed6e61e87cf694f1dffdbf61cd811f7ea592675610` | 216,727 B `2d6c926a1d539a41447cddd4afc1084a51056b3ae5175b285d2e046bf7013302` | 1,335 B `5ba3219033d244a54dd7e359c90526d4237d99199d3b9ce7b2ddfb798df5103c` | 2,813 B `a5fa28e1334114f6fd30d92f7d54ef8adf4f843117d2090432a8d0aead872cbe` |
| [CobbleFurnies](https://github.com/jan-guenter/bluemap-cobblefurnies-addon/releases/tag/v0.1.0-alpha.2) | 109,187 B `71bf381f34e5fcb93aed8737198afba4909d8e07a6d8da4183ec5d6a618db52e` | 55,106 B `7726d20c435a7352143747683375871efeadd53abc291748dbf7c70086bb2278` | 1,407 B `89ec5f41f98ca7425fa4cc116f9c7d92207c9fc74aafd298a42d9dfdcf04b183` | 2,861 B `3adebf6abb8bb26ce9674cfd68133fb1b95a5540bfd70063eaee88ac821ce8d1` |
| [Connected Glass](https://github.com/jan-guenter/bluemap-connectedglass-addon/releases/tag/v0.1.0-alpha.2) | 158,546 B `f73841c78da88808bbb9a5a630526e75902a2c56bfc9f7600ccbc39d3572e446` | 94,085 B `ee652f580e614e6dd52db181519d50a38183e001b8e2239e3d829bc8f49b4da9` | 1,375 B `3f6a1e8250bd0dbf62ff046605e7d3d3bec80ae6b8a24444c14aa7f2306c38ec` | 2,868 B `c76ad74c76aedf7886060071cad0507aa1d81f745fb39e7972b50095fbc78f59` |
| [Rechiseled](https://github.com/jan-guenter/bluemap-rechiseled-addon/releases/tag/v0.1.0-alpha.2) | 647,540 B `083425a0bbaf7e4c99673fb169b63e452af9aea2621a4831664680a544f9695a` | 581,629 B `09687fd9c0f4f3c30d6eb98eb312a0a5c233b3fb0e34f91f527e01d6955461d7` | 1,359 B `2866efd132e69c2547031f6fc5a82a7ebf58f550fe090b8efd3139f0136a2e79` | 2,841 B `14870408c317c5c2b205cd71d466ab0cb3b61995cea2fe94aa072d52707fea35` |

Every downloaded release bundle passed `SHA256SUMS`. Sigstore/SLSA
attestations verified both JARs for every consumer against its exact tagged
main commit. Each release workflow also published and re-read the Maven
payloads and checksum sidecars before publishing the GitHub Release.

## Remaining boundary

Factory Blocks remains a non-migrated Athena candidate. Glassential and
Rechiseled: Create remain non-migrated Fusion candidates. Their emitters,
profiles, and bridge-specific behavior are not transferred by this pilot; each
requires its own package-normalized parity and archive-diff gate before it can
pin either module.

The immutable `atmons-1.2.0` compatibility tag and manifest remain unchanged.
These later compatible releases are recorded on main as consolidation
evidence and can be selected by a future compatibility snapshot; they do not
retroactively rewrite the published 1.2.0 snapshot.
