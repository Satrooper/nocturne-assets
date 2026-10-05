import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1]
m=json.loads((P/'player_animation/animation_manifest.json').read_text());results=[]
for ext,filename in [('fbx','Player_Moves_AnimationOnly.fbx'),('glb','Player_Moves_With_Existing_Mannequin.glb')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
 bpy.ops.import_scene.fbx(filepath=str(P/'player_animation'/filename)) if ext=='fbx' else bpy.ops.import_scene.gltf(filepath=str(P/'player_animation'/filename))
 rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];rig=rigs[0];actions=list(bpy.data.actions)
 for track in rig.animation_data.nla_tracks:track.mute=True
 names={a.name.split('|')[-1].removesuffix('_'+rig.name) for a in actions};reviews=[]
 for c in m['clips']:
  a=next(a for a in actions if a.name.split('|')[-1].removesuffix('_'+rig.name)==c['name']);rig.animation_data.action=a;first,last=a.frame_range;poses=[]
  for f in [first,first+(last-first)*.37,last]:
   bpy.context.scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();poses.append({p.name:rig.matrix_world@p.head for p in rig.pose.bones})
  delta=poses[-1]['NocturneRoot']-poses[0]['NocturneRoot'];root_error=(delta-__import__('mathutils').Vector(c['root_displacement_m'])).length
  loop_error=max(((poses[0][n]-poses[0]['NocturneRoot'])-(poses[-1][n]-poses[-1]['NocturneRoot'])).length for n in poses[0]) if c['loop'] else None
  moving=max((pose[n]-poses[0][n]).length for pose in poses[1:] for n in poses[0])>.0001
  reviews.append({'clip':c['name'],'root_delta_error_m':root_error,'loop_joint_position_error_m':loop_error,'moving':moving,'root_delta_passed':root_error<.015,'loop_passed':loop_error is None or loop_error<.01})
 skinned=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(mod.type=='ARMATURE' for mod in o.modifiers)]
 r={'format':ext,'rigs':len(rigs),'skinned_meshes':len(skinned),'clips':len(actions),'names_match':names=={c['name'] for c in m['clips']},'all_root_delta_passed':all(c['root_delta_passed'] for c in reviews),'all_loop_passed':all(c['loop_passed'] for c in reviews),'all_moving':all(c['moving'] for c in reviews),'clips_review':reviews,'engine_tested':False};results.append(r);print('PLAYER_REIMPORT',ext,r['names_match'],r['all_root_delta_passed'],r['all_loop_passed'],r['all_moving'],flush=True)
(P/'player_validation.json').write_text(json.dumps(results,indent=2))
paths=['animations/Pistol_Handgun Locomotion Pack/pistol idle.fbx','animations/Extras/Reload.fbx','animations/Extras/Reload 2.fbx','animations/Extras/Reload 3.fbx','animations/Extras/Standing Up.fbx'];audit=[]
for i,path in enumerate(paths):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(P/'audit_inputs'/(str(i)+'.fbx')));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');scene=bpy.context.scene
 for track in rig.animation_data.nla_tracks:track.mute=True
 for a in bpy.data.actions:
  rig.animation_data.action=a;first,last=a.frame_range;sample=[]
  bones=[p.name for p in rig.pose.bones if any(w in p.name for w in ['RightHand','LeftHand','Hips']) and not any(w in p.name for w in ['Index','Thumb','Pinky','Middle','Ring'])]
  for j in range(21):
   f=first+(last-first)*j/20;scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();sample.append({n:list(rig.matrix_world@rig.pose.bones[n].head) for n in bones})
  ranges={n:[max(s[n][axis] for s in sample)-min(s[n][axis] for s in sample) for axis in range(3)] for n in bones}
  audit.append({'repository_path':path,'imported_action':a.name,'fps':scene.render.fps,'duration_s':(last-first)/scene.render.fps,'sampled_world_axis_ranges_m':ranges,'samples':sample,'review_scope':'Imported actual FBX and sampled hips/hands; no engine, weapon-prop or full visual validation. Generic reloads are present, so a missing reload cannot be inferred just from filenames.'})
(P/'repository_motion_audit.json').write_text(json.dumps({'checked_commit':'f2305cd7bb1021d4e8bb26e557e2ad86567b1e33','actual_files_sampled':5,'audits':audit},indent=2));print('REPOSITORY_ACTUAL_MOTION_AUDIT',len(audit),flush=True)
