# Shared Gradle convention cohort 8

This records the eighth artifact-parity adoption of the BlueMap Add-on Toolkit
Gradle convention. It changes development tooling only. It does not update the
ATMons 1.2.0 compatibility manifest, meta-repository gitlinks, add-on versions,
accepted release tags, provenance, galleries, or renderer behavior.

## Scope

The cohort contains four exact-profile add-ons with multi-input admission and
different gallery and acceptance-state contracts:

- Camol;
- Integrated Dynamics;
- Oritech; and
- Mekanism.

Every repository pins toolkit `v0.3.0-alpha.1` at commit
`6cd34a8368cc4ee8628fbe830a90ec5b14960629` with a mode-160000 gitlink and the
same explicit trust pin in `settings.gradle`. The corresponding 20,585-byte
Python wheel has SHA-256
`82f1ec53603646849a7c2d4b58f3fb7000413fe83043a302bee88cc88daeb8f7`.
CI and release checkouts initialize recursive submodules without stored
credentials. Oritech uses the hash-locked verifier CLI; the other three
repositories do not acquire an unnecessary Python build dependency.

Each validation used BlueMap commit
`9be321df995a1103808621d529eb72773e719d4d` with BlueMapAPI commit
`285c9a60eff3ac2b0cab308ce1058d1565be0971`. The complete exact-input set was:

| Add-on | Input | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Camol | Camol 1.21.1-0.3.1 | 62,188 | `aafdbe962a4bbab97207f747ec52561ea34be9c49a4b044a835da82ff7d45609` |
| Integrated Dynamics | CyclopsCore 1.29.2 | 1,161,287 | `1d36aaa3d9abb71d0151bb5edd02f5580dfb020a229c63f6534a87a04d1cfab6` |
| Integrated Dynamics | Integrated Dynamics 1.34.0 | 4,369,336 | `2e6afc62a572cf3e1bd6b91321946790103c72793bc5fe1d0295c1138c072e87` |
| Integrated Dynamics | Integrated Tunnels 1.9.4-652 | 682,381 | `90dfa97a5666e377197e83fb3b90bdc4bb4a337eac61c7baa2336d8ce0573ca0` |
| Integrated Dynamics | Integrated Terminals 1.7.0-800 | 662,663 | `add10be15370234fd1491c318f1fadc2d7b621aa31ecf674a9c38f8b5befec92` |
| Integrated Dynamics | Integrated Crafting 1.4.6-605 | 377,591 | `25651914d0e59120129829687ad8f9a8ab44e6fd2c3176c53bb219b3764d58a4` |
| Integrated Dynamics | Integrated Scripting 1.0.24-424 | 27,892,500 | `10cafdeeece71175741f8b6c405c1bbfca09c7dfff416b565b87720af4f40545` |
| Oritech | Oritech 1.2.10 | 10,990,540 | `7c17c78ac55d9cbb71a9108a2bec7e2659192e08c5a1b49026088f875dbde821` |
| Oritech | Athena 4.0.6 | 99,944 | `43699885bbce3343916d4c5c4940cf0e3f9f6f02fdeb46e8655e121b42282ec5` |
| Oritech | GeckoLib 4.9.2 | 630,584 | `5e548466af9ab6aca7a91a7c7d4dc0dc8bc385e22958aed5da0e7bebd0fa3fba` |
| Mekanism | Mekanism 10.7.19.85 | 11,976,009 | `004dbc9f3106f4d192aeaa1ee1190dd16ec9ca8059ed3d093b80034f4c574f43` |
| Mekanism | Mekanism Generators 10.7.19.85 | 1,114,598 | `0e5783b111e756f27b48c62b2f0e02fff750c77f7985ff809bfadc5f444ba4ac` |
| Mekanism | Mekanism Covers 1.3-BETA | 136,513 | `7e67b8f5c111ef0d94abcd0c24580fa74c0532dbfa9e5cdbf58521e57cbbdc95` |
| Mekanism | MoreMachine 1.3.3 | 2,983,024 | `aebd1136a2e328a23d1801c768b387cf336bc1ebdab40770274d068bdaac9a12` |

## Reviewed merges

| Add-on | Reviewed PR | Feature commit | Merge commit | Gate |
| --- | --- | --- | --- | --- |
| Camol | [#4](https://github.com/jan-guenter/bluemap-camol-addon/pull/4) | `0227e8c0728f0bd786920610420201c331553ae6` | `ff27ec83b3a72d8171d40778f6e2ce6f41b4742f` | Gradle 9.6.1 exact Camol and accepted-JAR gate |
| Integrated Dynamics | [#4](https://github.com/jan-guenter/bluemap-integrated-dynamics-addon/pull/4) | `516162e6072975a741c72a9a2b7174a3464b3478` | `9763e4c54c50f02a77356da8d32c6b546114405a` | Gradle 9.6.1 exact six-input and installed-texture gate |
| Oritech | [#3](https://github.com/jan-guenter/bluemap-oritech-addon/pull/3) | `63469b2fb12ae416ef60a8028df5435197dcbca4` | `1f9789a6048ed51b4bb66aac5ca51392a794ac5b` | Gradle 9.6.1 exact three-input resource and gallery gate |
| Mekanism | [#3](https://github.com/jan-guenter/bluemap-mekanism-addon/pull/3) | `456329477bc8f9f4fcd35bfdee2ad2921d46078c` | `9ada186413d68b2f0513ba8c1d3167708fbc83f0` | Gradle 9.6.1 exact four-input and gallery gate |

Every merge has the reviewed base and feature commits as its two parents, and
each merge tree equals its reviewed feature tree. The resulting trees are
`54c50763f13828209e26dcee99b23ea94d3ee71c` for Camol,
`58671dd853f0dce2db0484c03993d9c79fb1af14` for Integrated Dynamics,
`950e56dfe70fca7d8abd3f430702fe0241c2e320` for Oritech, and
`b6d0004cc3343fb5b260ad513928b21f96eaaa1c` for Mekanism.

The PR and post-merge `main` CI runs passed for all four repositories:

- [Camol PR CI](https://github.com/jan-guenter/bluemap-camol-addon/actions/runs/33279745031)
  and [main CI](https://github.com/jan-guenter/bluemap-camol-addon/actions/runs/33279822205);
- [Integrated Dynamics PR CI](https://github.com/jan-guenter/bluemap-integrated-dynamics-addon/actions/runs/33279905139)
  and [main CI](https://github.com/jan-guenter/bluemap-integrated-dynamics-addon/actions/runs/33280009867);
- [Oritech PR CI](https://github.com/jan-guenter/bluemap-oritech-addon/actions/runs/33280510376)
  and [main CI](https://github.com/jan-guenter/bluemap-oritech-addon/actions/runs/33280711852); and
- [Mekanism PR CI](https://github.com/jan-guenter/bluemap-mekanism-addon/actions/runs/33280417555)
  and [main CI](https://github.com/jan-guenter/bluemap-mekanism-addon/actions/runs/33280605468).

No migration triggered a release workflow. Existing annotated release tags
remain on their accepted publication commits rather than the tooling merges:

| Add-on | Version | Tag object | Peeled release commit |
| --- | --- | --- | --- |
| Camol | `0.1.0-alpha.2` | `b5e78115d5281202487cbda3c4cbea50e11bcf16` | `3a3f3b37943fc506893a1548a28953ef1a5f0da9` |
| Integrated Dynamics | `0.1.0-alpha.2` | `8055ec4e3247fc6bb6ad61ae5f545fbe2541870e` | `f6f0d7c89563aa63f27970c898fda4cc720cc32f` |
| Oritech | `0.1.0-alpha.1` | `e981e92b60de6182a7da7a2229f28b815d93119f` | `a4ffa5632459193d10be181005a03e6cae5b4743` |
| Mekanism | `0.1.0-alpha.1` | `70fc32eb92cf6eff13dc497acebe1093bc927110` | `fd38ee958fa24795112fdd2ab91b9f3dfc36b29c` |

Camol and Integrated Dynamics retain their repository wording that alpha.2 is
the published aggregate candidate while alpha.1 remains the latest separately
owner-accepted release. Oritech and Mekanism have no such split: their alpha.1
publication and recorded owner acceptance refer to the same immutable bytes.

## Artifact and gallery parity

The complete consumer gates reproduced these files byte for byte before and
after each migration. They match the corresponding published release assets,
and downloaded PR and post-merge CI outputs match the same frozen bytes.

| Add-on | Production JAR | Sources JAR | POM | Module metadata |
| --- | --- | --- | --- | --- |
| Camol | `2c707f0cb1e8ebbef735f3afeae818e9154029a4d3892c58a737ae75891d197b` | `7962b84ad72f3b54ef65f5c84d95db86799ca96cdb613bf1572232f234624ba8` | `ad79cfab87c43d203d2eb664a2e5e1d563cf1251cf38594826a143342b023b84` | `ab35ac9c5b4fbb245fa6a8bbaf3cf5b54a04833a80c35f817630266220d4de09` |
| Integrated Dynamics | `11fdae6eb18513d7d06bbca1973e2eded36ae12f30a69bd9e09af148f8e70f18` | `8aca1d9e8b7bd79907daf3e92627bbe0788a2f384461c8a1cdc7d3319c8dc95b` | `acb19314d78f399cc80847a8a441c5dcd93e937aed089113d97d34486fd8d127` | `a828ee0c44390caf2548cbc099775f28b4497c08f637136bbf4b0b75dbc06b4c` |
| Oritech | `958ae6fa2ae5a17893cccc348d3a6ce90498ff16ded21a97b0575774b7698a8e` | `d8b3a391430a1a52d8efff61fec7b80d03449d4daf455c56ab28a474b6610858` | `3329db0d084ac41b8ed858bce552e9ef67591bfb4dfa0c567267c734585a8552` | `e768b4ec4bacdde766c1e35b322aad8003c5bf8bcd78a88a814cd6b38dfde147` |
| Mekanism | `fc0b0144dcd3dd5ec24747961bd57960f5f00d699c7bb5dc67975739fb0d61c7` | `c19f80ddd6f88be7f2fe587c8285c987f7a18466f464cfb88c09f3a19ef00ca0` | `0035d7538751c8242288e3cfc842a097780b6f4b25ee388b9bf0dbf6a0de5966` | `34c25ee65959dbf309011bd6b39c06456885e7b35e2311e22b0cc4d181dcfa12` |

Camol and Integrated Dynamics have manual source-only galleries rather than a
Gradle gallery artifact. Their unchanged gallery trees are respectively
`7db3ef119ff521f83f5cea6ff8c8a94f58dcbded` and
`1c0e48e9f8289fdfe090bf70990346d99a57cece`. The deterministic gallery ZIPs
for the other two add-ons remained byte-identical:

| Add-on | Gallery size | Gallery SHA-256 |
| --- | ---: | --- |
| Oritech | 3,051 bytes | `b3e7b3bcd825cafc1964623135c73a8f23bf322cf21308e633c331a6b6b746b7` |
| Mekanism | 4,024 bytes | `c20f657f3460a3ad201e9a8bf6d32298843b5a2ffa64800c00dc157285352f2a` |

## Build-contract parity

Dependency trees, outgoing variants, normalized consumer task surfaces, and
sorted release dry-run sets remained unchanged. Camol and Integrated Dynamics
retain 28 release tasks; Oritech and Mekanism retain 22. The four additional
`:gradle` tasks only compile the included convention plugin.

Consumer repository, dependency, publication, manifest, gallery, packaging,
debug, resource-pin, and release configuration remains local. All four retain
DEFLATED archives and Gradle's full default Java debug metadata. Existing
Gradle 10 deprecation warnings originate in the pinned BlueMap build.

Dirty toolkit worktrees and a checkout at toolkit v0.2 were rejected before
consumer configuration. Wrong release tags were rejected by every historical
release gate. After the probes, every toolkit checkout was restored clean at
the exact v0.3 gitlink.

The migration removes 110 repeated convention lines and adds four plugin
applications, a net reduction of 106 lines:

| Add-on | Before | After | Net reduction |
| --- | ---: | ---: | ---: |
| Camol | 139 | 115 | 24 lines |
| Integrated Dynamics | 139 | 115 | 24 lines |
| Oritech | 148 | 119 | 29 lines |
| Mekanism | 148 | 119 | 29 lines |

The consumer-owned trust preflight remains repeated because an included
plugin cannot authenticate the source checkout from which it is loaded.
Oritech's file-presence guard preserves manual resume of its historical tag,
which predates the toolkit lock. Tag-triggered historical runs otherwise keep
their tag-local workflow definitions.

## Result

The eighth cohort confirms the v0.3 convention across four exact multi-input
consumers without changing accepted artifacts, galleries, release identities,
or renderer behavior. Further adoption remains a repository-by-repository
migration with exact inputs, a frozen baseline, the complete local gate,
artifact comparison, reviewed PR CI, and post-merge `main` CI.
