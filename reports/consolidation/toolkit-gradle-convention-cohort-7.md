# Shared Gradle convention cohort 7

This records the seventh artifact-parity adoption of the BlueMap Add-on
Toolkit Gradle convention. It changes development tooling only. It does not
update the ATMons 1.2.0 compatibility manifest, meta-repository gitlinks,
add-on versions, accepted release tags, provenance, or renderer behavior.

## Scope

The cohort contains four exact-profile add-ons with multi-artifact admission,
installed-resource contracts, and deterministic galleries:

- Extreme Reactors;
- Ars Creo;
- Ars Energistique; and
- Ars Technica.

Every repository pins toolkit `v0.3.0-alpha.1` at commit
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` with a mode-160000 gitlink and the
same explicit trust pin in `settings.gradle`. The corresponding 20,585-byte
Python wheel has SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
CI and release checkouts initialize recursive submodules without stored
credentials.

Each accepted validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The complete exact-input set was:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Extreme Reactors | Extreme Reactors 2.4.28 | 2,554,779 | `74fdfdfc91c3c8e5a439d411e6f081d12193635fffe2c55142f2f28f75b9d621` |
| Extreme Reactors | ZeroCore 2.4.21 | 1,551,013 | `54ac755031b05c3a5b6ddfa22dabc45fb3775481041503dcecd75e5e86627779` |
| Ars Creo | Ars Creo 5.4.0 | 95,973 | `50f0fe5c5f855151c1482c1772ea94c2eaadc2b0c85c963bb9aeb421fc801e4f` |
| Ars Creo | Ars Nouveau 5.13.0 | 20,096,005 | `90796df69bfb39b1a9c79edbfa01c2425e5b86aea47dc55ebdcbf30e88f47592` |
| Ars Creo | Create 6.0.10 | 19,123,767 | `ef87fe5709f1ba1f5b8bb20a2925b5afb4669e178fd6d8bf10c167759eefe37a` |
| Ars Energistique | Ars Energistique 2.1.1-beta | 123,229 | `9e2b78101f08bf325589cb98ffba9d91171fdd76ba587d54bdef9d5de18080bc` |
| Ars Energistique | Applied Energistics 2 19.2.17 | 8,230,896 | `460d779a0609b81409907d9956de8f6f70a1b0912257e3e5c3c7e75ac9630e95` |
| Ars Energistique | Ars Nouveau 5.13.0 | 20,096,005 | `90796df69bfb39b1a9c79edbfa01c2425e5b86aea47dc55ebdcbf30e88f47592` |
| Ars Energistique | BlueMap AE2 add-on 0.1.0-alpha.3 | 1,252,649 | `f7014e1c60bdf02fa22583a7b5b5cbf6f3076a0b2371601360775507d473a12d` |
| Ars Technica | Ars Technica 2.7.6 | 3,691,171 | `64b70f39f8c8ca38262c69e2b84a6494a8a11c8ef7e570d8136b1818d5d3159d` |
| Ars Technica | Ars Nouveau 5.13.0 | 20,096,005 | `90796df69bfb39b1a9c79edbfa01c2425e5b86aea47dc55ebdcbf30e88f47592` |
| Ars Technica | Create 6.0.10 | 19,123,767 | `ef87fe5709f1ba1f5b8bb20a2925b5afb4669e178fd6d8bf10c167759eefe37a` |

## Reviewed merges

| Add-on | Reviewed PR | Feature commit | Merge commit | Gate |
| --- | --- | --- | --- | --- |
| Extreme Reactors | [#4](https://github.com/jan-guenter/bluemap-extreme-reactors-addon/pull/4) | `aef40b2de00632df2d0db37c91c901a2490c3a40` | `1451f3aaff6cb4df55faa7ab75b4511862aad920` | Gradle 9.6.1 exact two-input turbine gate |
| Ars Creo | [#4](https://github.com/jan-guenter/bluemap-ars-creo-addon/pull/4) | `62815b83c547f9e4902be39d83728c2d59a4ced7` | `527ca68d39cec284a3baee2cb81625324d469bfe` | Gradle 9.6.1 exact three-input animation-resource gate |
| Ars Energistique | [#4](https://github.com/jan-guenter/bluemap-ars-energistique-addon/pull/4) | `5ea61daa182368f5909918805e1d672aee9cc486` | `a88c4932eccb86e5e857d0b73d50b3a56019dd60` | Gradle 9.6.1 exact four-input AE2 API gate |
| Ars Technica | [#4](https://github.com/jan-guenter/bluemap-ars-technica-addon/pull/4) | `bc2d83f325eaa9cb0a1035e0fc051342fa14c710` | `48523b5ae13b4926f00dfd9fe3f208b86d5a4bad` | Gradle 9.6.1 exact three-input installed-resource gate |

Every completed merge has the reviewed base and feature commits as its two
parents, and each merge tree equals its reviewed feature tree. The resulting
trees are `ddf036f22f8e75451bf62e5a0f0b9203cd60d5e7` for Extreme Reactors,
`220953caf0bbecb2c393cdba48be4e0545fba470` for Ars Creo,
`393e9ee102f8c0f7bb403afb224d59aa5ffe569a` for Ars Energistique, and
`073f3da76abe429b9b5c964c46aad124936c658c` for Ars Technica.

The PR and post-merge `main` CI runs passed for all four repositories:

- [Extreme Reactors PR CI](https://github.com/jan-guenter/bluemap-extreme-reactors-addon/actions/runs/33278839451)
  and [main CI](https://github.com/jan-guenter/bluemap-extreme-reactors-addon/actions/runs/33279010952);
- [Ars Creo PR CI](https://github.com/jan-guenter/bluemap-ars-creo-addon/actions/runs/33279136092)
  and [main CI](https://github.com/jan-guenter/bluemap-ars-creo-addon/actions/runs/33279259133);
- [Ars Energistique PR CI](https://github.com/jan-guenter/bluemap-ars-energistique-addon/actions/runs/33278032742)
  and [main CI](https://github.com/jan-guenter/bluemap-ars-energistique-addon/actions/runs/33278179764); and
- [Ars Technica PR CI](https://github.com/jan-guenter/bluemap-ars-technica-addon/actions/runs/33278584319)
  and [main CI](https://github.com/jan-guenter/bluemap-ars-technica-addon/actions/runs/33278710256).

No migration triggered a release workflow. Every repository remains at
`0.1.0-alpha.1`. Its existing annotated `v0.1.0-alpha.1` tag remains on the
accepted release commit rather than the tooling merge:

| Add-on | Tag object | Peeled release commit |
| --- | --- | --- |
| Extreme Reactors | `3d9b429ebc65888a251fd939a8894e162817ba37` | `c6a70f0ec38e984c4c349742b921a87cd4d21e18` |
| Ars Creo | `650e7ef6d6235a207e040e9d02bf5852926ac6f9` | `f27921f918928a813d8bf9d0aa607184de41d9e2` |
| Ars Energistique | `b364b769c0018e01241f1b38a656b8f716ce151d` | `33a8cc848d51384dcc11d817c09957601a9c7234` |
| Ars Technica | `abd47fdb245d2c8c122cfe5243b47e4452e5f3bb` | `76c8a262fc42f309f3ad8ba039c79d8fe0a42ae1` |

## Artifact and gallery parity

The complete consumer gates reproduced these files byte for byte before and
after each migration. They also match the corresponding published
`0.1.0-alpha.1` release assets. Downloaded PR and post-merge CI artifacts were
compared to the same frozen bytes.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Extreme Reactors | `60eaf0b401742fbc40a8500948234e72010b4a8224395893af8b521b2aed0d24` | `10eefcfc78fb589cb157b11e84026463cf59937aa6508ff42b719f42dcad7774` | `bd8a6380c0ae036e2523d843957c8bdbdb9d876d071aba229daee3af2d832baa` | `7e5de5c86484e0d3ce5ae6e97ad8e81de9235e573e98109de3a7f5290bc2fde0` |
| Ars Creo | `bcf9ac905e3d9b7702da666c3be131a6b24ab6b8dfd472b8ffa5d5e014cb1938` | `7eb10fb91b2f6236a33774302aae099f13d0e63c75863fb83f0b449b2c04a731` | `bb12a4739aad8a04fff8d08f8bd6e6630c6ac9074cb7e401f2466b8551353e82` | `9c159e78c4a9f0a1f7550ebcd904612c558063e3e844a6296d7ae7ebf25973b2` |
| Ars Energistique | `5f679b5af007401e0456e0de7168527d401c77cf79c500b5f18a102184659a7f` | `6c6bd79053f3da435b1d8e735714a3462d4334473737f07d777a5bc3c5a32d42` | `d631d912a2bd53e7e39d7debe37c723c1c0714e1810e3238b426fdaf14398c99` | `50d76647c8ec340ba46cb3a5a6fded627d2c4942b87ef0ab08046d25ff9a30c7` |
| Ars Technica | `4b36968ee1ed53614ba1de5d11277f073ed43c94c48470e53fbbca2679e8e643` | `33a905f4f2d0482240874a1245ae1ba917c768747432a95713cff61e5f45e4db` | `dc5304a9541054f0963aea021d468c082be44375829f6b23908aed43fd601705` | `9a59fd709fb6d118c2f5a18bcf5b6706c06024674a46a97de80ea26e5587d393` |

The deterministic gallery ZIPs also remained byte-identical:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| Extreme Reactors | 5,235 bytes | `ac32372112dd9455d40516b922745304ddf89393dd00d94fcce2921e57d47f1b` |
| Ars Creo | 2,054 bytes | `728cc0dcb72be87b7bda26a5520a4b907a7638e3107bf493f648ab622e922274` |
| Ars Energistique | 2,966 bytes | `9e9471807fecb1f7a13d1d61aa2cc8e4f16c18039ea8f8ff48d07d8f56e59a1a` |
| Ars Technica | 2,443 bytes | `fb9796612f2ff0de1f3a777df6ffe6e966c99884a54fb18f46171f26ccae7703` |

## Build-contract parity

Dependency trees, outgoing variants, normalized task surfaces, and sorted
release dry-run sets remained unchanged in every repository. Extreme
Reactors, Ars Creo, and Ars Technica retain 39 tasks. Ars Energistique retains
40 because its family-owned `verifyAe2AddonApiJar` gate validates the exact
AE2 add-on API dependency. The additional `:gradle` tasks only compile the
included convention plugin.

Consumer repository, dependency, publication, manifest, gallery, packaging,
debug, resource-pin, and release configuration remains local. Java compile
debug metadata and STORED archive compression are unchanged. Existing Gradle
10 deprecation warnings originate in the pinned BlueMap build and were not
changed as part of this migration.

Dirty toolkit worktrees and a checkout at toolkit v0.2 were rejected before
consumer configuration. Wrong release tags were rejected by every historical
release gate. After the probes, every toolkit checkout was restored clean at
the exact v0.3 gitlink.

The migration removes 104 repeated convention lines and adds four plugin
applications, a net reduction of 100 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Extreme Reactors | 505 | 480 | 25 lines |
| Ars Creo | 506 | 481 | 25 lines |
| Ars Energistique | 532 | 507 | 25 lines |
| Ars Technica | 506 | 481 | 25 lines |

The consumer-owned trust preflight remains repeated because an included
plugin cannot authenticate the source checkout from which it is loaded. CI
derives the toolkit CLI version from the exact wheel URL. Historical release
tags without `requirements/toolkit.txt` retain their tag-local release path
through the existing file-presence guard.

## Result

The seventh cohort confirms the v0.3 convention and corrected checker across
four multi-artifact Gradle 9.6.1 consumers without changing accepted artifacts
or release identities. Further adoption remains a repository-by-repository
migration with exact inputs, a frozen baseline, the complete local gate,
artifact comparison, reviewed PR CI, and post-merge `main` CI.
