import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];out={'coordinate_conventions':{'authoring':'metres; Blender Z up, -Y forward; right-handed. Player anatomical left is +X.','glb':'glTF uses Y up; importer applies basis conversion. Resolve sockets by bone names rather than copying authoring XYZ into engine coordinates.','fbx':'Units and axis conversion must be verified in the destination importer; do not double-apply armature scale.'},'engine_tested':False,'assets':[]}
for folder in [P/'dragons/Cinder_Crown',P/'bosses/Siege_Sentinel',P/'player_animation']:
 name=folder.name;bpy.ops.wm.open_mainfile(filepath=str(folder/('Player_Moves.blend' if name=='player_animation' else name+'.blend')));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data.action=None
 for track in rig.animation_data.nla_tracks:track.mute=True
 anchors={}
 def anchor(label,bone,point=None):
  b=rig.data.bones[bone];local=b.matrix_local.inverted()@Vector(point) if point is not None else Vector((0,0,0));anchors[label]={'bone':bone,'offset_bone_local_authoring_units':list(local),'bone_rest_matrix_armature_local_row_major':[list(row) for row in b.matrix_local],'rest_point_armature_local':list(b.matrix_local@local),'status':'authored attachment; effect direction and collision still require engine review'}
 if name=='Cinder_Crown':
  anchor('mouth_and_breath','head',(0,-3.64,2.34*1.02));anchor('jaw_contact','jaw',(0,-3.37,2.13*1.02));anchor('claw_L','frontL_foot');anchor('claw_R','frontR_foot');anchor('tail_tip','tail5');anchor('body_origin','root')
 elif name=='Siege_Sentinel':
  for side,s in [('L',-1),('R',1)]:anchor('muzzle_'+side,'turret'+side+'_recoil',(s*.53,-.48,2.60));anchor('fist_'+side,'arm'+side+'_hand')
  anchor('ground_slam_reference','root')
 else:
  anchor('weapon_R','WeaponSocket_R');anchor('weapon_L','WeaponSocket_L');anchor('pelvis','mixamorig:Hips');anchor('root_motion','NocturneRoot')
 item={'name':name,'rig_object_scale':list(rig.scale),'anchors':anchors,'root_motion_bone':'NocturneRoot' if name=='player_animation' else 'root','root_extraction':'Use accumulated root transform; subtract the clip first-frame transform. Apply final displacement to actor once, then reset animation root at a state transition. A looping travel clip wraps its sampled root; accumulate cycle displacement rather than teleporting actor back.','root_rotation':'Cinder turns authored 45 degrees; Sentinel turns 90 degrees. Paired frontal victim begins rotated 180 degrees. Extract yaw as well as translation for turning clips.','bounds_and_collision':'Mesh bounds are art bounds. Collision capsules, hurtboxes and swept weapon hitboxes are not supplied or validated.'};out['assets'].append(item)
 if name!='player_animation':
  mf=folder/'asset.json';m=json.loads(mf.read_text());m['effect_anchors']=anchors
  for c in m['clips']:c['exported_duration_s']=(c['frames']-1)/30;c['timing_basis']='Events and contact samples are authored on the nominal clip clock; normalize by duration if importer resamples.'
  mf.write_text(json.dumps(m,indent=2))
 else:
  mf=folder/'animation_manifest.json';m=json.loads(mf.read_text());m['effect_anchors']=anchors
  for c in m['clips']:c['exported_duration_s']=(c['frames']-1)/30
  m['paired_alignment_contract']={'units':'metres in authoring coordinates','Backstab':{'attacker_start_translation':[0,0,0],'attacker_start_yaw_degrees':0,'victim_start_translation':[0,-.92,0],'victim_start_yaw_degrees':0},'Frontal_Execution':{'attacker_start_translation':[0,0,0],'attacker_start_yaw_degrees':0,'victim_start_translation':[0,-1.04,0],'victim_start_yaw_degrees':180},'clock':'Both roles start at frame 1 and last 73 frames at 30 fps. Align scene origins, play the named pair at the same normalized time, and disable independent locomotion during the pair. Victim alignment is already embedded in the animation root.','warning':'No synchronized weapon mesh, collision, camera, opponent-size adaptation or runtime interruption test. These pairs are prototypes.'};mf.write_text(json.dumps(m,indent=2))
out['gameplay_code_required']=['stamina costs and regeneration','target selection and lock-on camera','dodge/parry invulnerability and cancel rules','hurtboxes, swept hit detection, damage and stagger','projectile spawning, trajectories, ammo and reload state','weapon attachment and switching state','root-motion controller and blending','paired-animation synchronization and collision suppression','swimming movement, water level and buoyancy','boss phase selection, AI navigation and encounter logic','ground alignment, foot placement on slopes and physics recovery','sound/VFX playback bound to authored cues']
out['contact_and_timing_validation']='Per-clip authoring cues and ankle-anchor samples are included. Bone stance drift is measured on reimported benchmark GLBs. This does not validate sole geometry contacts, damage windows, invulnerability or effect direction in a game engine.'
(P/'integration_metadata.json').write_text(json.dumps(out,indent=2));print('INTEGRATION_METADATA_WRITTEN',flush=True)
