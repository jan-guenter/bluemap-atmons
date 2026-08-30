# Shared Gradle convention cohort 14

This report records the fourteenth artifact-parity adoption of the BlueMap
Add-on Toolkit Gradle convention. It changes development tooling only. It does
not update the ATMons 1.2.0 compatibility manifest, meta-repository gitlinks,
add-on versions, release tags, provenance, galleries, acceptance records, or
renderer behavior.

## Scope

The cohort contains Factory Blocks, Functional Storage, Logistics Networks,
and Rechiseled. Each repository pins toolkit `v0.3.0-alpha.1` at commit
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` with a mode-160000 gitlink and
the same consumer-owned trust preflight in `settings.gradle`.

Factory Blocks, Logistics Networks, and Rechiseled consume only the toolkit's
source-distributed Gradle convention. Functional Storage's promotion gates
also adopt the repository checker, so it pins the 20,585-byte
wheel with SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
The wheel and source checkout remain development-only and add no installed
runtime dependency or packaged file.

Every validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact candidate inputs were:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Factory Blocks | Factory Blocks | 809,234 | `404080fcf4747c6d84b73d1c204d047408aae476f57752bc5f38e9c16c7f51cd` |
| Factory Blocks | Athena | 99,944 | `43699885bbce3343916d4c5c4940cf0e3f9f6f02fdeb46e8655e121b42282ec5` |
| Functional Storage | Functional Storage 1.21.1-1.5.8 | 810,628 | `e3e7368c28a24e7de5b877988aa92cc94ca7417c8f60b7d28e7f584a94a51147` |
| Functional Storage | Titanium 1.21-4.0.45 | 606,801 | `d224a9bd5cfb9e921ba644b2a7a2ce1041f879a9945f80dacebd87d95888530c` |
| Logistics Networks | Logistics Networks | 988,995 | `d94395da601ce93d8d7c9ffc434a018f6f46488303c654f6d6d5747961f56187` |
| Rechiseled | Rechiseled 1.2.5 | 11,498,611 | `7bf14cf8a4bfdc4b6c990126a75da29fd2bb7559d1c05b71e29c8fd5ae044435` |
| Rechiseled | Fusion 1.3.12 | 923,270 | `17f5215648a98bcde4134577b013200dbf363273ae282449c51408ae8346f2fa` |

## Reviewed merges

| Add-on | Reviewed PR | Base commit | Feature commit | Merge commit | Merge tree |
| --- | --- | --- | --- | --- | --- |
| Factory Blocks | [#6](https://github.com/jan-guenter/bluemap-factory-blocks-addon/pull/6) | `0e5122a4fbfa5ab1daad03a9fa82422142746932` | `985301a55a843239b741eb256b0deca8abdfe5df` | `667c601c92357b7e757aaae78393cbe45f531456` | `39b86ba7d4cc4bed83cd3b1450a7f5edb5f8913f` |
| Functional Storage | [#6](https://github.com/jan-guenter/bluemap-functional-storage-addon/pull/6) | `cf234be4cf2e966a3e7591c29d1dc029600a25b7` | `5c19cfbcd964afe7eadd95b472dc2d747298f4b1` | `a72660c41f0f7f03ae56ae31bb4b38914e65e280` | `d12beed0a04bf45979e352c25d77594ebe22631a` |
| Logistics Networks | [#3](https://github.com/jan-guenter/bluemap-logistics-networks-addon/pull/3) | `40cdfc5000d00a0ef78dd3d25aba6dee5a23902d` | `5dc18041de8382973a4875130fde6d041cc7dc5e` | `5343837fe80aa74c6a168a8ac2bbce0f7da71693` | `78aeb1f44165bb686a0d17d44658bf393fd24cac` |
| Rechiseled | [#3](https://github.com/jan-guenter/bluemap-rechiseled-addon/pull/3) | `f2f7e5cb6c8421346892514d12d210c193ae0b00` | `ce1966bf4e4809fd789614e47bf6428635137868` | `a8ab2d7070d8667fc73112b46977b15b819cef1a` | `8aff9e89aa56dd5061210a9fa0678561d5dff1c7` |

Every feature commit is owner-signed. Every true merge has the reviewed base
and feature as its two parents, its tree equals the reviewed feature tree, and
the GitHub API verifies its merge signature.

Pull-request CI ran against GitHub's synthetic merge commits
`8661c7a8a862d546601af1a97fe794c77d93be6d`,
`02f2ebd09e7dfeffada48d130a66c3e4a1a8c253`,
`26798c4e77b2663670440e643bb5a6f78d5f2470`, and
`64a6cab083ad89e487b7fbb45b60fd9d5418f94f`, in table order. Each synthetic
commit has the reviewed base and feature as parents and the reviewed feature
tree. The Actions run metadata reports the feature commit as `headSha`; the
artifact name and checked-out pull-request merge ref preserve the actual test
identity.

| Add-on | Pull-request CI | Job | Artifact | Main CI | Job | Artifact |
| --- | --- | --- | --- | --- | --- | --- |
| Factory Blocks | [33285913130](https://github.com/jan-guenter/bluemap-factory-blocks-addon/actions/runs/33285913130) | `99188970053` | `9724450419` | [33286069010](https://github.com/jan-guenter/bluemap-factory-blocks-addon/actions/runs/33286069010) | `99189375108` | `9724488328` |
| Functional Storage | [33286219983](https://github.com/jan-guenter/bluemap-functional-storage-addon/actions/runs/33286219983) | `99189765994` | `9724534943` | [33286364171](https://github.com/jan-guenter/bluemap-functional-storage-addon/actions/runs/33286364171) | `99190135127` | `9724586107` |
| Logistics Networks | [33286057843](https://github.com/jan-guenter/bluemap-logistics-networks-addon/actions/runs/33286057843) | `99189343969` | `9724491239` | [33286190703](https://github.com/jan-guenter/bluemap-logistics-networks-addon/actions/runs/33286190703) | `99189694071` | `9724533579` |
| Rechiseled | [33286474995](https://github.com/jan-guenter/bluemap-rechiseled-addon/actions/runs/33286474995) | `99190416722` | `9724601568` | [33286569094](https://github.com/jan-guenter/bluemap-rechiseled-addon/actions/runs/33286569094) | `99190663342` | `9724628948` |

No migration triggered a release workflow. Existing annotated release tags
remain on their publication commits:

| Add-on | Version | Tag object | Peeled release commit |
| --- | --- | --- | --- |
| Factory Blocks | `0.1.0-alpha.1` | `e378cf3ebbd613ab182eba11eb6f545abd415bc3` | `ad9ee2bcf0e2886ee88931f1eaf50ccb4b8a03bd` |
| Functional Storage | `0.1.0-alpha.1` | `fd65c9c3139664418c8a8a3cbb378d0503112ac8` | `d085e3a4450dd2e8b1dc6d54541054ee36b4646c` |
| Logistics Networks | `0.1.0-alpha.1` | `f5b4fa88be85c68e75233adf44636ded1713e433` | `e6dc2ebe4c3ddbf4942b07c9208147d901f411fb` |
| Rechiseled | `0.1.0-alpha.1` | `9552bf8bef387375e697b0b78d3dab6e3b902953` | `8588d99388c213b938d79931dd6d9e9ef8e4099c` |

Factory Blocks' existing annotated tag is unsigned. This report records tag
identity without generalizing a signature claim across the cohort.

## Artifact and gallery parity

Complete local gates plus downloaded baseline, pull-request, and post-merge CI
outputs reproduced every published file byte for byte:

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Factory Blocks | 86,501 B `69f4f53022aac455a4bcc362dc09cbaf5b3f73cf108ccc154dffa8e238869302` | 51,485 B `c94167752f16ddc6b5f3bf9c711ca719dcedb1a9bb437fc8b9e65f3149072613` | 1,373 B `eb1a67ad49ba54f28ea28fa10966fc30f1913f294ef20c861881596247b6f300` | 2,866 B `14cb9927206ce573f4af4306adced9e2167c9194402131973629cc4a7b2479bb` |
| Functional Storage | 82,274 B `ffe80812802c2c8f68d50ee74f17dd492561f3b44a9e650545064f66e285b048` | 39,515 B `5b5b91d6d17f658a8de6dc99920e39bbe0e54518d5f2b9093760c9e17b13d9ef` | 1,397 B `1d037275fa62154cf962e408497235e43d96e039a2eb39b6e142638320a04d0a` | 2,894 B `2ba7a4cc10ebcc230cf2128bbf086817985d94e7efa0a6e2945866e043ea330f` |
| Logistics Networks | 67,367 B `5f813504e2dccd63ad0a2cc1bd33a129da2e2934e5576d149b6b215c12ba8f18` | 31,656 B `df0b53155df3c1add4fbea839fbc125a212ed2c6a4d25ebe812c4801a85bfa98` | 1,408 B `d2d0f5443803bd3e6be9fb874a3a4e7997f14c6b88dd82fb24359f4b9e15730b` | 2,894 B `941a1cef0811d1f88d974f7c401141aa5d73ce8e56a04a13b7a35a5c4a341936` |
| Rechiseled | 645,622 B `39793187b97b504e085664a23eb5e54961dfdeac1e9ccf57e1bd701bd90c0242` | 580,393 B `a00d8eaa0da20541a51a9829121cadb14e25e0a63f91fee0d02b0a629a5a5519` | 1,359 B `88cdd312091817832c82b8715142ffaaacd41281468930ab07f39785f11b3151` | 2,841 B `11cb4de88025a775751360d35d725321d4b0581b8ad41cb93cb824c12df43ec2` |

Factory Blocks, Functional Storage, and Logistics Networks retain deterministic
gallery ZIPs of 3,707, 4,697, and 9,179 bytes with SHA-256
`cbea339239d7ddcfd2a771de204d64ba63e1941d28e74416c51919c32888e25b`,
`51dd3845398b9c624631e227468bcce65e693dce15e2f764c67dfe8ba9fddd27`,
and `38960663ba58bfdba3ca40d9b6f834177870395a1e305c9f10710b488e11e4da`.
Rechiseled's gallery tree remains exact at
`13cf08c5294a7be52184ee11b493275197eed0fc`; fresh baseline and migrated
packages match at 27,563 bytes and SHA-256
`cb1fd953920ab8aa7be1ad1d33605d93cbe2edd6e7c027a8a8998a636d1ae1d2`.
The separately recorded accepted historical archive is not reinterpreted by
this tooling-only change.

## Build-contract parity

Normalized consumer task surfaces, compile-classpath dependencies, outgoing
variants, and release dry-run task sets remained exact in every repository.
The only new build actions compile the source-distributed convention plugin.
Factory Blocks' full gate added four actions, and Rechiseled's authoritative
gate moved from 39 to 43 actions for the same reason.

The four `build.gradle` files remove 113 duplicated convention lines and add
four plugin applications, a net reduction of 109 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Factory Blocks | 436 | 408 | 28 lines |
| Functional Storage | 408 | 383 | 25 lines |
| Logistics Networks | 386 | 358 | 28 lines |
| Rechiseled | 310 | 282 | 28 lines |

Applicable exact-profile, gallery, Python, Java, Checkstyle, repository, and
workflow gates passed. The retained reports include 31 Java plus four Python
tests for Factory Blocks, 49 Java tests for Functional Storage, and 23 Java
plus eight Python tests for Rechiseled. No renderer, profile, gallery,
provenance, version, or acceptance source changed.

Uninitialized, dirty, stale-v0.2, and mismatched-index toolkit states failed
closed. Functional Storage additionally rejected an altered wheel hash, a
missing shared convention, and a wrong release tag. Consumer-owned dependency,
publication, manifest, packaging, input-pin, gallery, and release rules remain
local.

## Result

The fourteenth cohort extends the v0.3 source convention to four previously
inline consumers while preserving their exact published artifacts, galleries,
build surfaces, release identities, and renderer behavior.
