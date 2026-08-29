# ATMons 1.2.0 BlueMap candidate integration report

Status on 2026-08-29: the combined add-on runtime gate, final structure
generation and catalog, bounded structure rendering, and gallery render
verification have passed. The lightweight browser check is recorded below.
This is a candidate report, not a release record.

## Scope and release boundary

This run tests the exact All the Mons 1.2.0 baseline with all 51 published
BlueMap add-ons installed together. It uses a candidate BlueMap backport from
`feature/backport-5.23-stateless-java-web-server`. The add-on JARs are verified
copies of the immutable `atmons-1.2.0` release artifacts with staging-only
compatibility overlays. Those overlays are test artifacts and must not be
published.

The published `atmons-1.2.0` tag, compatibility manifest, BlueMap gitlink, and
51 add-on gitlinks remain unchanged. No result in this report changes the
meaning of that tag.

## Candidate identity

| Component | Exact identity |
| --- | --- |
| All the Mons | `1.2.0`, pack commit `c7bb230f21d14d26859d0b92548f089b3a493ad9` |
| Minecraft | `1.21.1` |
| NeoForge | `21.1.248` |
| Java | `21` |
| BlueMap source | `feature/backport-5.23-stateless-java-web-server` at `7e07f4e74ec1e92a6ead9aa1e66054af3e133aac` |
| BlueMap runtime version | `5.22-feature.backport-5.23-stateless-java-web-server-46` |
| BlueMap candidate JAR | 6,545,661 bytes, SHA-256 `86a0323d24f472e425dda4d4e6bba2d7d8ce8315ad009930a67131128c715e62` |
| Published compatibility manifest | SHA-256 `c181203ddaf4ad353cecf7975af21acb1f55011b5a8c8f1b25bf79a8202db138` |
| Candidate overlay manifest | SHA-256 `7fafd6364cacd080409990e3dfa99b3f33dcd86a8176eef7053cb1d88f8f1ad9` |
| Candidate pack inventory | 51 packs, SHA-256 `2e3da52ddd957d51a1e4b99caff55b98da0abfd6861a0ebde3a9475c37e79004` |
| Final structure and render harness | 190,653 bytes, SHA-256 `b35fc567c60d79a56ad4c20857979f94d900d3c09169f9ff87f1ac538f7826ed` |
| Canonical base-mod ledger | 375 JARs, SHA-256 `aba2db94fbcd6cf756d6ab2f03e7adc35422d4a2c1eb82e47d998ed740e4d70c` |

The server contains 377 exact JARs on disk. That is the 375-file canonical
base ledger plus BlueMap and the server-only integration harness. BlueMap
loads the 51 candidate add-on packs separately from its packs directory.

## Completed test gates

### Released add-on source gates

All 51 add-on repositories passed their applicable tracked gallery checks and
common Gradle gates against the BlueMap commit pinned by the published
manifest.

| Result | Value |
| --- | ---: |
| Add-ons passed | 51 of 51 |
| Commands passed | 180 of 180 |
| Failed or not run | 0 |
| Duration | 3,019.278 seconds |
| Result SHA-256 | `fa7994f6949ee10a30afa4766117ea11be0ce0413e333c38bed4adfb339defbb` |

That positive run used runner version 1.2.0. A later runner version capable of
rehashing external inputs before and after each command confirmed that the
same input endpoints were ready. The retained bridge attestation cannot rule
out a transient input change that was restored during the older positive run.
It does establish matching pre-run and post-run endpoints, clean child
repositories, and final BlueMap source integrity.

An earlier candidate source at `07a4293fd95f1fcee799a1aa69e564f38f00e699`
also exercised the fail-closed source-pin policy. Forty-four add-ons rejected
the unknown BlueMap commit as expected, seven declared candidate-aware paths
passed, and there were no unexpected outcomes. Its result SHA-256 is
`d2da2ef2b018780aaf78b28d0f6d41d57a97fe87fbfe1d0f0969dc888e2eee18`.
This is policy evidence, not build evidence for the final candidate commit.

### Combined runtime gallery gate

The exact final BlueMap candidate and all 51 staging add-on packs passed one
combined server run. The runner required a container replacement, then repeated
the artifact, activation, datapack, and composition attestations before it
built any gallery.

| Result | Value |
| --- | ---: |
| Gallery builds performed | 51 |
| Gallery builds skipped | 0 |
| Asserted passes | 51 |
| Failed or performed without assertion | 0 |
| Mirrored verifier branches | 24,308 |
| Activation markers before restart | 51 |
| Activation markers after restart | 51 |
| Runtime result SHA-256 | `e7c992d97f7fd6504bae763f3dde370f3366cd88dcb44cfddd28bda870b20c60` |

After their completion barriers, AE2's pre-verification counter contained four
transient failures and XNet's contained one. The runner retained those two
counts, totaling five failures, as diagnostics, reset the counters before
authoritative verification, and then observed zero failures for both add-ons.
No reset occurred after the final verification.

The runtime gallery receipt binds an earlier 159,347-byte revision of the
test-only harness, SHA-256
`863b8de701915b9258c0405f75c6925001cf0cf10b29da51f0a3c83357e2c602`.
It binds the same BlueMap candidate JAR and candidate add-on inventory shown
above. The structure catalog and render work used the final 190,653-byte
harness. The completed gallery receipt proves the product runtime and gallery
gate. The completed generation and structure-suite receipts prove the final
harness's generation and render behavior.

### Gallery composition

The composer placed all 51 child galleries on a divided high-altitude campus.
Each add-on has its own labeled area and bounded load, build, verify, and
release lifecycle.

| Artifact | Exact identity |
| --- | --- |
| Gallery datapack | 592,097 bytes, SHA-256 `002e3c551a8edcfde32d92e7e70204622a403b151976e6114621f6803af6ad77` |
| Gallery layout | SHA-256 `6a8d0169090c100f5bd03b5c881ed4275a4f11643b958d9df07f247e57635479` |
| Composition ledger | SHA-256 `e6c9dc8051420597b3513e554c44ac977768a008564f30c6c3c549a386ee48f6` |
| Composition ID | `e95195166bb5c4db49fd86358d6be378757721be1ae8e54a0b3823ff7f9a15a2` |
| Campus bounds | X `8192..9203`, Y `194..256`, Z `8192..8985` |

## Structure reference catalog

The harness inspected the live registry in every loaded dimension. It found
one seed-derived instance for every structure with an eligible placement,
read the generated structure bounds, clamped vertical bounds to the dimension
build limits, and added a four-block border.

| Catalog result | Count |
| --- | ---: |
| Registered structure entries | 329 |
| Eligible, placed, and located | 313 |
| Registry-only entries | 16 |
| Planned structure markers | 313 |
| Unique chunks selected for generation | 15,270 |
| Unique BlueMap regions | 300 |
| Selected dimensions | 10 |

The 16 registry-only entries are not unresolved locate failures. Twelve have
no enabled placement eligible in any loaded dimension. Exact pack rules
deliberately disable the other four: Better Dungeons disables
`betterdungeons:small_nether_dungeon` in the shipped configuration. Better
Mineshafts disables the vanilla `minecraft:mineshaft` and
`minecraft:mineshaft_mesa` placements. Better Strongholds disables
`minecraft:stronghold` through its exact shipped mixin. Ten Better Mineshafts
variants used the wider bounded search; all were located.

| Catalog artifact | SHA-256 |
| --- | --- |
| Structure catalog | `c0a47c7b06b79a9d2aa7181e6bf628caa7b5e54ea2e8e703c42a0167255a2e5d` |
| Render masks | `4862a7f8f7c8ba71df6cabadf1e7505297d9ac71d6d421980bf174d8d64915b1` |
| Work state at catalog completion | `3586d1dff36424fcff2d51b01af3a9e1f1da58ab6a9800d36d3624e37aeaccea` |
| Generated BlueMap map manifest | `b2fa94af6b4a7e219f8184d4e0cdf63f51b02fe01198b459a5a286bb381253bf` |

The first complete generation pass exposed final vertical bounds for eight
vanilla structures whose provisional starts had reported different heights.
The harness rejected publication on that mismatch before it scheduled any
render. This final catalog was produced against the fully generated world; its
located structures, X/Z bounds, selected chunks, regions, and dimension set
remain unchanged, while its corrected vertical masks are the ones installed
for rendering.

The selected dimension maps are:

| Dimension | BlueMap map ID |
| --- | --- |
| `aether:the_aether` | `atmons_aether_the_aether_631a209451dd` |
| `allthemodium:the_other` | `atmons_allthemodium_the_other_04c6fa08832b` |
| `deeperdarker:otherside` | `atmons_deeperdarker_otherside_4678eef36fca` |
| `eternal_starlight:starlight` | `atmons_eternal_starlight_starlight_7c58a177a673` |
| `legendarymonuments:distortion_world` | `atmons_legendarymonuments_distortion_world_0c460c619581` |
| `minecraft:overworld` | `atmons_minecraft_overworld_3f60de212b48` |
| `minecraft:the_end` | `atmons_minecraft_the_end_03cf6b592c8f` |
| `minecraft:the_nether` | `atmons_minecraft_the_nether_60143955c503` |
| `the_bumblezone:the_bumblezone` | `atmons_the_bumblezone_the_bumblezone_212294a35f1d` |
| `undergarden:undergarden` | `atmons_undergarden_undergarden_6a372f9c0928` |

Structure generation completed all 15,270 of 15,270 target chunks at
`2026-08-29T02:10:56.951167313Z`. The target digest is
`eef15fcafda32172cc149eab410ffa4cf07f24e05f865a0cf6a11c33b7f84d6c`,
the generation receipt SHA-256 is
`b91b98f1fa5b21fc4ad2b64d5ae5ac797ce565be5c2dd7a2f3335f123e5f58ef`,
and the final work-state SHA-256 is
`571208d5d752f0b5f6d58e7a3d376fb2687320a7857cd048675f4cecbf522c83`.
The terminal state had no remaining batches and no harness-owned force-loaded
chunks.

The final edge-disabled structure suite passed with result SHA-256
`0fb20ccff67ec0b45016748c783952b517c46bff2c821f3d403cf3b0daa72fae`.
Its schedule SHA-256 is
`9cc771cb11732d4dc573295779f8a42f76b911b0964962406d678729accc20d4`,
scheduled at `2026-08-29T03:59:23.526Z`. It validated all 300 requested
region states across ten maps and found 4,827 fresh high-resolution tiles.
The retained storage evidence contained 30 fresh region-state files and 6,353
files in total. Its tile-evidence SHA-256 is
`3000547d1e8a0c21f33625d62eb1d174dbdf07b68af946bcd91973e4e894daba`.
The suite replayed and byte-compared all ten map configurations against
generator SHA-256
`1c5f7099840b07473c1d4ba5fe63b21f0ef3efa677a0a257749ca33a29ad21ea`
and completed at `2026-08-29T04:44:26.412582Z` on the same server boot.

An earlier storage-valid render used BlueMap's artificial mask-edge caps. The
lightweight browser pass exposed those caps as black or clipped views in nine
of the ten structure maps. The tracked generator now disables `render-edges`
for these small disjoint masks and chooses a located structure as each map's
presentation anchor. The final suite above is a complete fresh rerender after
that correction; its result supersedes the earlier render receipt.

Owner review then exposed a marker lifecycle problem. BlueMap retained the
marker JSON on disk after a restart, but the harness did not restore structure
markers to the live API, and browser-local visibility state could hide the
shared marker-set ID on every map. The corrected harness replays only a
catalog with its matching sealed generation receipt, publishes the versioned
`atmons-structures-v2` set, and disables depth testing for underground bounds.
The public endpoints expose all 313 markers across the ten maps with exact
counts `4, 42, 1, 4, 3, 204, 7, 11, 33, 4`. A fresh Chromium profile loaded
the Overworld set as visible with all 204 markers and an active WebGL 2
context. No structure rerender was required.

## Public inspection

- [BlueMap base](https://bluemap-atmons.guenter.cloud/)
- [Combined 51-add-on gallery](https://bluemap-atmons.guenter.cloud/#atmons_integration:8303:195:8461:200:0.65:0.95:0:0:perspective)
- In-game gallery teleport: `/execute in minecraft:overworld run tp @s 8303 210 8461`

The authorized player is whitelisted and has operator level 4. Player identity,
credentials, and session-local network forwarding details are not recorded.

The harness published 102 gallery markers to `atmons_integration`. The first
verification found five omitted edge tiles because their adjacent chunk and
light prerequisites were absent. Only those five tile footprints were
generated and lighted, and no force-loaded chunks were left behind. The
browser pass then exposed the same artificial mask-edge caps as the structure
maps. The final gallery configuration disables `render-edges` and starts on a
real Immersive Engineering test pad. Its fresh render was scheduled at
`2026-08-29T04:45:25.486Z`; the schedule SHA-256 is
`487e2befc7adeff4e0f4db6dad30fe854433b7b6a0ad90066343af881966d69f`.
The verifier confirmed all 589 fresh high-resolution tiles across four
regions, with evidence SHA-256
`6f7a3206cd643f6188f1207bec7c1dac77438b74ad18dea43bb63295ef0ec598`.

Representative links target located structures at the center of their
four-block-bordered markers. Camera distance is widened where a close
perspective would start inside tall or underground geometry:

| Dimension | Representative structure | Public BlueMap view |
| --- | --- | --- |
| `aether:the_aether` | `aether:gold_dungeon` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_aether_the_aether_631a209451dd:-532:114:62:24:0.65:0.95:0:0:perspective) |
| `allthemodium:the_other` | `dungeons_arise:illager_galley` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_allthemodium_the_other_04c6fa08832b:-2382:191:832:24:0.65:0.95:0:0:perspective) |
| `deeperdarker:otherside` | `deeperdarker:ancient_temple` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_deeperdarker_otherside_4678eef36fca:-371:45:4:24:0.65:0.95:0:0:perspective) |
| `eternal_starlight:starlight` | `eternal_starlight:cursed_garden` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_eternal_starlight_starlight_7c58a177a673:329:71:873:24:0.65:0.95:0:0:perspective) |
| `legendarymonuments:distortion_world` | `legendarymonuments:distortion_portal` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_legendarymonuments_distortion_world_0c460c619581:-125:26:111:24:0.65:0.95:0:0:perspective) |
| `minecraft:overworld` | `cobblemonextrastructures:dragons_den` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_minecraft_overworld_3f60de212b48:-439:7:42:160:0.65:0.95:0:0:perspective) |
| `minecraft:the_end` | `minecraft:end_city` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_minecraft_the_end_03cf6b592c8f:-1193:233:-870:80:0.65:0.95:0:0:perspective) |
| `minecraft:the_nether` | `legendarymonuments:heatran_cave` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_minecraft_the_nether_60143955c503:-3011:78:460:160:0.65:0.95:0:0:perspective) |
| `the_bumblezone:the_bumblezone` | `the_bumblezone:honey_slime_ranch` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_the_bumblezone_the_bumblezone_212294a35f1d:560:46:1057:24:0.65:0.95:0:0:perspective) |
| `undergarden:undergarden` | `undergarden:forgotten_vestige` | [Open map](https://bluemap-atmons.guenter.cloud/#atmons_undergarden_undergarden_6a372f9c0928:-41:58:11:160:0.65:0.95:0:0:perspective) |

The final browser sanity pass completed at
`2026-08-29T05:25:40.928Z`. Fresh Chromium contexts opened the exact gallery
link and all ten final structure links. Every view returned HTTP 200, selected
the expected map ID, created five 1,600 by 900 canvases, initialized WebGL 2,
and retained an active context. There were no HTTP 4xx/5xx responses or socket
timeouts; canceled lower-detail tile requests were ordinary LOD replacement.
The gallery, Aether, Other, Otherside, Starlight, Distortion, and Bumblezone
were coherent at distance 24. Wider perspectives were required to keep the
camera outside geometry in Overworld (160), End (80), Nether (160), and
Undergarden (160). The final Undergarden link uses the visible located
`undergarden:forgotten_vestige` instead of the predominantly empty Denizen
Camp view. Daylight was forced while judging intentionally dark dimensions.

A passing automated rendering check proves that BlueMap wrote fresh
high-resolution tiles for the requested regions and reached an idle queue. It
does not compare those tiles with the Minecraft client and does not prove
visual parity. Owner review remains the visual acceptance gate.

## Disposable server profile

The integration server uses a fresh normal world with structures enabled and
seed `731963181124214131`. It disables time and weather advance, random ticks,
ordinary mob spawning, patrols, phantoms, traders, wardens, raids, PvP, fire,
fall, freeze, and drowning damage. It also disables global sound events and
uses peaceful difficulty. These controls reduce staging load. They are not
recommended production settings.

Minecraft 1.21.1 does not expose the later `spawnerBlocksWork` gamerule, and
the exact pack has no equivalent configuration switch. Peaceful difficulty
and the global spawn controls prevent the practical hostile-entity load, but
they do not disable the vanilla spawner block tick itself.

The world, generated chunks, maps, logs, raw receipts, and cluster storage are
disposable and remain outside Git.

## Consolidation audit

The [ATMons 1.2.0 deduplication audit](../deduplication/atmons-1.2.0.md)
scanned all 51 exact add-on commits. It covered 2,887 eligible files and
29,115,561 bytes. The scan found 7 exact file groups, 45 exact and 47 renamed
whole-Java-file groups, plus 374 exact and 195 renamed Java method groups.

The recommended extraction order is:

1. `bluemap-addon-dev-toolkit`
2. `bluemap-addon-runtime`
3. `bluemap-addon-adapter-api`, after the 5.23 integration API settles
4. `bluemap-addon-render-core`
5. `bluemap-addon-connected-textures`

No shared module has been extracted yet. Clone matches justify review, not a
claim that rendering behavior is interchangeable. Geometry, UV, translucency,
connected-texture, and block-entity helpers need visual conformance fixtures
before code moves between repositories.

## Publication state

The public meta repository is
[`jan-guenter/bluemap-atmons`](https://github.com/jan-guenter/bluemap-atmons).
Candidate integration work is isolated on
`feature/integration-testing-atmons-1.2.0`. This run does not authorize a new
compatibility tag, a BlueMap release, or altered child add-on releases.

The initial completed implementation state was commit
`27dc37991748f780e264ea99b0cc53f2175edd8d`. The subsequent structure-marker
lifecycle correction is commit
`de8bf48a95ce9113e8562b09534ad11740dc2388`. Both were pushed to
`origin/feature/integration-testing-atmons-1.2.0` and reviewed in
[pull request #1](https://github.com/jan-guenter/bluemap-atmons/pull/1).

The complete 13-command local validation matrix passed for that implementation
state, including the 15-test child gate suite and the integration harness
`clean check build`. The corrected production harness JAR is 191,145 bytes
with SHA-256
`6eba5639fc97760a784d765e7b9eab692b4ef9b18d36fc0b1992bf2f7328646a`.
The corrected build also passed the repository validator, structure-suite unit
checks, its full Gradle gate, and the observed restart/public-browser test.
GitHub Actions
[Validate run 33236458241](https://github.com/jan-guenter/bluemap-atmons/actions/runs/33236458241)
passed for the initial implementation commit, and
[Validate run 33251833741](https://github.com/jan-guenter/bluemap-atmons/actions/runs/33251833741)
passed for the exact marker-correction commit in 1 minute 32 seconds.
