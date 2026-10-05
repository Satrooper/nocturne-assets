# Nocturne V4 — Batch 02 (incremental prototypes)

This is an additive batch for the repaired V3 collection and the later V4 benchmark iteration. **The full collection and requested realistic visual target are unfinished.** Keep both earlier packs. This batch is not a replacement for all 30 creatures or the 656-clip bank.

## Delivered changes

- **Siege Sentinel:** head/chest geometry revision, continuous sensor band, sloped helmet profile, split pectoral carapace, neck linkage, scapular mounts, radiator and replacement shoulder recoil shrouds. Original rest skeleton and 21 benchmark clips retained. Existing limbs remain visibly boxy. New automatic UV atlas and four 2048px baked PBR maps; editable authoring materials retained. No claim of sculpted or manually retopologized AAA anatomy.
- **Vesper Pistol / Bastion Rifle / Gravesong Sword:** original authored weapon geometry, rigs and attachment anchors, FBX and GLB, editable Blender authoring and game scenes, four baked 1024px maps each and two decimated FBX LODs each. Firearms have separate slide/bolt, magazine and trigger bones. Four weapon-mechanism clips show firing cycles and magazine service; these are **not player animations**. They do not complete natural hand handling, two-hand rifle aiming or holster choreography.
- **Four WAV files:** deterministic synthetic close-range pistol/rifle impulses and mechanical service prototypes, 48kHz mono 16-bit. They are not recordings. Audio manifest includes cue times and provenance; listening and mix approval remain unfinished.
- **Collection audit:** status records for every creature, baseline texture, sound and effect; actual source-motion sampling of all 656 V3 clips; explicit remaining player coverage. All baseline audio/effects are retained, not claimed upgraded.
- **Previews:** matching neutral front/side/back/close-up Sentinel comparisons from imported GLBs; neutral weapon views, an additional cinematic Sentinel view, and actual imported-model Sentinel walk and rifle mechanism previews. The retained Sentinel walk has not been polished in this batch.

## Scope of validation

`audit/Export_Reimport_Validation.json` reports each FBX/GLB/LOD reimport, finite geometry, normalized skin weights, action coverage, texture availability and sampled joint motion. LODs intentionally contain no animation. FBX embeds maps; GLB embeds maps. Editable game scenes use relative map paths. Authoring scenes pack image dependencies.

Structural validation is distinct from visual review. Renders exposed a disconnected neck section, which was corrected before delivery. The revised helmet/chest and weapon silhouettes were reviewed, but the Sentinel retains simple limb shapes and inconsistent material detail. This is not an approved realism benchmark. Joint-motion sampling is not a full vertex collision, sole-contact, grip or combat validation.

**Engine testing: not performed. iPhone performance: not measured.** No destination-engine project or running device test was supplied.

## Motion audit findings

All 656 V3 source actions were sampled at 17 normalized times using evaluated world-space rig joints. Sunken Leviathan's Flight_Takeoff / Flight_Hover / Flight_Glide / Flight_Landing share sampled joint poses; Razorfin's Swim_Turn / Swim_Surface do too. These groups do not establish distinct useful choreography. 143 root-return candidates were flagged. Some are intentional; none are automatically relabelled as confirmed bugs. Declared loops passed sampled endpoint joint continuity, which does not prove seamless mesh deformation or ground contact.

The prior Cinder Crown/Sentinel/player revisions are separately inventoried. This batch preserves Sentinel's 21 existing actions, adds four **mechanism-only** clips and does not count them as new player coverage. Clip-specific stance/timing metadata for retained Sentinel clips comes from the preceding benchmark pack and remains authoring metadata. Attack cues have not become validated hit windows.

## Integration and compatibility

Authoring convention: metres, Z up. Firearm muzzle / sword blade extends along negative Y. Weapon socket positions in `asset.json` are weapon-local rest positions. Bone names are embedded in exports. GLB uses its standard Y-up export transform; FBX is exported Y-up / -Z-forward. Inspect imported orientation in the destination engine.

Calibrate a weapon-to-hand offset for each character and animation; identity parenting is **not** validated. Sword blade_base / blade_tip are trace-anchor candidates, not a damage implementation. Rifle support anchor is for a future two-hand grip solve. Mechanism-only clips have no player-hand contact. Spawn a detachable magazine object in the engine if a physical drop is required. Do not mistake the animated magazine bone for that gameplay behavior.

Damage, stamina, invulnerability, lock-on, projectiles, ammunition, weapon switching state, hand IK, paired actor alignment, boss phases, AI, audio spatialization and particle playback still require engine work. Paired finishers and root extraction requirements remain in the previous benchmark metadata; none have been newly contact-validated here.

## Remaining collection work

28 original V3 creatures are marked unfinished. Cinder Crown's preceding benchmark revision is retained with its realism target unfinished. Sentinel is marked upgraded **only for the partial geometry work described above**. Every baseline audio/effect/texture is retained with a reason and an unfinished quality target. `audit/Collection_Status.json` is the per-asset record; `audit/Player_Coverage.json` records animation gaps.

Manual-quality sculpting, coherent quad retopology, locally authored creature textures, detailed faces/clothing, natural combat choreography and full deformation review remain to be done. Existing automatic mesh reconstruction/decimation and UV projection do not satisfy those requirements by themselves. The available workflow authors meshes, rigs, bakes and motion through Blender scripting; it does not include a motion-capture performance, recorded audio library or destination-engine test session. It has not produced the requested AAA finish, and that limitation is reported rather than hidden by a larger clip count.

## Editable sources and reproducibility

Use Blender 4.2.9. The `.blend` files are independently editable; authoring scenes preserve material graphs, game scenes preserve rigs/actions and baked maps. Run build_weapons.py, refine_mechanism_motion.py and finalize_exports.py in that order to regenerate the weapon exports. Sentinel refinement expects the previously delivered `nocturne-v4` benchmark folder beside this folder. The V3 audit expects repaired V3 extracted as `nocturne-dark-fantasy-v3` beside it. Source motion audit uses evaluated rig joints, not clip names alone. Audio regeneration requires Python, NumPy and SciPy. Previews require Blender; encoding requires FFmpeg and Pillow.

All newly authored geometry, material graphs and DSP synthesis in this batch are original. No franchise meshes, textures or sound samples were used. Preserve the preceding pack's attribution for its existing mannequin and any inherited materials. The comparison's Before column is the **preceding V4 benchmark**, not the older V3 creature. No independent before/after comparison is claimed for weapons that had no model in the preceding player bank.

## Packaging

The outside packaging report and SHA-256 file certify ZIP entry CRC checks, ordinary extraction, every extracted file's hash and `unzip -tq`. The archive contains a per-file SHA-256 manifest. Raw frame caches, backup scenes, diagnostic logs and generated FBX texture-extraction folders are omitted; delivered game and authoring files, maps, WAVs, previews, source and metadata are included.

## Creature-by-creature status

These weaknesses are source-construction findings except where benchmark renders were reviewed.

| Asset | Status in this batch | Remaining model work |
| --- | --- | --- |
| Abyss_Maw | Unfinished; V3 baseline | Jaw/gill/fin structure, scale transitions and swimming propulsion need anatomical work. |
| Cathedral_Bellwarden | Unfinished; V3 baseline | Face, fitted armour, cloth folds, articulated hands and equipment attachment need dedicated modelling and deformation review. |
| Crypt_Arachnarch | Unfinished; V3 baseline | Cephalothorax anatomy, carapace, mouthparts and joint/leg contact need review; generic shared movement is insufficient. |
| Furnace_Titan | Unfinished; V3 baseline | Generic forms need purposeful mechanical construction, actuators, joints and credible hands/feet. |
| Horned_Regent | Unfinished; V3 baseline | Skull, facial planes, muscle/joint transitions, fingers and locomotion personality require dedicated work. |
| Hundredleg | Unfinished; V3 baseline | Segment transitions, mouthparts and contact-consistent coordinated leg motion need inspection. |
| Mirror_Colossus | Unfinished; V3 baseline | Repeated geometric structure and generic limb design need an original coherent construction language. |
| Neon_Reaper | Unfinished; V3 baseline | Cloth silhouette, face and fitted equipment need modelling and simulation or authored deformation. |
| Root_Matriarch | Unfinished; V3 baseline | Root/limb continuity, bark transitions and creature-specific mass transfer require sculpt and motion review. |
| Siege_Sentinel | Partial geometry revision; target unfinished | Machine construction and material separation need refinement; armour and joints remain visibly simplified. |
| Cinder_Crown | Prior benchmark retained; target unfinished | Primitive-derived skull/body masses, generic limb articulation and angular scale overlays need anatomical rebuilding, wing attachment and facial review. |
| Crimson_Vesper | Unfinished; V3 baseline | Wing digit/membrane structure and hindlimb load-bearing anatomy need rebuild; shared flight primitives need visual inspection. |
| Dune_Glasswing | Unfinished; V3 baseline | Wing digit/membrane structure and hindlimb load-bearing anatomy need rebuild; shared flight primitives need visual inspection. |
| Frost_Antler | Unfinished; V3 baseline | Primitive-derived skull/body masses, generic limb articulation and angular scale overlays need anatomical rebuilding, wing attachment and facial review. |
| Iron_Seraph | Unfinished; V3 baseline | Primitive-derived skull/body masses, generic limb articulation and angular scale overlays need anatomical rebuilding, wing attachment and facial review. |
| Moonveil | Unfinished; V3 baseline | Primitive-derived skull/body masses, generic limb articulation and angular scale overlays need anatomical rebuilding, wing attachment and facial review. |
| Obsidian_Bastion | Unfinished; V3 baseline | Primitive-derived skull/body masses, generic limb articulation and angular scale overlays need anatomical rebuilding, wing attachment and facial review. |
| Storm_Wyvern | Unfinished; V3 baseline | Wing digit/membrane structure and hindlimb load-bearing anatomy need rebuild; shared flight primitives need visual inspection. |
| Sunken_Leviathan | Unfinished; V3 baseline | Axial body undulation, fin transitions, head/oral detail and wet surface response need anatomy-specific authoring. |
| Thornback | Unfinished; V3 baseline | Primitive-derived skull/body masses, generic limb articulation and angular scale overlays need anatomical rebuilding, wing attachment and facial review. |
| Bamboo_Mantis | Unfinished; V3 baseline | Functional limb hinges, foreleg attack arc and chitin transitions need biological reference-driven work. |
| Cinder_Hound | Unfinished; V3 baseline | Source derives the body from a wingless dragon; canine scapulae, digitigrade limbs, skull and gait need rebuilding. |
| Crimson_Imp | Unfinished; V3 baseline | Skull, facial planes, muscle/joint transitions, fingers and locomotion personality require dedicated work. |
| Crypt_Skitter | Unfinished; V3 baseline | Cephalothorax anatomy, carapace, mouthparts and joint/leg contact need review; generic shared movement is insufficient. |
| Moon_Bat | Unfinished; V3 baseline | Wing fingers, membrane attachment, head detail and flight articulation need anatomical authoring. |
| Neon_Wisp | Unfinished; V3 baseline | Identity relies on simple luminous shapes; distinctive silhouette and authored effects remain required. |
| Razorfin | Unfinished; V3 baseline | Jaw/gill/fin structure, scale transitions and swimming propulsion need anatomical work. |
| Scrapling | Unfinished; V3 baseline | Generic forms need purposeful mechanical construction, actuators, joints and credible hands/feet. |
| Shard_Crab | Unfinished; V3 baseline | Chela mechanics, mouthparts and lateral gait/contact need anatomy-specific work. |
| Sporeling | Unfinished; V3 baseline | Root/limb continuity, bark transitions and creature-specific mass transfer require sculpt and motion review. |

Baseline sounds: 66 retained, synthesized; listening/design revision unfinished. Effects: 12 retained; engine playback/design revision unfinished. Baseline textures: 51 retained; local-detail/UV quality work unfinished. These records are itemized in Collection_Status.json.
