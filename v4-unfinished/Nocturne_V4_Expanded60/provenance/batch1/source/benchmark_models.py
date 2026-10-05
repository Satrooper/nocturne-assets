import bpy,math,bmesh,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from math import sin,cos,pi
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_creatures import Creature,ROSTER,P
OLD=P/'source'/'v3_baselines'

def mat(c,name,color,metal=0,rough=.5):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;c.mats[name]=m;return m

def skin_shader(m,organic=True):
 n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF');coord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(5,8,6) if organic else (35,110,40);l.new(coord.outputs['Object'],mapping.inputs[0])
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.0;noise.inputs['Detail'].default_value=3.0;l.new(mapping.outputs[0],noise.inputs['Vector'])
 base=bs.inputs['Base Color'].default_value[:];ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.25;ramp.color_ramp.elements[0].color=(base[0]*.4,base[1]*.4,base[2]*.4,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(min(1,base[0]*1.6),min(1,base[1]*1.6),min(1,base[2]*1.6),1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.32;bump.inputs['Distance'].default_value=.008 if organic else .0006
 if organic:
  # Continuous micro scales: size varies anatomically by height and head position, not loose polygons.
  sep=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs['Object'],sep.inputs[0]);size=n.new('ShaderNodeMapRange');size.inputs['From Min'].default_value=.35;size.inputs['From Max'].default_value=2.2;size.inputs['To Min'].default_value=2.0;size.inputs['To Max'].default_value=.78;l.new(sep.outputs['Z'],size.inputs[0]);mul=n.new('ShaderNodeVectorMath');mul.operation='SCALE';l.new(mapping.outputs[0],mul.inputs[0]);l.new(size.outputs[0],mul.inputs['Scale'])
  vor=n.new('ShaderNodeTexVoronoi');vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=1.0;l.new(mul.outputs[0],vor.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.01;r.color_ramp.elements[1].position=.10;l.new(vor.outputs['Distance'],r.inputs[0]);l.new(r.outputs[0],bump.inputs['Height']);bs.inputs['Subsurface Weight'].default_value=.065
 else:l.new(noise.outputs['Fac'],bump.inputs['Height'])
 l.new(bump.outputs[0],bs.inputs['Normal'])

def discard(c,starts):
 for o in list(c.parts):
  if any(o.name.startswith(s) for s in starts):c.parts.remove(o);bpy.data.objects.remove(o,do_unlink=True)

def fuse_body(c,objects):
 # Continuous volume reconstruction, followed by nearest-surface blended weight transfer.
 points=[];weights=[]
 for o in objects:
  gn={g.index:g.name for g in o.vertex_groups}
  for v in o.data.vertices:points.append(v.co.copy());weights.append({gn[g.group]:g.weight for g in v.groups})
 kd=KDTree(len(points))
 for i,p in enumerate(points):kd.insert(p,i)
 kd.balance();bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='Continuous_Anatomical_Skin'
 mod=o.modifiers.new('Volume_reconstruction','REMESH');mod.mode='VOXEL';mod.voxel_size=.044;mod.use_smooth_shade=True;mod.use_remove_disconnected=False;bpy.ops.object.modifier_apply(modifier=mod.name)
 sm=o.modifiers.new('Surface_relax','SMOOTH');sm.factor=.55;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
 tris=sum(len(p.vertices)-2 for p in o.data.polygons)
 if tris>24500:
  d=o.modifiers.new('Surface_budget','DECIMATE');d.ratio=24500/tris;bpy.ops.object.modifier_apply(modifier=d.name)
 o.vertex_groups.clear();groups={name:o.vertex_groups.new(name=name) for name in c.rig.data.bones.keys()}
 for v in o.data.vertices:
  neighbors=kd.find_n(v.co,4);merged={};total=0
  for _,idx,dist in neighbors:
   w=1/max(.003,dist)**2;total+=w
   for name,val in weights[idx].items():merged[name]=merged.get(name,0)+w*val
  for name,val in merged.items():groups[name].add([v.index],val/total,'REPLACE')
 o.data.materials.clear();o.data.materials.append(c.mats['dermis'])
 for p in o.data.polygons:p.material_index=0;p.use_smooth=True
 c.parts=[a for a in c.parts if a not in objects]+[o]
 return o

def dragon_wings(c):
 for side in [-1,1]:
  s=side;pre='wingL' if s<0 else 'wingR';root=Vector((s*.50,-.35,2.05));elbow=root+Vector((s*1.62,-.25,.81));wrist=root+Vector((s*2.79,-.7,.99));fore=pre+'_fore'
  c.tube('Wing_humerus',[root,elbow,wrist],[.18,.105,.07],['chest',pre,fore],sides=12,sub=4)
  tips=[wrist+Vector((s*1.8,.25,-.49)),wrist+Vector((s*1.35,1.34,-1.12)),wrist+Vector((s*.54,2.52,-1.44)),root+Vector((s*.55,2.12,-.5)),root+Vector((0,1.26,-.4))]
  digits=[]
  for j in range(4):
   name=pre+'_digit'+str(j);c.bone(name,wrist,tips[j],fore);digits.append(name);mid=wrist.lerp(tips[j],.48)+Vector((0,-.06,.08));c.tube('Metacarpal_'+name,[wrist,mid,tips[j]],[.049,.032,.008],[fore,name,name],'skin',sides=10,sub=3)
  for j in range(4):
   vs=[];uv=[];ww=[];ff=[]
   for row in range(11):
    t=row/10
    for col in range(9):
     u=col/8;edge=tips[j].lerp(tips[j+1],u);edge+=(wrist-edge).normalized()*(.18*sin(pi*u));p=wrist.lerp(edge,t);p.z-=.06*sin(pi*t)*sin(pi*u);vs.append(p);uv.append((t,u))
     if j<3:ww.append({fore:1-t,digits[j]:t*(1-u),digits[j+1]:t*u})
     else:ww.append({fore:1-t,digits[j]:t*(1-u),'chest':t*u})
   for row in range(10):
    for col in range(8):q=row*9+col;ff.append((q,q+1,q+10,q+9))
   ob=c.mesh('Anatomically_attached_membrane',vs,ff,uv,ww,'wing_skin');sol=ob.modifiers.new('Membrane_thickness','SOLIDIFY');sol.thickness=.005;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=sol.name)
  # Trailing membrane attaches to the trunk rather than ending at a floating fan.
  c.mesh('Axillary_membrane',[root,wrist,tips[3],tips[4],root+Vector((0,.65,-.2))],[(0,1,2),(0,2,3),(0,3,4)],[(0,0),(1,0),(1,1),(.4,1),(0,1)],['chest',fore,digits[3],'chest','chest'],'wing_skin')

def dragon(c):
 c.dragon();mat(c,'charred_keratin',(.055,.039,.025),0,.38);skin_shader(c.mats['charred_keratin'],False)
 for ob in c.parts:
  if ob.name.startswith(('main_horn','cheek_spur','dorsal_spine')):ob.data.materials.clear();ob.data.materials.append(c.mats['charred_keratin'])
 discard(c,['skull','mandible','socket','eye','pupil','brow','nostril','fang','lower_fang','wingL','wingR','mouth_cavity'])
 mat(c,'dermis',(.085,.027,.014),0,.60);skin_shader(c.mats['dermis']);mat(c,'oral',(.115,.025,.018),0,.65);mat(c,'wing_skin',(.045,.022,.018),0,.62);skin_shader(c.mats['wing_skin'],False)
 c.tube('Reworked_skull',[(0,-2.31,2.44),(0,-2.58,2.52),(0,-2.93,2.44),(0,-3.28,2.39),(0,-3.60,2.35)],[.22,.365,.29,.205,.15],['head']*5,sides=24,sub=4,ellipse=.75)
 c.tube('Reworked_jaw',[(0,-2.43,2.18),(0,-2.72,2.06),(0,-3.2,2.10),(0,-3.58,2.14)],[.215,.215,.145,.085],['jaw']*4,'dermis',sides=16,sub=4,ellipse=.45)
 for s in [-1,1]:
  c.ell('Temporal_mass',(s*.24,-2.56,2.45),(.16,.20,.15),'head')
  c.tube('Orbital_ridge',[(s*.22,-2.99,2.61),(s*.35,-2.77,2.635),(s*.28,-2.50,2.69)],[.037,.054,.018],['head']*3,sides=10,sub=3)
  c.ell('Shoulder_muscle',(s*.50,-.48,1.63),(.34,.44,.36),'chest');c.ell('Thigh_muscle',(s*.51,.90,1.38),(.35,.42,.36),'hindL' if s<0 else 'hindR')
  c.tube('Forearm_tendon',[(s*.96,-.10,.90),(s*.93,-.55,.45),(s*.89,-.72,.29)],[.08,.05,.035],['frontL_shin' if s<0 else 'frontR_shin']*3,sides=8,sub=3)
 organic=[o for o in c.parts if o.name.startswith(('torso_neck','Temporal_mass','Orbital_ridge','Reworked_skull','Shoulder_muscle','Thigh_muscle','Forearm_tendon','frontL','frontR','hindL','hindR','tail')) and not ('claw' in o.name or 'spine' in o.name)]
 fuse_body(c,organic)
 for s in [-1,1]:
  c.ell('Jaw_hinge',(s*.24,-2.47,2.20),(.09,.13,.075),'jaw','dermis',rings=10,sides=14)
  c.ell('Eye_socket',(s*.305,-2.74,2.57),(.035,.085,.064),'head','black',rings=10,sides=16);c.ell('Amber_iris',(s*.334,-2.77,2.57),(.032,.047,.038),'head','eye',rings=12,sides=16);c.ell('Vertical_pupil',(s*.361,-2.78,2.57),(.009,.013,.031),'head','black',rings=8,sides=10)
  lid='lidL' if s<0 else 'lidR';c.bone(lid,(s*.33,-2.77,2.59),(s*.33,-2.77,2.67),'head')
  pts=[(s*.352,-2.77+.068*cos(a),2.57+.047*sin(a)) for a in [pi*i/8 for i in range(9)]];c.tube('Upper_eyelid',pts,[.012]*9,[lid]*9,'dermis',sides=6,sub=1)
  pts=[(s*.350,-2.77+.068*cos(a),2.57-.041*sin(a)) for a in [pi*i/8 for i in range(9)]];c.tube('Lower_eyelid',pts,[.009]*9,['head']*9,'dermis',sides=6,sub=1)
  c.ell('Nasal_opening',(s*.135,-3.43,2.44),(.033,.062,.019),'head','black',rings=8,sides=10)
  for row in [0,1]:
   for j in range(10):
    y=-2.70-j*.079;w=.205-j*.007;length=.14 if j in [1,6] else .062+.015*sin(j*1.3);z=2.22 if row==0 else 2.105;sign=-1 if row==0 else 1;bone='head' if row==0 else 'jaw'
    c.horn('Individually_shaped_tooth',(s*w,y,z),(s*(w-.009),y-.012,z+sign*length*.7),(s*(w-.017),y-.028,z+sign*length),.018 if j not in [1,6] else .025,bone,'tooth')
  for row,bone,z in [(0,'head',2.217),(1,'jaw',2.10)]:c.tube('Gingival_margin',[(s*.22,-2.60,z),(s*.20,-2.98,z),(s*.13,-3.47,z)],[.025,.022,.015],[bone]*3,'oral',sides=8,sub=4)
 c.ell('Dark_oral_cavity',(0,-2.96,2.177),(.178,.42,.057),'head','black');c.ell('Palate',(0,-3.0,2.194),(.145,.35,.022),'head','oral');c.ell('Tongue',(0,-2.96,2.10),(.105,.29,.020),'jaw','oral')
 dragon_wings(c)
 return c

def shell(c,name,center,width,depth,height,bone,matname='ceramic',taper=.72):
 # Chamfered, tapered manufactured casing; flat planes and bevelled edges.
 vs=[];uv=[];ff=[];levels=[0,.08,.22,.80,.94,1];profile=[(-.78,-1),(.78,-1),(1,-.68),(1,.68),(.78,1),(-.78,1),(-1,.68),(-1,-.68)];sides=8
 for j,t in enumerate(levels):
  z=center[2]+height*(t-.5);r=width*.5*(taper+(1-taper)*sin(t*pi*.68+.32));d=depth*.5*(.88+.12*sin(pi*t))
  for i,(x,y) in enumerate(profile):vs.append((center[0]+r*x,center[1]+d*y,z));uv.append((i/sides,t))
 for j in range(len(levels)-1):
  for i in range(sides):q=j*sides+i;ff.append((q,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,q+sides))
 ff.extend([tuple(range(sides-1,-1,-1)),tuple((len(levels)-1)*sides+i for i in range(sides))]);ob=c.mesh(name,vs,ff,uv,[bone]*len(vs),matname,False)
 bevel=ob.modifiers.new('Machined_edge_chamfer','BEVEL');bevel.width=min(width,depth,height)*.035;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.25;bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=bevel.name)
 return ob

def mech(c):
 mat(c,'steel',(.055,.064,.078),.88,.31);mat(c,'ceramic',(.028,.046,.051),.55,.45);mat(c,'joint',(.021,.026,.03),.5,.59);mat(c,'copper',(.22,.11,.046),.78,.34);mat(c,'optic',(.025,.12,.19),.2,.18);mat(c,'warning',(.42,.12,.022),.35,.5)
 for n in ['steel','ceramic','joint','copper']:skin_shader(c.mats[n],False)
 shell(c,'Thoracic_chassis',(0,.01,2.30),.88,.43,.73,'chest','steel');shell(c,'Forged_chest_shell',(0,-.15,2.32),.91,.34,.68,'chest','ceramic',.68)
 c.tube('Spine_actuator',[(0,.19,1.60),(0,.23,2.03),(0,.18,2.63)],[.12,.115,.105],['pelvis','chest','chest'],'joint',sides=12,sub=2)
 shell(c,'Pelvic_yoke',(0,0,1.59),.71,.42,.39,'pelvis','steel');c.ell('Waist_bearing',(0,0,1.92),(.23,.20,.15),'pelvis','joint',rings=10,sides=16)
 for j in range(4):shell(c,'Abdominal_lamella',(0,-.23,1.89+j*.064),.48,.12,.092,'pelvis' if j<2 else 'chest','steel')
 shell(c,'Sensor_head',(0,-.05,3.16),.42,.32,.40,'head','ceramic',.81);c.tube('Neck_gimbal',[(0,0,2.67),(0,-.02,2.9),(0,-.04,3.06)],[.11,.087,.10],['chest','neck1','head'],'joint',sides=12,sub=2)
 c.ell('Central_sensor_recess',(0,-.22,3.22),(.165,.026,.042),'head','joint',rings=12,sides=16)
 c.ell('Central_optical_lens',(0,-.244,3.22),(.140,.026,.020),'head','optic',rings=12,sides=16)
 shell(c,'Brow_armour',(0,-.245,3.29),.34,.055,.065,'head','steel',.91)
 shell(c,'Sternal_service_panel',(0,-.339,2.33),.27,.05,.36,'chest','steel',.9)
 for ss in [-1,1]:
  shell(c,'Pectoral_panel',(ss*.27,-.305,2.41),.27,.075,.30,'chest','ceramic',.86)
  for jj in range(4):shell(c,'Radiator_vent',(ss*.28,-.35,2.19+jj*.047),.19,.028,.018,'chest','joint',.98)
  c.tube('Panel_retaining_fastener',[(ss*.112,-.37,2.46),(ss*.112,-.38,2.46)],[.018,.018],['chest']*2,'steel',sides=6,sub=1)
 shell(c,'Optic_side_armour',(0,.015,3.18),.43,.35,.26,'head','steel',.75)
 for s in [-1,1]:
  c.ell('Optical_lens',(s*.108,-.223,3.08),(.024,.016,.022),'head','optic',rings=10,sides=14);c.ell('Lens_recess',(s*.108,-.212,3.08),(.036,.018,.034),'head','joint',rings=10,sides=14)
  a='armL' if s<0 else 'armR';f=a+'_fore';h=a+'_hand';leg='hindL' if s<0 else 'hindR';shin=leg+'_shin';foot=leg+'_foot'
  for name,pos,r,bone in [('Shoulder',(s*.58,0,2.50),.18,a),('Elbow',(s*.95,-.01,1.94),.12,f),('Hip',(s*.28,0,1.50),.145,leg),('Knee',(s*.36,-.07,.86),.12,shin),('Ankle',(s*.32,.08,.27),.095,foot)]:
   c.ell(name+'_bearing',pos,(r,r*.91,r),bone,'joint',rings=10,sides=16)
   c.tube(name+'_axle',[Vector(pos)+Vector((-r,0,0)),Vector(pos)+Vector((r,0,0))],[r*.6,r*.6],[bone]*2,'steel',sides=14,sub=1)
  c.tube('Humeral_frame',[(s*.60,.045,2.45),(s*.81,.055,2.2),(s*.93,.045,2.0)],[.07,.068,.05],[a]*3,'steel',sides=12,sub=2)
  c.tube('Ulna_frame',[(s*.95,.02,1.94),(s*1.01,.015,1.63),(s*1.02,-.10,1.39)],[.067,.055,.043],[f]*3,'steel',sides=12,sub=2)
  c.ell('Wrist_gimbal',(s*1.02,-.10,1.38),(.070,.068,.063),h,'joint',rings=8,sides=12)
  c.tube('Wrist_link',[(s*1.02,-.10,1.39),(s*1.055,-.12,1.27)],[.050,.045],[h]*2,'steel',sides=10,sub=2)
  shell(c,'Upper_arm_shell',(s*.78,-.015,2.24),.25,.27,.34,a,'ceramic',.77);shell(c,'Forearm_shell',(s*.99,-.085,1.66),.23,.28,.40,f,'ceramic',.68)
  shell(c,'Shoulder_guard',(s*.61,-.005,2.59),.41,.39,.21,a,'ceramic',.78)
  c.tube('Femoral_frame',[(s*.29,.05,1.44),(s*.34,.03,1.16),(s*.35,-.03,.91)],[.09,.07,.065],[leg]*3,'steel',sides=12,sub=2)
  shell(c,'Thigh_shell',(s*.33,-.025,1.20),.28,.30,.36,leg,'ceramic',.78);shell(c,'Shin_shell',(s*.33,.015,.57),.24,.25,.40,shin,'ceramic',.66)
  c.tube('Leg_hydraulic_ram',[(s*.39,.12,1.32),(s*.40,.14,.94)],[.038,.028],[leg]*2,'steel',sides=10,sub=2);c.tube('Ankle_piston',[(s*.41,.12,.69),(s*.40,.13,.31)],[.025,.02],[shin]*2,'steel',sides=8,sub=2)
  c.tube('Arm_service_hose',[(s*.69,.15,2.42),(s*.87,.21,2.10),(s*1.05,.14,1.62)],[.025,.028,.025],[a,a,f],'joint',sides=8,sub=3)
  shell(c,'Heel_chassis',(s*.34,.015,.19),.29,.39,.22,foot,'steel',.85);shell(c,'Articulated_forefoot',(s*.35,-.22,.11),.31,.40,.17,foot,'ceramic',.9)
  c.tube('Ankle_bellows',[(s*.32,.08,.24),(s*.32,.08,.34)],[.105,.10],[foot,shin],'joint',sides=12,sub=2)
  shell(c,'Palm',(s*1.055,-.12,1.205),.20,.105,.19,h,'steel',.84)
  for j in range(5):
   x=s*(.985+j*.044) if j<4 else s*.92;y=-.12 if j<4 else -.14;z=1.15 if j<4 else 1.25;p0=Vector((x,y,z));p1=p0+Vector((s*.007,-.01,-.095));p2=p1+Vector((0,-.035,-.079));p3=p2+Vector((0,-.028,-.049));names=[]
   for k,(v,w) in enumerate([(p0,p1),(p1,p2),(p2,p3)]):
    b=a+'_finger'+str(j)+'_'+str(k);c.bone(b,v,w,h if k==0 else names[-1]);names.append(b);c.tube('Finger_phalanx',[v,w],[.021,.017],[b]*2,'steel',sides=8,sub=1);c.ell('Finger_knuckle',v,(.025,.022,.022),b,'joint',rings=5,sides=8)
  # Integrated shoulder turret with separate heat guard and recoil sled.
  turret='turretL' if s<0 else 'turretR';c.bone(turret,(s*.53,.18,2.58),(s*.53,-.48,2.58),'chest')
  slide=turret+'_recoil';c.bone(slide,(s*.53,.08,2.60),(s*.53,-.48,2.60),turret)
  shell(c,'Turret_housing',(s*.53,.18,2.58),.26,.30,.25,'chest','steel')
  for j in range(3):
   x=s*(.47+j*.061);c.tube('Rotary_barrel',[(x,.08,2.60),(x,-.36,2.60),(x,-.48,2.60)],[.028,.027,.033],[slide]*3,'steel',sides=10,sub=1)
  for j in range(5):c.tube('Cooling_fin',[(s*.37,.29,2.10+j*.085),(s*.68,.29,2.10+j*.085)],[.018,.018],['chest']*2,'steel',sides=6,sub=1)
  c.tube('Power_bus',[(s*.29,.26,2.45),(s*.28,.30,2.14),(s*.24,.25,1.93)],[.018,.018,.018],['chest']*3,'copper',sides=8,sub=2)
 for j in range(6):shell(c,'Service_rib',(0,.25,2.05+j*.07),.41,.08,.028,'chest','steel')
 shell(c,'Battery_module',(0,.34,2.33),.38,.20,.42,'chest','joint');shell(c,'Battery_latch',(0,.45,2.40),.23,.032,.075,'chest','warning')
 return c

def assemble(c):
 # Model geometry and new bones inherit the original V3 rig/rest scale.
 dragonlike=c.name=='Cinder_Crown';warp=lambda v:Vector((v.x*1.05,v.y,v.z*1.02)) if dragonlike else Vector(v)
 for o in c.parts:
  for v in o.data.vertices:v.co=warp(v.co)
 bpy.context.view_layer.objects.active=c.rig;bpy.ops.object.mode_set(mode='EDIT')
 for n,(h,t,parent) in c.bones.items():
  if n in c.rig.data.edit_bones:continue
  b=c.rig.data.edit_bones.new(n);b.head=warp(Vector(h));b.tail=warp(Vector(t));b.parent=c.rig.data.edit_bones[parent]
 bpy.ops.object.mode_set(mode='OBJECT')
 for o in c.parts:o.parent=c.rig
 bpy.ops.object.select_all(action='DESELECT')
 for o in c.parts:o.select_set(True)
 bpy.context.view_layer.objects.active=c.parts[0];bpy.ops.object.join();c.meshobj=bpy.context.object;c.meshobj.name='CreatureMesh';mod=c.meshobj.modifiers.new('Skin','ARMATURE');mod.object=c.rig
 bpy.context.view_layer.objects.active=c.meshobj;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.08,island_margin=.008);bpy.ops.object.mode_set(mode='OBJECT')
 return c

def build(name):
 idx=0 if name=='Cinder_Crown' else 15;cat='dragons' if idx==0 else 'bosses';src=OLD/cat/name;bpy.ops.wm.open_mainfile(filepath=str(src/(name+'.blend')));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 for o in list(bpy.context.scene.objects):
  if o!=rig:bpy.data.objects.remove(o,do_unlink=True)
 rig.animation_data.action=None
 for track in rig.animation_data.nla_tracks:track.mute=True
 for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 bpy.context.scene.frame_set(1);c=Creature(ROSTER[idx],idx);c.rig=rig;c.parts=[]
 if idx==15:c.bones={b.name:(tuple(b.head_local),tuple(b.tail_local),b.parent.name if b.parent else None) for b in rig.data.bones}
 dragon(c) if idx==0 else mech(c);assemble(c)
 return c
