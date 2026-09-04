# Disposable ATMons 1.2.0 integration server

This is the credential-free identity and operating contract for the combined
BlueMap test server. The namespace, world, maps, and storage are disposable.
Player identity and the RCON password live only in Kubernetes Secrets.

## Runtime identity

| Component | Exact identity |
| --- | --- |
| Namespace | `bluemap-atmons-integration` |
| All the Mons | `1.2.0`, pack commit `c7bb230f21d14d26859d0b92548f089b3a493ad9` |
| Minecraft / NeoForge / Java | `1.21.1` / `21.1.248` / `21` |
| World | normal overworld, structures enabled, seed `731963181124214131` |
| BlueMap source | `feature/backport-5.23-stateless-java-web-server` at `7e07f4e74ec1e92a6ead9aa1e66054af3e133aac` |
| BlueMap runtime version | `5.22-feature.backport-5.23-stateless-java-web-server-46` |
| BlueMap release | `v5.23-agent.backport-5.23-mc1.21.1-2`; 6,545,661 bytes; SHA-256 `86a0323d24f472e425dda4d4e6bba2d7d8ce8315ad009930a67131128c715e62` |
| Add-ons | all 51 exact production releases in the refreshed `atmons-1.2.0` manifest, with no compatibility overlays |
| Integration harness | 190,653 bytes; SHA-256 `b35fc567c60d79a56ad4c20857979f94d900d3c09169f9ff87f1ac538f7826ed` |
| Gallery datapack | 592,097 bytes; SHA-256 `002e3c551a8edcfde32d92e7e70204622a403b151976e6114621f6803af6ad77` |
| Gallery layout / composition ledger | `6a8d0169090c100f5bd03b5c881ed4275a4f11643b958d9df07f247e57635479` / `e6c9dc8051420597b3513e554c44ac977768a008564f30c6c3c549a386ee48f6` |
| Canonical base-mod ledger | 375 JARs; SHA-256 `aba2db94fbcd6cf756d6ab2f03e7adc35422d4a2c1eb82e47d998ed740e4d70c` |

The BlueMap release contains the exact owner-accepted branch-context build.
Its internal runtime version remains
`5.22-feature.backport-5.23-stateless-java-web-server-46`, which is the exact
identity admitted by the published add-ons, while its source is the 5.23
backport commit recorded above. The refreshed manifest pins this release and
FramedBlocks `v0.1.0-alpha.5` directly; the final integration gate uses only
published production artifacts.

The runtime inventory contains 377 exact on-disk JARs. NeoForge exposes 374 of
them through `ModList`: the exact pack-pinned CrashAssistant wrapper,
KotlinForForge library, and ScalableCatsForce library root are bootstrap/library
inputs rather than ordinary mod files. The harness binds those three by exact
filename, size, and SHA-256 while still including them in the 377-file byte
inventory.

## Cluster layout

- One `Recreate` Deployment named `minecraft`, scheduled on the disposable
  staging node.
- One disposable, single-replica 50 GiB Longhorn PVC mounted at `/data`;
  pod-local `emptyDir` volumes hold `mods/` and `libraries/` to avoid repeated
  metadata-heavy PVC scans. Cross-node replication is deliberately disabled
  for this test-only volume because gallery and structure fixtures use
  synchronous chunk flushes.
- ClusterIP Service ports: Minecraft `25565`, BlueMap `8100`, RCON `25575`.
- Public BlueMap ingress: `bluemap-atmons.guenter.cloud`.
- The authorized player is whitelisted and has operator level 4. Credentials
  and identity values are not recorded here.

The gallery map ID is `atmons_integration`. Its render mask is limited to the
composed campus at X `8192..9203`, Y `194..256`, Z `8192..8985`. Structure
reference maps are generated after the live catalog, one collision-resistant
map ID per selected dimension and only for the four-block-bordered bounds.
The gallery starts on the Immersive Engineering pad at X `8303`, Z `8461`.
Both gallery and structure maps set `render-edges` to `false`; artificial edge
caps otherwise hide or fragment geometry inside these small disjoint masks.

## Stable test controls

The server disables time, weather, random ticks, vines, ordinary mob and
patrol spawning, insomnia, traders, wardens, raids, PvP, fire, fall, freeze,
drowning damage, and global sound events. It also disables animal, monster,
and NPC spawning in `server.properties`, allows flight, and uses peaceful
difficulty.

Minecraft 1.21.1 has no `spawnerBlocksWork` or general
`disablePlayerMovementCheck` gamerule. This profile uses
`disableElytraMovementCheck=true` and the global/server spawn controls as the
closest available equivalents.

Runtime worlds, BlueMap output, logs, raw test results, Kubernetes manifests,
Secrets, and generated structure catalogs stay outside Git.
