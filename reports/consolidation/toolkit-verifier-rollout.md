# Shared verifier rollout

This records the first source-preserving extraction from the All the Mons
1.2.0 BlueMap add-on portfolio. It does not move a compatibility tag, alter a
released add-on artifact, or change the server installer.

## Shared tool identity

The public [BlueMap Add-on Toolkit](https://github.com/jan-guenter/bluemap-addon-toolkit)
release is `v0.1.0-alpha.1` at commit
`ce02e66412e595ec0c002cfe1579af65c7e17e0d`. Consumers pin its wheel by the
immutable release URL and SHA-256
`1a82280178a6a8468b485893c2759f834e58743143bfe518d16d155512ca9491`.
The meta-repository pins the same gitlink and wheel identity in
`tooling/manifest.json` through [PR #2](https://github.com/jan-guenter/bluemap-atmons/pull/2).

The toolkit remains development-only. It contributes no class, resource,
dependency, or nested JAR to an installed add-on.

## Exact cohort

The original scan found 24 byte-exact copies of each of these files:

- `tools/verify_pinned_artifacts.py`, SHA-256
  `dc7c6d80796f9d5773183a499aa61320a0126ac21f1fdb5c8e872bbf618ca798`;
- `tools/verify_staged_equivalence.py`, SHA-256
  `cc8fa6cb1e79b85555b9f10920909b0c03fdc8d78445e07c877674e513fcff9f`.

Three representative consumers first proved exact artifact, accepted-entry,
release-seal, historical-tag-resume, and clean-install behavior. The remaining
21 exact members were then promoted without admitting a structurally similar
but non-identical verifier.

| Consumer | PR | Merge commit |
| --- | ---: | --- |
| Ars Creo | [#3](https://github.com/jan-guenter/bluemap-ars-creo-addon/pull/3) | `afb211d5b650774f1c7ceabfb2cc8d1ca1a486c0` |
| Ars Energistique | [#3](https://github.com/jan-guenter/bluemap-ars-energistique-addon/pull/3) | `5d7aeacd485f4d02189cac61c549fcb86f5539dc` |
| Ars Nouveau | [#3](https://github.com/jan-guenter/bluemap-ars-nouveau-addon/pull/3) | `01468a35095326d8470ca7fb06f595b69f90a45a` |
| Ars Technica | [#3](https://github.com/jan-guenter/bluemap-ars-technica-addon/pull/3) | `264a923ffe97896c467baeb0602ac5bb70dfb457` |
| Draconic Evolution | [#3](https://github.com/jan-guenter/bluemap-draconic-evolution-addon/pull/3) | `ada76d3d71cd005a3680854cb7d80fcac37e2b6c` |
| Extreme Reactors | [#3](https://github.com/jan-guenter/bluemap-extreme-reactors-addon/pull/3) | `ea5451522ac97fdfc84e5bededaf4df3dd87a08e` |
| Immersive Energistics | [#3](https://github.com/jan-guenter/bluemap-immersive-energistics-addon/pull/3) | `cf6f576781bafcf977b4aa1fbc594545d762d80d` |
| Immersive Engineering | [#3](https://github.com/jan-guenter/bluemap-immersive-engineering-addon/pull/3) | `eab8786558ededb1720f8533af23b333c295d533` |
| Laser Bridges | [#3](https://github.com/jan-guenter/bluemap-laser-bridges-addon/pull/3) | `5b60d010bd94eaa5e3016256bce19c1f639cf619` |
| LaserIO | [#3](https://github.com/jan-guenter/bluemap-laserio-addon/pull/3) | `62b86f308d718853bd8f2976dd9b58d3b0218c73` |
| Little Big Redstone | [#3](https://github.com/jan-guenter/bluemap-little-big-redstone-addon/pull/3) | `9dd25519442e49a2ff433a92d026dd94b3a6bfa2` |
| Lootr | [#3](https://github.com/jan-guenter/bluemap-lootr-addon/pull/3) | `4c348f351d92f5482adef66a5a6c854481234046` |
| More Red | [#3](https://github.com/jan-guenter/bluemap-morered-addon/pull/3) | `22ff20c96890920cff65d8c6f318b240972cef6b` |
| Nature's Aura | [#3](https://github.com/jan-guenter/bluemap-natures-aura-addon/pull/3) | `3efbaadcf24990cdf3eb003300bebcc4be37c636` |
| PneumaticCraft | [#3](https://github.com/jan-guenter/bluemap-pneumaticcraft-addon/pull/3) | `574a5eed8b411cd36d060f0473d09c584b3b83ae` |
| Productive Bees | [#3](https://github.com/jan-guenter/bluemap-productive-bees-addon/pull/3) | `cc5101a7f7c5cf2db131147058ac5a75338948de` |
| Productive Metalworks | [#3](https://github.com/jan-guenter/bluemap-productive-metalworks-addon/pull/3) | `7e4265970360249f83ad2bbdf09e6f0ee0b3a1a1` |
| Railcraft Reborn | [#3](https://github.com/jan-guenter/bluemap-railcraft-reborn-addon/pull/3) | `8364e1564ec1125604b11e58a8f886a09c3b90ec` |
| RFTools Utility | [#3](https://github.com/jan-guenter/bluemap-rftools-utility-addon/pull/3) | `18fdf86841e07b9f310bdd8c7360642fb652dd95` |
| Supplementaries | [#3](https://github.com/jan-guenter/bluemap-supplementaries-addon/pull/3) | `02971fdff2252224952fc26f7ae3309e725813d5` |
| Tempad | [#3](https://github.com/jan-guenter/bluemap-tempad-addon/pull/3) | `2268b495a7aa3030f2e106639fe1042fbb133828` |
| Theurgy | [#3](https://github.com/jan-guenter/bluemap-theurgy-addon/pull/3) | `d04809060073d488e220707c6e82c17f8bb76c37` |
| Trophy Manager | [#3](https://github.com/jan-guenter/bluemap-trophy-manager-addon/pull/3) | `5592be65c5a6c83a23d6d135801ecd2ac8e98810` |
| XNet | [#3](https://github.com/jan-guenter/bluemap-xnet-addon/pull/3) | `3a936dc85fe915147d92085d9502cfe6b56980f1` |

Every PR changed exactly eight paths and passed its required isolated
release-candidate build. Across the cohort, the reviewed diffs contain 816
additions and 5,447 deletions, a net reduction of 4,631 lines. The two shared
commands eliminate 48 duplicate script files containing 5,280 physical lines.

No PR changed Java source, tests, galleries, provenance, `gradle.properties`,
add-on versions, accepted seals, or release tags. Historical release workflow
resumes remain valid because toolkit installation is conditional on the file
present in the checked-out immutable tag.

## Next gate

The next toolkit slice is Gradle and workflow conventions. It should first
prove a distribution and pinning model that works in a fresh clone without
creating an installed runtime dependency. Production-source extraction into
`bluemap-addon-runtime` remains behind that gate because its classes must be
merged or relocated safely into each consumer while preserving separate
BlueMap add-on classloaders.

The immutable ATMons 1.2.0 clone report still describes the released
compatibility snapshot. It is intentionally not rewritten to substitute
tooling-only `main` commits for release-tag targets.
