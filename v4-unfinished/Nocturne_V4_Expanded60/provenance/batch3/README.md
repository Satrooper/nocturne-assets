# Nocturne V4 — Sentinel limbs, Batch03

This additive batch replaces Siege_Sentinel's limb/pelvis geometry. It is not the completed full V4 collection or an AAA realism claim. Use the final batch archive in preference to the earlier limb checkpoint.

## Files and changes

`bosses/Siege_Sentinel/` contains animated FBX/GLB, a packed editable game Blender scene, a separate higher-detail geometry authoring scene, two geometry-only FBX LODs and integration metadata. `textures/` contains four 2048 PBR maps. `previews/` contains matching Batch02/batch03 neutral front, side, back, limb, hand and foot renders and three videos rendered from the final delivered GLB.

The limb mesh is replaced with open curved armour shells, tapered load spines, side links, exposed bearing axles/flanges, elbow/knee guards, wrist yokes, individual phalanges/pins, hip cradles, ankle bearings, heel supports, sole load rails and grounded pads. The waist column connects the rebuilt pelvis to the retained chest. Roughness varies spatially and a shallow metal grain is baked. Original 52 rest bones are preserved; final game mesh is 47,900 triangles. Automatic UV projection and budget decimation are used. This is custom procedural geometry authoring, not a hand-sculpted or manually retopologized production character.

The current polished actions are in `Siege_Sentinel.blend`. `Siege_Sentinel_Authoring.blend` is the editable higher-detail geometry scene with the original motion bank, saved before contact correction. The scripts reproduce geometry from the restored Batch02 source, then polish the game scene. To rebuild: place Batch02 at `restored/nocturne-v4-batch02` beside this batch folder, run `source/sentinel_limbs.py` then `source/polish_contacts.py` in Blender 4.2.9. Keep that order. Review/packaging scripts are included.

## Animation and integration

All 21 existing clips remain. Nineteen receive a two-bone leg solve and level foot orientation correction; they are not 19 new attack choreographies. Actual delivered foot geometry is sampled each frame at 30 fps. `audit/Foot_Geometry_Motion_Check.json` records the results. `Clip_Contact_Findings.json` derives clip-specific floor-near intervals, horizontal joint travel, root displacement and endpoint differences. Those intervals indicate geometry near the floor, not certified planted contact or damage timing.

In-place and root-motion labels remain in `asset.json`. In-place stance movement needs actor movement at the matching authored speed. Root displacement and endpoint measurements must be reviewed when configuring extraction. Do not silently turn root-return clips into displacement attacks. Existing sockets and effect anchors are retained; the shoulder weapon geometry is unchanged from Batch02. Existing event cues and hit-window labels are unvalidated author cues. Paired finishers/player weapon handling are not included in this Sentinel batch.

Engine work is still required for root extraction, locomotion blending, collision shapes, damage/hit detection, stamina, invulnerability, lock-on, boss AI/phases, projectiles, effect/audio routing and LOD switching.

## Validation and visible limitations

Structural checks: full FBX, GLB and both LOD FBX are reimported in Blender; action presence, 52-bone skeleton, finite geometry, normalized weights and texture availability are checked. Sources pack their image dependencies; GLB embeds textures. The external texture folder is also supplied. Every final ZIP entry is CRC-tested, normal extraction is performed and every extracted file is compared against its packaged source. A separate SHA-256 and packaging report are supplied.

Visual review: front/side/back/close-ups from actual delivered GLB, plus locomotion/punch/brace playback. Limb/foot construction is visibly revised, but the asset remains stylized. The retained head/chest, narrow neck, simple coating response and atlas seams need further improvement. Bearing parts are kinematic rigid components, not a physical actuator simulation. Clearance sampling is not an exhaustive self-intersection test.

Nineteen corrected clips have positive measured foot-geometry clearance. `Ground_Slam` and `Death_RootMotion` still have severe floor penetration and are NOT approved for gameplay. Foot sliding, full-body clipping, weight transfer and attack anticipation/recovery remain incomplete. Those two clips are retained to preserve the source bank and clearly marked unfinished.

Engine testing: not performed; no destination game project/runtime is supplied in the restored asset pack. iPhone testing: not performed. No performance claim is made.

## Full collection status

`audit/Collection_Status.json` carries the previous full-pack tracker forward. Other creatures, player handling, sounds, effects and weapon prototypes are retained in prior packs and not upgraded by this batch. The lost earlier player-handling work has not been delivered and is not counted as complete.
