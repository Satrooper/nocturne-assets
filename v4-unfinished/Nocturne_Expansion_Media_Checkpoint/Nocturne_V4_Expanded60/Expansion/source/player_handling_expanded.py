import bpy,json,math,os
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path('/workspace/scratch/c638d9b24e22/Nocturne_V4_Visual_Revision');folder=Path('/workspace/scratch/c638d9b24e22/Nocturne_Expansion_60/player_handling');folder.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'player_animation/Player_Moves.blend'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=True
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
bpy.context.view_layer.update();bodyrest={b.name:b.matrix_local.copy() for b in rig.data.bones};bodymeshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];wm=rig.matrix_world.copy();wi=wm.inverted();B=lambda n:rig.pose.bones['mixamorig:'+n]
OFF=Vector((0,-.022,-.15));QR=Matrix(((-1,0,0),(0,0,-1),(0,-1,0))).to_quaternion();QL=Matrix(((1,0,0),(0,0,1),(0,1,0))).to_quaternion();QLR=Matrix(((-1,0,0),(0,-1,0),(0,0,1))).to_quaternion()
# Use a right-handed palm frame (local finger axis points toward muzzle for rifle).
QL=Matrix(((1,0,0),(0,0,-1),(0,1,0))).to_quaternion()
weapons={};parts=list(bodymeshes);base=Vector((.4,.2,.8))
for key,name,scale in [('Pistol','Vesper_Pistol',1),('Rifle','Bastion_Rifle',.82)]:
 with bpy.data.libraries.load(str(P/'weapons'/name/(name+'.blend')),link=False) as (fr,to):to.objects=list(fr.objects)
 added=[o for o in to.objects if o]
 for o in added:bpy.context.collection.objects.link(o)
 wr=next(o for o in added if o.type=='ARMATURE');wo=next(o for o in added if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
 for v in wo.data.vertices:v.co=wi@(base+(wo.matrix_world@v.co)*scale)
 wo.matrix_world=wm;wo.name=name+'_Player_Fitted';source={b.name:b.matrix_local.copy() for b in wr.data.bones};prefix='W_'+key+'_'
 # Shorter fitted rifle support point lies within the player's actual limb reach.
 if key=='Rifle':source['support'].translation=Vector((0,-.215,.103))
 for g in wo.vertex_groups:g.name=prefix+g.name
 for mod in wo.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 wo.parent=rig;wo.matrix_world=wm
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for n,m in source.items():
  eb=rig.data.edit_bones.new(prefix+n);a=base+(wr.matrix_world@m.translation)*scale;b=(wr.matrix_world@wr.data.bones[n].tail_local)*scale+base;eb.head=wi@a;eb.tail=wi@b
  dm=wi@(Matrix.Translation(base)@Matrix.Diagonal((scale,scale,scale,1))@wr.matrix_world@m)
  for col in range(3):dm.col[col].xyz=dm.col[col].xyz.normalized()
  eb.matrix=dm
 for n,m in source.items():
  eb=rig.data.edit_bones[prefix+n];par=wr.data.bones[n].parent;eb.parent=rig.data.edit_bones[prefix+par.name] if par else rig.data.edit_bones['NocturneRoot']
 bpy.ops.object.mode_set(mode='OBJECT')
 for o in added:
  if o!=wo and o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
 weapons[key]={'name':name,'mesh':wo,'prefix':prefix,'source':source,'scale':scale};parts.append(wo)
 for im in bpy.data.images:
  if im.source=='FILE':
   path=P/'textures'/Path(im.filepath).name
   if path.exists():im.filepath=str(path);im.reload()
# Preserve embedded body textures and source licenses; mannequin art is unchanged.
restW={b.name:wm@b.matrix_local for b in rig.data.bones};feet={s:wm@rig.data.bones['mixamorig:'+s+'Foot'].head_local for s in ['Left','Right']}
def reset():
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
def worldbone(n,p,q):
 pb=rig.pose.bones[n];mat=wi@(Matrix.Translation(p)@q.to_matrix().to_4x4())
 for i in range(3):mat.col[i].xyz=mat.col[i].xyz.normalized()
 pb.matrix=mat;bpy.context.view_layer.update()
def solve(s,typ,target,handq=None):
 n1='mixamorig:'+s+('Arm' if typ=='arm' else 'UpLeg');n2='mixamorig:'+s+('ForeArm' if typ=='arm' else 'Leg');n3='mixamorig:'+s+('Hand' if typ=='arm' else 'Foot');a=wm@rig.pose.bones[n1].head;l1=rig.data.bones[n1].length*.01;l2=rig.data.bones[n2].length*.01;delta=target-a;axis=delta.normalized();d=max(abs(l1-l2)+.00001,min(l1+l2-.00001,delta.length));target=a+axis*d
 pole=Vector(((-1 if s=='Right' else 1)*.6,.3,-.2)) if typ=='arm' else Vector((0,-1,0));bend=(pole-axis*pole.dot(axis)).normalized();along=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0,l1*l1-along*along));mid=a+axis*along+bend*h
 for n,p,end in [(n1,a,mid),(n2,mid,target)]:
  rq=restW[n].to_quaternion();q=(rq@Vector((0,1,0))).rotation_difference((end-p).normalized())@rq;worldbone(n,p,q)
 worldbone(n3,target,handq or restW[n3].to_quaternion());return target

def ease(t,a,b):
 x=max(0,min(1,(t-a)/(b-a)));return x*x*(3-2*x)
def path(t,keys):
 for (a,va),(b,vb) in zip(keys,keys[1:]):
  if a<=t<=b:return Vector(va).lerp(Vector(vb),ease(t,a,b))
 return Vector(keys[-1][1])
def aim(key):return Vector((-.025,-.33,1.60) if key=='Pistol' else (-.10,-.245,1.63))
def holster(key):return (Vector((-.25,.07,1.05)) if key=='Pistol' else Vector((.0,.18,1.50)),Quaternion((1,0,0),math.pi/2))
def grab(key):p,q=holster(key);return p-q@OFF
spec=[]
for key in ['Pistol','Rifle']:
 for suffix,kind,dur in [('Aim_High','Aim_Idle',2),('Aim_Low','Aim_Idle',2),('Peek_Left','Aim_Raise',1),('Peek_Right','Aim_Raise',1),('Fire_Hip' if key=='Pistol' else 'Fire_Burst3','Fire_Aimed',.8),('Crouch_Fire','Fire_Aimed',.7),('Reload_Crouched','Reload_Tactical',2.8),('Draw_LowReady','Draw',1.35),('Holster_Crouched','Holster',1.35)]:spec.append((key+'_'+suffix,key,kind,dur))
records=[]
for name,key,kind,dur in spec:
 action=bpy.data.actions.new(name);rig.animation_data.action=None;cache=[];end=round(dur*30)+1;frames=[];events=[];previous={}
 if kind=='Fire_Aimed':events=[{'time_s':tt,'event':'projectile_and_muzzle_cue','bone':weapons[key]['prefix']+'muzzle','validated_damage_window':False} for tt in ([.07,.27,.47] if name.endswith('Fire_Burst3') else [2/30])]
 if kind.startswith('Reload'):events=[{'time_s':.5,'event':'magazine_detach'},{'time_s':1.8,'event':'magazine_insert'}]
 if kind=='Draw':events=[{'time_s':.4,'event':'attach_primary_hand'}]
 if kind=='Holster':events=[{'time_s':.8,'event':'attach_body_carry'}]
 if kind.startswith('Switch'):events=[{'time_s':.5,'event':'stow_old_weapon'},{'time_s':1.1,'event':'attach_next_weapon'}]
 for frame in range(1,end+1):
  t=(frame-1)/30;reset();crouch=any(v in name for v in ['Crouch','Crouched']);B('Hips').location=bodyrest[B('Hips').name].to_3x3().inverted()@(wi.to_3x3()@Vector((0,0,-.32 if crouch else -.065)));bpy.context.view_layer.update()
  for side in ['Left','Right']:solve(side,'leg',feet[side])
  q=Quaternion((1,0,0),0);wrist=aim(key);held=key;active=True;newkey=None
  if kind in ['Aim_Raise','Aim_Lower']:
   v=ease(t,0,dur);v=1-v if kind=='Aim_Lower' else v;wrist=Vector((-.16,-.17,1.08)).lerp(aim(key),v);q=Quaternion((1,0,0),.65*(1-v))
  elif kind=='Draw':
   wrist=path(t,[(0,(-.18,-.12,1.10)),(.4,grab(key)),(dur,aim(key))]);hq=holster(key)[1];q=hq.slerp(q,ease(t,.4,dur));active=t>=.4
  elif kind=='Holster':
   wrist=path(t,[(0,aim(key)),(.8,grab(key)),(dur,(-.18,-.12,1.10))]);q=q.slerp(holster(key)[1],ease(t,0,.8));active=t<=.8
  elif kind.startswith('Switch'):
   newkey=kind.split('_')[-1];wrist=path(t,[(0,aim(key)),(.5,grab(key)),(1.1,grab(newkey)),(dur,aim(newkey))]);held=key if t<=.5 else newkey;active=t<=.5 or t>=1.1
   q=Quaternion((1,0,0),0).slerp(holster(key)[1],ease(t,0,.5)) if t<=.5 else holster(newkey)[1].slerp(Quaternion((1,0,0),0),ease(t,1.1,dur))
  elif kind=='Fire_Aimed':
   recoil=math.sin(math.pi*ease(t,0,.15)) if t<.15 else 0;wrist+=Vector((0,.024*recoil,.012*recoil));q=Quaternion((1,0,0),-.14*recoil);B('Spine2').rotation_quaternion=Quaternion((1,0,0),-.025*recoil)
  elif kind.startswith('Reload'):wrist+=Vector((0,.035,-.11))*math.sin(math.pi*t/dur);q=Quaternion((1,0,0),.12*math.sin(math.pi*t/dur))
  if name.endswith('Aim_High'):wrist+=Vector((0,.015,.16));q=Quaternion((1,0,0),-.25)
  if name.endswith('Aim_Low'):wrist+=Vector((0,.015,-.18));q=Quaternion((1,0,0),.28)
  if name.endswith('Peek_Left'):wrist+=Vector((.12,0,.03))*math.sin(math.pi*t/dur);B('Spine2').rotation_quaternion=Quaternion((0,1,0),-.16*math.sin(math.pi*t/dur))
  if name.endswith('Peek_Right'):wrist+=Vector((-.12,0,.03))*math.sin(math.pi*t/dur);B('Spine2').rotation_quaternion=Quaternion((0,1,0),.16*math.sin(math.pi*t/dur))
  if crouch:wrist.z-=.22
  if name.endswith('Fire_Hip'):wrist+=Vector((-.10,.12,-.4));q=Quaternion((1,0,0),.05)
  if name.endswith('Fire_Burst3'):
   pulse=sum(max(0,1-abs(t-tt)/.08) for tt in [.07,.27,.47]);wrist+=Vector((0,.025*pulse,.014*pulse));q=Quaternion((1,0,0),-.12*pulse);B('Spine2').rotation_quaternion=Quaternion((1,0,0),-.024*pulse)
  if name.endswith('Draw_LowReady'):wrist+=Vector((0,.05,-.20))*ease(t,.5,dur)
  actual=solve('Right','arm',wrist,q@QR);handW=wm@B('RightHand').matrix;actualQ=handW.to_quaternion()@QR.inverted();roots={}
  for wk in weapons:
   p,hq=holster(wk);roots[wk]=Matrix.Translation(p)@hq.to_matrix().to_4x4()
  if active:roots[held]=Matrix.Translation(actual+actualQ@OFF)@actualQ.to_matrix().to_4x4()
  wk=held if active else key;W=roots[wk];weapon=weapons[wk];scale=weapon['scale'];support=W@(weapon['source']['support'].translation*scale);leftq=(QLR if wk=='Rifle' else QL);palmoffset=leftq@Vector((0,.10,0));target=support-palmoffset;contact='support'
  if not active:target=Vector((.22,-.12,1.05));contact='free'
  if kind.startswith('Reload'):
   mag=weapon['source'].get('magazine');grabpoint=mag.translation*scale+Vector((0,0,.045));magW=W@grabpoint
   palm=path(t,[(0,support),(.5,magW),(.95,(.23,.04,.99)),(1.8,magW),(2.3,support),(dur,support)])
   if kind=='Reload_Empty' and 1.9<t<2.55:palm=path(t,[(1.9,magW),(2.15,W@Vector((0,-.12,.15))),(2.35,W@Vector((0,.01,.15))),(2.55,support)])
   target=palm-palmoffset;contact='magazine' if .5<=t<=1.8 else 'service'
  elif kind in ['Aim_Raise','Aim_Lower','Draw','Holster']:
   blend=ease(t,dur*.35,dur*.90) if kind=='Aim_Raise' else 1-ease(t,.02,dur*.45) if kind=='Aim_Lower' else ease(t,.72,1.05) if kind=='Draw' else 1-ease(t,0,.4)
   target=Vector((.22,-.12,1.05)).lerp(target,blend);contact='support' if blend>.999 and active else 'free'
  elif kind.startswith('Switch') and .25<t<1.45:target=Vector((.22,-.12,1.05));contact='free'
  leftactual=solve('Left','arm',target,leftq);palmactual=leftactual+leftq@Vector((0,.10,0))
  # Mechanical channels share the same player skeleton and clock.
  for wk,w in weapons.items():
   root=roots[wk];prefix=w['prefix']
   for n,m in w['source'].items():
    world=root@m.copy();world.translation=root@(m.translation*w['scale'])
    if n=='magazine' and wk==key and kind.startswith('Reload') and .5<=t<=1.8:world.translation+=palmactual-(root@(m.translation*w['scale']+Vector((0,0,.045))))
    if n in ['slide','bolt'] and wk==key and kind=='Fire_Aimed':world.translation+=root.to_quaternion()@Vector((0,.025*math.sin(math.pi*ease(t,0,.15)) if t<.15 else 0,0))
    worldbone(prefix+n,world.translation,world.to_quaternion())
  for side in ['Right','Left']:
   for finger in ['Middle','Ring','Pinky']:
    for i in [1,2,3]:
     bn='mixamorig:'+side+'Hand'+finger+str(i)
     if bn in rig.pose.bones:rig.pose.bones[bn].rotation_quaternion=Quaternion((0,0,1),(.70 if side=='Right' else -.55))
  bpy.context.view_layer.update()
  values={}
  for pb in rig.pose.bones:
   local=rig.convert_space(pose_bone=pb,matrix=pb.matrix.copy(),from_space='POSE',to_space='LOCAL');loc,qq,sc=local.decompose()
   if pb.name in previous and previous[pb.name].dot(qq)<0:qq.negate()
   previous[pb.name]=qq.copy();values[pb.name]=(loc,qq,sc)
  cache.append((frame,values))
  frames.append({'time_s':t,'held':held if active else None,'left_contact':contact,'left_target_error_m':(leftactual-target).length,'right_target_error_m':(actual-wrist).length,'left_palm_world_m':list(palmactual),'right_wrist_world_m':list(actual),'weapon_root_world_m':list(roots[held].translation) if active else None})
 for pb in rig.pose.bones:
  for j,prop in enumerate(['location','rotation_quaternion','scale']):
   for axis in range(4 if j==1 else 3):
    fc=action.fcurves.new('pose.bones["'+pb.name+'"].'+prop,index=axis,action_group=pb.name);fc.keyframe_points.add(len(cache))
    for kp,(frame,values) in zip(fc.keyframe_points,cache):kp.co=(frame,values[pb.name][j][axis]);kp.interpolation='LINEAR'
 action.use_fake_user=True;records.append({'name':name,'duration_s':(end-1)/30,'fps':30,'motion_kind':'in_place','loop':kind=='Aim_Idle','events':events,'frames':frames,'quality_status':'authored handling prototype; visual/collision polish required','hit_windows_validated':False})
rig.animation_data.action=None;reset();bpy.context.view_layer.update()
for m in bodymeshes:
 for mod in m.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
bpy.ops.object.select_all(action='DESELECT')
for o in parts+[rig]:o.select_set(True)
bpy.context.view_layer.objects.active=rig;bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Player_Handling.blend'))
bpy.ops.export_scene.fbx(filepath=str(folder/'Player_With_Firearms.fbx'),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
bpy.ops.export_scene.gltf(filepath=str(folder/'Player_With_Firearms.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_optimize_animation_size=False)
assert all(rig.data.bones[n].matrix_local==m for n,m in bodyrest.items())
manifest={'name':'Player_Firearm_Handling','clips':records,'original_body_bones':len(bodyrest),'rig_bones':len(rig.data.bones),'player_art':'Existing supplied mannequin; not a new realistic humanoid','contact_method':'Two-bone analytic arm/leg solve; rigid weapon calibration; hand markers are not collision certification','provenance':'Source player and weapon credits retained in provenance and SOURCE_CREDITS.txt','missing':['Trigger/index fine contact','Magazine identity and dropped prop handling','Melee handling polish','Paired finishers polish','Full body collision review'],'engine_tested':False,'iphone_tested':False};(folder/'handling_manifest.json').write_text(json.dumps(manifest,indent=2));print('PLAYER_HANDLING_EXPORTED',len(records),len(rig.data.bones),flush=True)

for f in folder.iterdir():
 if f.is_file():
  with f.open("rb") as h:os.fsync(h.fileno())
