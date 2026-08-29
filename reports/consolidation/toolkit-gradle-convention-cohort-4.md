# Shared Gradle convention cohort 4

This records the fourth artifact-parity adoption of the BlueMap Add-on Toolkit
Gradle convention. It changes development tooling only. It does not update the
ATMons 1.2.0 compatibility manifest, meta-repository gitlinks, add-on versions,
accepted release tags, provenance, or renderer behavior.

## Scope

The cohort contains four exact-profile add-ons with deterministic galleries
and sealed release gates:

- XNet;
- LaserIO;
- Little Big Redstone; and
- Nature's Aura.

Every repository pins toolkit `v0.2.0-alpha.1` at commit
`f58da04567f10efe615c582797f3ab00b7a7343f` with a mode-160000 gitlink and the
same explicit trust pin in `settings.gradle`. The corresponding 19,827-byte
Python wheel has SHA-256
`cbfbad7ea12ea631b9f36a5261482dde3ca4d8f270df1b5faf75310020b115f9`.
CI and release checkouts initialize recursive submodules without stored
credentials.

Each accepted validation used its own clean BlueMap checkout at commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The exact upstream inputs were:

- XNet, 611,577 bytes at
  `0f393a4bff91a90e0665ec6d66ff649e45f9c33311dc038e4a5df0b154ea9d80`,
  with RFTools Base, 463,973 bytes at
  `5195ba530e6cf9ba61c9954a3297679e6d29aa1b6182e27ae14ea43463dd4b00`;
- LaserIO, 1,305,285 bytes at
  `03e8537d75bc2f4ced2fc214d3409753e684d1056ee63b26db7a2b9e199ef4df`;
- Little Big Redstone, 1,415,860 bytes at
  `ba4eac4050528c274db4b8b43c38152ef58407298f499d28b13c97a7ca8a0896`;
  and
- Nature's Aura, 1,443,280 bytes at
  `c76a257fdf5da2bf2c21dcc4e474a7a1ff11202a13fca02fedc97e329426e517`.

## Reviewed merges

| Add-on | Reviewed PR | Feature commit | Merge commit | Gate |
| --- | --- | --- | --- | --- |
| XNet | [#4](https://github.com/jan-guenter/bluemap-xnet-addon/pull/4) | `e4e01c738ad4c60e5f015a281ab5da3548ad2013` | `a4fe9359106f6af6a814d09947b5e08ba7022c89` | Gradle 9.6.1 exact XNet/RFTools Base gate plus gallery checks |
| LaserIO | [#4](https://github.com/jan-guenter/bluemap-laserio-addon/pull/4) | `0662559d960a3fe2b111da931480b5cd8aa0a431` | `86c9feb02e2abe9e030b0cd2fc8e96342a723377` | Gradle 9.6.1 exact LaserIO gate plus gallery checks |
| Little Big Redstone | [#4](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/pull/4) | `a2bc0a84cec476215eeef957431655c4ebf7659f` | `acead980d43fd072a0e3b988f54eddfa00515345` | Gradle 9.6.1 exact Little Big Redstone gate plus gallery checks |
| Nature's Aura | [#4](https://github.com/jan-guenter/bluemap-natures-aura-addon/pull/4) | `0346b2baf8b5c7ccaf9c20ca4f213b802131f095` | `cf49c3e27bf7e10959785cfc6ce906a925ee13da` | Gradle 9.6.1 exact Nature's Aura gate plus gallery checks |

Every merge has the reviewed base and feature commits as its two parents, and
each merge tree equals its reviewed feature tree. The resulting merge trees
are `9b240a270c959a926b8f0ff3686d82f79ad94d34` for XNet,
`81b67247ae2f37cb3b4c8f92a8f99f90ae142665` for LaserIO,
`df9bfb625ecde1e9b90792f732c9ee00b1f7851f` for Little Big Redstone, and
`9f1937f5c9788ac76ce2c80251595b2bb6907ac0` for Nature's Aura.

The PR and post-merge `main` CI runs passed for all four repositories:

- [XNet PR CI](https://github.com/jan-guenter/bluemap-xnet-addon/actions/runs/33270874102)
  and [main CI](https://github.com/jan-guenter/bluemap-xnet-addon/actions/runs/33271024225);
- [LaserIO PR CI](https://github.com/jan-guenter/bluemap-laserio-addon/actions/runs/33270910048)
  and [main CI](https://github.com/jan-guenter/bluemap-laserio-addon/actions/runs/33271073908);
- [Little Big Redstone PR CI](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/actions/runs/33271187477)
  and [main CI](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/actions/runs/33271350928); and
- [Nature's Aura PR CI](https://github.com/jan-guenter/bluemap-natures-aura-addon/actions/runs/33271394170)
  and [main CI](https://github.com/jan-guenter/bluemap-natures-aura-addon/actions/runs/33271564741).

No migration triggered a release workflow. Every repository remains at
`0.1.0-alpha.1`. Its existing annotated `v0.1.0-alpha.1` tag remains on the
accepted release commit rather than the tooling merge:

| Add-on | Tag object | Peeled release commit |
| --- | --- | --- |
| XNet | `c8767931d911ea4615310a1a823fd6ac4f693751` | `925a5e890e0f97791599c063825bc0ac4fc2bd51` |
| LaserIO | `ae9ce209208402a49fe6531cbce48258c2940142` | `2148a344b1ae78e77b95aa2baa51efe46c1357e8` |
| Little Big Redstone | `a8fa875f2dd46865cbdcecfcab22bdc7573575c9` | `cee9ed82e22e8041d53c3d9d54a61bee82da72a1` |
| Nature's Aura | `1bcb3bcea2f7e25981ba0fe31e8f6a3f73536541` | `8c2cef5d5782061aa4effa3d1a550ee7d262639c` |

## Artifact and gallery parity

The complete consumer gates reproduced these files byte for byte before and
after each migration. They also match the corresponding published
`0.1.0-alpha.1` release assets. Downloaded PR and post-merge CI artifacts were
compared to the same frozen bytes.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| XNet | `bd08f4e4d0c7e88e7dbe15863e7f6669bd4c6c2cb495bfdbff43af2d35e49bb4` | `85974eb7e762ae30bb206559366a6484253c4b42eb38a0eb66fa75f0a91486c3` | `1b8bb96191f58dadff61af20cbc5ded6584182428fc4a3a3cf2ea097d70339ea` | `44fc26b47e40ecf2fe4d6810dcd7610abb3244410dc8cc2c719857f0578603f5` |
| LaserIO | `006900dd9000c6614c60b38df46b6cd1940dab53f059a381c282e9d79e89dbf1` | `f4dc9e678e3730c6f54f1e0bd81bd1ef3424e227e8bd7a73c7ad59e947878aee` | `2d74e77f8c4d1bc2369c363d05c75bc421eee0b2f0567227dea500d66d115bab` | `ca08ac2e7cc605c1ae135319e645dc916f371d9712243c2794fb608826f5e5bf` |
| Little Big Redstone | `d3bf3ee012b5a00e3f1d546429c1f7f72a183e27e38088deaae9654a9d4750a5` | `acb64bab01d29e8926acb215677e932c330e02c382f0807bd93976dcddb7d74f` | `900fa602d948bc1ce790b86670e44a07fc529b5acc8791233ad5a3a34f5ca800` | `14050ff87f40d87da5a08c53134b59777550ed100013af07465fc121fcc65272` |
| Nature's Aura | `ba98a71dce55a343cfdf3c2f22421beebf26ac631f8a42841643da6f03d5f5e6` | `1de2324e2e908c3e5827c4289d5c5b6cf83d6efe45c53c2b9f57cde0d6e50af2` | `6947d6b7a9510c0ed08bf490c9fd094e33434c067ad3972ef893d5341403f29f` | `ca3f91807c5b813df681ca58bdf25f2652a94ff2f8b1359d0dd263064fe686e2` |

The deterministic gallery ZIPs also remained byte-identical:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| XNet | 3,095 bytes | `d1d8fd654212d1d24f435fe7f34dd9df69b63677c27527c895879ca0056770f8` |
| LaserIO | 3,870 bytes | `acea3d7134891204f9b2246ed584fa6bfe730a7b8e3cfe2ab19b6187ddaf474b` |
| Little Big Redstone | 2,469 bytes | `cf2f3b370ef25ee2f3cbbef7d3c92b5a6d56e27f80985bee917346fd8a8ffe26` |
| Nature's Aura | 3,348 bytes | `8d33788f2a13074802d829c292b88b3ece888bbcfe11fef345508f93042c1264` |

## Build-contract parity

All five dependency trees, outgoing variants, and normalized consumer task
sets remained unchanged in each repository. The additional tasks compile the
included convention plugin. Family-owned repository, dependency, publication,
manifest, gallery, packaging, debug, and release configuration remains in the
consumers. Java compile debug metadata and STORED archive compression are
unchanged.

The migration removes 104 repeated convention lines and adds four plugin
applications, a net reduction of 100 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| XNet | 505 | 480 | 25 lines |
| LaserIO | 504 | 479 | 25 lines |
| Little Big Redstone | 504 | 479 | 25 lines |
| Nature's Aura | 504 | 479 | 25 lines |

The consumer-owned trust preflight remains repeated because an included plugin
cannot authenticate the source checkout from which it is loaded. Current CI
derives the toolkit CLI version from the exact wheel URL. Historical release
tags without `requirements/toolkit.txt` retain their tag-local release path
through the existing file-presence guard.

Toolkit `v0.2.0-alpha.1` has one advisory checker limitation: the
`conventions check` command searches for eight convention-owned literals in
`build.gradle` and therefore reports them as absent after the plugin replaces
those literals.
The exact Gradle, artifact, gallery, dependency, task, PR CI, and post-merge CI
gates above do not invoke that advisory check and remain valid. The migrator
already reports the plugin-based repositories as current. A bounded toolkit
`v0.3` correction is tracked separately.

## Result

The fourth cohort confirms the convention across four more Gradle 9.6.1
consumers without changing accepted artifacts or release identities. Further
adoption remains a repository-by-repository migration with exact inputs, a
frozen baseline, the complete local gate, artifact comparison, reviewed PR
CI, and post-merge `main` CI.
