package io.github.janguenter.bluemap.atmons.integration;

import blusunrize.immersiveengineering.api.IEProperties;
import blusunrize.immersiveengineering.api.multiblocks.MultiblockHandler;
import blusunrize.immersiveengineering.api.multiblocks.MultiblockHandler.IMultiblock;
import blusunrize.immersiveengineering.api.multiblocks.TemplateMultiblock;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.scores.Objective;
import net.minecraft.world.scores.ScoreHolder;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;

/** Exact staging bridge for the IE 12.4.2-194 gallery helper contract. */
final class ImmersiveEngineeringGalleryBridge {
    static final ResourceLocation STORAGE = ResourceLocation.fromNamespaceAndPath(
            "immersiveengineering_gallery", "formation"
    );
    private static final String FAILURE_SCORE_HOLDER = "#immersive_engineering";
    private static final String FAILURE_OBJECTIVE = "bma_test";
    private static final int MAX_REPORTED_MISMATCHES = 8;
    private static final ResourceLocation IMPROVED_BLAST_FURNACE =
            ResourceLocation.fromNamespaceAndPath(
                    "immersiveengineering", "multiblocks/improved_blast_furnace"
            );
    private static final ResourceLocation CHUNK_LOADER = ResourceLocation.fromNamespaceAndPath(
            "immersiveengineering", "multiblocks/chunk_loader"
    );

    private final MinecraftServer server;

    ImmersiveEngineeringGalleryBridge(MinecraftServer server) {
        this.server = server;
    }

    IntegrationController.ActionResult form(ServerLevel level) {
        try {
            Request request = request();
            ResolvedMultiblock resolved = resolve(level, request);
            Verification existing = inspect(level, request, resolved);
            if (existing.matches()) {
                writeResult("form", request, true, existing.checked(), "already formed");
                return IntegrationController.ActionResult.success(
                        request.caseId() + " already formed", existing.checked()
                );
            }

            FakePlayer player = FakePlayerFactory.getMinecraft(level);
            MultiblockHandler.MultiblockFormEvent event =
                    MultiblockHandler.postMultiblockFormationEvent(
                            player, resolved.multiblock(), resolved.trigger(), ItemStack.EMPTY
                    );
            if (event.isCanceled()) {
                writeResult("form", request, false, 0, "formation event cancelled");
                return IntegrationController.ActionResult.failure(
                        request.caseId() + ": IE formation event was cancelled"
                );
            }
            boolean formed = resolved.multiblock().createStructure(
                    level,
                    resolved.trigger(),
                    request.facing().getOpposite(),
                    player
            );
            Verification verification = inspect(level, request, resolved);
            if (!formed || !verification.matches()) {
                String detail = !formed
                        ? "IE createStructure returned false"
                        : verification.summary();
                writeResult("form", request, false, verification.checked(), detail);
                return IntegrationController.ActionResult.failure(
                        request.caseId() + ": " + detail
                );
            }
            writeResult("form", request, true, verification.checked(), "formed");
            return IntegrationController.ActionResult.success(
                    "Formed " + request.caseId() + " using " + request.multiblock(),
                    verification.checked()
            );
        } catch (RuntimeException exception) {
            writeFailureResult("form", exception.getMessage());
            return IntegrationController.ActionResult.failure(
                    "IE formation request failed: " + exception.getMessage()
            );
        }
    }

    IntegrationController.ActionResult verify(ServerLevel level) {
        try {
            Request request = request();
            ResolvedMultiblock resolved = resolve(level, request);
            Verification verification = inspect(level, request, resolved);
            if (!verification.matches()) {
                recordVerificationFailure();
                writeResult(
                        "verify",
                        request,
                        false,
                        verification.checked(),
                        verification.summary()
                );
                return IntegrationController.ActionResult.failure(
                        request.caseId() + ": " + verification.summary()
                );
            }
            writeResult("verify", request, true, verification.checked(), "formed");
            return IntegrationController.ActionResult.success(
                    "Verified " + request.caseId() + " ("
                            + verification.checked() + " formed blocks)",
                    verification.checked()
            );
        } catch (RuntimeException exception) {
            recordVerificationFailure();
            writeFailureResult("verify", exception.getMessage());
            return IntegrationController.ActionResult.failure(
                    "IE verification request failed: " + exception.getMessage()
            );
        }
    }

    private Request request() {
        CompoundTag root = server.getCommandStorage().get(STORAGE);
        if (!root.contains("request", Tag.TAG_COMPOUND)) {
            throw new IllegalArgumentException("missing request compound in " + STORAGE);
        }
        CompoundTag request = root.getCompound("request");
        requireType(request, "schema", Tag.TAG_ANY_NUMERIC);
        if (request.getInt("schema") != 2) {
            throw new IllegalArgumentException("request schema must be 2");
        }
        String caseId = requiredString(request, "case_id");
        ResourceLocation formedBlock = requiredLocation(request, "formed_block");
        ResourceLocation template = requiredLocation(request, "template");
        ResourceLocation multiblock = requiredLocation(request, "multiblock");
        BlockPos origin = requiredPosition(request, "origin");
        BlockPos formationOffset = requiredPosition(request, "formation_origin_offset");
        String facingName = requiredString(request, "facing");
        Direction facing = Direction.byName(facingName);
        if (facing == null || facing.getAxis().isVertical()) {
            throw new IllegalArgumentException("facing must be horizontal: " + facingName);
        }
        requireType(request, "mirrored", Tag.TAG_ANY_NUMERIC);
        boolean mirrored = request.getBoolean("mirrored");
        if (!"immersiveengineering".equals(formedBlock.getNamespace())
                || !"immersiveengineering".equals(template.getNamespace())
                || !"immersiveengineering".equals(multiblock.getNamespace())) {
            throw new IllegalArgumentException("all IE request IDs must use its namespace");
        }
        return new Request(
                caseId,
                formedBlock,
                template,
                multiblock,
                origin,
                formationOffset,
                facing,
                mirrored
        );
    }

    private ResolvedMultiblock resolve(ServerLevel level, Request request) {
        IMultiblock multiblock = MultiblockHandler.getByUniqueName(request.multiblock());
        if (multiblock == null) {
            throw new IllegalArgumentException(
                    "IE did not register multiblock " + request.multiblock()
            );
        }
        Block expectedBlock = BuiltInRegistries.BLOCK.get(request.formedBlock());
        if (expectedBlock == null
                || !request.formedBlock().equals(BuiltInRegistries.BLOCK.getKey(expectedBlock))) {
            throw new IllegalArgumentException(
                    "formed block is not registered: " + request.formedBlock()
            );
        }
        if (multiblock.getBlock() != expectedBlock) {
            throw new IllegalArgumentException(
                    "formed_block does not match IE multiblock: expected "
                            + BuiltInRegistries.BLOCK.getKey(multiblock.getBlock())
            );
        }
        Rotation rotation = rotation(request.facing());
        Mirror mirror = request.mirrored() ? Mirror.FRONT_BACK : Mirror.NONE;
        BlockPos formationOrigin = transformedFormationOrigin(
                request.origin(), request.formationOffset(), mirror, rotation
        );
        BlockPos trigger = TemplateMultiblock.withSettingsAndOffset(
                formationOrigin, multiblock.getTriggerOffset(), mirror, rotation
        );
        if (!level.isLoaded(trigger)) {
            throw new IllegalArgumentException("formation trigger chunk is not loaded");
        }
        return new ResolvedMultiblock(
                multiblock,
                expectedBlock,
                formationOrigin,
                trigger,
                mirror,
                rotation
        );
    }

    private Verification inspect(
            ServerLevel level,
            Request request,
            ResolvedMultiblock resolved
    ) {
        List<String> mismatches = new ArrayList<>();
        int checked = 0;
        for (var blockInfo : resolved.multiblock().getStructure(level)) {
            BlockPos absolute = TemplateMultiblock.withSettingsAndOffset(
                    resolved.formationOrigin(),
                    blockInfo.pos(),
                    resolved.mirror(),
                    resolved.rotation()
            );
            checked++;
            BlockState actual = level.getBlockState(absolute);
            if (actual.getBlock() != resolved.expectedBlock()) {
                addMismatch(
                        mismatches,
                        absolute + "=" + BuiltInRegistries.BLOCK.getKey(actual.getBlock())
                );
                continue;
            }
            if (actual.hasProperty(IEProperties.MIRRORED)
                    && actual.getValue(IEProperties.MIRRORED)
                    != expectedMirrored(request.multiblock(), request.mirrored())) {
                addMismatch(mismatches, absolute + " has wrong mirrored state");
            }
            if (actual.hasProperty(IEProperties.FACING_HORIZONTAL)
                    && actual.getValue(IEProperties.FACING_HORIZONTAL)
                    != expectedFacing(request.multiblock(), request.facing())) {
                addMismatch(mismatches, absolute + " has wrong facing state");
            }
        }
        if (checked == 0) {
            addMismatch(mismatches, "IE returned an empty structure");
        }
        return new Verification(checked, List.copyOf(mismatches));
    }

    private static void addMismatch(List<String> mismatches, String detail) {
        if (mismatches.size() < MAX_REPORTED_MISMATCHES) {
            mismatches.add(detail);
        }
    }

    private void recordVerificationFailure() {
        Objective objective = server.getScoreboard().getObjective(FAILURE_OBJECTIVE);
        if (objective != null) {
            server.getScoreboard().getOrCreatePlayerScore(
                    ScoreHolder.forNameOnly(FAILURE_SCORE_HOLDER), objective
            ).increment();
        }
    }

    private void writeResult(
            String action,
            Request request,
            boolean successful,
            int checked,
            String message
    ) {
        CompoundTag root = server.getCommandStorage().get(STORAGE).copy();
        CompoundTag result = new CompoundTag();
        result.putInt("schema", 1);
        result.putString("action", action);
        result.putString("case_id", request.caseId());
        result.putBoolean("ok", successful);
        result.putInt("checked", checked);
        result.putString("message", safeMessage(message));
        root.put("result", result);
        server.getCommandStorage().set(STORAGE, root);
    }

    private void writeFailureResult(String action, String message) {
        CompoundTag root = server.getCommandStorage().get(STORAGE).copy();
        CompoundTag result = new CompoundTag();
        result.putInt("schema", 1);
        result.putString("action", action);
        result.putBoolean("ok", false);
        result.putInt("checked", 0);
        result.putString("message", safeMessage(message));
        root.put("result", result);
        server.getCommandStorage().set(STORAGE, root);
    }

    private static String safeMessage(String message) {
        if (message == null || message.isBlank()) {
            return "unspecified failure";
        }
        return message.length() <= 512 ? message : message.substring(0, 512);
    }

    private static String requiredString(CompoundTag tag, String key) {
        requireType(tag, key, Tag.TAG_STRING);
        String value = tag.getString(key);
        if (value.isBlank() || value.length() > 256) {
            throw new IllegalArgumentException(key + " must be 1-256 characters");
        }
        return value;
    }

    private static ResourceLocation requiredLocation(CompoundTag tag, String key) {
        ResourceLocation value = ResourceLocation.tryParse(requiredString(tag, key));
        if (value == null) {
            throw new IllegalArgumentException("invalid resource location in " + key);
        }
        return value;
    }

    private static BlockPos requiredPosition(CompoundTag tag, String key) {
        requireType(tag, key, Tag.TAG_INT_ARRAY);
        int[] value = tag.getIntArray(key);
        if (value.length != 3) {
            throw new IllegalArgumentException(key + " must contain exactly three integers");
        }
        return new BlockPos(value[0], value[1], value[2]);
    }

    private static void requireType(CompoundTag tag, String key, int type) {
        if (!tag.contains(key, type)) {
            throw new IllegalArgumentException("missing or invalid " + key);
        }
    }

    private static Rotation rotation(Direction facing) {
        return switch (facing) {
            case NORTH -> Rotation.NONE;
            case EAST -> Rotation.CLOCKWISE_90;
            case SOUTH -> Rotation.CLOCKWISE_180;
            case WEST -> Rotation.COUNTERCLOCKWISE_90;
            default -> throw new IllegalArgumentException("facing must be horizontal");
        };
    }

    static BlockPos transformedFormationOrigin(
            BlockPos templateOrigin,
            BlockPos formationOffset,
            Mirror mirror,
            Rotation rotation
    ) {
        return TemplateMultiblock.withSettingsAndOffset(
                templateOrigin, formationOffset, mirror, rotation
        );
    }

    static Direction expectedFacing(ResourceLocation multiblock, Direction requestedFacing) {
        // IE deliberately reflects the improved blast furnace around its master and
        // reverses the facing supplied to the ordinary template-forming path.
        return IMPROVED_BLAST_FURNACE.equals(multiblock)
                ? requestedFacing.getOpposite()
                : requestedFacing;
    }

    static boolean expectedMirrored(ResourceLocation multiblock, boolean requestedMirrored) {
        // The chunk-loader template is mirror-symmetric. IE tests the non-mirrored
        // candidate first, so both raw variants form with MIRRORED=false.
        return !CHUNK_LOADER.equals(multiblock) && requestedMirrored;
    }

    record Request(
            String caseId,
            ResourceLocation formedBlock,
            ResourceLocation template,
            ResourceLocation multiblock,
            BlockPos origin,
            BlockPos formationOffset,
            Direction facing,
            boolean mirrored
    ) {
    }

    private record ResolvedMultiblock(
            IMultiblock multiblock,
            Block expectedBlock,
            BlockPos formationOrigin,
            BlockPos trigger,
            Mirror mirror,
            Rotation rotation
    ) {
    }

    private record Verification(int checked, List<String> mismatches) {
        boolean matches() {
            return mismatches.isEmpty();
        }

        String summary() {
            return mismatches.isEmpty()
                    ? "formed"
                    : mismatches.size() + " mismatch(es): " + String.join("; ", mismatches);
        }
    }
}
