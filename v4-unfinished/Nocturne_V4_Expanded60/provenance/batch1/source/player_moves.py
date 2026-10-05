import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
from math import sin,cos,pi
sys.path.insert(0,str(Path(__file__).resolve().parent))
from benchmark_motion import ease,bump
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(P/'source'/'Player_Reference.fbx'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];rig.name='PlayerRig';rig.animation_data.action=None
for track in rig.animation_data.nla_tracks:track.mute=True
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');root=rig.data.edit_bones.new('NocturneRoot');root.head=rig.matrix_world.inverted()@Vector((0,0,0));root.tail=rig.matrix_world.inverted()@Vector((0,0,.15));rig.data.edit_bones['mixamorig:Hips'].parent=root
for side in ['Left','Right']:
 hand=rig.data.edit_bones['mixamorig:'+side+'Hand'];direction=(hand.tail-hand.head).normalized();b=rig.data.edit_bones.new('WeaponSocket_'+('L' if side=='Left' else 'R'));b.head=hand.head+direction*7;b.tail=hand.head+direction*18;b.parent=hand
bpy.ops.object.mode_set(mode='OBJECT')
B=lambda n:rig.pose.bones['mixamorig:'+n]
worldvector=lambda bone,vec:(rig.matrix_world@bone.bone.matrix_local).to_3x3().inverted()@Vector(vec)
controls=[];legs={};arms={}
for side in ['Left','Right']:
 for typ,last,first,foot in [('leg','Leg','UpLeg','Foot'),('arm','ForeArm','Arm','Hand')]:
  lower=B(side+last);target=bpy.data.objects.new(side+'_'+typ+'_IK',None);bpy.context.collection.objects.link(target);target.location=rig.matrix_world@lower.tail;target.rotation_mode='QUATERNION';target.rotation_quaternion=(rig.matrix_world@B(side+foot).bone.matrix_local).to_quaternion();pole=bpy.data.objects.new(side+'_'+typ+'_Pole',None);bpy.context.collection.objects.link(pole)
  sg=1 if side=='Left' else -1;pole.location=Vector((sg*.40,-.55,.55) if typ=='leg' else (sg*.65,.25,1.2));con=lower.constraints.new('IK');con.target=target;con.pole_target=pole;con.chain_count=2;con.use_stretch=False;rotation=B(side+foot).constraints.new('COPY_ROTATION');rotation.target=target;rotation.target_space='WORLD';rotation.owner_space='WORLD';controls.extend([target,pole])
  info={'target':target,'pole':pole,'ik':con,'rot':rotation,'base':rig.matrix_world@lower.bone.tail_local,'foot_rotation':(rig.matrix_world@B(side+foot).bone.matrix_local).to_quaternion(),'bone':B(side+foot).name}
  (legs if typ=='leg' else arms)[side]=info
  if typ=='leg':
   best=(999,0);knee=rig.matrix_world@lower.bone.head_local
   for angle in [0,pi/2,pi,-pi/2]:
    con.pole_angle=angle;bpy.context.view_layer.update();error=(rig.matrix_world@lower.head-knee).length
    if error<best[0]:best=(error,angle)
   con.pole_angle=best[1]
  else:con.pole_angle=-pi/2 if side=='Left' else pi/2
spec=[]
def add(name,duration,kind,delta=(0,0,0),role=None):spec.append({'name':name,'duration':duration,'kind':kind,'delta':Vector(delta),'role':role})
add('Pistol_Fire',.42,'fire');add('Pistol_Fire_Aimed',.45,'fire');add('Pistol_Reload_Tactical',2.25,'reload');add('Pistol_Reload_Empty',2.75,'reload')
for direction,delta in [('Forward',(0,-1.5,0)),('Backward',(0,1.10,0)),('Left',(.95,0,0)),('Right',(-.95,0,0))]:
 add('Dodge_'+direction+'_RootMotion',.70,'dodge',delta);add('Dodge_'+direction+'_InPlace',.70,'dodge')
add('Backstep_RootMotion',.50,'dodge',(0,.72,0))
for side in ['Left','Right']:add('Sword_Parry_'+side,.68,'parry')
add('Sword_Riposte_RootMotion',1.12,'riposte',(0,-.62,0));add('Sword_Riposte_InPlace',1.12,'riposte')
for i,duration in [(1,.52),(2,.56),(3,.70)]:
 add('Sword_Light_Combo_'+str(i)+'_InPlace',duration,'light'+str(i));add('Sword_Light_Combo_'+str(i)+'_RootMotion',duration,'light'+str(i),(0,-.22 if i!=3 else -.36,0))
for i,duration in [(1,1.05),(2,1.22)]:
 add('Sword_Heavy_Combo_'+str(i)+'_InPlace',duration,'heavy'+str(i));add('Sword_Heavy_Combo_'+str(i)+'_RootMotion',duration,'heavy'+str(i),(0,-.34,0))
add('Weapon_Switch_Pistol_To_Sword',1.0,'switch');add('Weapon_Switch_Sword_To_Pistol',1.0,'switch')
for direction in ['Front','Back','Left','Right']:add('Hit_'+direction,.55,'hit')
add('Knockdown_Back_RootMotion',1.05,'knock',(0,.43,-.69));add('GetUp_From_Back',1.9,'getup')
for name,kind in [('Swim_Idle_InPlace','swimidle'),('Swim_Tread_InPlace','tread'),('Swim_Crawl_InPlace','swim'),('Swim_Burst_InPlace','swimfast')]:add(name,2.0,kind)
add('Swim_Crawl_RootMotion',2.0,'swim',(0,-1.2,0));add('Swim_Burst_RootMotion',2.0,'swimfast',(0,-2.0,0));add('Swim_Dive_RootMotion',1.5,'swim',(0,-.65,-.60))
for pair in ['Backstab','Frontal_Execution']:
 add('Paired_'+pair+'_Attacker',2.4,'finish', (0,-.24,0),'attacker');add('Paired_'+pair+'_Victim',2.4,'finish',(0,0,-.62),'victim')
records=[]
for clip in spec:
 name=clip['name'];kind=clip['kind'];duration=clip['duration'];end=round(duration*30)+1;frames=list(range(1,end+1,2))
 if frames[-1]!=end:frames.append(end)
 cache=[];contact=[];events=[];last_euler={}
 if kind=='fire':events=[{'time':.08,'event':'projectile_spawn_and_muzzle_flash','socket':'WeaponSocket_R'}]
 elif kind=='reload':events=[{'time':.30,'event':'magazine_detach','socket':'WeaponSocket_R'},{'time':1.17,'event':'magazine_insert','socket':'WeaponSocket_R'},{'time':1.68 if 'Empty' in name else 1.85,'event':'slide_rack_or_grip_restore','socket':'WeaponSocket_R'}]
 elif kind=='parry':events=[{'time':.20,'event':'parry_contact_start'},{'time':.31,'event':'parry_contact_end'}]
 elif kind.startswith('light'):events=[{'time':round(duration*.39,3),'event':'blade_contact_start'},{'time':round(duration*.55,3),'event':'blade_contact_end'},{'time':round(duration*.53,3),'event':'combo_branch_open'}]
 elif kind.startswith('heavy'):events=[{'time':round(duration*.56,3),'event':'blade_contact_start'},{'time':round(duration*.72,3),'event':'blade_contact_end'},{'time':round(duration*.72,3),'event':'combo_branch_open'}]
 elif kind=='riposte':events=[{'time':.43,'event':'blade_contact_start'},{'time':.60,'event':'blade_contact_end'}]
 elif kind=='switch':events=[{'time':.24,'event':'weapon_stow'},{'time':.64,'event':'weapon_attach_hand','socket':'WeaponSocket_R'}]
 elif kind=='finish':events=[{'time':.98,'event':'paired_impact_start'},{'time':1.16,'event':'paired_impact_end'},{'time':2.30,'event':'pair_release'}]
 for frame in frames:
  t=(frame-1)/(end-1);ts=t*duration
  for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
  rootpb=rig.pose.bones['NocturneRoot'];disp=clip['delta']*(t if kind.startswith('swim') else ease(t,.44,.90) if clip['role']=='victim' else ease(t,.08,.68));yaw=0;hipdrop=-.075
  hand={'Right':Vector((-.18,-.28,1.22)),'Left':Vector((.24,-.11,1.13))};aim={'Right':Vector((0,-1,.12)),'Left':Vector((0,-1,0))}
  if kind in ['fire','reload']:
   hand={'Right':Vector((-.16,-.42,1.42)),'Left':Vector((-.045,-.34,1.38))}
   if kind=='fire':
    recoil=bump(ts,.065,.27,.09);hand['Right'].y+=.045*recoil;hand['Right'].z+=.025*recoil;hand['Left']+=Vector((0,.028*recoil,.018*recoil));aim['Right'].z+=.33*recoil;B('Spine2').rotation_euler[0]=-.02*recoil
   else:
    # Left hand removes the magazine, reaches the belt, inserts a replacement, then restores grip.
    key=[(0,(-.045,-.34,1.38)),(.28,(-.16,-.35,1.26)),(.67,(.19,.02,.98)),(1.02,(-.13,-.29,1.22)),(1.27,(-.16,-.34,1.30)),(1.68,(-.13,-.42,1.47) if 'Empty' in name else (-.045,-.34,1.38)),(duration,(-.045,-.34,1.38))]
    for (a,pa),(b,pb) in zip(key,key[1:]):
     if a<=ts<=b:hand['Left']=Vector(pa).lerp(Vector(pb),ease(ts,a,b));break
    hand['Right'].z-=.07*bump(t,.05,.94,.42);B('Spine2').rotation_euler[1]=.05*bump(t,.04,.9,.35)
  if kind=='dodge':
   hipdrop-=.17*bump(t,.02,.95,.37);B('Spine').rotation_euler[0]=.20*bump(t,.02,.94,.42)*(1 if 'Forward' in name else -1 if 'Back' in name else 0);B('Spine').rotation_euler[2]=(.20 if 'Left' in name else -.20 if 'Right' in name else 0)*bump(t,.02,.94,.42)
   hand['Right']+=Vector((0,.07,-.10))*sin(pi*t)
  if kind in ['parry','riposte']:
   p=bump(t,.02,.85,.36);hand['Right']=hand['Right'].lerp(Vector((-.04,-.36,1.49) if kind=='parry' else (-.05,-.47,1.31)),p);hand['Left']=hand['Left'].lerp(Vector((.17,-.29,1.40)),p);aim['Right']=Vector((.5 if name.endswith('Left') else -.5,0,1)) if kind=='parry' else Vector((0,-1,0));B('Spine2').rotation_euler[0]=.10*p
  if kind.startswith('light') or kind.startswith('heavy'):
   i=int(kind[-1]);heavy=kind.startswith('heavy');wind=ease(t,.03,.28 if not heavy else .47)*(1-ease(t,.32 if not heavy else .52,.54 if not heavy else .72));impact=bump(t,.22 if not heavy else .43,.91,.49 if not heavy else .66)
   start=Vector((-.40,-.03,1.43)) if i==1 else Vector((.14,-.13,1.53));hit=Vector((.17,-.37,1.18)) if i==1 else Vector((-.31,-.43,1.32))
   if i==3:start=Vector((-.24,-.05,1.25));hit=Vector((-.06,-.48,1.30))
   if heavy:start=Vector((-.09,-.14,1.91));hit=Vector((-.13,-.41,1.12));hand['Left']=hand['Left'].lerp(Vector((.05,-.18,1.82)),wind).lerp(Vector((.04,-.30,1.27)),impact)
   hand['Right']=hand['Right'].lerp(start,wind).lerp(hit,impact);B('Spine2').rotation_euler[1]=(-.17*wind+.23*impact)*(1 if i%2 else -1);B('Spine2').rotation_euler[0]=.09*impact;aim['Right']=Vector((0,-1,.4 if wind>impact else -.4 if heavy else -.08));hipdrop-=.10*impact if heavy else .025*impact
  if kind=='switch':
   hand['Right']=hand['Right'].lerp(Vector((-.23,.13,1.02)),bump(t,.05,.68,.31));hand['Right']=hand['Right'].lerp(Vector((-.16,-.42,1.42)),ease(t,.68,.92) if name.endswith('Pistol') else 0)
  if kind=='hit':
   p=bump(t,0,.93,.19);B('Spine').rotation_euler[0]=(-.16 if name.endswith('Back') else .16 if name.endswith('Front') else 0)*p;B('Spine').rotation_euler[2]=(.16 if name.endswith('Left') else -.16 if name.endswith('Right') else 0)*p;hand['Right'].z-=.06*p
  if kind in ['knock','getup']:
   progress=ease(t,.05,.69) if kind=='knock' else 1-ease(t,.16,.94);B('Hips').rotation_euler[0]=-pi/2*progress;hipdrop=-.075 if kind=='knock' else -.69*progress;hand={'Right':Vector((-.29,.19,.22)).lerp(Vector((-.18,-.28,1.22)),1-progress),'Left':Vector((.29,.19,.22)).lerp(Vector((.24,-.11,1.13)),1-progress)}
  swim=kind in ['swim','swimfast','swimidle','tread']
  if swim:
   hipdrop=0;B('Hips').rotation_euler[0]=pi*.47 if kind!='tread' else .12;rate=2 if kind=='swimfast' else 1
   for side in ['Left','Right']:
    p=t*2*pi*rate+(0 if side=='Left' else pi);sg=1 if side=='Left' else -1;hand[side]=Vector((sg*(.22+.14*sin(p)), -.41-.29*cos(p),.98+.13*sin(p))) if kind!='tread' else Vector((sg*.33,-.07,1.22+.09*sin(p)));B(side+'UpLeg').rotation_euler[0]=.12*sin(p);B(side+'Leg').rotation_euler[0]=.10*(1+sin(p));aim[side]=Vector((0,-1,0))
   B('Spine2').rotation_euler[1]=.035*sin(t*2*pi)
  if kind=='finish':
   if clip['role']=='attacker':
    p=bump(t,.10,.78,.44);hand['Right']=hand['Right'].lerp(Vector((-.06,-.45,1.24) if 'Backstab' in name else (-.12,-.42,1.09)),p);B('Spine2').rotation_euler[0]=.12*p;aim['Right']=Vector((0,-1,-.1));hipdrop-=.09*p
   else:
    base=Vector((0,-.92 if 'Backstab' in name else -1.04,0));yaw=0 if 'Backstab' in name else pi;collapse=ease(t,.44,.90);disp+=base;hipdrop=-.075;B('Spine').rotation_euler[0]=.55*collapse;hand={'Right':Vector((-.23,-.23,1.11-.10*collapse)),'Left':Vector((.23,-.23,1.11-.10*collapse))}
  rootpb.location=worldvector(rootpb,disp);rootpb.rotation_euler[1]=yaw;B('Hips').location=worldvector(B('Hips'),(0,0,hipdrop))
  qyaw=Quaternion((0,0,1),yaw)
  for side,info in arms.items():
   info['ik'].influence=1;info['rot'].influence=1;info['target'].location=qyaw@hand[side]+disp;info['target'].rotation_quaternion=qyaw@aim[side].normalized().to_track_quat('Y','Z');sg=1 if side=='Left' else -1;info['pole'].location=qyaw@Vector((sg*.65,.26,1.15+hipdrop))+disp
   for pb in rig.pose.bones:
    if pb.name.startswith('mixamorig:'+side+'Hand') and any(w in pb.name for w in ['Index','Middle','Ring','Pinky']):pb.rotation_euler[2]=.28 if kind in ['fire','reload'] else .19
  for side,info in legs.items():
   airborne=swim or kind=='knock' or kind=='getup' and t<.62 or kind=='dodge' and .12<t<.74;info['ik'].influence=0 if airborne else 1;info['rot'].influence=0 if airborne else 1;target=info['base'].copy();planted=not airborne
   if kind=='dodge':
    if airborne:B(side+'UpLeg').rotation_euler[0]=.33*sin(pi*t);B(side+'Leg').rotation_euler[0]=-.30*sin(pi*t)
    target+=disp;target.z=info['base'].z
   elif clip['delta'].length>.01 and kind not in ['knock','finish']:
    a,b=(.08,.39) if side=='Right' else (.39,.70);planted=not(a<t<b);target+=clip['delta']*ease(t,a,b);target.z=info['base'].z+.12*bump(t,a,b)
   elif kind=='finish' and clip['role']=='victim':target=qyaw@info['base']+Vector((0,disp.y,0));target.z=info['base'].z
   info['planted']=planted and not airborne;info['target'].location=target;info['target'].rotation_quaternion=qyaw@info['foot_rotation'];sg=1 if side=='Left' else -1;info['pole'].location=qyaw@Vector((sg*.20,-.60,.50+hipdrop))+disp
  bpy.context.view_layer.update();values={}
  for pb in rig.pose.bones:
   matrix=rig.convert_space(pose_bone=pb,matrix=pb.matrix.copy(),from_space='POSE',to_space='LOCAL');pos,quat,scale=matrix.decompose();e=matrix.to_euler('XYZ',last_euler[pb.name]) if pb.name in last_euler else matrix.to_euler('XYZ');last_euler[pb.name]=e.copy();values[pb.name]=(pos,e,scale)
  cache.append((frame,values));contact.append({'time':round(ts,4),'feet':{side:{'position_m':list(rig.matrix_world@B(side+'Foot').head),'planted':legs[side]['planted']} for side in ['Left','Right']}})
 action=bpy.data.actions.new(name);action.use_fake_user=True
 for pb in rig.pose.bones:
  for index,prop in enumerate(['location','rotation_euler','scale']):
   for axis in range(3):
    fc=action.fcurves.new('pose.bones["'+pb.name+'"].'+prop,index=axis,action_group=pb.name);fc.keyframe_points.add(len(cache))
    for kp,(frame,vals) in zip(fc.keyframe_points,cache):kp.co=(frame,vals[pb.name][index][axis]);kp.interpolation='LINEAR'
 records.append({'name':name,'duration':duration,'frames':end,'fps':30,'kind':kind,'motion_kind':'root_motion' if clip['delta'].length>.001 else 'in_place','root_displacement_m':list(clip['delta']),'root_snapback':False,'loop':swim and 'Dive' not in name,'events':events,'contact_samples':contact,'timing_status':'authoring cues; no engine hitbox/invulnerability validation','paired_role':clip['role'],'paired_alignment':'same scene origins; victim root contains alignment offset, do not add the offset twice' if kind=='finish' else None})
for pb in rig.pose.bones:
 for con in list(pb.constraints):pb.constraints.remove(con)
 pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
for o in controls:bpy.data.objects.remove(o,do_unlink=True)
rig.animation_data.action=None;bpy.context.scene.render.fps=30
folder=P/'player_animation';folder.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(folder/'Player_Moves_AnimationOnly.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0)
for o in meshes:o.select_set(True)
rig.animation_data.action=list(bpy.data.actions)[0];bpy.ops.export_scene.gltf(filepath=str(folder/'Player_Moves_With_Existing_Mannequin.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_animations=True)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Player_Moves.blend'),compress=True)
meta={'new_character_design':False,'preview_character':'existing repository Y Bot, not a new Nocturne character','animation_authorship':'new procedural key poses and IK, not motion capture; require game/artist review','root_bone':'NocturneRoot','skeleton':'Mixamo names preserved; root and weapon socket bones added','clips':records,'sockets':{'WeaponSocket_R':{'parent':'mixamorig:RightHand','axis_forward':'+Y','axis_up':'+Z','offset_m_from_wrist':.07},'WeaponSocket_L':{'parent':'mixamorig:LeftHand','axis_forward':'+Y','axis_up':'+Z','offset_m_from_wrist':.07}},'engine_tested':False,'weapon_props_included':False,'paired_status':'matched clocks and authored root alignment; gameplay synchronization and collision remain external'}
(folder/'animation_manifest.json').write_text(json.dumps(meta,indent=2));print('PLAYER_MOVES_EXPORTED',len(records),flush=True)
