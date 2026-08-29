# Shared Gradle convention cohort 6

This records the sixth artifact-parity adoption of the BlueMap Add-on Toolkit
Gradle convention. It changes development tooling only. It does not update the
ATMons 1.2.0 compatibility manifest, meta-repository gitlinks, add-on versions,
accepted release tags, provenance, or renderer behavior.

## Scope

The cohort contains four exact-profile add-ons with deterministic galleries
and sealed release gates:

- Theurgy;
- Draconic Evolution;
- PneumaticCraft; and
- Ars Nouveau.

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

- Theurgy, 5,324,349 bytes at
  `c4bc955e30f1155b83954a0c2aba80adf19f72e6f5d95cfd8d72e5afb5e60d8f`;
- Draconic Evolution, 6,045,942 bytes at
  `623d7d58e58428a206015b56bf67387c79ff6d97f7221cff23b1dad0bed9544e`;
- PneumaticCraft, 11,884,697 bytes at
  `647ce20d52cf139f3b693b9b4c4753966a95a6dafc82d9e538ae4ae5b0249f9c`;
  and
- Ars Nouveau, 20,096,005 bytes at
  `90796df69bfb39b1a9c79edbfa01c2425e5b86aea47dc55ebdcbf30e88f47592`.

## Reviewed merges

| Add-on | Reviewed PR | Feature commit | Merge commit | Gate |
| --- | --- | --- | --- | --- |
| Theurgy | [#4](https://github.com/jan-guenter/bluemap-theurgy-addon/pull/4) | `ba259cb89689715d815bf76462dab76a70827e56` | `2389f2706aa7291712a8bfc2bd7ac98d6590d157` | Gradle 9.6.1 exact Theurgy gate plus gallery checks |
| Draconic Evolution | [#4](https://github.com/jan-guenter/bluemap-draconic-evolution-addon/pull/4) | `36db3e9c1a024ebf64ab89e55bd2e214206fcff4` | `2add73bee015a7264e6707c19920ecb94337c5e5` | Gradle 9.6.1 exact Draconic Evolution gate plus gallery checks |
| PneumaticCraft | [#4](https://github.com/jan-guenter/bluemap-pneumaticcraft-addon/pull/4) | `a259b99679341ad7ea0f2a0fbf81ab6b91c64c9e` | `9266bc022662ea7611e17334ef3f03d91a5355dc` | Gradle 9.6.1 exact PneumaticCraft gate plus gallery checks |
| Ars Nouveau | [#4](https://github.com/jan-guenter/bluemap-ars-nouveau-addon/pull/4) | `a247a095ea534c0092c8d772d743ccdfdf45cd82` | `c5eaf5307079250cdc88a39c7cb584f84f592230` | Gradle 9.6.1 exact Ars Nouveau gate plus gallery checks |

Every merge has the reviewed base and feature commits as its two parents, and
each merge tree equals its reviewed feature tree. The resulting merge trees
are `8ebcf46b184ee0c57e609e7a8cfc5d5725489987` for Theurgy,
`2a046f05b8547278ae8a010d0f671f7167d31556` for Draconic Evolution,
`603e28214c86a65a47dfb62016e018576fd89c58` for PneumaticCraft, and
`ffd39878c2bf874aeeab173bbde34caa217531d2` for Ars Nouveau.

The PR and post-merge `main` CI runs passed for all four repositories:

- [Theurgy PR CI](https://github.com/jan-guenter/bluemap-theurgy-addon/actions/runs/33276137562)
  and [main CI](https://github.com/jan-guenter/bluemap-theurgy-addon/actions/runs/33276275136);
- [Draconic Evolution PR CI](https://github.com/jan-guenter/bluemap-draconic-evolution-addon/actions/runs/33276666032)
  and [main CI](https://github.com/jan-guenter/bluemap-draconic-evolution-addon/actions/runs/33276820271);
- [PneumaticCraft PR CI](https://github.com/jan-guenter/bluemap-pneumaticcraft-addon/actions/runs/33277071585)
  and [main CI](https://github.com/jan-guenter/bluemap-pneumaticcraft-addon/actions/runs/33277230656); and
- [Ars Nouveau PR CI](https://github.com/jan-guenter/bluemap-ars-nouveau-addon/actions/runs/33277590506)
  and [main CI](https://github.com/jan-guenter/bluemap-ars-nouveau-addon/actions/runs/33277737382).

No migration triggered a release workflow. Every repository remains at
`0.1.0-alpha.1`. Its existing annotated `v0.1.0-alpha.1` tag remains on the
accepted release commit rather than the tooling merge:

| Add-on | Tag object | Peeled release commit |
| --- | --- | --- |
| Theurgy | `3b80685f2e10c95534826c5dbea4bab38082cfd0` | `7d27df09578fd521644ac15a4caf232b9729f312` |
| Draconic Evolution | `761f83b003694470bbabecc94fda5af14e4b82b0` | `c9c37d3a07fdcbf971a1e1c28b2845c494260a7b` |
| PneumaticCraft | `4bb5e7c1038cc98812dcd2b7d9808aafa6e898d2` | `91a4f84bce2d76e0204daeb05ad7d720b3fd548f` |
| Ars Nouveau | `fe0c5a00e661b196903b8de537fe6fed78a54ffe` | `32cb3e041bc7bc5bb4e6325cfb8b57a9604f4c28` |

## Artifact and gallery parity

The complete consumer gates reproduced these files byte for byte before and
after each migration. They also match the corresponding published
`0.1.0-alpha.1` release assets. Downloaded PR and post-merge CI artifacts were
compared to the same frozen bytes.

Ars Nouveau's historical staging JAR was no longer available for a direct
whole-file comparison. Its unchanged 44-entry acceptance manifest still
passed against the reproduced production JAR, and the production JAR and all
published metadata matched prior CI and the public release byte for byte.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Theurgy | `8517196b56ddc9c180e792ad33f28347781b3f08ffe9805f23b7932182035ce0` | `bece16bcb70dbcc1acba7a0957a67a8855f6373433abace9276d2eafe5a111fd` | `6eea85da84054cfafbf51ec182907d5910dace7fdced157b10e73b4ea94b772e` | `68c8a936745f36276394a7e6b325892fd375fe411c8e5247e1c5738ff8285eb2` |
| Draconic Evolution | `78281d7a3a8f2badfd0c7fb01312d3a15f0adcf261889e9b662b3f5ab33403ef` | `80a5da38d1e26c525a61b67175cd99b5ea1e8a8c90945cfeb354fb08b2c6ca7f` | `73636c790f5be28e3b027355b2faff5a6e47875f01eebe590b844b8477e4a8d9` | `c289eaa6c943338b9f59d57ec20a551a29cfd59e082950223b07aa5d188945e5` |
| PneumaticCraft | `683a151fa8156136e3ce30df3cc887ed7ccfc695b3457cd27bc281c29d836f6c` | `ad77fc1caa9a1ee38cda2e1557cb43ad99ab4274510403bfd87536b432301910` | `bc3a2d2a9695fcb0539fe944b0c94b736e2b7e659e4e2b167283256602531cb1` | `20aa8e912556f2ca298b2f82da3353061322bc675bfde6295c2e15438f0d90b6` |
| Ars Nouveau | `d048145174754f9a134fcac449fd200ee6b423aedeca74fff3eef21f60e20c2d` | `85029f1eda5878b76d742f39fa96a3470fe7718ed121d58ad99431a426b16369` | `776cac1ec9abcf4a2b16e3ff1102036f18948e93ef5040fa22054904bba2686c` | `2b22525d6e3108d9540b0a599405c9cade6aa933f707969022029d36955fdc9b` |

The deterministic gallery ZIPs also remained byte-identical:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| Theurgy | 2,055 bytes | `54fa39efe9482be486e4da2f787e8e50257c34a8fbfe62ab9107f43fb6568927` |
| Draconic Evolution | 2,532 bytes | `9e6fcc7c16c973355fe35aa7a24dcf08efb8b809e010155a82fc7015cc4d9cc5` |
| PneumaticCraft | 2,939 bytes | `cf4057532ac43ae5e68db672e4343f5321a59906d46cd4146a35583f8fddd941` |
| Ars Nouveau | 2,993 bytes | `a226b8ad42bbd3a6b8fea422d72fc941d1741f6f879287e600b75bd1f64bb21e` |

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
| Theurgy | 504 | 479 | 25 lines |
| Draconic Evolution | 504 | 479 | 25 lines |
| PneumaticCraft | 504 | 479 | 25 lines |
| Ars Nouveau | 504 | 479 | 25 lines |

The consumer-owned trust preflight remains repeated because an included
plugin cannot authenticate the source checkout from which it is loaded. CI
derives the toolkit CLI version from the exact wheel URL. Historical release
tags without `requirements/toolkit.txt` retain their tag-local release path
through the existing file-presence guard.

## Result

The sixth cohort confirms the v0.3 convention and its corrected checker across
four more Gradle 9.6.1 consumers without changing accepted artifacts or
release identities. Further adoption remains a repository-by-repository
migration with exact inputs, a frozen baseline, the complete local gate,
artifact comparison, reviewed PR CI, and post-merge `main` CI.
