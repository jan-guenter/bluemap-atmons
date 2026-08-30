# Shared Gradle convention cohort 15

This report records the fifteenth artifact-parity adoption of the BlueMap
Add-on Toolkit Gradle convention. It changes development tooling only. It does
not update the ATMons 1.2.0 compatibility manifest, meta-repository gitlinks,
add-on versions, release tags, provenance, galleries, acceptance records, or
renderer behavior.

## Scope

The cohort contains Modular Routers, Rechiseled Create, Cobblemon Stone
Statues, and Botany Pots. Each repository pins toolkit `v0.3.0-alpha.1` at
commit `6cd34a8368cc4ee8628fbe830a90ec5b14960629` with a mode-160000 gitlink
and the same consumer-owned trust preflight in `settings.gradle`.

All four repositories consume only the toolkit's source-distributed Gradle
convention. None adopts the toolkit wheel or repository checker: their
existing Python tools and tests remain family-owned and do not call the
toolkit CLI. The source checkout is development-only and adds no installed
runtime dependency or packaged file.

Every validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact candidate inputs were:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Modular Routers | Modular Routers 13.2.7 | 1,285,765 | `10f84e7f2d1bc7b655d8398d8c2e7146c4929c3ad2c97408f940ca86c1bf898c` |
| Modular Routers | Glassential add-on 0.1.0-alpha.1 | 162,440 | `a956e62f7b843391917b861c831545b07af43ccceaa0bb84465e7e0b14c49780` |
| Rechiseled Create | Rechiseled Create 1.1.1 | 983,177 | `ba89cd5d1221621ed226cc7f1c26dc84a660cc4f6d122753052429f96d71248d` |
| Rechiseled Create | Rechiseled 1.2.5 | 11,498,611 | `7bf14cf8a4bfdc4b6c990126a75da29fd2bb7559d1c05b71e29c8fd5ae044435` |
| Rechiseled Create | Fusion 1.3.12 | 923,270 | `17f5215648a98bcde4134577b013200dbf363273ae282449c51408ae8346f2fa` |
| Rechiseled Create | Create 6.0.10 | 19,123,767 | `ef87fe5709f1ba1f5b8bb20a2925b5afb4669e178fd6d8bf10c167759eefe37a` |
| Cobblemon Stone Statues | Stone Statues 1.1 | 170,977 | `0fece8e5a988b660f2b608a316f88e2572290835fec1acf67d78329133e92f09` |
| Cobblemon Stone Statues | Cobblemon 1.7.3+1.21.1 | 128,748,941 | `962d75df4fb649d94863a7a7d130d4d2b3de4da9b3cae4c44b1ce90f37ec0ed5` |
| Botany Pots | Botany Pots 21.1.44 | 1,068,816 | `45b23ac195511f724f62ab5f0c2d7a1c2c2403ff324a7403a1142e28a7d65edd` |

## Reviewed merges

| Add-on | Reviewed PR | Base commit | Owner-signed feature commit | True verified merge | Merge tree |
| --- | --- | --- | --- | --- | --- |
| Modular Routers | [#7](https://github.com/jan-guenter/bluemap-modular-routers-addon/pull/7) | `0ed76c1f08ac9a644bd58cfef74a6c574f6dffcb` | `7fc3487e2e801f8ba2c8a2704f30550b6480f9d6` | `5e3b494718968b6cffdb7bd5bac66c13e738d576` | `2736ce93fb7b070fafbdf883e9d942ffc72edd87` |
| Rechiseled Create | [#3](https://github.com/jan-guenter/bluemap-rechiseled-create-addon/pull/3) | `ec34adeece54fbbba4d0312ec5f18f47556cc9ec` | `dfb15d3e7ec09f1c7b06d69e4b2c985cb0ca0040` | `28c508ec804187d340f29626251ad581accc592e` | `b8dec785205b1c3735e0495d743cd4da1ff800b4` |
| Cobblemon Stone Statues | [#3](https://github.com/jan-guenter/bluemap-cobblemonstonestatues-addon/pull/3) | `531fd94f0b982a571839d782a8a4788d3873494f` | `ee638e0983eeda0308d042a3863c388d8d4cb1b2` | `952a65bf6087d53b342950cb0989579219c8ab7a` | `6a7208b4caa4107bde1ca440c5380f762f57592b` |
| Botany Pots | [#3](https://github.com/jan-guenter/bluemap-botanypots-addon/pull/3) | `250da38f5601c6defef66949479b1b8d74c87be9` | `935654211b8f3e816bf753305de14c6c3179ab4d` | `e96cf6aac90c72920a3cd2eda7cfc19e6d20f71e` | `b8ce95d563de3f62d8b26751d47dbd8706991b83` |

Every feature commit has a valid owner signature. Every true merge has the
reviewed base and feature as its two parents, its tree equals the reviewed
feature tree, and the GitHub API reports `verified: true` with reason `valid`.

Pull-request CI did not test those feature commits directly. GitHub reported
the feature as the Actions `headSha`, while the checkout and artifact used the
synthetic pull-request merge commit shown below. Each synthetic commit has the
same reviewed base and feature parents and the same tree as its feature; the
GitHub API also reports each synthetic commit as verified and valid.

| Add-on | Synthetic PR checkout | Pull-request CI / job / artifact | Main CI / job / artifact |
| --- | --- | --- | --- |
| Modular Routers | `f1276723e634fa97c587500c3c454bfa80ee052e` | [33286680526](https://github.com/jan-guenter/bluemap-modular-routers-addon/actions/runs/33286680526) / `99190956003` / `9724674120` | [33286808330](https://github.com/jan-guenter/bluemap-modular-routers-addon/actions/runs/33286808330) / `99191294839` / `9724708196` |
| Rechiseled Create | `0631924ec5261a38af7de40be672f6179ff2e5ed` | [33287071745](https://github.com/jan-guenter/bluemap-rechiseled-create-addon/actions/runs/33287071745) / `99192005808` / `9724772745` | [33287175521](https://github.com/jan-guenter/bluemap-rechiseled-create-addon/actions/runs/33287175521) / `99192277066` / `9724807173` |
| Cobblemon Stone Statues | `38bef5c1c69af0a94144494de3fdb866f5aea12d` | [33287020365](https://github.com/jan-guenter/bluemap-cobblemonstonestatues-addon/actions/runs/33287020365) / `99191868671` / `9724768474` | [33287152559](https://github.com/jan-guenter/bluemap-cobblemonstonestatues-addon/actions/runs/33287152559) / `99192218239` / `9724807870` |
| Botany Pots | `4a14e994cd0622b6c629ed5240f79dd153b940ce` | [33287591631](https://github.com/jan-guenter/bluemap-botanypots-addon/actions/runs/33287591631) / `99193386241` / `9724933417` | [33287705976](https://github.com/jan-guenter/bluemap-botanypots-addon/actions/runs/33287705976) / `99193710776` / `9724965127` |

All eight runs and jobs completed successfully. The pull-request artifacts are
named for the synthetic checkout commits; the main artifacts are named for
the true merge commits. No migration triggered a release workflow.

Existing annotated release tags remain on their publication commits:

| Add-on | Version | Tag object | Peeled release commit | Tag verification |
| --- | --- | --- | --- | --- |
| Modular Routers | `0.1.0-alpha.1` | `fe79bf15cfdab66349f2631e3e9573eac9de86db` | `7fd7a4d0c40bd2dae13bb87e48445eb905322993` | unsigned |
| Rechiseled Create | `0.1.0-alpha.1` | `67f1f9970a77874952beb03cb12214009ce8c3ba` | `e1fd8afc1816154a95e224815ca4015528fd0e2e` | unsigned |
| Cobblemon Stone Statues | `0.1.0-alpha.1` | `6f7b820cf001b98d27d5150e14f5c41e0a6faeee` | `576c3030a60b5b9af266c2af4b3f8556a69aaa0f` | unsigned |
| Botany Pots | `0.1.0-alpha.1` | `15d47d2bb1f4a87efc7a4fc5565f2551efa59fba` | `f40eed6c1f7f30356bcdfabbc3e2a6455fec7884` | verified, valid signature |

## Artifact and gallery parity

Complete local gates and downloaded pull-request and post-merge CI outputs
reproduced the published Modular Routers, Rechiseled Create, and Botany Pots
files byte for byte. Cobblemon Stone Statues reproduced all four published
JAR assets byte for byte; its local and CI publication metadata also remained
exact.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Modular Routers | 46,780 B `c8e0c591169e12334abc85c3a917caffb5c82e4dd000acf92d0ff101b8f97a31` | 25,493 B `7e48efaaae36d1350e0e9096200146f4659b2b919ca740032933696b6f718384` | 1,376 B `2a381dbaa802d14f1ae71cdbf66b5be26b76d649b909e0fa161655e3ee637ab3` | 2,873 B `ae7988b2a033583b0b79515e1c8bea527ae6ee53d573c969526bf200768a245a` |
| Rechiseled Create | 209,444 B `651b8be8a41d459f04f3ec1cbc64ba7441cceb3c2bb3c07d518556a11c83596b` | 126,474 B `c64d5b21eabe488ed6b5c1dc8584fefb172f2a247cb8c29847374a26b8030a9f` | 1,378 B `9bf59963958a7a595e0c520d66565280327e14cf0f9e692e7884feee169197e1` | 2,890 B `cda1e40a526407a50312aee37e0fc277f6029ba4dcb29f6cd9094cc5aa1dd1ff` |
| Cobblemon Stone Statues add-on | 286,752 B `9800484109aa7e571f393aa96b069e6248186c35103b6e26fd9dad920e4efcd4` | 118,224 B `61d6d640792e88526998e5f2e4f8f3228acb8add360cb3b8de670e383d73d4ac` | 1,944 B `cab1a67ae2cbfdd9f67aa3da6edbae89fe0c2b6c5f826271d33eb765cb3df8cc` (local/CI) | 2,918 B `5f636b577ba92f37c7a46cec667f0749621f7dca21837cb880963c99f2f5a63a` (local/CI) |
| Botany Pots | 147,258 B `ab32bdad893e95847e191b86fee1da727757e1ee006449128acb897fe5eb05b0` | 66,843 B `022435e236461b3e8dfcdf9fc6fd92cea8a8859e32e6d1b31906d473e41cc10a` | 1,412 B `ab8bb4044a733c9789b860b1c78d90ccd37fac6b62f896381382844a34158ef0` | 2,840 B `d98847753abd9ef2b30cbb7cd703eb13b3902c0655aef0a42304f3cd38ab2d79` |

Cobblemon Stone Statues' separately published pose-exporter JARs also remain
exact: 284,840 bytes with SHA-256
`f35727ba2ce5c96abe085df36d5d02534b6a19e1f710eb4c145c0d7243c75b98`
and 103,586-byte sources with SHA-256
`fc4a4c0808b006ec07c8a17965c800b2e612ac11e0ed755749824d3524c61dde`.
Its local exporter POM is 1,694 bytes with SHA-256
`d98b797d5d65b25788432b1fe1d7041eed58b397497ca5ef43a7a8c8b7b849ab`;
its 2,872-byte module metadata has SHA-256
`225870090dd453906329bbb09fb4cf95b84809f536374c0f2361a4b8f5835941`.
Those two metadata files are local publication outputs, not GitHub release
assets or files in the reviewed CI artifact.

Deterministic baseline and migrated gallery packages also match exactly:
Modular Routers is 3,825 bytes with SHA-256
`f6011f220590f8ddb6d557e9be01830e3872e3c0ec17cfb8fd3c9816a9b9cd6f`;
Rechiseled Create is 13,516 bytes with SHA-256
`f5084c9b24d9645565b9e6708ee3ac10ea004ecacf7e2a45d6e85b3e5490ac4c`;
Cobblemon Stone Statues is 3,153 bytes with SHA-256
`1d8193b783eb1d30dd347896cc433e6de72549a472d800ff7484b16a17d04121`;
and Botany Pots is 10,840 bytes with SHA-256
`f7dbd8665e6e17bf14ae43ab65612d990b43fdca832869cc3a6cb20159aa1fc1`.
Rechiseled Create's pull-request and main artifacts independently reproduce
that same gallery package. Its existing owner-accepted gallery freeze, and
all other acceptance records, remain unchanged.

## Build-contract parity

Normalized consumer task surfaces, compile-classpath dependencies, outgoing
variants, and release dry-run task sets remained exact in every repository.
Each root full gate added four actions to compile the source-distributed
convention: Modular Routers 44 to 48, Rechiseled Create 40 to 44, Cobblemon
Stone Statues 44 to 48, and Botany Pots 43 to 47. Cobblemon Stone Statues'
family-owned exporter gate remains at 17 actions.

The four `build.gradle` files have a net reduction of 110 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Modular Routers | 437 | 409 | 28 lines |
| Rechiseled Create | 359 | 331 | 28 lines |
| Cobblemon Stone Statues | 713 | 688 | 25 lines |
| Botany Pots | 330 | 301 | 29 lines |

Applicable exact-input, profile, gallery, Python, Java, Checkstyle, repository,
workflow, and release-dry-run gates passed. Retained results include 28 Java
tests for Modular Routers; 36 Java and five Python tests for Rechiseled
Create; 83 add-on Java, 61 exporter Java, and two Python tests for Cobblemon
Stone Statues; and 32 Java plus five Python tests for Botany Pots. All passed.

Uninitialized, dirty, stale or wrong toolkit heads, mismatched gitlink-index
states, missing conventions, and wrong release tags failed closed where
applicable. Consumer-owned dependency, publication, manifest, packaging,
input-pin, gallery, and release rules remain local. No renderer, profile,
gallery, provenance, version, tag, release, or acceptance source changed.

## Result

The fifteenth cohort extends the v0.3 source convention to four more inline
consumers while preserving their exact published artifacts, galleries, build
surfaces, release identities, and renderer behavior.
