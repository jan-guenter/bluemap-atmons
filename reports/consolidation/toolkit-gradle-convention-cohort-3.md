# Shared Gradle convention cohort 3

This records the third artifact-parity adoption of the BlueMap Add-on Toolkit
Gradle convention. It changes development tooling only. It does not update the
ATMons 1.2.0 compatibility manifest, meta-repository gitlinks, add-on versions,
accepted release tags, licenses, provenance, or renderer behavior.

## Scope

The cohort contains four exact-profile add-ons with generated-gallery and
staged-equivalence release gates:

- Trophy Manager;
- Laser Bridges & Doors;
- More Red; and
- Lootr.

Every repository pins toolkit `v0.2.0-alpha.1` at commit
`f58da04567f10efe615c582797f3ab00b7a7343f` with a mode-160000 gitlink and the
same explicit trust pin in `settings.gradle`. The matching 19,827-byte Python
wheel has SHA-256
`cbfbad7ea12ea631b9f36a5261482dde3ca4d8f270df1b5faf75310020b115f9`.
CI and release checkouts initialize recursive submodules without stored
credentials.

Each accepted validation used its own clean BlueMap checkout at commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact upstream inputs were
Trophy Manager `1.21.1-2.5.0`, Laser Bridges `5.3` with Deimos `2.7`, More Red
`1.21.1-6.0.0.3`, and Lootr `1.21.1-1.11.37.122`.

## Reviewed merges

| Add-on | Reviewed PR | Feature commit | Merge commit | Gate |
| --- | --- | --- | --- | --- |
| Trophy Manager | [#4](https://github.com/jan-guenter/bluemap-trophy-manager-addon/pull/4) | `7584dc1c7d101e3a6d2d0ef4318ed396e5efdb4b` | `0c792db70c131cc7f9a43ae70eb03f7e07e48bdb` | Gradle 9.6.1 exact Trophy Manager gate plus gallery checks |
| Laser Bridges & Doors | [#4](https://github.com/jan-guenter/bluemap-laser-bridges-addon/pull/4) | `f1ca171eb48674d6971125417074767963142b47` | `dddc23c089b52be1b40a56849f24e2759c8fd302` | Gradle 9.6.1 exact Laser Bridges/Deimos gate plus gallery checks |
| More Red | [#4](https://github.com/jan-guenter/bluemap-morered-addon/pull/4) | `1e23674ea2c990f9a10473d2c4fd8b3a8158584f` | `a05bc8ce0e249fe2feafb426f8fb504f3ff498aa` | Gradle 9.6.1 exact More Red gate plus gallery checks |
| Lootr | [#4](https://github.com/jan-guenter/bluemap-lootr-addon/pull/4) | `6e066fef24e44c038872ffdabd86ca30374631b3` | `9f99af6b9f00e35297e16a3dc8a6d59eb6b3c4de` | Gradle 9.6.1 exact Lootr gate plus gallery checks |

Every merge has the reviewed base and feature commits as its two parents, and
each merge tree equals its reviewed feature tree. The resulting merge trees
are `3a94e8dea8b619ef1742b7efecbd2f3ae0a06293` for Trophy Manager,
`9ff673280320999f4c53a8ae4164e66b17a6bf81` for Laser Bridges,
`5d95589e68b74df74ff59e52c7a1bf8896002499` for More Red, and
`29ca88b75f0bbe817fcf4af25a171b93f55be03d` for Lootr.

The PR and post-merge `main` CI runs passed for all four repositories:

- [Trophy Manager PR CI](https://github.com/jan-guenter/bluemap-trophy-manager-addon/actions/runs/33270097614)
  and [main CI](https://github.com/jan-guenter/bluemap-trophy-manager-addon/actions/runs/33270237894);
- [Laser Bridges PR CI](https://github.com/jan-guenter/bluemap-laser-bridges-addon/actions/runs/33269965353)
  and [main CI](https://github.com/jan-guenter/bluemap-laser-bridges-addon/actions/runs/33270092475);
- [More Red PR CI](https://github.com/jan-guenter/bluemap-morered-addon/actions/runs/33269972528)
  and [main CI](https://github.com/jan-guenter/bluemap-morered-addon/actions/runs/33270084956); and
- [Lootr PR CI](https://github.com/jan-guenter/bluemap-lootr-addon/actions/runs/33270010742)
  and [main CI](https://github.com/jan-guenter/bluemap-lootr-addon/actions/runs/33270144591).

No migration triggered a release workflow. Every repository remains at
`0.1.0-alpha.1`. Its existing annotated `v0.1.0-alpha.1` tag remains on the
accepted release commit rather than the tooling merge:

| Add-on | Tag object | Peeled release commit |
| --- | --- | --- |
| Trophy Manager | `3350ced94263d88a5a94e0073ab62d1a74c0fe25` | `235fe54839a9521b0a70fd95822779fa499eee37` |
| Laser Bridges & Doors | `a15fdb8bb26d5c632072f7d977c792536c50bb12` | `e801361fa3495b1752cf4ab8d6c2a48e0caabd53` |
| More Red | `cfc514ec40e87161157075d9d42e52923cf407c6` | `845033ad8d49eab73986622dd964b6f5072a559e` |
| Lootr | `eda91967a5e56bac6927a42f6e06eb51dcd26199` | `f01d71c1f55a743d73d171677b18ed13be5756eb` |

## Artifact and gallery parity

The complete consumer gates reproduced these files byte for byte before and
after each migration. They also match the corresponding published
`0.1.0-alpha.1` release assets.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Trophy Manager | `3eb5e33df93231f362e749b9044fc450748e2a3d0f3998711d6871586aae00d9` | `a2b66804a4aafa17ef33a95da9a1091f02804e89c491e3ffa99ab20d11702087` | `86847924364a335698cf2cba160bf8772db7de9d2f00bc1317b069b5e9bdf018` | `3fd27364db38a912850ef37fe2410c2737f8be9d03849a72333e680a600b97d3` |
| Laser Bridges & Doors | `f4229a2ad89eafbc7c0d1a434cec53c859c051221804ee3013ed4fde34284193` | `970204e3e5024c1d82ec0917303dedfdbe389d65ef8e810f4a4d55f6dac2e5c8` | `f7447c62eb5d94b02b270c1a000ca72a7c76e4438d27e2ba9abc3e361d09d4c4` | `61ce9aba68e7d8e23cb7f21cd489cdf55590283269c903c75d44d83f7a715eef` |
| More Red | `8c146f92d2939a38093423e70dd7db248a28426fade75e5eb0cefb477dcc0f9d` | `d654247036513ebf968261fe6e80e2062dbca45761b352ff92be23f9bbd0784b` | `c144c5b76f6ab6c53c4a5b4159492e9da6c502c32650011c31c64e71c6e84df3` | `68209f0c70501f6e2b771fdebaa797ccc2b09b2107cf74aded43c004cadc9539` |
| Lootr | `009495162e9319990f7dfc427c4b5a9caa9279fbcd64740e51ccacaa37b06cc3` | `1b4ee55eaa619efe227080da7e5ae8190a8ec6647be4d398af4e70ce6abfe6f3` | `f158a4f7c4a7f7f7ff18a02cb8887df1baf1191c25c9094d8c7b11150a5ddd81` | `416cceed4718ebeb35033a771144c9ed9b4a0a0648d76db536b9bb8baef82b7e` |

The deterministic gallery ZIPs also remained byte-identical:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| Trophy Manager | 2,725 bytes | `ccd3126c7a7a89b3eabf9f94ac9d6437025a51e90b0965764142fda8b6f8353a` |
| Laser Bridges & Doors | 2,807 bytes | `26db018545e4ac16a99f15bb52ecf3b336385fa6f097a576321e1ed2db2ee4c6` |
| More Red | 4,546 bytes | `faebaf1139ebf88b6dc5656fa57276957f6120ceea5e75007f2eb9b0df15a8b8` |
| Lootr | 2,627 bytes | `cc05029c506345bfeabe651faa5d9c0d0f13828430fd33ed8a6ce75d0154200b` |

## Build-contract parity

Laser Bridges and Lootr reproduced their dependency and outgoing-variant
reports byte for byte. Trophy Manager reproduced the dependency trees and
outgoing-variant body; its full reports differ only by the included plugin's
own task lines and timing summary. More Red reproduced its normalized
dependency graph, semantic outgoing-variant body, and 39-task consumer set;
the only other normalized outgoing difference is one blank line after BlueMap
API configuration. Consumer and BlueMap task sets remain unchanged in all four
repositories. The additional tasks compile the included convention plugin.

All four build scripts retain family-owned repository, dependency,
publication, manifest, gallery, packaging, debug, and release configuration.
The migration preserves Java compile debug metadata and STORED archive
compression. It removes 104 repeated convention lines and adds four plugin
applications, a net reduction of 100 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Trophy Manager | 504 | 479 | 25 lines |
| Laser Bridges & Doors | 505 | 480 | 25 lines |
| More Red | 504 | 479 | 25 lines |
| Lootr | 504 | 479 | 25 lines |

The consumer-owned trust preflight remains repeated because an included plugin
cannot authenticate the source checkout from which it is loaded. Current CI
derives the toolkit CLI version from the exact wheel URL. Historical release
tags without `requirements/toolkit.txt` retain their tag-local release path
through the existing file-presence guard.

## Result

The third cohort confirms the convention across four more Gradle 9.6.1
consumers without changing accepted artifacts or release identities. Further
adoption remains a repository-by-repository migration with exact inputs, a
frozen baseline, the complete local gate, artifact comparison, reviewed PR CI,
and post-merge `main` CI.
