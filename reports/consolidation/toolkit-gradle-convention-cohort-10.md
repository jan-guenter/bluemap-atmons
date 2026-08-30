# Toolkit v0.3 trust cohort 10

This records the tenth artifact-parity toolkit cohort. Pipez, Create,
Supplementaries, and Connected Glass already used the shared Gradle convention
from toolkit `v0.2.0-alpha.1`. This cohort moves their trust pins and applicable
tooling to `v0.3.0-alpha.1`. It does not update the ATMons 1.2.0 compatibility
manifest, meta-repository gitlinks, add-on versions, existing release tags,
provenance, galleries, or renderer behavior.

## Scope and unchanged Gradle convention

Every repository replaces toolkit commit
`f58da04567f10efe615c582797f3ab00b7a7343f` with
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` in its mode-160000 gitlink and
consumer-owned `settings.gradle` trust preflight.

The Gradle convention tree is byte-for-byte identical at both commits:

```text
f58da04567f10efe615c582797f3ab00b7a7343f:gradle = b99dca5be05340e92229c3912d4ec0486d99b54b
6cd34a8368cc4ee8628fbe830a90ec5b14960629:gradle = b99dca5be05340e92229c3912d4ec0486d99b54b
```

The change therefore updates trust and checker tooling, not the convention
executed by Gradle. All four consumer `build.gradle` files remain byte-identical.

The current 20,585-byte `v0.3.0-alpha.1` wheel has SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
Supplementaries replaces its previous hash-locked `v0.2.0-alpha.1` wheel,
which was 19,827 bytes with SHA-256
`cbfbad7ea12ea631b9f36a5261482dde3ca4d8f270df1b5faf75310020b115f9`.
Create adds the exact v0.3 wheel and runs the corrected repository checker in
CI and on future release commits. Pipez and Connected Glass need only the
gitlink and settings pin, so they do not acquire a Python build dependency.

Each validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact candidate inputs were:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Pipez | Pipez 1.21.1-1.2.31 | 456,599 | `9b37e922443ea3452daeacbfba4bcf69de07692183c4ee09f1d1e82c9fc5cc5f` |
| Create | Create 6.0.10 | 19,123,767 | `ef87fe5709f1ba1f5b8bb20a2925b5afb4669e178fd6d8bf10c167759eefe37a` |
| Create | Create Aquatic Ambitions 2.0.4 | 1,074,131 | `d50180fd30dc7f034ea4ad5185d18cfa652457be1d8e7a45f0b491d0e6642d44` |
| Create | Create Crafts & Additions 1.6.0 | 1,661,802 | `41876c3780b70365a1848994d146a73423cc19fbe86485885795d9e7d855e7e9` |
| Create | Create Hypertube 0.6.0 | 546,142 | `7bdb8979c7ff7d3b29f7a23771b6ae4870a6dcb7ce2e4a3214fdd6059aacace8` |
| Create | Create: Enchantment Industry 2.5.0 | 1,573,021 | `02a184531c11433cd6521f612982568398aaf510b8ff51e052a78cf7d09d9a49` |
| Supplementaries | Supplementaries 1.21.1-3.8.5 | 13,469,336 | `c05b1c9d39d37694d197ef84ffe70f9dbe995261333cc7c06610c7bff6d9599e` |
| Supplementaries | Moonlight 1.21.1-3.3.0 | 2,135,671 | `30420824c7f9fbca0317551c8fd6bbdce01c8d745edf5bc8d61e42393c5f0335` |
| Connected Glass | Connected Glass 1.1.14 | 819,976 | `e5b2a1cd8ef1b8a49a322aeccfc5cd9a53d8303613b9f30718f12a1e525d49fe` |
| Connected Glass | Fusion 1.3.12 | 923,270 | `17f5215648a98bcde4134577b013200dbf363273ae282449c51408ae8346f2fa` |

## Reviewed merges

| Add-on | Reviewed PR | Base commit | Feature commit | Merge commit | Merge tree |
| --- | --- | --- | --- | --- | --- |
| Pipez | [#4](https://github.com/jan-guenter/bluemap-pipez-addon/pull/4) | `adafc5e683198edc025c001ef8b3dea270261880` | `7f3ba8faff6e2e3998a053d9090e3859a196a020` | `e1ffb394cec4e9860433f7c187b3d09afb6e30b3` | `7ba2b2f4cdbfd0cdd2caf7c3717f3e71c0cf54c6` |
| Create | [#4](https://github.com/jan-guenter/bluemap-create-addon/pull/4) | `aa9fe263faeaf3fc85d689a0c3e4b1ca0da08251` | `0b92ad1c5b940cbd406e1eb37cc1396cd797ff27` | `2835580988d3bcf190991c7baec6427e92862d59` | `d54bccd36764f050ea3aa1fea2178dad4e9500cc` |
| Supplementaries | [#5](https://github.com/jan-guenter/bluemap-supplementaries-addon/pull/5) | `cabfb0a740d4eb843a7e0389e6744acf1fa45b13` | `dc00a4a998ef4e5731bcd5bca0d69668c3f2612f` | `80375683840570fbe5cdb4e9f15531dd86d9d7fd` | `3352d482b15e3c1dab7a885dc0a058478a3cdaa1` |
| Connected Glass | [#4](https://github.com/jan-guenter/bluemap-connectedglass-addon/pull/4) | `4f36d14943b15d6e650f4ff4bd12037f9bb9e064` | `2d4ff917c66216bccf27c8ca19aaf56ba9eea346` | `55dc1a0c5a12a02b204c95ab96d3bec044568abf` | `8795c4b90f476259f70b071ef6e60a51c7264aa8` |

Every merge has the reviewed base and feature as its two parents. Each merge
tree equals its reviewed feature tree, and GitHub verifies every merge
signature.

The pull-request CI runs passed against GitHub's synthetic merge commits
(`2b6cd8bdffdfce8fa79ba1a38b9c8583198d1762`,
`8ccf371986f6aef094fecc502ab0c9465092f7a5`,
`1174e9e65073376db9322a6b23524e73be85113e`, and
`6e51a7cc598319f0596b15af3577e5827bec337d`, in table order). Each synthetic
commit has the reviewed base and feature parents and the same tree as the
feature and final merge commits. The post-merge `main` runs passed at the exact
merge commits:

| Add-on | Pull-request CI | Job | Artifact | Main CI | Job | Artifact |
| --- | --- | --- | --- | --- | --- | --- |
| Pipez | [33282205973](https://github.com/jan-guenter/bluemap-pipez-addon/actions/runs/33282205973) | `99179141404` | `9723328284` | [33282302646](https://github.com/jan-guenter/bluemap-pipez-addon/actions/runs/33282302646) | `99179390984` | `9723351914` |
| Create | [33282633014](https://github.com/jan-guenter/bluemap-create-addon/actions/runs/33282633014) | `99180265284` | `9723444509` | [33282720966](https://github.com/jan-guenter/bluemap-create-addon/actions/runs/33282720966) | `99180499938` | `9723470603` |
| Supplementaries | [33282605291](https://github.com/jan-guenter/bluemap-supplementaries-addon/actions/runs/33282605291) | `99180189385` | `9723452067` | [33282746692](https://github.com/jan-guenter/bluemap-supplementaries-addon/actions/runs/33282746692) | `99180568177` | `9723489849` |
| Connected Glass | [33282531493](https://github.com/jan-guenter/bluemap-connectedglass-addon/actions/runs/33282531493) | `99180005056` | `9723417102` | [33282620481](https://github.com/jan-guenter/bluemap-connectedglass-addon/actions/runs/33282620481) | `99180233663` | `9723441013` |

No migration triggered a release workflow. Existing annotated release tags
remain on their publication commits:

| Add-on | Version | Tag object | Peeled release commit |
| --- | --- | --- | --- |
| Pipez | `0.1.0-alpha.1` | `5648f630f99c5f6d195606fe15c58e4107c801bf` | `fa3e773a7d1b7e9af52277bf104e70f704b0bb2a` |
| Create | `0.1.0-alpha.1` | `75a93ad0903407564c486ec6e2f6c5545d9f4168` | `987b1a2d4e579878d605ec9c003ee8eef69f8686` |
| Supplementaries | `0.1.0-alpha.1` | `56cb0003aebeb7b2af871039e5dc4ab22ab70618` | `f9e1035ce356e749489e67e65f5f83c42415bd2b` |
| Connected Glass | `0.1.0-alpha.1` | `ba281fdd9852e8a64b63bfc2004b118c3dab2e81` | `4a4eb5030d18f1e54cd5a8ad1c2dc093a187ac06` |

## Artifact and gallery parity

The complete consumer gates reproduced every publication file byte for byte
before and after each migration. Downloaded pull-request and post-merge CI
outputs match the same published bytes.

| Add-on | Output | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Pipez | Production JAR | 53,921 | `e81dea280d08e19ea4602e5a0700f4ab7004ca74e3408bfba3a898cb745e67db` |
| Pipez | Sources JAR | 29,858 | `e15cd1e987fefb0433a8c3ab2b8bb5d7f8a3901f586c91a9a6dbfa76fbdf1ae1` |
| Pipez | POM | 1,339 | `83a20b47360cd35aef83fdee06567c2bae2a6587cd225c08b301e522bdfe5ce0` |
| Pipez | Module metadata | 2,803 | `8b5504702e56f2ca0c324fe05a11dd60acaa219f297fa9a84266327e8c410d4a` |
| Create | Production JAR | 312,744 | `e9e860ff0a3cc3398090d03f36441a9df863ec96c0c5e6da408815a1f9c1cd05` |
| Create | Sources JAR | 105,438 | `c795af0a4082da8af8dc3e653836c6a8cba8b2825094cd6e1b2ab7926bed6bec` |
| Create | POM | 1,336 | `e747a3d8ce0b52e5621ec13ef69ac21bfad00ca74b02504a0c5ff3b9592eeb7f` |
| Create | Module metadata | 2,813 | `a7fbf84d73c5c8941792f404dbab86d79849bf51eb8ed228ff4a5c6735fd4d08` |
| Supplementaries | Production JAR | 64,385 | `7559ec3eff162a279a1a3ba1ce4b061d0ed2ff6726e016614ed0973cc407e5da` |
| Supplementaries | Sources JAR | 46,479 | `bf0bcd6ae6edf884ac9ee70d71b8c8ad02fa8414a7223726d55598ab21d803ad` |
| Supplementaries | POM | 1,365 | `b664b59c2e04d60e1f6857ddb366e70e030c463b10b02d989aa022f80f03d795` |
| Supplementaries | Module metadata | 2,873 | `63cc651c48816d2b5cb9c79ec3e4f6b4223e5e53c2909080cfca2040a10af381` |
| Connected Glass | Production JAR | 155,396 | `eb1dc07a6f9906f83a710e175cb8c119f0464bda73f651fa13a6e24900ffb70e` |
| Connected Glass | Sources JAR | 92,165 | `a2f65dd74c439ab6b1152db6e3255a7f4d282b4870b56c0c8e7f1ee65f2999f9` |
| Connected Glass | POM | 1,375 | `87489782df3acdad2046243d840bb4f1d81cf5cf685298f66072f6b883d0dc38` |
| Connected Glass | Module metadata | 2,868 | `209c4f441d9e2e5a3eb0da13a136c955d54de7cc09875bb677317a2aed6c1c8b` |

Gallery sources are unchanged. Fresh deterministic packages retain these
identities:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| Pipez | 3,504 bytes | `08f1de94a139ae0910a755cdcdf9f59c4c3faef03f00cdbbce91b7532245efd2` |
| Create | 3,990 bytes | `640863b2370550bd2cfd9ca867a49f3c46b5e12a8be8bf9a39fcdea0c3313332` |
| Supplementaries | 4,659 bytes | `242de0fa1a8949e6bcaa59c02eca96f356ee9f45939b0a5cd9abd9975359b6a0` |
| Connected Glass | 11,686 bytes | `3d1d004acab93d725e4437d3d900a884b2a113caaeb04025b9c15030eaa12f78` |

## Build-contract parity

Normalized consumer task surfaces, dependency trees, outgoing variants, and
release dry-run sets remained unchanged. All four complete Gradle gates passed.
Their Gradle test reports recorded 20, 125, 10, and 30 passing tests,
respectively.

Dirty toolkit worktrees and checkouts at toolkit v0.2 were rejected. Wrong
release tags were rejected by the historical release gates. Create also
proved that an uninitialized toolkit and a wrong wheel hash fail closed.
Every toolkit checkout was restored clean at the exact v0.3 gitlink after the
probes.

There is no convention-line reduction in this cohort because each repository
already used the shared convention. Consumer-owned dependency, publication,
manifest, gallery, packaging, exact-input, and release configuration remains
local.

## Result

The tenth cohort moves four existing convention consumers to the v0.3 toolkit
trust identity. Create additionally adopts the corrected repository checker,
and Supplementaries updates its hash-locked toolkit wheel. The cohort does not
change the Gradle convention, published artifacts, galleries, release
identities, or renderer behavior.
