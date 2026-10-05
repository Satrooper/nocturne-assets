import bpy,json,math,sys,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];rows=json.loads((P/'asset_manifest.json').read_text())['characters'];report=[]
for row in rows:
 name=row['asset'];path=P/row['category']/name/(name+'.glb');bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(path));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data_create()
 for tr in rig.animation_data.nla_tracks:tr.mute=True
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 for extra in list(bpy.context.scene.objects):
  if extra.type=='MESH' and extra not in meshes:bpy.data.objects.remove(extra,do_unlink=True)
 actions=list(bpy.data.actions);clips=[]
 for act in actions:
  for bone in rig.pose.bones:bone.rotation_mode='QUATERNION';bone.rotation_quaternion=(1,0,0,0);bone.location=(0,0,0);bone.scale=(1,1,1)
  rig.animation_data.action=act;first,last=act.frame_range;frames=[first+(last-first)*i/12 for i in range(13)];roots=[];feet={b.name:[] for b in rig.pose.bones if 'foot' in b.name or 'claw' in b.name};heads=[]
  for f in frames:
   bpy.context.scene.frame_set(int(f),subframe=f-int(f));root=rig.pose.bones.get('root') or rig.pose.bones[0];roots.append(rig.matrix_world@root.head);heads.append({b.name:rig.matrix_world@b.head for b in rig.pose.bones})
   for bn in feet:feet[bn].append(rig.matrix_world@rig.pose.bones[bn].tail)
  net=roots[-1]-roots[0];travel=sum((b-a).length for a,b in zip(roots,roots[1:]));exc=max((x-roots[0]).length for x in roots);seam=max((heads[-1][b]-heads[0][b]).length for b in heads[0]);relative_seam=max(((heads[-1][b]-roots[-1])-(heads[0][b]-roots[0])).length for b in heads[0]);horizontal_exc=max(Vector((x.x-roots[0].x,x.y-roots[0].y,0)).length for x in roots);horizontal_net=Vector((net.x,net.y,0)).length;body=max((p[b]-heads[0][b]).length for p in heads for b in p)
  item={'name':act.name,'frame_range':[first,last],'duration_seconds':float((last-first)/30),'fps':30,'root_motion_observed':'in_place_horizontal' if horizontal_exc<.005 else 'root_translation','root_net_displacement_m':list(net),'root_travel_m':travel,'root_max_excursion_m':exc,'root_max_horizontal_excursion_m':horizontal_exc,'max_root_relative_joint_seam_m':relative_seam,'potential_root_return':horizontal_exc>.08 and horizontal_net<horizontal_exc*.15,'max_joint_position_seam_m':seam,'sampled_joint_motion_m':body,'foot_tracks':{},'timing_contacts_status':'not validated; generic inherited cues are not approved damage windows','required_integration':['Engine damage windows and hit detection','Invulnerability/stamina/lock-on','Boss state and phase logic'],'quality_status':'sampled playback structural audit; clipping, contacts and choreography need visual approval'}
  for bn,ps in feet.items():
   low=min(p.z for p in ps);segments=[(i,a,b) for i,(a,b) in enumerate(zip(ps,ps[1:])) if max(a.z,b.z)<low+.035];item['foot_tracks'][bn]={'lowest_observed_world_z_m':low,'low_height_intervals_seconds':[[float((frames[i]-first)/30),float((frames[i+1]-first)/30)] for i,a,b in segments],'max_horizontal_shift_in_low_height_interval_m':max((Vector((b.x-a.x,b.y-a.y,0)).length for i,a,b in segments),default=0),'interpretation':'geometric heuristic; not validated contact markers'}
  clips.append(item)
 # Motion preview from delivered GLB, with actual deformed vertices defining camera bounds.
 act=next((a for a in actions if 'InPlace' in a.name and any(w in a.name for w in ['Walk','Swim','Fly'])),next((a for a in actions if any(w in a.name for w in ['Walk','Swim','Fly'])),actions[0]));rig.animation_data.action=act;sc=bpy.context.scene;sc.render.fps=30;sc.frame_set(int(act.frame_range[0]));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pts=[]
 for o in meshes:
  e=o.evaluated_get(dg);me=e.to_mesh();pts.extend([e.matrix_world@v.co for v in me.vertices]);e.to_mesh_clear()
 lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);c=(hi+lo)/2;extent=max(hi-lo);sc.render.engine='CYCLES';sc.cycles.samples=1;sc.cycles.use_denoising=True;sc.render.use_persistent_data=True;sc.render.resolution_x=256;sc.render.resolution_y=256;sc.world=bpy.data.worlds.new('Neutral_motion_world');sc.world.color=(.18,.18,.18)
 for delta,power in [((1,-1,2),160),((-1,-.4,1),90),((0,1,1),120)]:
  bpy.ops.object.light_add(type='AREA',location=c+Vector(delta)*extent);o=bpy.context.object;o.data.energy=power*extent**2;o.data.size=extent;o.rotation_euler=(c-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add(location=c+Vector((1,-1,.3)).normalized()*extent*3);cam=bpy.context.object;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=extent*1.25;sc.camera=cam;d=P/'previews/roster'/name/'frames_motion';d.mkdir(parents=True,exist_ok=True)
 for i in range(8):
  f=act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/7;sc.frame_set(int(f),subframe=f-int(f));sc.render.filepath=str(d/(str(i).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
 report.append({'asset':name,'source':str(path.relative_to(P)),'preview_action':act.name,'clips':clips,'engine_tested':False});print('MOTION_REVIEW',name,len(clips),flush=True)
 with (P/'audit/Clip_Motion_Audit.json').open('w') as f:json.dump(report,f,indent=2);f.flush();os.fsync(f.fileno())
