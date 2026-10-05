# Nocturne V4 — benchmark iteration

This is a concrete two-benchmark asset revision and a player motion prototype bank. It is **not a completed realistic/AAA upgrade of all 30 V3 creatures**. The other 28 remain unchanged in the separately repaired V3 pack. No new creature designs were added.

## Delivered files

| Asset | Triangles | Bones | Exported clips |
|---|---:|---:|---:|
| Cinder_Crown | 49,888 | 39 | 27 |
| Siege_Sentinel | 33,616 | 52 | 21 |
| Existing repository mannequin / new player bank | Existing Y Bot geometry | Mixamo skeleton plus root/sockets | 46 |

Each benchmark includes animated FBX, self-contained animated GLB, skeletal LOD1/LOD2 FBX, a baked-material Blender file, a procedural-material Authoring Blender file and an `asset.json`. Four 2048px PBR atlases per benchmark contain base colour, tangent normal, roughness and metallic. Original texture inputs are retained for editable materials. The player FBX contains the animation skeleton without a mesh; its GLB and Blender source include the existing repository mannequin for preview/retargeting. These are 94 exported clips including in-place/root-motion and other variants, **not 94 distinct motion-capture types**.

## What changed

Cinder_Crown has continuous weighted skin reconstructed from the V3 geometry, reworked skull/jaw masses, socket recesses, upper/lower lids, a dark mouth interior, palate, tongue, gums and individually shaped teeth. Neck/limb masses blend into the torso; separate overlapping body scale tiles were removed. Wing humerus/forearm/digit structure and weighted trunk-attached membranes replace the loose fan. A spatially varying procedural scale mask supplies surface relief. Its skin remains stylized; it does not have a production-quality manual sculpt or anatomically hand-placed scales.

Siege_Sentinel is a coherent machine. Tapered, chamfered armour planes replace rounded generic shells. Exposed bearings/axles, forearm/wrist links, articulated fingers, heel/forefoot pieces, service panels, radiators, power bus, battery attachment and recoil-mounted shoulder barrels are included. The visor and distinct ceramic/steel/joint/copper materials separate functions. The construction is still simplified, and its pistons are visual components rather than validated mechanical linkages.

Benchmark motion was reauthored with clip-specific poses and baked FK/IK. Walk/run targets use planted stance segments; poles follow the moving body; lunge distances were reduced to remain within limb reach. Turns use stepping targets (dragon 45°, Sentinel 90°). Sentinel punches/backhand/slam use hand targets as well as body preparation/recovery. Flight uses asymmetric flap timing and swimming adds body/tail motion. The results remain procedural rather than motion capture or final animator polish.

## Player moves and repository audit

The bank supplies pistol firing/aimed firing, tactical/empty reloads, forward/backward/left/right dodges in place and with root travel, backstep, left/right parry, riposte, three light and two heavy combo stages, two weapon switches, four directional reactions, knockdown/get-up, swimming/treading/diving and two attacker/victim finisher pairs. It is a starting animation bank, not a validated complete combat system. No pistol, magazine, sword or shield art props are included; the final weapons change required grip and contact poses.

`repository_inventory.txt` records the tracked paths at commit `f2305cd7bb1021d4e8bb26e557e2ad86567b1e33`. The repository already contains reloads, Standing Up, rolls, Drinking, Flying, Stabbing and melee packs. These are not treated as absent merely because a new clip exists here. `repository_motion_audit.json` records imports and actual hips/hand trajectory samples from pistol idle, three reload files and Standing Up. The generic reload imports include substantial world translation (about 14.61m for Reload/Reload 3, 5.03m for Reload 2); isolate/extract their root before layering them. Only these five repository FBXs were sampled; the other 458 animation files were not visually audited. No pistol-specific firing, complete directional dodge set, paired finisher contract, or swimming set was identifiable by filename, which is a candidate gap rather than proof of absence.

## Timing, contacts and attachment contract

`integration_metadata.json`, both `asset.json` files and `player_animation/animation_manifest.json` contain per-clip events, motion kinds, nominal/exported duration, root displacement, foot samples and effect/weapon anchors. Benchmark stance intervals refer to **ankle bone origins**, not sole surfaces or physics contacts. Player samples include a planted flag derived from the authoring IK state; no player foot-slip certification is claimed.

Event times are authored on each nominal clip clock. Frame rounding means exported duration can differ by up to one frame; use normalized event time or the supplied exported duration when resampling. Attack cues are **not validated damage windows**. No invulnerability window or hitbox volume is implicitly guaranteed by a clip name or event.

Extract travel from `root` on benchmarks and `NocturneRoot` on the player. Root-motion lunges/dodges finish at their authored displacement rather than returning to their start. For looping travel, accumulate cycle displacement in the actor controller instead of wrapping the actor back with the animation curve. In-place locomotion needs matching controller speed. Takeoff/landing and knockdown have vertical motion: decide explicitly whether animation or physics owns that axis.

Bone-local rest matrices and offsets define mouth/breath, claws, tail, fists, muzzle centres and player hand sockets. Offsets are in authoring coordinates; do not copy XYZ blindly across an importer basis conversion. The Sentinel muzzle anchors are barrel-group centres. Orient the final muzzle flash/projectile axis to the actual barrel before use.

Paired clips use a shared 73-frame clock at 30fps. Backstab victim starts 0.92m forward of the attacker, same yaw; frontal-execution victim starts 1.04m forward, rotated 180°. Those offsets are embedded in the victim root. Align both actor scene origins and do not add them a second time. Synchronization, opponent-size adaptation, weapons, collision suppression and interruptions are untested.

## Validation — separate scopes

**Structural / mathematical:** Main benchmark FBX and GLB exports were reimported into Blender 4.2.9. Clip names/counts, skeleton/skin presence, finite vertices and normalized weights pass. Both formats of the 46-player bank reimport with expected names, moving poses, root endpoints and loop joint-position seams. All four skeletal LOD FBXs reimport. JSON reports contain exact checks and scope. A malformed dragon FBX was detected and regenerated before delivery.

- Siege_Sentinel: maximum sampled stance-anchor drift 0.162 cm.
- Cinder_Crown: maximum sampled stance-anchor drift 1.734 cm.

These are selected stance endpoint measurements on reimported GLBs; they do not certify full sole contact, every-frame slip, mesh intersection, or slopes. All 48 benchmark clips pass root-endpoint and applicable loop joint-position checks. Passing these checks does not establish realistic animation quality.

**Visual:** Front, side, back, three-quarter and close-ups use the actual imported delivered GLBs in neutral lighting. Motion videos also render those imports, including a two-mannequin paired preview. Selected frames were reviewed. Dragon face/body detail remains simplified, wings may intersect in some poses, Sentinel shapes remain stylized and player get-up/finishers need more natural support/contact. Unpreviewed clips have mathematical checks rather than exhaustive human visual review.

**Engine:** Not performed. There was no destination engine/project import, mobile build, runtime combat test, GPU budget test or terrain/contact evaluation. Blender reimport must not be reported as engine testing.

## Gameplay work still required

Stamina and regeneration; lock-on targeting/camera; dodge/parry invulnerability/cancel rules; hurtboxes and swept weapon detection; projectile spawning/ammo/reload logic; weapon switching/attachment; root-motion blending/controller; paired synchronization; water movement/buoyancy; AI/navigation/boss phases; slope foot placement/physics recovery; effect and sound playback. V3 sounds/effects are retained in the repaired baseline, not newly polished in this benchmark package.

## Editable source / rebuilding

Open either benchmark `.blend` for the baked asset; `_Authoring.blend` preserves procedural materials. Neither is a manually sculpted high-poly/quad-retopology production source. UVs are a smart-projected atlas and need artist cleanup. `source/v3_baselines` retains the original benchmark rest rigs used as inputs; `source/Player_Reference.fbx` is the repository's existing Y Bot reference. `source/*.py` contains modelling, motion, baking, export and verification scripts.

From this extracted folder, with Blender 4.2.9 available:

```bash
blender -b -t 2 --python source/export_benchmarks.py -- Cinder_Crown
blender -b -t 2 --python source/export_benchmarks.py -- Siege_Sentinel
blender -b -t 2 --python source/player_moves.py
blender -b -t 2 --python source/finalize_sources.py
blender -b -t 2 --python source/reimport_benchmarks.py
blender -b -t 2 --python source/validate_lods.py
blender -b -t 2 --python source/integration_metadata.py
```

The repository audit source additionally needs its five listed audit FBXs downloaded into `audit_inputs/`; these original animation files are not bundled again. Preview scripts recreate neutral renders and sample frames from the exported GLBs. Existing Mixamo reference geometry is credited to the user's repository; this package does not claim that geometry is an original Nocturne design or assign it a new license.

## Rollout status

The requested realism gate has not been achieved. The remaining 28 assets were not relabeled as V4 or changed cosmetically to imply the pack is finished. They remain available in the intact repaired V3 archive. A full high-quality V4 requires production sculpting/material/animation work beyond this benchmark iteration, then the same asset-specific work and engine validation across the roster.
