# Toolkit v0.3 trust cohort 11

This records the eleventh artifact-parity toolkit cohort. Chipped, Chisel,
CobbleFurnies, and Glassential already used the shared Gradle convention from
toolkit `v0.2.0-alpha.1`. This cohort moves their trust pins to
`v0.3.0-alpha.1`. It does not update the ATMons 1.2.0 compatibility manifest,
meta-repository gitlinks, add-on versions, release tags, provenance, galleries,
acceptance records, or renderer behavior.

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

The change therefore updates the authenticated toolkit identity, not the
convention executed by Gradle. All four `build.gradle` files remain
byte-identical. Chisel also corrects the toolkit version and commit stated in
its README. None of these repositories uses the toolkit Python wheel, so the
migration does not add a Python build dependency.

Each validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact candidate inputs were:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Chipped | Chipped 4.0.2 | 15,020,578 | `18ac6fd6b30db4922ccc6ee8bea5b113f69587505b7529834f37ace506427291` |
| Chipped | Athena 4.0.6 | 99,944 | `43699885bbce3343916d4c5c4940cf0e3f9f6f02fdeb46e8655e121b42282ec5` |
| Chisel | Chisel 2.0.1 | 8,268,524 | `66ae1f65374a7409af069d5ccde63a338d1754494555b3b5a00f1e862e50e2a6` |
| Chisel | Athena 4.0.6 | 99,944 | `43699885bbce3343916d4c5c4940cf0e3f9f6f02fdeb46e8655e121b42282ec5` |
| CobbleFurnies | CobbleFurnies 1.2 | 2,343,464 | `82894965d01bfb00fb6109ac275622a157d415ef0957d41fd6478b6d64ce34f8` |
| CobbleFurnies | Athena 4.0.6 | 99,944 | `43699885bbce3343916d4c5c4940cf0e3f9f6f02fdeb46e8655e121b42282ec5` |
| Glassential | Glassential 3.4.5 | 702,249 | `1f0c8f7533bf3b2002575219ba795fd32a44cc5085c2710624ebbf69e6121471` |
| Glassential | Fusion 1.3.12 | 923,270 | `17f5215648a98bcde4134577b013200dbf363273ae282449c51408ae8346f2fa` |

## Reviewed merges

| Add-on | Reviewed PR | Base commit | Feature commit | Merge commit | Merge tree |
| --- | --- | --- | --- | --- | --- |
| Chipped | [#4](https://github.com/jan-guenter/bluemap-chipped-addon/pull/4) | `96f7fd386882aeee670c0038a2a90a20d3fa0f28` | `df73874cbacf24922b54b9603b9ab4ed755d3f42` | `26df095af693d36c75b4d82738736157be3d1f9d` | `5d19f4c8e43c5533477210511cd786e85739ff35` |
| Chisel | [#4](https://github.com/jan-guenter/bluemap-chisel-addon/pull/4) | `53db81a989737c45614ed2c7a76c933613baac5a` | `63ac49e88f0a31f0c96bf5ad3b7aa5d64acb3946` | `6553da70621f6039db5f0fb961c2843a1c36988d` | `418c46b14fb89aa179df6b92ca124e02e9d64200` |
| CobbleFurnies | [#4](https://github.com/jan-guenter/bluemap-cobblefurnies-addon/pull/4) | `dc73b48cd80984fa810864edf2e6a95f056efd95` | `d2078f3ece9d9b1a096756420c73fe11a3012e18` | `90ca220d0fa4d4dfd258fd54b14b8b2606a0975d` | `2d0161eb272b680e0566ba1529bace95e97baba5` |
| Glassential | [#4](https://github.com/jan-guenter/bluemap-glassential-addon/pull/4) | `0e9ea3442b0be80643ea61fab88998a85d272329` | `13696168b6d50aa25a4a760b26d12cd2609e307b` | `c1c8af752cae298e8a9690db5ea62e6731fddc20` | `a37bf29e6a3128098d037d77693d732288db7566` |

Every feature commit is owner-signed. Every merge has the reviewed base and
feature as its two parents, its tree equals the reviewed feature tree, and the
GitHub API verifies its merge signature.

Pull-request CI passed against GitHub's synthetic merge commits
(`80df6f5161812788e98f72fe80542de48a795f33`,
`d87e234a52154fc44a532f1f8d75b9849cb252f7`,
`fe547e366b76526f5988a974f2779f6bf6078742`, and
`385b0202cdb67db7eebe796619cab551af36351d`, in table order). The post-merge
`main` runs passed at the exact merge commits:

| Add-on | Pull-request CI | Job | Artifact | Main CI | Job | Artifact |
| --- | --- | --- | --- | --- | --- | --- |
| Chipped | [33282866891](https://github.com/jan-guenter/bluemap-chipped-addon/actions/runs/33282866891) | `99180883863` | `9723513052` | [33282949275](https://github.com/jan-guenter/bluemap-chipped-addon/actions/runs/33282949275) | `99181097113` | `9723536804` |
| Chisel | [33283127080](https://github.com/jan-guenter/bluemap-chisel-addon/actions/runs/33283127080) | `99181568177` | `9723590862` | [33283217230](https://github.com/jan-guenter/bluemap-chisel-addon/actions/runs/33283217230) | `99181800133` | `9723615551` |
| CobbleFurnies | [33283410399](https://github.com/jan-guenter/bluemap-cobblefurnies-addon/actions/runs/33283410399) | `99182308727` | `9723673317` | [33283509201](https://github.com/jan-guenter/bluemap-cobblefurnies-addon/actions/runs/33283509201) | `99182570813` | `9723696068` |
| Glassential | [33283616300](https://github.com/jan-guenter/bluemap-glassential-addon/actions/runs/33283616300) | `99182859515` | `9723728438` | [33283695715](https://github.com/jan-guenter/bluemap-glassential-addon/actions/runs/33283695715) | `99183071295` | `9723752880` |

No migration triggered a release workflow. Existing annotated release tags
remain on their publication commits:

| Add-on | Version | Tag object | Peeled release commit |
| --- | --- | --- | --- |
| Chipped | `0.1.0-alpha.1` | `fab9c700d64794cedc5f1531081d084cc6afd82c` | `c474a82b6bfd1b4173d119cb1e053a5458167e4b` |
| Chisel | `0.1.0-alpha.1` | `c081a7c39eef24078981d10f74056068e4cd7e5e` | `f9131a5143062e2045cf26823aabb8628bb5d94d` |
| CobbleFurnies | `0.1.0-alpha.1` | `c99b55a4b22b002aea10d09267475b6dfc435d83` | `eea5407dbbd162cbe4dd8fc5bc247f6617cf5d98` |
| Glassential | `0.1.0-alpha.1` | `a011ba00b4e8c47d797cd6f8c8c5bcde25649c2d` | `13fd12412573c62847700d1cfc8e4aa9d2bb5ea1` |

## Artifact and gallery parity

The complete consumer gates reproduced every publication file byte for byte
before and after each migration. Downloaded pull-request and post-merge CI
outputs match the same public release bytes.

| Add-on | Output | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Chipped | Production JAR | 598,326 | `b43c238b764e068db4009ab16fc2af140b54d84feaf37bd6577602e1dc97fd21` |
| Chipped | Sources JAR | 557,360 | `c1372d4543fc17d296b006afc4208075cb142660cfd2e4a2dad0001b2092a903` |
| Chipped | POM | 1,341 | `5df7a4724f97e888926ad9071cb218d02965abe9b91150f3edfb9a85d30722a7` |
| Chipped | Module metadata | 2,820 | `e8c7c51c5ca4d02b0e4ee5de67f5d204768b2c6df1adcc532c1403056c6b7c49` |
| Chisel | Production JAR | 249,972 | `053e048f9332094571b25b2edc5ddb9a172e1f89c0a65c2f7ceb05e4a946510e` |
| Chisel | Sources JAR | 215,526 | `12c42cf2f07af1291cdd2c3be6cb7f4947431e5607f8f6dcf3c12da30c2a4723` |
| Chisel | POM | 1,335 | `2312a8ae1ee9160f5ebc8cef745064e933798f12b0b1da4c5c884c1b6176660d` |
| Chisel | Module metadata | 2,813 | `698b6393c881c7e3d57e82abe68c35d0d448c0eee0297c94a515b6f48ddf59d9` |
| CobbleFurnies | Production JAR | 108,237 | `2c9df027e4cd1b4f56856dcb05a65499b6ed1df3f8592e9d662ad59e477564a3` |
| CobbleFurnies | Sources JAR | 54,163 | `2ed8b9bbb2cdbec31d27e7d75b0909b170ab3d0b30dd45ade05d25c3bf3304f0` |
| CobbleFurnies | POM | 1,407 | `2d7f961881efa6752f583ceeddb7e8beae1a38ca80d61b4987219d14fa83da13` |
| CobbleFurnies | Module metadata | 2,861 | `eadd613cd2bddc92f1ebb2bb460665100c79c467d7ed0dbabf2a99c955a8d57e` |
| Glassential | Production JAR | 162,440 | `a956e62f7b843391917b861c831545b07af43ccceaa0bb84465e7e0b14c49780` |
| Glassential | Sources JAR | 79,193 | `b2cc577972e8dec52c0ce1ea2a4c0321ec209c96b0476fab340f8bbc0125db9b` |
| Glassential | POM | 1,355 | `ac64d9ec689cf7be1826a62e1dfb347fb63b4d04724b2ab11d0cb44f5dc3e7e7` |
| Glassential | Module metadata | 2,847 | `f96bdd237f750d581fc79069814ded305851b76169e2a6e87b73d47eec057553` |

Gallery sources are unchanged. Fresh deterministic packages retain these
identities:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| Chipped | 23,501 bytes | `d7ac831d95ef043c29ea31eb4e2d19985df31a9824d87a7289d5b9b49f492169` |
| Chisel | 10,508 bytes | `fc9a49c0f0a60d905fc8860a3f4d80f6651cfe50ad0b67a904e2d018bc44a09b` |
| CobbleFurnies | 4,004 bytes | `a9764211e6bc05815e27cade4b62c9c373ed3eb3203ccf9a7fb555a21414b3ee` |
| Glassential | 10,655 bytes | `847067eab454eb646300c5f08887c6172de952f796dd090c7ab84d63aae304f0` |

## Build-contract parity

Normalized consumer task surfaces, dependency trees, outgoing variants, and
release dry-run sets remained unchanged. The complete Gradle gates passed with
43, 43, 46, and 44 actionable tasks and 24, 29, 27, and 45 passing Java tests,
respectively. Glassential's 13 Python tests also passed.

Dirty toolkit worktrees, old toolkit checkouts, and wrong release tags were
rejected by the applicable trust and release gates. Staged or indexed
mismatches were also rejected where a repository has that preflight. Every
toolkit checkout was restored clean at the exact v0.3 gitlink after the probes.

There is no convention-line reduction in this cohort because each repository
already used the shared convention. Consumer-owned dependency, publication,
manifest, gallery, packaging, exact-input, and release configuration remains
local. Existing acceptance statements are unchanged and are not reinterpreted
by this tooling-only migration.

## Result

The eleventh cohort moves four existing convention consumers to the v0.3
toolkit trust identity while retaining the byte-identical Gradle convention,
published artifacts, galleries, release identities, and renderer behavior.
