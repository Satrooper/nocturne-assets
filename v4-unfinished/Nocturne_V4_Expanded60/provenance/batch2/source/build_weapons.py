import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector
from types import SimpleNamespace
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'source'));from texture_bake import bake
(P/'textures').mkdir(exist_ok=True);(P/'weapons').mkdir(exist_ok=True)

def material(name,color,metal,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=180;noise.inputs['Detail'].default_value=2;coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Object'],noise.inputs['Vector']);r=n.new('ShaderNodeMapRange');r.inputs['To Min'].default_value=rough*.83;r.inputs['To Max'].default_value=min(1,rough*1.2);l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],b.inputs['Roughness']);return m

def part(name,vertices,faces,mat,bone,bevel=.002):
 me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(mats[mat]);o.vertex_groups.new(name=bone).add(list(range(len(vertices))),1,'REPLACE');parts.append(o);bpy.context.view_layer.objects.active=o
 if bevel:
  mod=o.modifiers.new('Manufactured_edge','BEVEL');mod.width=bevel;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o

def profile(name,poly,width,mat='coat',bone='weapon_root',x=0,bevel=.002):
 # Purpose-shaped silhouette in the longitudinal Y/Z plane, extruded across X.
 vs=[(x+s*width/2,y,z) for s in [-1,1] for y,z in poly];n=len(poly);ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];return part(name,vs,ff,mat,bone,bevel)

def box(name,center,size,mat='steel',bone='weapon_root',bevel=.001):
 x,y,z=center;w,d,h=size;return profile(name,[(y-d/2,z-h/2),(y+d/2,z-h/2),(y+d/2,z+h/2),(y-d/2,z+h/2)],w,mat,bone,x,bevel)

def cylinder(name,a,b,r,mat='steel',bone='weapon_root',inner=0,sides=24):
 a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
 if u.length<.01:u=axis.cross(Vector((1,0,0)))
 u.normalize();v=axis.cross(u);vs=[]
 for p in [a,b]:
  for rr in [r,inner or r*.5]:
   for i in range(sides):vs.append(p+rr*(u*math.cos(i*2*math.pi/sides)+v*math.sin(i*2*math.pi/sides)))
 ff=[]
 for i in range(sides):
  j=(i+1)%sides;ff.extend([(i,j,2*sides+j,2*sides+i),(sides+i,3*sides+i,3*sides+j,sides+j),(i,sides+i,sides+j,j),(2*sides+i,2*sides+j,3*sides+j,3*sides+i)])
 return part(name,vs,ff,mat,bone,.0005)

def pistol():
 profile('Forged_slide',[(-.205,.115),(-.205,.146),(-.19,.168),(.045,.168),(.065,.148),(.065,.119)],.031,'coat','slide')
 profile('Frame_dustcover',[(-.185,.095),(-.185,.115),(.056,.115),(.05,.08),(.018,.068),(-.035,.081)],.029)
 profile('Grip_backstrap',[(.045,.092),(.078,-.09),(.050,-.113),(.011,-.098),(-.015,.076)],.029,'polymer')
 for s in [-1,1]:
  profile('Recessed_grip_insert',[(.037,.073),(.066,-.074),(.047,-.093),(.020,-.08),(-.003,.07)],.003,'rubber',x=s*.0155)
  for j in range(11):box('Grip_traction',(s*.017,.033+j*.002,.059-j*.012),(.002,.027,.002),'polymer')
  for j in range(7):box('Slide_serration',(s*.016,.022+j*.005,.139),(.0016,.0018,.036),'steel','slide',.0003)
  cylinder('Frame_pin',(s*.015,.013,.084),(s*.017,.013,.084),.004,'steel')
 profile('Trigger_guard',[(-.019,.081),(-.074,.077),(-.082,.03),(-.068,.013),(.013,.014),(.019,.03),(-.062,.025),(-.070,.035),(-.064,.068),(-.017,.069)],.009)
 profile('Trigger',[(-.02,.071),(-.029,.063),(-.025,.034),(-.017,.034),(-.02,.055),(-.013,.068)],.009,'steel','trigger')
 cylinder('Barrel_bore',(0,-.222,.138),(0,-.164,.138),.010,'steel','weapon_root',.006)
 box('Front_sight',(0,-.17,.174),(.006,.012,.010),'steel','slide');box('Rear_sight',(0,.041,.177),(.025,.008,.013),'steel','slide')
 box('Sight_inlay',(0,-.176,.177),(.002,.001,.004),'sight','slide',0)
 box('Ejection_port',(0,-.018,.169),(.019,.034,.0015),'steel','slide',.0003)
 box('Slide_stop',(-.020,.001,.091),(.005,.022,.006),'steel')
 profile('Detachable_magazine',[(.021,.05),(.060,-.105),(.038,-.110),(-.003,.05)],.022,'steel','magazine')
 box('Magazine_floorplate',(.0,.047,-.113),(.032,.035,.012),'polymer','magazine')
 return {'muzzle':(0,-.225,.138),'grip':(0,.014,0),'support':(0,-.055,.068),'holster':(0,0,.07)}

def rifle():
 profile('Upper_receiver',[(-.29,.122),(-.31,.145),(-.285,.187),(.075,.187),(.099,.161),(.085,.12)],.053)
 profile('Lower_receiver',[(-.18,.12),(.069,.12),(.065,.063),(-.018,.048),(-.033,.095),(-.17,.091)],.047)
 profile('Angled_grip',[(.057,.077),(.09,-.085),(.061,-.104),(.024,-.079),(.014,.066)],.035,'polymer')
 profile('Stock_strut',[(.09,.174),(.34,.154),(.36,.105),(.12,.110)],.027,'steel')
 profile('Adjustable_buttstock',[(.21,.159),(.355,.163),(.385,.145),(.383,.003),(.352,-.004),(.332,.068),(.210,.103)],.045,'polymer')
 box('Shoulder_pad',(0,.389,.075),(.050,.012,.152),'rubber');box('Cheek_rest',(0,.29,.164),(.055,.13,.023),'polymer')
 profile('Free_float_handguard',[(-.48,.103),(-.485,.171),(-.30,.177),(-.285,.112)],.057)
 cylinder('Barrel',(0,-.59,.138),(0,-.31,.138),.012,'steel',inner=.0045)
 cylinder('Muzzle_brake',(0,-.635,.138),(0,-.58,.138),.019,'steel',inner=.006)
 for s in [-1,1]:
  for j in range(7):box('Handguard_recess',(s*.030,-.325-j*.020,.142),(.001,.013,.026),'rubber',bevel=.001)
  for j in range(3):box('Brake_port',(s*.020,-.593-j*.012,.138),(.001,.006,.017),'rubber',bevel=.0004)
  cylinder('Receiver_pin',(s*.024,.002,.11),(s*.027,.002,.11),.004)
 box('Ejection_chamber',(.027,-.08,.153),(.002,.085,.022),'steel','bolt')
 box('Charging_handle',(0,.087,.167),(.072,.01,.012),'steel','bolt')
 for j in range(33):box('Accessory_rail',(0,-.467+j*.017,.191),(.032,.006,.006),'steel',bevel=.0008)
 profile('Magazine_well',[(-.17,.1),(-.08,.1),(-.075,.047),(-.156,.047)],.046)
 profile('Curved_magazine',[(-.15,.077),(-.09,.077),(-.10,-.14),(-.131,-.207),(-.180,-.190),(-.155,-.12)],.030,'polymer','magazine')
 for s in [-1,1]:
  for j in range(3):box('Magazine_channel',(s*.016,-.112-j*.012,-.045),(.001,.004,.14),'rubber','magazine')
 profile('Trigger_guard',[(-.012,.058),(-.047,.058),(-.054,.015),(.029,.007),(.036,.023),(-.043,.026),(-.038,.048),(-.012,.048)],.011)
 profile('Trigger',[(-.012,.058),(-.022,.048),(-.016,.025),(-.009,.024),(-.013,.046),(-.005,.057)],.01,'steel','trigger')
 box('Optic_mount',(0,-.04,.21),(.04,.081,.024),'steel')
 cylinder('Sealed_optic',(0,-.10,.245),(0,-.005,.245),.025,'coat',inner=.018)
 cylinder('Optic_front_glass',(0,-.101,.245),(0,-.103,.245),.018,'glass',inner=.00001)
 box('Front_sight',(0,-.45,.219),(.012,.018,.044),'steel');box('Sling_lug',(.034,.28,.12),(.008,.025,.018),'steel')
 return {'muzzle':(0,-.638,.138),'grip':(0,.028,0),'support':(0,-.37,.103),'holster':(0,.20,.1)}

def sword():
 # Lenticular blade cross section with a fuller and continuous distal taper.
 stations=[(-.18,.039),(-.28,.041),(-.76,.031),(-1.12,.019),(-1.28,.001)];vs=[]
 for y,w in stations:
  vs.extend([(-w,y,.0),(-w*.55,y,.007),(-w*.22,y,.004),(w*.22,y,.004),(w*.55,y,.007),(w,y,0),(w*.55,y,-.007),(w*.22,y,-.004),(-w*.22,y,-.004),(-w*.55,y,-.007)])
 faces=[]
 for j in range(4):
  for i in range(10):faces.append((j*10+i,j*10+(i+1)%10,(j+1)*10+(i+1)%10,(j+1)*10+i))
 faces.extend([tuple(range(9,-1,-1)),tuple(range(40,50))]);part('Distal_tapered_fullered_blade',vs,faces,'blade','weapon_root',.0005)
 profile('Swept_crossguard',[(-.18,-.019),(-.16,-.019),(-.16,.019),(-.18,.019)],.245,'steel',bevel=.003)
 for s in [-1,1]:profile('Guard_quillon',[(-.20,-.012),(-.16,-.012),(-.11,.012),(-.12,.025),(-.18,.022)],.043,'steel',x=s*.11)
 cylinder('Grip_core',(0,-.15,0),(0,.055,0),.019,'rubber',sides=16)
 for j in range(15):cylinder('Leather_binding',(0,-.142+j*.012,0),(0,-.137+j*.012,0),.020,'polymer',inner=.018,sides=16)
 cylinder('Grip_ferrule',(0,-.158,0),(0,-.14,0),.024,'steel');cylinder('Pommel',(0,.049,0),(0,.079,0),.031,'steel',sides=16)
 return {'muzzle':(0,-1.28,0),'grip':(0,-.045,0),'support':(0,.018,0),'holster':(0,-.17,0),'blade_base':(0,-.19,0),'blade_tip':(0,-1.28,0)}

def camera(location,target,scale):
 bpy.ops.object.camera_add(location=location);cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;bpy.context.scene.camera=cam;return cam

def lighting():
 scene=bpy.context.scene;scene.world.color=(.18,.18,.18);scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1100;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
 for loc,power,size in [((2,-2,3),220,3),((-2,-1,1),150,2),((0,2,3),280,2)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()

for name,builder in [('Vesper_Pistol',pistol),('Bastion_Rifle',rifle),('Gravesong_Sword',sword)]:
 bpy.ops.wm.read_factory_settings(use_empty=True);parts=[];mats={key:material(key,color,metal,rough) for key,color,metal,rough in [('coat',(.025,.032,.039),.7,.38),('steel',(.15,.17,.19),.95,.27),('blade',(.28,.31,.34),1,.23),('polymer',(.055,.061,.047),0,.60),('rubber',(.012,.014,.013),0,.8),('glass',(.035,.13,.15),.25,.1),('sight',(.55,.64,.42),0,.3)]};sockets=builder();folder=P/'weapons'/name;folder.mkdir(exist_ok=True)
 bpy.ops.object.armature_add();rig=bpy.context.object;rig.name=name+'_Rig';bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones;eb.remove(eb[0]);root=eb.new('weapon_root');root.head=(0,0,0);root.tail=(0,0,.06)
 for bone,head in [('slide',(0,0,.138)),('bolt',(0,-.03,.15)),('magazine',(0,.02,-.05)),('trigger',(0,-.02,.06))]+list(sockets.items()):
  b=eb.new(bone);b.head=head;b.tail=Vector(head)+Vector((0,0,.025));b.parent=root
 bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();mesh=bpy.context.object;mesh.name=name;mesh.parent=rig;mod=mesh.modifiers.new('Weapon_components','ARMATURE');mod.object=rig
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'_Authoring.blend')))
 c=SimpleNamespace(name=name,meshobj=mesh);images=bake(c,P,size=1024)
 for im in images.values():im.filepath='//../../textures/'+Path(im.filepath_raw).name
 actions=[];fps=30;bpy.context.scene.render.fps=fps
 if 'Sword' not in name:
  for clip,duration in [('Mechanical_Fire',.4),('Mechanical_Reload',2.4)]:
   act=bpy.data.actions.new(clip);act.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=act
   for i in range(round(duration*fps)+1):
    t=i/fps
    for b in rig.pose.bones:b.location=(0,0,0);b.rotation_mode='XYZ';b.rotation_euler=(0,0,0)
    if 'Fire' in clip:
     amount=max(0,1-abs(t-.06)/.06);rig.pose.bones['slide' if 'Pistol' in name else 'bolt'].location.y=.034*amount;rig.pose.bones['trigger'].rotation_euler.x=.18*amount
    else:
     # Visible magazine removal/insertion only; no player-hand animation or physical magazine drop.
     amount=max(0,min(1,(t-.25)/.30,(1.85-t)/.35));rig.pose.bones['magazine'].location.z=-.16*amount;rig.pose.bones['magazine'].location.y=.025*amount
     amount=max(0,1-abs(t-2.08)/.12);rig.pose.bones['slide' if 'Pistol' in name else 'bolt'].location.y=.034*amount
    for b in rig.pose.bones:
     if b.name in ['slide','bolt','magazine','trigger']:b.location=rig.data.bones[b.name].matrix_local.to_3x3().inverted()@b.location;b.keyframe_insert('location',frame=i+1);b.keyframe_insert('rotation_euler',frame=i+1)
   actions.append({'name':act.name,'duration_s':duration,'root_motion':False,'type':'weapon_mechanism_only','events':[{'time_s':.06,'event':'mechanical_rearward_peak'}] if 'Fire' in clip else [{'time_s':.55,'event':'magazine_removed'},{'time_s':1.85,'event':'magazine_seated'},{'time_s':2.08,'event':'action_retracted'}],'hit_window_validated':False})
 rig.animation_data_create();rig.animation_data.action=None
 for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0)
 bpy.context.scene.frame_set(1);bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
 bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_yup=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')))
 tris=sum(len(p.vertices)-2 for p in mesh.data.polygons)
 for level,ratio in [(1,.6),(2,.3)]:
  d=mesh.modifiers.new('LOD','DECIMATE');d.ratio=ratio;bpy.ops.export_scene.fbx(filepath=str(folder/(name+'_LOD'+str(level)+'.fbx')),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y');mesh.modifiers.remove(d)
 (folder/'asset.json').write_text(json.dumps({'name':name,'status':'new_weapon_gap_asset','design':'original authored mesh; no external franchise assets','triangles':tris,'units':'metres','authoring_axes':'Z up, muzzle/blade along -Y, grip origin near world origin','sockets':{k:{'bone':k,'position_weapon_local_m':v} for k,v in sockets.items()},'clips':actions,'lod_ratios':[1,.6,.3],'attachment':'Parent weapon_root to player hand socket with an asset-specific calibrated offset. Socket alignment and two-hand grips require player animation work. Do not assume identity transform.','texture_maps':['basecolor','roughness','metallic','normal'],'engine_tested':False,'limitations':['Weapons have not been aligned to player hands or holster poses.','Magazine animation uses a bone; engine must spawn/drop a separate magazine if desired.','Baked material atlas consolidates material slots; authoring source preserves separate metal, coating and polymer materials.','No cloth simulation, projectile, damage or ammunition logic.']},indent=2))
 print('BUILT',name,tris,flush=True)
