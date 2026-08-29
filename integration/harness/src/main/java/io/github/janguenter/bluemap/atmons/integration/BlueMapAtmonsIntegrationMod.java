package io.github.janguenter.bluemap.atmons.integration;

import de.bluecolored.bluemap.api.BlueMapAPI;
import java.io.IOException;
import java.nio.file.Path;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.loading.FMLPaths;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.server.ServerStoppingEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

/** Dedicated-server-only entry point with no blocks, items, payloads, or client hooks. */
@Mod(value = BlueMapAtmonsIntegrationMod.MOD_ID, dist = Dist.DEDICATED_SERVER)
public final class BlueMapAtmonsIntegrationMod {
    public static final String MOD_ID = "bluemap_atmons_integration";
    private final IntegrationController controller;

    public BlueMapAtmonsIntegrationMod() throws IOException {
        Path directory = FMLPaths.CONFIGDIR.get().resolve("bluemap-atmons-integration");
        HarnessConfig config = HarnessConfig.loadOrCreate(directory);
        controller = new IntegrationController(directory, config);
        HarnessCommands.setController(controller);

        NeoForge.EVENT_BUS.addListener(HarnessCommands::register);
        NeoForge.EVENT_BUS.addListener(this::serverStarted);
        NeoForge.EVENT_BUS.addListener(this::serverStopping);
        NeoForge.EVENT_BUS.addListener(this::serverTick);
        BlueMapAPI.onEnable(controller::blueMapEnabled);
    }

    private void serverStarted(ServerStartedEvent event) {
        controller.serverStarted(event.getServer());
    }

    private void serverStopping(ServerStoppingEvent event) {
        controller.serverStopping();
    }

    private void serverTick(ServerTickEvent.Post event) {
        controller.tick();
    }
}
