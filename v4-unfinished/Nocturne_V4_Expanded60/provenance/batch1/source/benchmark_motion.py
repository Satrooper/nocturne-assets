import bpy,math,json
from mathutils import Vector,Quaternion
from math import sin,cos,pi

def ease(t,a,b):
 u=max(0,min(1,(t-a)/(b-a)));return u*u*(3-2*u)
def bump(t,a,b,peak=None):
 peak=(a+b)/2 if peak is None else peak
 return ease(t,a,peak)*(1-ease(t,peak,b))

def setup_ik(c):
 rig=c.rig;scale=rig.scale.x;controls=[];chains={}
 for pre in ['hindL','hindR','frontL','frontR']:
  if pre+'_shin' not in rig.data.bones:continue
  upper=rig.data.bones[pre];shin=rig.data.bones[pre+'_shin'];foot=rig.data.bones[pre+'_foot'];target=bpy.data.objects.new('IK_'+pre,None);bpy.context.collection.objects.link(target);target.location=rig.matrix_world@shin.tail_local;target.rotation_mode='QUATERNION';target.rotation_quaternion=(rig.matrix_world@foot.matrix_local).to_quaternion();controls.append(target)
  pole=bpy.data.objects.new('Pole_'+pre,None);bpy.context.collection.objects.link(pole);h=upper.head_local;k=shin.head_local;end=shin.tail_local;v=end-h;project=h+v*((k-h).dot(v)/v.length_squared);off=(k-project).normalized();pole.location=rig.matrix_world@(k+off*1.5);controls.append(pole)
  con=rig.pose.bones[pre+'_shin'].constraints.new('IK');con.target=target;con.pole_target=pole;con.chain_count=2;con.use_tail=True;con.use_stretch=False
  best=(1e9,0)
  for angle in [0,pi/2,pi,-pi/2]:
   con.pole_angle=angle;bpy.context.view_layer.update();dist=(rig.pose.bones[pre+'_shin'].head-k).length
   if dist<best[0]:best=(dist,angle)
  con.pole_angle=best[1]
  rot=rig.pose.bones[pre+'_foot'].constraints.new('COPY_ROTATION');rot.target=target;rot.target_space='WORLD';rot.owner_space='WORLD'
  chains[pre]={'target':target,'pole':pole,'ik':con,'rot':rot,'pole_point':(k+off*1.5).copy(),'ankle':shin.tail_local.copy(),'toe':foot.tail_local.copy(),'toe_bone':foot.name}
 return chains,controls

def animate_benchmark(c):
 rig=c.rig;dragon=c.name=='Cinder_Crown';scale=rig.scale.x;chains,controls=setup_ik(c);spec=[];arms={}
 if not dragon:
  for pre,sg in [('armL',-1),('armR',1)]:
   lower=rig.pose.bones[pre+'_fore'];hand=rig.data.bones[pre+'_hand'];target=bpy.data.objects.new('Hand_target_'+pre,None);bpy.context.collection.objects.link(target);target.location=rig.matrix_world@hand.head_local;target.rotation_mode='QUATERNION';target.rotation_quaternion=(rig.matrix_world@hand.matrix_local).to_quaternion();pole=bpy.data.objects.new('Elbow_pole_'+pre,None);bpy.context.collection.objects.link(pole);pole.location=rig.matrix_world@Vector((sg*1.5,.4,2.05));con=lower.constraints.new('IK');con.target=target;con.pole_target=pole;con.chain_count=2;con.use_stretch=False;best=(999,0)
   for angle in [0,pi/2,pi,-pi/2]:
    con.pole_angle=angle;bpy.context.view_layer.update();error=(lower.head-lower.bone.head_local).length
    if error<best[0]:best=(error,angle)
   con.pole_angle=best[1];rot=rig.pose.bones[pre+'_hand'].constraints.new('COPY_ROTATION');rot.target=target;rot.owner_space='WORLD';rot.target_space='WORLD';arms[pre]={'target':target,'pole':pole,'base':hand.head_local.copy(),'rotation':target.rotation_quaternion.copy(),'sign':sg};controls.extend([target,pole])
 def add(n,dur,loop=False,kind=None,delta=(0,0,0),events=None):spec.append({'name':n,'duration':dur,'loop':loop,'kind':kind or n,'delta':Vector(delta),'events':events or []})
 add('Idle_Breathe',3,True)
 for kind,dur,speed in [('Walk',2.4,.45 if dragon else .36),('Run',1.2,1.25 if dragon else .9)]:
  add(kind+'_InPlace',dur,True,kind);add(kind+'_RootMotion',dur,True,kind,(0,-speed*dur,0))
 for side in ['Left','Right']:add('Turn_'+side,1.4,False,'Turn',events=[])
 for side in ['Front','Back','Left','Right']:add('Hit_'+side,.70)
 add('Stagger',1.3);add('Death_RootMotion',2.4,kind='Death',delta=(0,0,-.68));add('Threat_Roar' if dragon else 'Threat_Scan',2.2)
 if dragon:
  add('Bite_Lunge_RootMotion',1.65,kind='Bite',delta=(0,-.55,0),events=[(.62,'jaw_contact_start'),(.76,'jaw_contact_end')])
  add('Bite_InPlace',1.65,kind='Bite',events=[(.62,'jaw_contact_start'),(.76,'jaw_contact_end')])
  for side in ['Left','Right']:add('Claw_Swipe_'+side,1.6,kind='Claw',events=[(.67,'claw_sweep_start'),(.85,'claw_sweep_end')])
  add('Tail_Sweep',2.0,events=[(.94,'tail_sweep_start'),(1.17,'tail_sweep_end')]);add('Breath_Exhale',3.0,events=[(.90,'breath_start'),(2.0,'breath_end')]);add('Wing_Slam',1.9,events=[(.88,'wing_contact_start'),(1.06,'wing_contact_end')])
  add('Flight_Takeoff_RootMotion',2.4,kind='Takeoff',delta=(0,-.6,3.0));add('Flight_Hover_InPlace',2.0,True,'Hover');add('Flight_Glide_InPlace',2.0,True,'Glide');add('Flight_Landing_RootMotion',2.4,kind='Landing',delta=(0,.4,-3.0))
  add('Swim_Cruise_InPlace',2.0,True,'Swim');add('Swim_Cruise_RootMotion',2.0,True,'Swim',(0,-2.2,0))
 else:
  add('Piston_Punch_Left',1.15,kind='Punch',events=[(.39,'fist_contact_start'),(.51,'fist_contact_end')]);add('Piston_Punch_Right',1.15,kind='Punch',events=[(.39,'fist_contact_start'),(.51,'fist_contact_end')]);add('Hydraulic_Backhand',1.5,kind='Backhand',events=[(.57,'fist_contact_start'),(.76,'fist_contact_end')])
  add('Cannon_Burst',1.65,events=[(.48,'muzzle_L'),(.61,'muzzle_R'),(.74,'muzzle_L')]);add('Ground_Slam',1.9,events=[(.86,'ground_contact'),(.90,'shockwave_anchor')]);add('Charge_RootMotion',1.6,kind='Charge',delta=(0,-1.6,0),events=[(.82,'body_contact_start'),(.98,'body_contact_end')]);add('Brace',1.4)
 records=[];motion_reviews=[]
 for clip in spec:
  name=clip['name'];kind=clip['kind'];end=round(clip['duration']*30)+1;frames=list(range(1,end+1,2))
  if frames[-1]!=end:frames.append(end)
  cache=[];contact_samples={p:[] for p in chains};foot_intervals={p:[] for p in chains};stance_last={p:False for p in chains};start_time={p:0 for p in chains}
  for frame in frames:
   t=(frame-1)/(end-1);time=(frame-1)/30
   for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
   root=rig.pose.bones['root'];disp=clip['delta']*t if kind in ['Walk','Run','Swim','Charge'] else clip['delta']*ease(t,.1,.57)
   if kind=='Bite':disp=clip['delta']*ease(t,.12,.8)
   if kind=='Takeoff':disp=clip['delta']*ease(t,.18,1)
   if kind=='Landing':disp=clip['delta']*ease(t,0,.88)+Vector((0,0,3))
   if kind=='Turn':root.rotation_euler[1]=(1 if name.endswith('Left') else -1)*pi*(.25 if dragon else .5)*ease(t,0,1)
   if name.startswith('Hit_'):
    amp=.21*bump(t,0,1,.23);rig.pose.bones['chest'].rotation_euler[0]=amp*(-1 if name.endswith('Back') else 1);rig.pose.bones['chest'].rotation_euler[1]=amp*(1 if name.endswith('Left') else -1 if name.endswith('Right') else 0)
   if name=='Stagger':disp.z=-.18*bump(t,0,1,.22);rig.pose.bones['chest'].rotation_euler[0]=.25*bump(t,0,1,.27)
   if kind=='Death':disp.z=-.68*ease(t,.05,.65);root.rotation_euler[2]=1.1*ease(t,.10,.82)
   if name=='Idle_Breathe':rig.pose.bones['chest'].rotation_euler[0]=.018*sin(t*2*pi);rig.pose.bones['chest'].scale=(1,1+.012*sin(t*2*pi),1+.015*sin(t*2*pi))
   if name.startswith('Threat'):
    if dragon:rig.pose.bones['jaw'].rotation_euler[0]=.55*bump(t,.1,.88,.36);rig.pose.bones['neck1'].rotation_euler[0]=-.12*bump(t,.06,.88,.31)
    else:rig.pose.bones['head'].rotation_euler[1]=.35*sin(t*2*pi)*sin(pi*t)
   if kind in ['Walk','Run','Charge']:
    rate=1 if kind=='Walk' else 2;body=.025 if kind=='Walk' else .055;disp.z+=body*(1-cos(t*2*pi*rate));rig.pose.bones['chest'].rotation_euler[0]=body*.3*sin(t*2*pi*rate)
   if kind=='Bite':
    wind=bump(t,.03,.40,.22);hit=bump(t,.26,.80,.43);rig.pose.bones['chest'].rotation_euler[0]=-.13*wind+.13*hit;rig.pose.bones['neck1'].rotation_euler[0]=-.14*wind+.21*hit;rig.pose.bones['neck2'].rotation_euler[0]=-.13*wind+.25*hit;rig.pose.bones['head'].rotation_euler[0]=-.08*wind-.10*hit;rig.pose.bones['jaw'].rotation_euler[0]=.53*bump(t,.08,.53,.32)
   if kind=='Claw':
    side='frontL' if name.endswith('Left') else 'frontR';sg=-1 if name.endswith('Left') else 1;rig.pose.bones['chest'].rotation_euler[1]=sg*(.12*bump(t,.02,.40,.22)-.23*bump(t,.26,.85,.47));rig.pose.bones['neck1'].rotation_euler[1]=-.5*rig.pose.bones['chest'].rotation_euler[1]
   if kind=='Tail_Sweep':
    turn=-.23*bump(t,.02,.52,.25)+.43*bump(t,.37,.95,.59);rig.pose.bones['pelvis'].rotation_euler[1]=turn
    for pb in rig.pose.bones:
     if pb.name.startswith('tail'):pb.rotation_euler[2]=(-.14*bump(t,.02,.5,.24)+.38*bump(t,.33,.98,.58))* (1+int(pb.name[4:])*.09)
   if kind=='Breath_Exhale':
    rig.pose.bones['jaw'].rotation_euler[0]=.45*bump(t,.1,.91,.40);rig.pose.bones['neck1'].rotation_euler[0]=-.09*bump(t,.04,.90,.32);rig.pose.bones['chest'].scale=(1,1+.045*bump(t,.02,.60,.24),1+.035*bump(t,.02,.60,.24))
   if kind in ['Takeoff','Hover','Glide','Landing','Wing_Slam','Swim']:
    for pb in rig.pose.bones:
     if pb.name.startswith('wing'):
      s=-1 if 'L' in pb.name else 1
      if kind=='Glide':angle=.08+.015*sin(t*2*pi)
      elif kind=='Swim':angle=.30+.14*sin(t*2*pi)
      elif kind=='Wing_Slam':angle=-.45*bump(t,.02,.55,.30)+.63*bump(t,.36,.89,.50)
      else:phase=(t*2)%1;angle=.43*(cos(phase/ .28*pi) if phase<.28 else -cos((phase-.28)/.72*pi))
      pb.rotation_euler[1]=s*angle*(.52 if 'fore' in pb.name else .13 if 'digit' in pb.name else 1)
    if kind=='Wing_Slam':disp.z=-.18*bump(t,.25,.85,.50)
   if kind in ['Swim','Hover','Glide','Takeoff','Landing']:
    for pre in chains:rig.pose.bones[pre].rotation_euler[0]=.55 if kind!='Swim' else .25*sin(t*2*pi+ (pi if pre.endswith('L') else 0));rig.pose.bones[pre+'_shin'].rotation_euler[0]=-.40
   if kind=='Swim':
    for pb in rig.pose.bones:
     if pb.name.startswith('tail'):pb.rotation_euler[2]=.14*sin(t*2*pi-int(pb.name[4:])*.65)
    rig.pose.bones['chest'].rotation_euler[1]=.055*sin(t*2*pi)
   if not dragon:
    for pb in rig.pose.bones:
     if '_finger' in pb.name:pb.rotation_euler[0]=.85 if kind in ['Punch','Backhand','Ground_Slam','Brace'] else .10
     if pb.name.startswith('turret') and not pb.name.endswith('recoil'):pb.rotation_euler[2]=.08*sin(pi*t) if kind=='Cannon_Burst' else 0
    if kind=='Punch':
     arm='armL' if name.endswith('Left') else 'armR';sg=-1 if arm.endswith('L') else 1;w=bump(t,.02,.42,.19);strike=bump(t,.23,.88,.43);rig.pose.bones[arm].rotation_euler[0]=.20*w-.98*strike;rig.pose.bones[arm+'_fore'].rotation_euler[0]=-.25*w+.13*strike;rig.pose.bones['chest'].rotation_euler[1]=sg*.13*strike
    if kind=='Backhand':rig.pose.bones['armR'].rotation_euler[1]=-.27*bump(t,.02,.48,.2)+.72*bump(t,.29,.92,.48);rig.pose.bones['chest'].rotation_euler[1]=.22*bump(t,.29,.92,.48)
    if kind=='Cannon_Burst':
     for side,ts in [('L',[.48,.74]),('R',[.61])]:
      recoil=sum(bump(time,s,s+.15,s+.025) for s in ts);rig.pose.bones['turret'+side+'_recoil'].location[1]=-.04*recoil;rig.pose.bones['chest'].rotation_euler[0]=.03*recoil
    if kind=='Ground_Slam':
     w=bump(t,.02,.55,.31);hit=bump(t,.34,.88,.49);disp.z=-.68*hit;rig.pose.bones['pelvis'].location=rig.data.bones['pelvis'].matrix_local.to_3x3().inverted()@Vector((0,0,-.32*hit));rig.pose.bones['chest'].rotation_euler[0]=-.18*w+.72*hit
     for arm in ['armL','armR']:rig.pose.bones[arm].rotation_euler[0]=-1.2*w+.22*hit
    if kind=='Brace':disp.z=-.18*bump(t,.02,.97,.40);rig.pose.bones['chest'].rotation_euler[0]=.12*bump(t,.02,.97,.40)
   if kind in ['Walk','Run','Turn','Charge','Bite']:
    rig.pose.bones['pelvis'].location=rig.data.bones['pelvis'].matrix_local.to_3x3().inverted()@Vector((0,0,(-.14 if kind in ['Turn','Bite'] else -.08) if dragon else -.14))
   root.location=root.bone.matrix_local.to_3x3().inverted()@disp
   bpy.context.view_layer.update()
   for pre,ch in chains.items():
    planted=True;target=ch['ankle'].copy();target+=disp;foot_yaw=0
    root_yaw=(1 if name.endswith('Left') else -1)*pi*(.25 if dragon else .5)*ease(t,0,1) if kind=='Turn' else 0
    pole_point=ch['pole_point']+disp
    if kind=='Turn':pole_point=Quaternion((0,0,1),root_yaw)@ch['pole_point']+disp
    ch['pole'].location=rig.matrix_world@pole_point
    airborne=kind in ['Hover','Glide','Swim'] or kind=='Takeoff' and t>.26 or kind=='Landing' and t<.78 or kind=='Death'
    ch['ik'].influence=0 if airborne else 1;ch['rot'].influence=0 if airborne else 1
    if airborne:planted=False
    elif kind in ['Walk','Run','Charge']:
     phase=(t*(2 if kind=='Run' else 1)+(0 if pre in ['hindL','frontR'] else .5))%1;duty=.66 if kind=='Walk' else .5;stride=(.45 if dragon else .36)*clip['duration'] if kind=='Walk' else abs(clip['delta'].y) if kind=='Charge' else (1.25 if dragon else .9)*clip['duration']/2;planted=phase<duty
     if planted:target.y+=stride*(phase-duty/2);target.z=ch['ankle'].z
     else:q=(phase-duty)/(1-duty);target.y+=stride*duty*(.5-ease(q,0,1));target.z=ch['ankle'].z+(.15 if kind=='Walk' else .27)*sin(pi*q)
    elif kind=='Turn':
     a,b=({'frontL':(.05,.28),'hindR':(.26,.48),'frontR':(.45,.70),'hindL':(.69,.95)} if dragon else {'hindL':(.10,.48),'hindR':(.50,.92)})[pre];u=ease(t,a,b);foot_yaw=(1 if name.endswith('Left') else -1)*pi*(.25 if dragon else .5)*u;planted=not(a<t<b);target=Quaternion((0,0,1),foot_yaw)@ch['ankle'];target.z=ch['ankle'].z+.17*bump(t,a,b)
    elif kind=='Bite' and clip['delta'].length>.01:
     a,b={'frontR':(.11,.36),'frontL':(.25,.5),'hindR':(.42,.69),'hindL':(.51,.79)}[pre];planted=t<a or t>=b;target=ch['ankle']+clip['delta']*ease(t,a,b);target.z=ch['ankle'].z+.18*bump(t,a,b)
    elif kind=='Claw' and pre==('frontL' if name.endswith('Left') else 'frontR'):
     planted=False;target.y-=.85*bump(t,.21,.89,.49);target.z+=.51*bump(t,.05,.9,.35)
    else:target.y-=disp.y;target.x-=disp.x;target.z=ch['ankle'].z
    ch['target'].location=rig.matrix_world@target
    ch['target'].rotation_quaternion=Quaternion((0,0,1),foot_yaw)@(rig.matrix_world@rig.data.bones[pre+'_foot'].matrix_local).to_quaternion()
    if planted and not stance_last[pre]:start_time[pre]=time
    if not planted and stance_last[pre]:foot_intervals[pre].append([round(start_time[pre],3),round(time,3)])
    stance_last[pre]=planted
   for pre,arm in arms.items():
    sg=arm['sign'];target=arm['base']+disp;rotation=arm['rotation'].copy()
    if kind=='Punch' and pre==('armL' if name.endswith('Left') else 'armR'):
     wind=bump(t,.02,.42,.19);strike=bump(t,.23,.88,.43);target=target.lerp(Vector((sg*.96,.17,2.03))+disp,wind).lerp(Vector((sg*.62,-.90,2.23))+disp,strike);rotation=Quaternion((1,0,0),-pi/2*strike)@rotation
    elif kind=='Backhand' and pre=='armR':
     wind=bump(t,.02,.48,.20);strike=bump(t,.29,.92,.48);target=target.lerp(Vector((.98,.12,2.32))+disp,wind).lerp(Vector((-.04,-.64,2.16))+disp,strike);rotation=Quaternion((1,0,0),-pi*.45*strike)@rotation
    elif kind=='Ground_Slam':
     wind=bump(t,.02,.55,.31);impact=bump(t,.34,.88,.49);target=target.lerp(Vector((sg*.63,-.08,3.33)),wind).lerp(Vector((sg*.46,-.64,.32)),impact)
    elif kind=='Brace':target=target.lerp(Vector((sg*.42,-.35,2.18))+disp,bump(t,.02,.97,.40))
    arm['target'].location=rig.matrix_world@target;arm['target'].rotation_quaternion=rotation;arm['pole'].location=rig.matrix_world@(Vector((sg*1.5,.4,2.05))+disp)
   bpy.context.view_layer.update()
   matrices={pb.name:rig.convert_space(pose_bone=pb,matrix=pb.matrix.copy(),from_space='POSE',to_space='LOCAL') for pb in rig.pose.bones};cache.append((frame,matrices))
   for pre,ch in chains.items():
    if stance_last[pre]:contact_samples[pre].append({'time':round(time,4),'position_m':list(rig.matrix_world@rig.pose.bones[ch['toe_bone']].head)})
  for pre in chains:
   if stance_last[pre]:foot_intervals[pre].append([round(start_time[pre],3),round(clip['duration'],3)])
  action=bpy.data.actions.new(name);action.use_fake_user=True
  for bone in rig.pose.bones:
   for prop,components in [('location',3),('rotation_euler',3),('scale',3)]:
    vals=[(frame,mat.decompose()[0] if prop=='location' else mat.to_euler('XYZ') if prop=='rotation_euler' else mat.decompose()[2]) for frame,allm in cache for mat in [allm[bone.name]]]
    for axis in range(components):
     fc=action.fcurves.new(data_path='pose.bones["'+bone.name+'"].'+prop,index=axis,action_group=bone.name);fc.keyframe_points.add(len(vals))
     for kp,(f,value) in zip(fc.keyframe_points,vals):kp.co=(f,value[axis]);kp.interpolation='LINEAR'
  eventlist=[{'time':ts,'event':ev,'status':'authored pose/contact cue; not engine-validated damage window'} for ts,ev in clip['events']]
  records.append({'name':name,'frames':end,'fps':30,'duration':clip['duration'],'loop':clip['loop'],'motion_kind':'root_motion' if clip['delta'].length>.001 or kind=='Turn' else 'in_place','root_motion':clip['delta'].length>.001 or kind=='Turn','root_displacement_m':list(clip['delta']*scale),'in_place_speed_mps':((.45 if dragon else .36) if kind=='Walk' else (1.25 if dragon else .9) if kind=='Run' else 0)*scale,'root_snapback':False,'events':eventlist,'contacts':{pre:{'bone':ch['toe_bone'],'stance_intervals':foot_intervals[pre],'samples':contact_samples[pre]} for pre,ch in chains.items()},'authorship':'clip-specific FK/IK authoring baked to deform skeleton; procedural, not mocap'})
 for pb in rig.pose.bones:
  for con in list(pb.constraints):pb.constraints.remove(con)
  pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
 for ob in controls:bpy.data.objects.remove(ob,do_unlink=True)
 rig.animation_data.action=None
 return records
