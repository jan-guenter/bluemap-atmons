# Toolkit v0.3 trust cohort 12

This records the twelfth artifact-parity toolkit cohort. Trophy Manager, Laser
Bridges & Doors, More Red, and Lootr already used the shared Gradle convention
from toolkit `v0.2.0-alpha.1`. This cohort moves their trust pins and
hash-locked toolkit wheels to `v0.3.0-alpha.1`. It does not update the ATMons
1.2.0 compatibility manifest, meta-repository gitlinks, add-on versions,
release tags, provenance, galleries, acceptance records, or renderer behavior.

## Scope and unchanged convention

Every repository replaces toolkit commit
`f58da04567f10efe615c582797f3ab00b7a7343f` with
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` in its mode-160000 gitlink and
consumer-owned `settings.gradle` trust preflight. The Gradle convention tree is
byte-for-byte identical at both commits:

```text
f58da04567f10efe615c582797f3ab00b7a7343f:gradle = b99dca5be05340e92229c3912d4ec0486d99b54b
6cd34a8368cc4ee8628fbe830a90ec5b14960629:gradle = b99dca5be05340e92229c3912d4ec0486d99b54b
```

Each repository replaces the 19,827-byte `v0.2.0-alpha.1` wheel, SHA-256
`cbfbad7ea12ea631b9f36a5261482dde3ca4d8f270df1b5faf75310020b115f9`,
with the 20,585-byte `v0.3.0-alpha.1` wheel, SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
Existing CI and release workflows derive the expected toolkit version from
the hash-locked requirement and remain byte-identical.

Each validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact candidate inputs were:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Trophy Manager | Trophy Manager 1.21.1-2.5.0 | 84,293 | `739f59d0879cff453e229e6a68a7f2e3dd131786da369f82204a8ff2004e7bbd` |
| Laser Bridges & Doors | Laser Bridges 5.3 | 199,979 | `51fbc91a5d5b28ff8664da3d60c1e13066f61d959ff7fabc15a7e3f55d8c9a72` |
| Laser Bridges & Doors | Deimos 2.7 | 49,576 | `ee35d4e8967ccb23dee3c1a05b55c8d4ac0e0045bf8d324e215b397869af0573` |
| More Red | More Red 1.21.1-6.0.0.3 | 535,669 | `8075126184f540c6b35b92127088f6cc4c9544627acac9f2287c62a0dfbde74e` |
| Lootr | Lootr 1.21.1-1.11.37.122 | 992,330 | `fd330d69bb0740d2833ad91784ee5f8b0e4c5d8dbee379e60e93ca2d1c252fce` |

## Reviewed merges

| Add-on | Reviewed PR | Base commit | Feature commit | Merge commit | Merge tree |
| --- | --- | --- | --- | --- | --- |
| Trophy Manager | [#5](https://github.com/jan-guenter/bluemap-trophy-manager-addon/pull/5) | `0c792db70c131cc7f9a43ae70eb03f7e07e48bdb` | `a76f3fb6c293c47ca030d25ec54b0c6ccfa2101f` | `6a7f5a7f49e18526ba04831f0c4d7bd8378a3946` | `9e9b8f567a818a310a95a8307d5ce9cec3260f2c` |
| Laser Bridges & Doors | [#5](https://github.com/jan-guenter/bluemap-laser-bridges-addon/pull/5) | `dddc23c089b52be1b40a56849f24e2759c8fd302` | `5ae6285c35ac96a4fe915a72c05e979e3eb06fbf` | `fb0b704b26e847558075eb263a9b450ce2df1a7f` | `db02852167f34e85fd0233479b3ff708ad39ea6d` |
| More Red | [#5](https://github.com/jan-guenter/bluemap-morered-addon/pull/5) | `a05bc8ce0e249fe2feafb426f8fb504f3ff498aa` | `f566e338c6a67caf1b2a17300539931a5031ab32` | `79a377bf340c646de19e08df15fb4a911bf55f44` | `d6e67356b36df131288d4cfe9f2dca90640aef52` |
| Lootr | [#5](https://github.com/jan-guenter/bluemap-lootr-addon/pull/5) | `9f99af6b9f00e35297e16a3dc8a6d59eb6b3c4de` | `2e352eca5bf178e607e43d04abcc18b47cbd65ee` | `ee513c7a6e30cd87c42cddfe5ba9e43107998310` | `a511658d286ec8633a0b991b6d7aba10951f2481` |

Every feature commit is owner-signed. Every merge has the reviewed base and
feature as its two parents, its tree equals the reviewed feature tree, and the
GitHub API verifies its merge signature.

Pull-request CI passed against GitHub's synthetic merge commits
(`8ce1a6b38be3b6afa01b3e4a45641628b5c22b40`,
`475f8c871b60ed25bd9e106bf998c72786661609`,
`45872dad26502b41337c4f069e44f4e6dc331604`, and
`8842416f12587d5546a5952d9b2bd32a38f4100d`, in table order). The post-merge
`main` runs passed at the exact merge commits:

| Add-on | Pull-request CI | Job | Artifact | Main CI | Job | Artifact |
| --- | --- | --- | --- | --- | --- | --- |
| Trophy Manager | [33283884676](https://github.com/jan-guenter/bluemap-trophy-manager-addon/actions/runs/33283884676) | `99183577474` | `9723826056` | [33284033736](https://github.com/jan-guenter/bluemap-trophy-manager-addon/actions/runs/33284033736) | `99183984385` | `9723865556` |
| Laser Bridges & Doors | [33284021042](https://github.com/jan-guenter/bluemap-laser-bridges-addon/actions/runs/33284021042) | `99183947301` | `9723858747` | [33284147252](https://github.com/jan-guenter/bluemap-laser-bridges-addon/actions/runs/33284147252) | `99184280897` | `9723897274` |
| More Red | [33284226872](https://github.com/jan-guenter/bluemap-morered-addon/actions/runs/33284226872) | `99184494230` | `9723923472` | [33284369424](https://github.com/jan-guenter/bluemap-morered-addon/actions/runs/33284369424) | `99184876224` | `9723963003` |
| Lootr | [33284617978](https://github.com/jan-guenter/bluemap-lootr-addon/actions/runs/33284617978) | `99185539432` | `9724039297` | [33284759143](https://github.com/jan-guenter/bluemap-lootr-addon/actions/runs/33284759143) | `99185906734` | `9724082497` |

No migration triggered a release workflow. Existing annotated release tags
remain on their publication commits:

| Add-on | Version | Tag object | Peeled release commit |
| --- | --- | --- | --- |
| Trophy Manager | `0.1.0-alpha.1` | `3350ced94263d88a5a94e0073ab62d1a74c0fe25` | `235fe54839a9521b0a70fd95822779fa499eee37` |
| Laser Bridges & Doors | `0.1.0-alpha.1` | `a15fdb8bb26d5c632072f7d977c792536c50bb12` | `e801361fa3495b1752cf4ab8d6c2a48e0caabd53` |
| More Red | `0.1.0-alpha.1` | `cfc514ec40e87161157075d9d42e52923cf407c6` | `845033ad8d49eab73986622dd964b6f5072a559e` |
| Lootr | `0.1.0-alpha.1` | `eda91967a5e56bac6927a42f6e06eb51dcd26199` | `f01d71c1f55a743d73d171677b18ed13be5756eb` |

## Artifact and gallery parity

The complete consumer gates reproduced every publication file byte for byte
before and after each migration. Downloaded pull-request and post-merge CI
outputs match the same public release bytes.

| Add-on | Output | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Trophy Manager | Production JAR | 92,121 | `3eb5e33df93231f362e749b9044fc450748e2a3d0f3998711d6871586aae00d9` |
| Trophy Manager | Sources JAR | 60,896 | `a2b66804a4aafa17ef33a95da9a1091f02804e89c491e3ffa99ab20d11702087` |
| Trophy Manager | POM | 1,359 | `86847924364a335698cf2cba160bf8772db7de9d2f00bc1317b069b5e9bdf018` |
| Trophy Manager | Module metadata | 2,866 | `3fd27364db38a912850ef37fe2410c2737f8be9d03849a72333e680a600b97d3` |
| Laser Bridges & Doors | Production JAR | 91,268 | `f4229a2ad89eafbc7c0d1a434cec53c859c051221804ee3013ed4fde34284193` |
| Laser Bridges & Doors | Sources JAR | 60,983 | `970204e3e5024c1d82ec0917303dedfdbe389d65ef8e810f4a4d55f6dac2e5c8` |
| Laser Bridges & Doors | POM | 1,377 | `f7447c62eb5d94b02b270c1a000ca72a7c76e4438d27e2ba9abc3e361d09d4c4` |
| Laser Bridges & Doors | Module metadata | 2,859 | `61ce9aba68e7d8e23cb7f21cd489cdf55590283269c903c75d44d83f7a715eef` |
| More Red | Production JAR | 93,178 | `8c146f92d2939a38093423e70dd7db248a28426fade75e5eb0cefb477dcc0f9d` |
| More Red | Sources JAR | 56,478 | `d654247036513ebf968261fe6e80e2062dbca45761b352ff92be23f9bbd0784b` |
| More Red | POM | 1,319 | `c144c5b76f6ab6c53c4a5b4159492e9da6c502c32650011c31c64e71c6e84df3` |
| More Red | Module metadata | 2,817 | `68209f0c70501f6e2b771fdebaa797ccc2b09b2107cf74aded43c004cadc9539` |
| Lootr | Production JAR | 138,464 | `009495162e9319990f7dfc427c4b5a9caa9279fbcd64740e51ccacaa37b06cc3` |
| Lootr | Sources JAR | 87,674 | `1b4ee55eaa619efe227080da7e5ae8190a8ec6647be4d398af4e70ce6abfe6f3` |
| Lootr | POM | 1,305 | `f158a4f7c4a7f7f7ff18a02cb8887df1baf1191c25c9094d8c7b11150a5ddd81` |
| Lootr | Module metadata | 2,805 | `416cceed4718ebeb35033a771144c9ed9b4a0a0648d76db536b9bb8baef82b7e` |

Gallery sources are unchanged. Fresh deterministic packages retain these
identities:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| Trophy Manager | 2,725 bytes | `ccd3126c7a7a89b3eabf9f94ac9d6437025a51e90b0965764142fda8b6f8353a` |
| Laser Bridges & Doors | 2,807 bytes | `26db018545e4ac16a99f15bb52ecf3b336385fa6f097a576321e1ed2db2ee4c6` |
| More Red | 4,546 bytes | `faebaf1139ebf88b6dc5656fa57276957f6120ceea5e75007f2eb9b0df15a8b8` |
| Lootr | 2,627 bytes | `cc05029c506345bfeabe651faa5d9c0d0f13828430fd33ed8a6ce75d0154200b` |

## Build-contract parity

Normalized consumer task surfaces, dependency trees, outgoing variants, and
39-task release dry-run sets remained unchanged. All four complete Gradle
gates passed with 51 actionable tasks. Their test reports recorded 7, 7, 15,
and 10 passing Java tests, respectively.

The hash-locked wheel version checks, repository checks where applicable,
gallery gates, and `actionlint` passed. Dirty toolkit worktrees, old or wrong toolkit
checkouts, altered wheel hashes, staged/index mismatches, and wrong release
tags were rejected by the applicable fail-closed gates. Every toolkit checkout
was restored clean at the exact v0.3 gitlink after the probes.

There is no convention-line reduction in this cohort because each repository
already used the shared convention. Consumer-owned dependency, publication,
manifest, gallery, packaging, exact-input, and release configuration remains
local. Existing acceptance statements are unchanged and are not reinterpreted
by this tooling-only migration.

## Result

The twelfth cohort moves four existing convention consumers to the v0.3
toolkit trust and wheel identities while retaining the byte-identical Gradle
convention, published artifacts, galleries, release identities, and renderer
behavior.
