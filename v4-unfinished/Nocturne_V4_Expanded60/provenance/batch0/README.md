# Nocturne Dark Fantasy Assets — revision 3

Asset-only delivery. Original procedural meshes, skeletons, animations, PBR maps, WAV audio and effects atlases. This pack does not contain a game, AI implementation, engine scene, or code changes to Nocturne.

## Read this before evaluating quality

This revision adds materially more geometry and texture detail than the earlier faceted prototype: shaped bodies, smooth tube skin weights, wing fingers and membranes, jaws, teeth, claws, surface normal maps and LOD meshes. **The results remain procedural and visibly stylised. They are not photorealistic AAA artwork, motion capture, or a claim to match Elden Ring, Black Myth: Wukong or television VFX.** The reference works informed the requested dark-fantasy mood; no meshes, textures, sounds, designs or animation files were extracted from those works.

## Changes in revision 3

The 30-model collection now includes overlapping dragon scale geometry and belly shields, more varied proportions, shaped armour with separate trim and rivets, masks, boots, fabric mantles, tactical pouches and harnesses, industrial cooling fins and cables, shell plates, gills and bark shingles. Bamboo Mantis has a new insect body; Neon Wisp has a new floating-core body. Creature names preserve v2 folder identity.

The 656-clip v2 procedural animation bank (with visible-core locomotion/threat adaptations for the rebuilt wisp), 66 synthesized sounds, 12 effects atlases and 51 texture maps are retained. This is an art revision, not 656 new animations or a new audio pack. Revised meshes and attachment weights still need anatomical/blending review in the destination engine. Plates are often rigid to their assigned bones; fabric is skinned without cloth simulation.

## Contents

- 10 dragon variations, 10 boss designs, 10 smaller enemy designs.
- Each creature: a skinned FBX with animation takes, animated GLB with embedded textures, editable Blender source, two lower-detail skinned FBXs, and `asset.json` metadata.
- 12 reusable movement/reaction clips per creature, 8 creature-specific staged sequences per creature (240 sequences total), plus flight/swimming clips for appropriate bodies.
- 17 original 2K PBR surface sets: base colour, tangent-space normal, and roughness maps.
- 66 original synthesised mono WAV effects at 48 kHz / 16 bit: 30 creature vocalisations and 36 combat/movement/elemental effects.
- 12 transparent effects atlases; 16 frames each in a 4×4 grid, 256 pixels per frame.
- Neutral studio renders of the actual exported artwork, manifests, structural validation and reproducible source scripts.

The 240 creature-specific sequences use combinations of reusable motion primitives with different ordering, sides, amplitudes, timing and root movement. **They are not 240 independently motion-captured animation types.** The original Mixamo files are not duplicated. Attack names are intended uses; they do not generate gameplay effects by themselves.

## Formats and paths

Keep the directory tree intact. FBXs reference textures at `../../textures/`. Blender files use the same relative layout. GLBs embed their image data. FBX and GLB can shade differently depending on engine material import settings: use the provided colour, normal and roughness maps explicitly if the importer omits them.

Models are authored in Blender with Z up, forward generally -Y, and metre units. Exporters apply their format conventions. Verify orientation and scale once in your engine. FPS is 30. Clip names in `asset.json` are authoritative. Each creature has its own non-Mixamo skeleton. Do not retarget humanoid Mixamo clips directly onto a dragon or arthropod without a suitable retargeting setup.

The LOD1/LOD2 FBXs keep the skeleton and vertex weights but omit duplicated animation banks. Reuse the base skeleton's animation data. Decimated mesh quality needs inspection under movement before a production release.

## Animations and event data

`asset.json` contains clip names, duration, loop flags, root-motion flags and suggested anticipation/attack/recovery markers. Markers are authoring cues, not gameplay hit windows certified by testing. Damage, hitboxes, sound triggering, blending, root-motion handling, stagger interruption and boss phases belong in your engine.

Run/walk clips are procedural cycles and need foot-contact polish. Some specialised attacks are approximate motion sketches and need anatomical cleanup. Wing membranes are weighted to wing/forearm/chest bones; jaw, tail and limb bones can be driven independently. Fins and many decorative elements are rigid attachments. Source models have overlapping anatomical components; they are not uniformly retopologised production sculpts.

## Audio

All included sounds are **original synthesis**, not recordings of animals, weapons, voices, or audio from existing games. The files have a -1.72 dBFS normalised peak and short fades. Import as positional mono sounds; add your engine's distance attenuation and room reverb. Three variations are supplied for each combat effect family to reduce repetition. Perceptual mix and device-speaker review remain necessary.

## Effects

Each PNG atlas uses straight alpha. Frame order starts top-left and runs left-to-right, row by row. The JSON manifest specifies suggested blending and playback. These are 2D billboard/particle texture assets; they are not an engine particle system, fluid simulation, or rendered 3D fire volume. For a sword trail, breath cone or lightning beam, author the emitter/path in the game and apply an appropriate atlas/material.

## Performance and final art work

Do not use the unoptimised whole collection simultaneously. Set LOD distances, animation culling, shadow limits, texture streaming and nearby-enemy budgets. No iPhone FPS, thermal behaviour or visual equivalence to commercial games is certified.

Remaining art work includes sculpting and retopology for a realistic finish, local texture painting, anatomy correction, animation cleanup, foot planting, collision authoring and engine material/particle tuning. The pack supplies editable assets for that work rather than claiming those steps have been completed.

## Provenance and rights

All delivered geometry, animation recipes, textures, synthetic audio, effects and scripts were generated for this task. No third-party art downloads or franchise assets are included. You may use and modify these outputs in Nocturne. Existing repository assets were excluded based on the prior audit of `Satrooper/nocturne-assets` at commit `f2305cd7bb1021d4e8bb26e557e2ad86567b1e33`; the external repository was not modified.

## Rebuild

Use Blender 4.2.9 for the Blender scripts. Python texture/audio scripts require numpy, scipy and Pillow. To reconstruct v2 inputs, copy this pack to a sibling folder named `nocturne-dark-fantasy-v2`, run `source/make_textures.py` there, then Blender with `--background --python source/export_pack.py -- 0 30`, and apply `source/fix_hound.py`. In the v3 folder, run Blender with `--background --python source/upgrade_v3.py -- 0 30`. This rebuild depends on those v2 source models; the final delivered .blend files are independently editable and do not need the old pack. Texture/audio generation scripts are included unchanged. Rendering is CPU Cycles. Source files and textures must stay in the supplied relative layout. A rebuild can take substantial time and disk space.


## Verification of this delivery

All 30 base FBXs passed rig, named-clip count, sampled skinned-mesh movement, finite-geometry and normalized-weight checks. All 30 GLBs passed clip-name, buffer-bound and embedded-image checks; embedded image bytes were additionally decoded. All 60 reduced-detail FBXs passed rig, geometry-reduction and weight checks. All 51 texture PNGs decoded successfully. The 66 synthesized WAV files and 12 effects atlases carry forward their v2 format checks. Base meshes range from 2,034 to 47,328 triangles. These checks do not certify anatomy, artistic realism, combat timing or playback in your engine.
