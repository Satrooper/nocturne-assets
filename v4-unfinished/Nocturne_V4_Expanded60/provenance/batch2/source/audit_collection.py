import json,wave,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];BASE=P.parent/'nocturne-dark-fantasy-v3';latest=P.parent/'nocturne-v4'
weakness={
'dragon':'Primitive-derived skull/body masses, generic limb articulation and angular scale overlays need anatomical rebuilding, wing attachment and facial review.',
'wyvern':'Wing digit/membrane structure and hindlimb load-bearing anatomy need rebuild; shared flight primitives need visual inspection.',
'serpent':'Axial body undulation, fin transitions, head/oral detail and wet surface response need anatomy-specific authoring.',
'knight':'Face, fitted armour, cloth folds, articulated hands and equipment attachment need dedicated modelling and deformation review.',
'construct':'Generic forms need purposeful mechanical construction, actuators, joints and credible hands/feet.',
'ent':'Root/limb continuity, bark transitions and creature-specific mass transfer require sculpt and motion review.',
'spider':'Cephalothorax anatomy, carapace, mouthparts and joint/leg contact need review; generic shared movement is insufficient.',
'demon':'Skull, facial planes, muscle/joint transitions, fingers and locomotion personality require dedicated work.',
'mech':'Machine construction and material separation need refinement; armour and joints remain visibly simplified.',
'fish':'Jaw/gill/fin structure, scale transitions and swimming propulsion need anatomical work.',
'wraith':'Cloth silhouette, face and fitted equipment need modelling and simulation or authored deformation.',
'crystal':'Repeated geometric structure and generic limb design need an original coherent construction language.',
'centipede':'Segment transitions, mouthparts and contact-consistent coordinated leg motion need inspection.',
'hound':'Source derives the body from a wingless dragon; canine scapulae, digitigrade limbs, skull and gait need rebuilding.',
'mantis':'Functional limb hinges, foreleg attack arc and chitin transitions need biological reference-driven work.',
'bat':'Wing fingers, membrane attachment, head detail and flight articulation need anatomical authoring.',
'crab':'Chela mechanics, mouthparts and lateral gait/contact need anatomy-specific work.',
'wisp':'Identity relies on simple luminous shapes; distinctive silhouette and authored effects remain required.'}
assets=[]
for a in json.loads((BASE/'asset_manifest.json').read_text()):
 status='unfinished';reason='V3 source retained as baseline; not upgraded in this batch.'
 if a['name']=='Cinder_Crown':reason='Prior benchmark revision retained; realism target unfinished; no further geometry or motion revision in batch02.'
 if a['name']=='Siege_Sentinel':status='upgraded_partial';reason='Batch02 replaces chest/head and shoulder weapon geometry. Limbs and existing 21 motion clips retained; whole-body quality target unfinished.'
 assets.append({'name':a['name'],'type':a['body_type'],'category':a['category'],'status':status,'reason':reason,'source_clip_count':len(a['clips']),'weaknesses':[weakness.get(a['body_type'],'Dedicated anatomy and visual inspection required.'),'Procedural material and automatic UV/decimation pipeline do not establish finished sculpt/retopology/texture quality.','Sampled motion audit is available; full mesh contact/clipping visual review remains unfinished.'],'visual_review':'Only benchmark preview assets and this batch inspected; other weaknesses are source-construction findings, not individual render approvals.'})
audio=[]
for entry in json.loads((BASE/'audio/audio_manifest.json').read_text()):
 p=BASE/'audio'/entry['file']
 with wave.open(str(p),'rb') as w:
  x=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float64)/32768;sr=w.getframerate();ch=w.getnchannels()
 audio.append({'file':entry['file'],'category':entry['category'],'status':'unfinished','reason':'Original synthesized audio retained pending auditory review and category-specific redesign; no recorded audio supplied.','source':entry['source'],'sample_rate':sr,'channels':ch,'duration_s':len(x)/sr/ch,'pcm_sha256':hashlib.sha256(x.tobytes()).hexdigest(),'peak_dbfs':float(20*np.log10(max(1e-12,np.abs(x).max()))),'rms_dbfs':float(20*np.log10(max(1e-12,np.sqrt(np.mean(x*x))))),'clipped_sample_count':int(np.sum(np.abs(x)>=32767/32768)),'near_silent_sample_fraction':float(np.mean(np.abs(x)<.0001)),'listened_to':False})
effects=[]
for e in json.loads((BASE/'effects/effects_manifest.json').read_text()):
 p=BASE/'effects'/e['file'];im=Image.open(p);im.load();alpha=np.array(im.getchannel('A'));effects.append({**e,'status':'unfinished','reason':'Baseline flipbook retained; no particle-system or engine playback validation.','dimensions':list(im.size),'alpha_nonzero_fraction':float(np.mean(alpha>0)),'structural_image_read_passed':True,'visual_review':False})
textures=[]
for p in sorted((BASE/'textures').glob('*.png')):
 with Image.open(p) as im:im.load();textures.append({'file':p.name,'size':list(im.size),'mode':im.mode,'structural_image_read_passed':True,'status':'unfinished','reason':'V3 procedural maps preserved as baseline; per-character local detail and UV quality remain unfinished.'})
(P/'audit/Collection_Status.json').write_text(json.dumps({'scope':'Entire collection; this delivery is incremental batch02, not finished V4','creatures':assets,'audio':audio,'effects':effects,'textures':textures,'rigs':'Prior rigs retained; batch02 Sentinel rest skeleton unchanged. Weapon rigs newly authored.','engine_tested':False,'iphone_performance_measured':False},indent=2))
(P/'audit/Audio_Structural_Audit.json').write_text(json.dumps(audio,indent=2));(P/'audit/Effects_Structural_Audit.json').write_text(json.dumps(effects,indent=2))
clips=[c for a in json.loads((P/'audit/V3_Actual_Motion_Audit.json').read_text()) for c in a['clips']];groups=[g for a in json.loads((P/'audit/V3_Actual_Motion_Audit.json').read_text()) for g in a['identical_sampled_joint_pose_groups']]
(P/'audit/Motion_Findings.json').write_text(json.dumps({'source_clips':len(clips),'sampled_clips':sum(c['status']=='sampled_actual_source_motion' for c in clips),'root_return_candidates':sum(c.get('root_returns_to_start_candidate',False) for c in clips),'identical_sampled_pose_groups':groups,'declared_loops_over_1cm_joint_endpoint_error':sum(c.get('declared_loop',False) and c.get('loop_endpoint_joint_error_m',0)>.01 for c in clips),'limitations':['17 samples per source action; rig-joint positions only.','Root-return candidates include intentional motion; they are triage findings, not confirmed bugs.','Pose signatures do not prove distinct choreography; similar procedural recipes can differ numerically.','No mesh intersections, sole-contact intervals or combat hit windows validated.']},indent=2))
requirements={
 'Pistol fire/reload':'Prior46 prototype bank available; new weapon mechanisms delivered, player hand/weapon alignment unfinished.',
 'Rifle aim/fire/reload':'New rifle mechanism only; player rifle choreography unfinished.',
 'Directional dodges':'Prior directional hop/dodge prototypes available; natural rolls/recovery unfinished.',
 'Weapon combos':'Prior sword light/heavy prototypes; charged/running/jumping and additional weapon sets unfinished.',
 'Starts/stops/turns':'V3 generic turns exist; character-specific transitions unfinished.',
 'Blocking/parry/guard break/riposte':'Prior parry/riposte prototype; block/guard break and full contact review unfinished.',
 'Paired finishers':'Prior backstab/frontal prototype pair alignment metadata; weapon contact, resizing and choreography unfinished.',
 'Weapon draw/switch/holster':'Prior switch prototype; new weapons require fitted grips and holster choreography.',
 'Reactions/knockdown/get-up/deaths':'Prior reactions and rigid get-up prototypes; natural floor contact and full deaths unfinished.',
 'Flight/swimming':'Prior prototypes and V3 motions; creature-specific propulsion/weight/contact review unfinished.'}
(P/'audit/Player_Coverage.json').write_text(json.dumps({'requirements':requirements,'validated_hit_windows':False,'engine_integration_required':['damage and hit detection','stamina','invulnerability windows','lock-on','projectiles','magazine spawning','weapon hand attachments and aim offsets','paired actor alignment/adaptation','boss phases and AI','effect playback and audio routing']},indent=2))
print('COLLECTION_AUDIT',len(assets),len(audio),len(effects),len(textures))
