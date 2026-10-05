import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];folder=P/'bosses/Siege_Sentinel';bpy.ops.wm.open_mainfile(filepath=str(folder/'Siege_Sentinel.blend'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=True
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
baseline=P.parent/'restored/nocturne-v4-batch02/bosses/Siege_Sentinel/Siege_Sentinel.blend'
with bpy.data.libraries.load(str(baseline),link=False) as (fr,to):to.actions=list(fr.actions)
names=['hind'+s+suffix for s in ['L','R'] for suffix in ['', '_shin','_foot']]
points={}
for bn in ['hindL_foot','hindR_foot']:
 g=mesh.vertex_groups[bn].index;points[bn]=[v.co.copy() for v in mesh.data.vertices if any(x.group==g and x.weight>.95 for x in v.groups)]
rest={n:rig.data.bones[n].matrix_local.copy() for n in names};lengths={n:rig.data.bones[n].length for n in names};polished=[]
def setbone(n,p,q):
 pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.matrix=Matrix.Translation(p)@q.to_matrix().to_4x4();bpy.context.view_layer.update()
for action in list(bpy.data.actions):
 if action.name.startswith(('Death','Ground_Slam')):continue
 rig.animation_data.action=action;first,last=map(int,action.frame_range);poses=[]
 for frame in range(first,last+1):
  for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();data={};rootyaw=rig.pose.bones['root'].matrix.to_quaternion().to_euler('XYZ').z
  from mathutils import Quaternion
  yaw=Quaternion((0,0,1),rootyaw)
  for s in ['L','R']:
   n='hind'+s;hip=rig.pose.bones[n].head.copy();ankle=rig.pose.bones[n+'_foot'].head.copy();skin=rig.pose.bones[n+'_foot'].matrix@rest[n+'_foot'].inverted();sole_z=min((skin@v).z for v in points[n+'_foot']);ankle.z=.27+max(0,sole_z);l1=lengths[n];l2=lengths[n+'_shin'];delta=ankle-hip;d=delta.length;axis=delta.normalized();d=min(l1+l2-.0001,max(abs(l1-l2)+.0001,d));ankle=hip+axis*d
   pole=Vector((0,-1,0));bend=(pole-axis*axis.dot(pole)).normalized();along=(l1*l1-l2*l2+d*d)/(2*d);height=math.sqrt(max(0,l1*l1-along*along));knee=hip+axis*along+bend*height
   for bn,a,b in [(n,hip,knee),(n+'_shin',knee,ankle)]:
    rq=rest[bn].to_quaternion();rv=rq@Vector((0,1,0));q=rv.rotation_difference((b-a).normalized())@rq;setbone(bn,a,q)
   setbone(n+'_foot',ankle,yaw@rest[n+'_foot'].to_quaternion())
  for n in names:
   pb=rig.pose.bones[n];data[n]=(pb.location.copy(),pb.rotation_quaternion.copy(),pb.scale.copy())
  poses.append((frame,data))
 # Replace leg channels only; retain torso, arms, root trajectory and clip duration.
 for fc in list(action.fcurves):
  if any(fc.data_path.startswith('pose.bones["'+n+'"]') for n in names):action.fcurves.remove(fc)
 prev={}
 for frame,data in poses:
  for n,(loc,q,scale) in data.items():
   if n in prev and prev[n].dot(q)<0:q.negate()
   prev[n]=q.copy();pb=rig.pose.bones[n];pb.location=loc;pb.rotation_quaternion=q;pb.scale=scale
   for prop in ['location','rotation_quaternion','scale']:pb.keyframe_insert(data_path=prop,frame=frame,group=n)
 for fc in action.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
 polished.append(action.name)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
bpy.context.scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Siege_Sentinel.blend'))
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(folder/'Siege_Sentinel.fbx'),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
bpy.ops.export_scene.gltf(filepath=str(folder/'Siege_Sentinel.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS')
meta=json.loads((folder/'asset.json').read_text());meta['contact_polish']={'clips':polished,'method':'Baked two-bone leg solve and level foot orientation; retained XY trajectory and lifted ankle below ground.','unfinished':['Death_RootMotion','Ground_Slam'],'validation':'See delivered geometry samples; do not infer approved stance/hit windows from inherited metadata.'};meta['inherited_contact_metadata_status']='Superseded by Foot_Geometry_Motion_Check; original generic stance labels require reauthoring.';(folder/'asset.json').write_text(json.dumps(meta,indent=2));print('CONTACT_POLISH_COMPLETE',len(polished))
