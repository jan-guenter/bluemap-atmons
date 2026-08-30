# Toolkit v0.3 trust cohort 13

This report records the thirteenth artifact-parity toolkit cohort and completes the
v0.2 trust-pin migration. XNet, LaserIO, Little Big Redstone, and Nature's Aura
already used the shared Gradle convention from toolkit `v0.2.0-alpha.1`. This
cohort moves their trust pins and hash-locked toolkit wheels to
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

Each repository replaces the 19,827-byte `v0.2.0-alpha.1` wheel, SHA-256
`cbfbad7ea12ea631b9f36a5261482dde3ca4d8f270df1b5faf75310020b115f9`,
with the 20,585-byte `v0.3.0-alpha.1` wheel, SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
XNet and Nature's Aura also run the corrected v0.3 repository checker in CI
and on future release commits. LaserIO and Little Big Redstone retain their
already dynamic, byte-identical workflows. All four `build.gradle` files
remain byte-identical.

Each validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact candidate inputs were:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| XNet | XNet 1.21-7.0.7 | 611,577 | `0f393a4bff91a90e0665ec6d66ff649e45f9c33311dc038e4a5df0b154ea9d80` |
| XNet | RFTools Base 1.21-6.0.11 | 463,973 | `5195ba530e6cf9ba61c9954a3297679e6d29aa1b6182e27ae14ea43463dd4b00` |
| LaserIO | LaserIO 1.9.11 | 1,305,285 | `03e8537d75bc2f4ced2fc214d3409753e684d1056ee63b26db7a2b9e199ef4df` |
| Little Big Redstone | Little Big Redstone 1.9.8-1.21.1 | 1,415,860 | `ba4eac4050528c274db4b8b43c38152ef58407298f499d28b13c97a7ca8a0896` |
| Nature's Aura | Nature's Aura 41.9 | 1,443,280 | `c76a257fdf5da2bf2c21dcc4e474a7a1ff11202a13fca02fedc97e329426e517` |

## Reviewed merges

| Add-on | Reviewed PR | Base commit | Feature commit | Merge commit | Merge tree |
| --- | --- | --- | --- | --- | --- |
| XNet | [#5](https://github.com/jan-guenter/bluemap-xnet-addon/pull/5) | `a4fe9359106f6af6a814d09947b5e08ba7022c89` | `41ff8db20a5654dc9add3ceca5acda919ddc9212` | `796b17baf40fa56a8e0348f6ba83843574d1b63a` | `fee0dc53ccc389285b5f520ca39f4f7f3078dbaf` |
| LaserIO | [#5](https://github.com/jan-guenter/bluemap-laserio-addon/pull/5) | `86c9feb02e2abe9e030b0cd2fc8e96342a723377` | `44aa43857930d188f59b1ec2cffc38198a22bb7e` | `d0c6b834310206251a92af136d01046a257a0bbf` | `0a5dd575299ddb829c18e577dd5abf08fc73f3e8` |
| Little Big Redstone | [#5](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/pull/5) | `acead980d43fd072a0e3b988f54eddfa00515345` | `0c985ad24afdbba2234e33a4cecb108cdd69d159` | `4ec7670e2d1aa7af4fb9ce4f06d4e66e2dc87a65` | `bd8635612b505158502a01f28e4bd48cefeb6973` |
| Nature's Aura | [#5](https://github.com/jan-guenter/bluemap-natures-aura-addon/pull/5) | `cf49c3e27bf7e10959785cfc6ce906a925ee13da` | `24e70730d5b19cfcb44169a07c1b15f0b4284ee2` | `aa76b6e1699202225470dcf4d85af959ec14fc35` | `a1aa5ff68682361b3f466266cfee95d1c0c24626` |

Every feature commit is owner-signed. Every merge has the reviewed base and
feature as its two parents, its tree equals the reviewed feature tree, and the
GitHub API verifies its merge signature.

Pull-request CI passed against GitHub's synthetic merge commits
(`1c1efdbd84a7e9ac641b1ef58ff1288bef086900`,
`a890f83fdb9f4b16fb790d5e00a545b84d34539e`,
`cc0ac7cdd8404f689f4253e5387caf61f00f8b9a`, and
`ee6821c93d94b39619c6b601d4787971734d8621`, in table order). The post-merge
`main` runs passed at the exact merge commits:

| Add-on | Pull-request CI | Job | Artifact | Main CI | Job | Artifact |
| --- | --- | --- | --- | --- | --- | --- |
| XNet | [33285173427](https://github.com/jan-guenter/bluemap-xnet-addon/actions/runs/33285173427) | `99187014375` | `9724206163` | [33285356322](https://github.com/jan-guenter/bluemap-xnet-addon/actions/runs/33285356322) | `99187496859` | `9724264297` |
| LaserIO | [33285101082](https://github.com/jan-guenter/bluemap-laserio-addon/actions/runs/33285101082) | `99186821370` | `9724182633` | [33285236911](https://github.com/jan-guenter/bluemap-laserio-addon/actions/runs/33285236911) | `99187180843` | `9724220830` |
| Little Big Redstone | [33285366495](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/actions/runs/33285366495) | `99187523448` | `9724264506` | [33285504703](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/actions/runs/33285504703) | `99187894424` | `9724311682` |
| Nature's Aura | [33285535039](https://github.com/jan-guenter/bluemap-natures-aura-addon/actions/runs/33285535039) | `99187972923` | `9724320538` | [33285671611](https://github.com/jan-guenter/bluemap-natures-aura-addon/actions/runs/33285671611) | `99188346868` | `9724374797` |

No migration triggered a release workflow. Existing annotated release tags
remain on their publication commits:

| Add-on | Version | Tag object | Peeled release commit |
| --- | --- | --- | --- |
| XNet | `0.1.0-alpha.1` | `c8767931d911ea4615310a1a823fd6ac4f693751` | `925a5e890e0f97791599c063825bc0ac4fc2bd51` |
| LaserIO | `0.1.0-alpha.1` | `ae9ce209208402a49fe6531cbce48258c2940142` | `2148a344b1ae78e77b95aa2baa51efe46c1357e8` |
| Little Big Redstone | `0.1.0-alpha.1` | `a8fa875f2dd46865cbdcecfcab22bdc7573575c9` | `cee9ed82e22e8041d53c3d9d54a61bee82da72a1` |
| Nature's Aura | `0.1.0-alpha.1` | `1bcb3bcea2f7e25981ba0fe31e8f6a3f73536541` | `8c2cef5d5782061aa4effa3d1a550ee7d262639c` |

## Artifact and gallery parity

The complete consumer gates reproduced every publication file byte for byte
before and after each migration. Downloaded pull-request and post-merge CI
outputs match the same public release bytes.

| Add-on | Output | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| XNet | Production JAR | 129,889 | `bd08f4e4d0c7e88e7dbe15863e7f6669bd4c6c2cb495bfdbff43af2d35e49bb4` |
| XNet | Sources JAR | 77,515 | `85974eb7e762ae30bb206559366a6484253c4b42eb38a0eb66fa75f0a91486c3` |
| XNet | POM | 1,299 | `1b8bb96191f58dadff61af20cbc5ded6584182428fc4a3a3cf2ea097d70339ea` |
| XNet | Module metadata | 2,798 | `44fc26b47e40ecf2fe4d6810dcd7610abb3244410dc8cc2c719857f0578603f5` |
| LaserIO | Production JAR | 110,887 | `006900dd9000c6614c60b38df46b6cd1940dab53f059a381c282e9d79e89dbf1` |
| LaserIO | Sources JAR | 73,956 | `f4dc9e678e3730c6f54f1e0bd81bd1ef3424e227e8bd7a73c7ad59e947878aee` |
| LaserIO | POM | 1,317 | `2d74e77f8c4d1bc2369c363d05c75bc421eee0b2f0567227dea500d66d115bab` |
| LaserIO | Module metadata | 2,819 | `ca08ac2e7cc605c1ae135319e645dc916f371d9712243c2794fb608826f5e5bf` |
| Little Big Redstone | Production JAR | 54,658 | `d3bf3ee012b5a00e3f1d546429c1f7f72a183e27e38088deaae9654a9d4750a5` |
| Little Big Redstone | Sources JAR | 38,436 | `acb64bab01d29e8926acb215677e932c330e02c382f0807bd93976dcddb7d74f` |
| Little Big Redstone | POM | 1,389 | `900fa602d948bc1ce790b86670e44a07fc529b5acc8791233ad5a3a34f5ca800` |
| Little Big Redstone | Module metadata | 2,901 | `14050ff87f40d87da5a08c53134b59777550ed100013af07465fc121fcc65272` |
| Nature's Aura | Production JAR | 115,630 | `ba98a71dce55a343cfdf3c2f22421beebf26ac631f8a42841643da6f03d5f5e6` |
| Nature's Aura | Sources JAR | 79,148 | `1de2324e2e908c3e5827c4289d5c5b6cf83d6efe45c53c2b9f57cde0d6e50af2` |
| Nature's Aura | POM | 1,349 | `6947d6b7a9510c0ed08bf490c9fd094e33434c067ad3972ef893d5341403f29f` |
| Nature's Aura | Module metadata | 2,854 | `ca3f91807c5b813df681ca58bdf25f2652a94ff2f8b1359d0dd263064fe686e2` |

Gallery sources are unchanged. Fresh deterministic packages retain these
identities:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| XNet | 3,095 bytes | `d1d8fd654212d1d24f435fe7f34dd9df69b63677c27527c895879ca0056770f8` |
| LaserIO | 3,870 bytes | `acea3d7134891204f9b2246ed584fa6bfe730a7b8e3cfe2ab19b6187ddaf474b` |
| Little Big Redstone | 2,469 bytes | `cf2f3b370ef25ee2f3cbbef7d3c92b5a6d56e27f80985bee917346fd8a8ffe26` |
| Nature's Aura | 3,348 bytes | `8d33788f2a13074802d829c292b88b3ece888bbcfe11fef345508f93042c1264` |

## Build-contract parity

Normalized consumer task surfaces, dependency trees, outgoing variants, and
39-task release dry-run sets remained unchanged. All four complete Gradle
gates passed with 51 actionable tasks. Their test reports recorded 11, 12, 5,
and 10 passing Java tests, respectively.

The hash-locked wheel checks, v0.3 repository checks where configured, gallery
gates, and `actionlint` passed. Dirty toolkit worktrees, old or uninitialized
toolkit checkouts, altered wheel hashes, staged/index mismatches, missing
convention plugins, and wrong release tags were rejected by the applicable
fail-closed gates. Every toolkit checkout was restored clean at the exact v0.3
gitlink after the probes.

There is no convention-line reduction in this cohort because each repository
already used the shared convention. Consumer-owned dependency, publication,
manifest, gallery, packaging, exact-input, and release configuration remains
local. Existing acceptance statements are unchanged and are not reinterpreted
by this tooling-only migration.

## Result

The thirteenth cohort moves the final four v0.2 consumers to the v0.3 toolkit
trust and wheel identities while retaining the byte-identical Gradle
convention, published artifacts, galleries, release identities, and renderer
behavior.
