from pathlib import Path
import json,os,shutil
P=Path('Nocturne_V4_Visual_Revision');old=json.loads((P/'asset_manifest.json').read_text());reimport=json.loads((P/'audit/Export_Reimport_Validation.json').read_text());motion=json.loads((P/'audit/Clip_Motion_Audit.json').read_text());source=json.loads((P/'audit/Editable_Source_Texture_Checks.json').read_text());items=[]
for row in old['characters']:
 name=row['asset'];folder=P/row['category']/name;meta=json.loads((folder/'asset.json').read_text());tests=[x for x in reimport if x['file'].startswith(str(folder.relative_to(P))+'/')];mc=next(x for x in motion if x['asset']==name);preview=P/'previews/roster'/name
 row.update(status='partially_revised_target_unfinished',files=[str(f.relative_to(P)) for f in sorted(folder.glob('*')) if f.is_file() and f.suffix in ['.blend','.fbx','.glb','.json'] and not f.name.endswith('_fresh.fbx')],changes=meta['visual_changes'],validation={'structural_reimport_passed':all(x['structural_passed'] for x in tests),'export_files_checked':len(tests),'neutral_views_rendered':10,'motion_preview_action':mc['preview_action'],'all_frame_clipping_approved':False,'cinematic_visual_target_met':False,'engine_tested':False,'iphone_tested':False},remaining=['Production sculpting and anatomy/mechanical design refinement; procedural forms remain visible','Manual topology/deformation approval, local texture detailing and cinematic visual approval','Clip-by-clip choreography, foot sliding, clipping, weight transfer, paired alignment and contact approval'])
 if name=='Cinder_Crown':row['status']='retained_previous_v4_visual_revision_rejected';row['remaining'].insert(0,'New orbital/face revision regressed visual quality; previous V4 default retained. Experimental files included separately.');row['validation']['motion_preview_source']='dragons/Cinder_Crown/Cinder_Crown_Experimental.glb'
 if name=='Neon_Wisp':row['remaining'].insert(0,'First pass mainly rebakes material/UVs; substantial underlying-form redesign remains required');row['status']='retained_form_material_revised_target_unfinished'
 items.append(row)
old['characters']=items;old['scope_complete']=False;old['sounds']=json.loads((P/'audio/audio_manifest.json').read_text());old['effects']=json.loads((P/'effects/effects_manifest.json').read_text());old['texture_packaging']={'relative_paths':True,'resolution':'Existing textures preserved; creature revision atlases 1024 square. No resolution-only quality claim.'}
old['quality_statement']='Full collection included; incomplete cinematic upgrade. Twenty-eight creature defaults have procedural geometry revisions; Cinder retains its stronger prior V4 face and includes the rejected iteration separately; Neon Wisp mainly retains its form. Motion normalization and synthesized audio/effect revisions do not establish production approval.'
requirements=[{'requirement':k,'status':s,'remaining':r} for k,s,r in [
 ('All 30 creatures','partial','Cinematic sculpting, anatomy, mechanical forms, texture and deformation approval; Wisp underlying-form redesign'),
 ('Player firearm handling','partial','18 saved body/weapon clips retained. Finger/magazine/trigger contacts and production motion review incomplete'),
 ('Melee combos, directional dodges, parry/riposte, paired finishers, reactions, knockdown/get-up, swimming','unfinished','Existing 46-clip procedural bank retained; full coverage/choreography and attacker-victim alignment not approved'),
 ('Creature locomotion/attacks/flight/swimming','partial','Existing choreography retained; sampled playback audit and motion previews supplied. Root-return warnings, contact drift and loop seams require clip-specific correction'),
 ('Weapons','retained_prototype','Three existing weapon models/mechanism clips preserved; production artwork and handling alignment unfinished'),
 ('Audio','partial','70 revised synthesized mono 48k WAVs. No recorded samples. Listening, realistic creature vocals/foley and engine mix approval unfinished'),
 ('Effects','partial','12 redesigned procedural transparent atlases and previews. Particle/volumetric/shader engine integration unfinished'),
 ('Exports and sources','structurally_validated','Reimport tests are structural; full animation deformation and visual approval unfinished'),
 ('Engine/iPhone','blocked','Destination game project, suitable engine runtime and connected device not supplied'),
 ('Cinematic realism','unfinished','Procedural mesh construction and synthesized motion/sound have not achieved the requested film/AAA standard; manual production art and motion refinement remain necessary')]]
check={'scope_complete':False,'character_count':30,'characters':items,'requirements':requirements,'player':old['player'],'weapons':old['weapons'],'sounds':old['sounds'],'effects':old['effects'],'next_task':'Review All30_Before_After.jpg; production redesign of weak silhouettes/faces including Wisp; then clip-specific contact/choreography corrections against Clip_Motion_Audit.json. Preserve this checkpoint.','exact_blockers':['No destination game project/runtime/device for integration or iPhone measurements.'],'quality_statement':old['quality_statement']}
for f,d in [(P/'asset_manifest.json',old),(P/'audit/Completion_Checklist.json',check)]:
 with f.open('w') as h:json.dump(d,h,indent=2);h.flush();os.fsync(h.fileno())
text='''# Nocturne V4 full-collection revision — unfinished quality target

This archive consolidates all 30 creatures, prior V4 player handling, three weapons, editable sources, textures, 70 synthesized sounds and 12 procedural effects. It is a checkpoint of actual saved work, not a completed cinematic/AAA pack.

28 creature defaults received procedural underlying geometry revisions. Cinder Crown retains its stronger saved V4 model; its attempted anatomical revision is supplied as Experimental and is not counted as an approved upgrade. Neon Wisp chiefly retains its previous form with rebaked material/UV work. No creature is claimed to have passed cinematic approval. Robot construction is still visibly procedural; organic anatomy, skulls, eyes, scales, wing attachments and humanoid faces require production refinement.

Existing animation choreography is retained. Mixed Euler/quaternion channels were normalized. Clip_Motion_Audit.json contains measured root excursion, net displacement, sampled seam and low-height foot drift. Low-height intervals are heuristics, not validated contact or hit windows. Potential root returns are flagged, not silently fixed. Gameplay must implement stamina, damage/hit detection, invulnerability, lock-on, projectiles and boss phases. Paired alignment and all-frame clipping are unfinished.

18 saved player firearm-handling clips animate the body and weapon props. The separate 46-clip body bank is retained; full melee/dodge/parry/paired-finisher/swimming approval remains unfinished. Three weapon prototypes are retained.

All 70 audio files were revised with original deterministic synthesized layers and DSP; none is a recorded sample. Listening and production foley/vocal realism remain unfinished. All 12 effect atlases were redesigned with effect-specific propagation and decay. They require particle/billboard materials and engine playback. No external franchise designs or media are included in this revision.

Previews/roster contains matching neutral before/after views and a representative motion preview rendered from each delivered GLB. Before is the saved previous V4 consolidated version. Cinder's After views and motion GIF show the delivered Experimental files, while its default model retains Before. Neutral comparisons use matching camera/light parameters and a ground plane at each model’s rest ground height. These previews are evidence of appearance, not cinematic approval.

Structural reimport, source texture checks and archive CRC/extraction checks are separate from visual approval. No destination-engine or iPhone tests were performed. The destination project/runtime/device were not available. See audit/Completion_Checklist.json for every character and unfinished requirement.
'''
(P/'README.md').write_text(text);Path('Nocturne_V4_Revision_Report.md').write_text(text)
# Remove stale alternative exports rather than allowing users to select an old version accidentally.
for f in P.glob('*/*/*_fresh.fbx'):f.unlink()
valid=P/'audit/Export_Reimport_Validation.json';valid.write_text(json.dumps([r for r in reimport if (P/r['file']).is_file()],indent=2))
print('INVENTORY_UPDATED',len(items),'SCOPE_COMPLETE_FALSE',flush=True)
