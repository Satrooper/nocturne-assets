import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];BASE=P.parent/'nocturne-dark-fantasy-v3';manifest=json.loads((BASE/'asset_manifest.json').read_text());out=[]
for asset in manifest:
 path=BASE/asset['category']/asset['name']/(asset['name']+'.blend');bpy.ops.wm.open_mainfile(filepath=str(path));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data_create()
 for t in rig.animation_data.nla_tracks:t.mute=True
 actions=list(bpy.data.actions);samples=[]
 for clip in asset['clips']:
  action=next((a for a in actions if a.name.split('|')[-1]==clip['name']),None)
  if action is None:samples.append({'clip':clip['name'],'status':'action_not_found'});continue
  rig.animation_data.action=action;first,last=action.frame_range;poses=[];roots=[];rootname='root' if 'root' in rig.pose.bones else rig.pose.bones[0].name
  for i in range(17):
   f=first+(last-first)*i/16;bpy.context.scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();root=rig.matrix_world@rig.pose.bones[rootname].head;roots.append(root.copy());poses.append([list((rig.matrix_world@b.head)-root) for b in rig.pose.bones])
  displacement=(roots[-1]-roots[0]).length;excursion=max((r-roots[0]).length for r in roots);movement=max(math.dist(poses[0][j],p[j]) for p in poses[1:] for j in range(len(p)));loop=max(math.dist(a,b) for a,b in zip(poses[0],poses[-1]));sig=hashlib.sha256(json.dumps([[[round(v,4) for v in b] for b in p] for p in poses]).encode()).hexdigest()
  samples.append({'clip':clip['name'],'status':'sampled_actual_source_motion','sample_count':17,'duration_s':(last-first)/bpy.context.scene.render.fps,'root_bone':rootname,'root_endpoint_delta_m':list(roots[-1]-roots[0]),'root_excursion_m':excursion,'root_path_length_m':sum((b-a).length for a,b in zip(roots,roots[1:])),'root_returns_to_start_candidate':excursion>.08 and displacement<.015,'max_root_relative_joint_movement_m':movement,'loop_endpoint_joint_error_m':loop,'declared_loop':clip['loop'],'declared_root_motion':clip['root_motion'],'pose_signature':sig})
 groups={}
 for c in samples:
  if 'pose_signature' in c:groups.setdefault(c['pose_signature'],[]).append(c['clip'])
 out.append({'asset':asset['name'],'clips':samples,'identical_sampled_joint_pose_groups':[v for v in groups.values() if len(v)>1]});(P/'audit'/'V3_Actual_Motion_Audit.json').write_text(json.dumps(out,indent=2));print('AUDITED',asset['name'],len(samples),flush=True)
# Current benchmark/player banks are additional revisions, not silently counted as V3 improvements.
new=[]
for p in [P.parent/'nocturne-v4/dragons/Cinder_Crown/Cinder_Crown.blend',P.parent/'nocturne-v4/bosses/Siege_Sentinel/Siege_Sentinel.blend',P.parent/'nocturne-v4/player_animation/Player_Moves.blend']:
 if p.exists():
  bpy.ops.wm.open_mainfile(filepath=str(p));new.append({'file':str(p.relative_to(P.parent)),'actions':[{'name':a.name,'frame_range':list(a.frame_range),'fcurves':len(a.fcurves)} for a in bpy.data.actions]})
(P/'audit/Latest_Revision_Action_Inventory.json').write_text(json.dumps(new,indent=2))
