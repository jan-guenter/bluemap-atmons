# Shared Gradle convention cohort 2

This records the second artifact-parity adoption of the BlueMap Add-on Toolkit
Gradle convention. It changes development tooling only. It does not update the
ATMons 1.2.0 compatibility manifest, meta-repository gitlinks, add-on versions,
accepted release tags, or renderer behavior.

## Scope

The cohort contains four model-pack add-ons with closely related build and
artifact gates:

- Chipped;
- Chisel;
- CobbleFurnies; and
- Glassential.

Every repository pins toolkit `v0.2.0-alpha.1` at commit
`f58da04567f10efe615c582797f3ab00b7a7343f` with a mode-160000 gitlink and the
same explicit trust pin in `settings.gradle`. CI and release checkouts
initialize recursive submodules without stored credentials.

Each accepted validation used its own clean BlueMap checkout at commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. An early shared-checkout build
race was discarded before baseline acceptance; no evidence below comes from
that run.

## Reviewed merges

| Add-on | Reviewed PR | Feature commit | Merge commit | Gate |
| --- | --- | --- | --- | --- |
| Chipped | [#3](https://github.com/jan-guenter/bluemap-chipped-addon/pull/3) | `4e66b259108659517c9e4c26d1d0842935c2240a` | `96f7fd386882aeee670c0038a2a90a20d3fa0f28` | Gradle 9.4.0 exact Chipped/Athena gate |
| Chisel | [#3](https://github.com/jan-guenter/bluemap-chisel-addon/pull/3) | `b16aeb5c86cfbcf56f440930e269f41def3854fa` | `53db81a989737c45614ed2c7a76c933613baac5a` | Gradle 9.4.0 exact Chisel/Athena gate |
| CobbleFurnies | [#3](https://github.com/jan-guenter/bluemap-cobblefurnies-addon/pull/3) | `252c26b99f0e41cb3870a644356704868aa6c151` | `dc73b48cd80984fa810864edf2e6a95f056efd95` | Gradle 9.6.1 release gate plus gallery checks |
| Glassential | [#3](https://github.com/jan-guenter/bluemap-glassential-addon/pull/3) | `35f627d0177da69a877d90777fb8e65d35100c89` | `0e9ea3442b0be80643ea61fab88998a85d272329` | Gradle 9.6.1 exact Glassential/Fusion gate |

Every merge has the reviewed base and feature commits as its two parents, and
each merge tree equals its reviewed feature tree. The PR and post-merge `main`
CI runs passed for all four repositories:

- [Chipped PR CI](https://github.com/jan-guenter/bluemap-chipped-addon/actions/runs/33268420109)
  and [main CI](https://github.com/jan-guenter/bluemap-chipped-addon/actions/runs/33268519645);
- [Chisel PR CI](https://github.com/jan-guenter/bluemap-chisel-addon/actions/runs/33268557885)
  and [main CI](https://github.com/jan-guenter/bluemap-chisel-addon/actions/runs/33268670433);
- [CobbleFurnies PR CI](https://github.com/jan-guenter/bluemap-cobblefurnies-addon/actions/runs/33268423608)
  and [main CI](https://github.com/jan-guenter/bluemap-cobblefurnies-addon/actions/runs/33268539639); and
- [Glassential PR CI](https://github.com/jan-guenter/bluemap-glassential-addon/actions/runs/33268417866)
  and [main CI](https://github.com/jan-guenter/bluemap-glassential-addon/actions/runs/33268510484).

No migration triggered a release workflow.

## Artifact parity

The complete consumer gates reproduced these files byte for byte before and
after each migration.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Chipped | `b43c238b764e068db4009ab16fc2af140b54d84feaf37bd6577602e1dc97fd21` | `c1372d4543fc17d296b006afc4208075cb142660cfd2e4a2dad0001b2092a903` | `5df7a4724f97e888926ad9071cb218d02965abe9b91150f3edfb9a85d30722a7` | `e8c7c51c5ca4d02b0e4ee5de67f5d204768b2c6df1adcc532c1403056c6b7c49` |
| Chisel | `053e048f9332094571b25b2edc5ddb9a172e1f89c0a65c2f7ceb05e4a946510e` | `12c42cf2f07af1291cdd2c3be6cb7f4947431e5607f8f6dcf3c12da30c2a4723` | `2312a8ae1ee9160f5ebc8cef745064e933798f12b0b1da4c5c884c1b6176660d` | `698b6393c881c7e3d57e82abe68c35d0d448c0eee0297c94a515b6f48ddf59d9` |
| CobbleFurnies | `2c9df027e4cd1b4f56856dcb05a65499b6ed1df3f8592e9d662ad59e477564a3` | `2ed8b9bbb2cdbec31d27e7d75b0909b170ab3d0b30dd45ade05d25c3bf3304f0` | `2d7f961881efa6752f583ceeddb7e8beae1a38ca80d61b4987219d14fa83da13` | `eadd613cd2bddc92f1ebb2bb460665100c79c467d7ed0dbabf2a99c955a8d57e` |
| Glassential | `a956e62f7b843391917b861c831545b07af43ccceaa0bb84465e7e0b14c49780` | `b2cc577972e8dec52c0ce1ea2a4c0321ec209c96b0476fab340f8bbc0125db9b` | `ac64d9ec689cf7be1826a62e1dfb347fb63b4d04724b2ab11d0cb44f5dc3e7e7` | `f96bdd237f750d581fc79069814ded305851b76169e2a6e87b73d47eec057553` |

Chipped, Chisel, and Glassential also match their published
`0.1.0-alpha.1` assets. CobbleFurnies parity is intentionally against its
108,237-byte current-main JAR. That is not the separately recorded
107,618-byte visual candidate, so this work makes no release or visual
acceptance claim for CobbleFurnies.

## Build-contract parity

Dependency reports and outgoing variants are byte-identical for all four
repositories. Their consumer and BlueMap dry-run task sets are unchanged. The
only additional tasks compile the included convention plugin; independent
consumer tasks may appear in a different order.

The four `build.gradle` files replaced 113 repeated convention lines with four
plugin applications:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Chipped | 288 | 260 | 28 lines |
| Chisel | 288 | 260 | 28 lines |
| CobbleFurnies | 386 | 361 | 25 lines |
| Glassential | 468 | 440 | 28 lines |

The consumer-owned trust preflight remains repeated because an included plugin
cannot authenticate the source checkout from which it is loaded. Repository,
dependency, publication, manifest, gallery, packaging, debug, and release
configuration remains in each consumer.

## Result

The second cohort confirms the convention across two more Gradle 9.4.0 and two
more Gradle 9.6.1 consumers. Further adoption remains a repository-by-
repository migration with exact inputs, a frozen baseline, the complete local
gate, artifact comparison, reviewed PR CI, and post-merge `main` CI.
