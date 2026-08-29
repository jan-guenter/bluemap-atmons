# Shared Gradle convention cohort 5

This records the fifth artifact-parity adoption of the BlueMap Add-on Toolkit
Gradle convention. It changes development tooling only. It does not update the
ATMons 1.2.0 compatibility manifest, meta-repository gitlinks, add-on versions,
accepted release tags, provenance, or renderer behavior.

## Scope

The cohort contains four exact-profile add-ons with deterministic galleries
and sealed release gates:

- Tempad;
- Productive Metalworks;
- Productive Bees; and
- Railcraft Reborn.

Every repository pins toolkit `v0.3.0-alpha.1` at commit
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` with a mode-160000 gitlink and the
same explicit trust pin in `settings.gradle`. The corresponding 20,585-byte
Python wheel has SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
CI and release checkouts initialize recursive submodules without stored
credentials. The v0.3 checker recognizes the exact applied convention while
continuing to require the consumer-owned plugins and repository shape.

Each accepted validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact upstream inputs were:

- Tempad, 1,696,464 bytes at
  `932dd8a1cbb86d7632330ee3b9da43211b7c7a2fb6246443fd8207f74a74eba3`;
- Productive Metalworks, 3,033,210 bytes at
  `100132424f9659b76fd1326a8f0068a58b91d6d94351d47484b5b9cee394e812`;
- Productive Bees, 5,216,551 bytes at
  `9d48d198bc6eacf3b7729f4d60b91e661cfa15d105264ba225dee87b1d547ba1`;
  and
- Railcraft Reborn, 5,290,986 bytes at
  `7de3dfeac277da57f9897822824332c99e53b9d36956143b38c0966f39144328`.

## Reviewed merges

| Add-on | Reviewed PR | Feature commit | Merge commit | Gate |
| --- | --- | --- | --- | --- |
| Tempad | [#4](https://github.com/jan-guenter/bluemap-tempad-addon/pull/4) | `706b85655c4d6555ea4a9a47ed153015d498d894` | `fa931d71aaedd1138e180144c36edb8ef6dd447b` | Gradle 9.6.1 exact Tempad gate plus gallery checks |
| Productive Metalworks | [#4](https://github.com/jan-guenter/bluemap-productive-metalworks-addon/pull/4) | `124e66a4ba21ae81d98fd7fba9a5bed41f472020` | `97f32f860193a0f54832feeaa92f71e93c78d577` | Gradle 9.6.1 exact Productive Metalworks gate plus gallery checks |
| Productive Bees | [#4](https://github.com/jan-guenter/bluemap-productive-bees-addon/pull/4) | `463eaee3bbaaa00c2094ed921988295e91e51c90` | `6410cf3e9dd53e5345482bd2b57b83cf9b817b92` | Gradle 9.6.1 exact Productive Bees gate plus gallery checks |
| Railcraft Reborn | [#4](https://github.com/jan-guenter/bluemap-railcraft-reborn-addon/pull/4) | `03a9798ab71328c3fa2193076751b95b8d891e96` | `4623a931b5b1659173799a51fc74b0d2ccefe554` | Gradle 9.6.1 exact Railcraft gate plus gallery checks |

Every merge has the reviewed base and feature commits as its two parents, and
each merge tree equals its reviewed feature tree. The resulting merge trees
are `ae0df7888a8ba96a85e964222e4d4c3a95a8acf9` for Tempad,
`8a5ae9b3a1068f0d25e73a216ce36038ee759623` for Productive Metalworks,
`121fe11f133ccbc34354c030289defffdfbb3778` for Productive Bees, and
`003a761173e7c53027d43916e7112668d9c27e1c` for Railcraft Reborn.

The PR and post-merge `main` CI runs passed for all four repositories:

- [Tempad PR CI](https://github.com/jan-guenter/bluemap-tempad-addon/actions/runs/33275166093)
  and [main CI](https://github.com/jan-guenter/bluemap-tempad-addon/actions/runs/33275320443);
- [Productive Metalworks PR CI](https://github.com/jan-guenter/bluemap-productive-metalworks-addon/actions/runs/33274797387)
  and [main CI](https://github.com/jan-guenter/bluemap-productive-metalworks-addon/actions/runs/33274960034);
- [Productive Bees PR CI](https://github.com/jan-guenter/bluemap-productive-bees-addon/actions/runs/33274263360)
  and [main CI](https://github.com/jan-guenter/bluemap-productive-bees-addon/actions/runs/33274404345); and
- [Railcraft Reborn PR CI](https://github.com/jan-guenter/bluemap-railcraft-reborn-addon/actions/runs/33275599811)
  and [main CI](https://github.com/jan-guenter/bluemap-railcraft-reborn-addon/actions/runs/33275747180).

No migration triggered a release workflow. Every repository remains at
`0.1.0-alpha.1`. Its existing annotated `v0.1.0-alpha.1` tag remains on the
accepted release commit rather than the tooling merge:

| Add-on | Tag object | Peeled release commit |
| --- | --- | --- |
| Tempad | `49a59ec07d3488cd0285dc656062df9afd1013ed` | `9bd217d642be3b0abdac77a2f93098eba8c15fe9` |
| Productive Metalworks | `e9ee4f029713f26febab68a104cef4af8154988e` | `f7706461f5500067d610c0c2e5ed97371f16af81` |
| Productive Bees | `9436c5ba9377d0896010ff98128938d8797586be` | `c2fb4e93bd765bbe2e4ffb151764ae7431db9695` |
| Railcraft Reborn | `7302d8dbbd49829c8ef2787644c9345eda55976e` | `3ef611818c1fd6b8f2f1671776cbb390aad56024` |

## Artifact and gallery parity

The complete consumer gates reproduced these files byte for byte before and
after each migration. They also match the corresponding published
`0.1.0-alpha.1` release assets. Downloaded PR and post-merge CI artifacts were
compared to the same frozen bytes.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Tempad | `0026de4bd3de80f52f11f6ae223351c7ecae51cbd59c0adc85ab755fddbae95d` | `5efc725f617c15a854d24955994e40c890ba8ad66082d9d527c180df06d4cf45` | `2561162468849eaa4582c83827c8c5e56c3b37936a0fce0daba320786a24380a` | `0f6e52525dd0644ee94e0ffe38ad3652570f179b4f1c8eb78f88dcd62d7a2d99` |
| Productive Metalworks | `7b7890329de51230a8a455a45acac83e860932fda12b3e685d42522b138df0cd` | `5770bab905b956e8fa3a02443a81ef44bd80d9a2ab4ac552623b34eb1f6995be` | `808c63a8c99a292ebf406516835223d027c8b9d7ea4814271660275b9d753778` | `df455c1cfe90dd0bfd3f226258283fa7babc5cae1fdf9dffd1ae689403cfa9d6` |
| Productive Bees | `17643a965eaf55d5746ec74bd39df153762ac03aaddcd4f47005d9b9f683b1dc` | `46bcac248a86ec7a12f5c9e3d8f50a885cb650ee5edc2376ff0d9545fb0d2dc8` | `0f55679ffbbc7b675baf3b5b6a4d3ae680a7194408d0e5d8ba5057f9bb3e7add` | `5a571c352a7749c43f5d270f47a40cf090f82533feb55ab426c82dcc56651ddf` |
| Railcraft Reborn | `e4822c8756cada38958646a3b0c0e022d961b4549aa26254ebfc289a52190996` | `743f921a313c66349b6c961993d3f27db1e73df2d3687e1834eee595430f9353` | `cca8b30c15beee5eb328586155c591a57cca84b79dc268bf4715c151d94ac8e1` | `0c449f5a60a117cd579efd759c63afd0932906f0d7fb6b81baf67d450a416b92` |

The deterministic gallery ZIPs also remained byte-identical:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| Tempad | 2,643 bytes | `411eb96bbaa4a5d5fe8826d77316d46f622e308ab36490f4e3ff2fc3e1b56c03` |
| Productive Metalworks | 2,821 bytes | `e6b01bc0790b5ea717e1651463c648284d5ba2077eaa395ff087b9bbbb221bb3` |
| Productive Bees | 2,344 bytes | `68bc274ab1e7e8537f1a0577352d9abf0bf12b5d1cf71486504fdc2779bcbe6c` |
| Railcraft Reborn | 2,237 bytes | `d89af4bcb32d63528fc96c4604f24ebf243e47f9da491cdbd9cdc81616a0edda` |

## Build-contract parity

Dependency trees, outgoing variants, normalized task surfaces, and sorted
39-task release dry-run sets remained unchanged in every repository. The
additional `:gradle` tasks compile the included convention plugin. Consumer
repository, dependency, publication, manifest, gallery, packaging, debug, and
release configuration remains local. Java compile debug metadata and STORED
archive compression are unchanged.

Dirty toolkit worktrees and a checkout at toolkit v0.2 were rejected before
consumer configuration. Wrong release tags were rejected by every historical
release gate. After the probes, every toolkit checkout was restored clean at
the exact v0.3 gitlink.

The migration removes 104 repeated convention lines and adds four plugin
applications, a net reduction of 100 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Tempad | 504 | 479 | 25 lines |
| Productive Metalworks | 504 | 479 | 25 lines |
| Productive Bees | 504 | 479 | 25 lines |
| Railcraft Reborn | 504 | 479 | 25 lines |

The consumer-owned trust preflight remains repeated because an included
plugin cannot authenticate the source checkout from which it is loaded. CI
derives the toolkit CLI version from the exact wheel URL. Historical release
tags without `requirements/toolkit.txt` retain their tag-local release path
through the existing file-presence guard.

## Result

The fifth cohort confirms the v0.3 convention and its corrected checker across
four more Gradle 9.6.1 consumers without changing accepted artifacts or
release identities. Further adoption remains a repository-by-repository
migration with exact inputs, a frozen baseline, the complete local gate,
artifact comparison, reviewed PR CI, and post-merge `main` CI.
