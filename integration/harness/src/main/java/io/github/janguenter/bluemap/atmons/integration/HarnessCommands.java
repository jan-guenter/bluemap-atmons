package io.github.janguenter.bluemap.atmons.integration;

import com.mojang.brigadier.CommandDispatcher;
import java.util.function.Function;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/** Stable operator command surface for the integration instance. */
final class HarnessCommands {
    private static IntegrationController controller;

    private HarnessCommands() {
    }

    static void setController(IntegrationController newController) {
        controller = newController;
    }

    static void register(RegisterCommandsEvent event) {
        register(event.getDispatcher());
    }

    private static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("bluemapatmons")
                .requires(source -> source.hasPermission(2))
                .then(Commands.literal("structures")
                        .then(action("catalog", source -> controller.startCatalog()))
                        .then(action("generate", source -> controller.startGenerate()))
                        .then(action("publish", source -> controller.publishStructures()))
                        .then(action("render", source -> controller.renderStructures()))
                        .then(action(
                                "verify-render",
                                source -> controller.verifyStructureRenders()
                        ))
                        .then(action("status", source -> controller.status()))
                        .then(action(
                                "clean-forceloads",
                                source -> controller.cleanOwnedForceLoads()
                        )))
                .then(Commands.literal("galleries")
                        .then(action("publish", source -> controller.publishGalleries()))
                        .then(action("render", source -> controller.renderGalleries()))
                        .then(action(
                                "verify-render",
                                source -> controller.verifyGalleryRender()
                        )))
                .then(Commands.literal("runtime")
                        .then(action("identity", source -> controller.runtimeIdentity())))
                .then(Commands.literal("immersive-engineering")
                        .then(action(
                                "form",
                                source -> controller.formImmersiveEngineering(
                                        source.getLevel()
                                )
                        ))
                        .then(action(
                                "verify",
                                source -> controller.verifyImmersiveEngineering(
                                        source.getLevel()
                                )
                        ))));
    }

    private static com.mojang.brigadier.builder.LiteralArgumentBuilder<CommandSourceStack>
            action(
                    String literal,
                    Function<CommandSourceStack, IntegrationController.ActionResult> operation
            ) {
        return Commands.literal(literal).executes(context -> {
            IntegrationController.ActionResult result = operation.apply(context.getSource());
            if (result.successful()) {
                context.getSource().sendSuccess(
                        () -> Component.literal(result.message()),
                        false
                );
                return Math.max(1, result.count());
            }
            context.getSource().sendFailure(Component.literal(result.message()));
            return 0;
        });
    }
}
