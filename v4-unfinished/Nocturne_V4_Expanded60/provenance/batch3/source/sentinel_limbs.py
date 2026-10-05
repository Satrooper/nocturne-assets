import bpy,bmesh,json,math,sys
from pathlib import Path
from mathutils import Vector
from types import SimpleNamespace
P=Path(__file__).resolve().parents[1]; BASE=P.parent/'restored/nocturne-v4-batch02';sys.path.insert(0,str(P/'source'))
from texture_bake import bake
bpy.ops.wm.open_mainfile(filepath=str(BASE/'bosses/Siege_Sentinel/Siege_Sentinel_Authoring.blend'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=True
for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
bpy.context.view_layer.update()
original={b.name:[list(r) for r in b.matrix_local] for b in rig.data.bones}
removed={g.index for g in mesh.vertex_groups if g.name.startswith(('armL','armR','hindL','hindR')) or g.name=='pelvis'}
indices={v.index for v in mesh.data.vertices if any(g.group in removed and g.weight>.5 for g in v.groups)}
bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in indices],context='VERTS');bm.to_mesh(mesh.data);bm.free()
parts=[mesh];materials={}
def mat(n,c,metal,rough):
 m=bpy.data.materials.new(n);m.use_nodes=True;ns=m.node_tree.nodes;bs=ns.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 # Spatially varying roughness and shallow machined grain, not texture enlargement.
 tc=ns.new('ShaderNodeTexCoord');noise=ns.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=180;noise.inputs['Detail'].default_value=2;m.node_tree.links.new(tc.outputs['Generated'],noise.inputs['Vector'])
 ramp=ns.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(max(.08,rough-.10),)*3+(1,);ramp.color_ramp.elements[1].color=(min(.9,rough+.13),)*3+(1,);m.node_tree.links.new(noise.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs['Color'],bs.inputs['Roughness'])
 bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.0005;m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal']);materials[n]=m
mat('Graphite_enamel',(.030,.039,.044),.66,.40);mat('Steel_bearing',(.22,.25,.28),.95,.30);mat('Black_innerframe',(.012,.017,.022),.85,.48);mat('Bronze_bushing',(.21,.12,.045),.88,.33);mat('Sole_composite',(.014,.019,.019),.0,.80);mat('Identification_ochre',(.33,.105,.025),.35,.48)
def obj(n,vs,fs,bone,material,bevel=0):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();
 for poly in me.polygons:poly.use_smooth=len(poly.vertices)==4
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.matrix_world=mesh.matrix_world.copy();o.data.materials.append(materials[material]);o.vertex_groups.new(name=bone).add(list(range(len(vs))),1,'REPLACE')
 bpy.context.view_layer.objects.active=o
 if bevel:
  mod=o.modifiers.new('Machined_edge','BEVEL');mod.width=bevel;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=.6;bpy.ops.object.modifier_apply(modifier=mod.name)
 parts.append(o);return o

def basis(a,b):
 v=(Vector(b)-Vector(a)).normalized();u=Vector((1,0,0))-v*v.x
 if u.length<.01:u=v.cross(Vector((0,1,0)))
 u.normalize();return u,v.cross(u).normalized(),v

def tube(n,a,b,r1,r2,bone,material,sides=16):
 a,b=Vector(a),Vector(b);u,w,v=basis(a,b);vs=[tuple(p+(u*math.cos(i*2*math.pi/sides)+w*math.sin(i*2*math.pi/sides))*r) for p,r in [(a,r1),(b,r2)] for i in range(sides)];fs=[tuple(range(sides-1,-1,-1)),tuple(range(sides,2*sides))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)];return obj(n,vs,fs,bone,material,.003 if r1>.04 else 0)

def shell(n,a,b,sections,bone,material,offset=(0,0,0),arc=2.6,thickness=.014):
 # Curved open C section with a genuine inner surface and varied longitudinal profile.
 a,b=Vector(a)+Vector(offset),Vector(b)+Vector(offset);u,w,v=basis(a,b);N=12;vs=[]
 for inner in [False,True]:
  for t,width,depth in sections:
   for j in range(N):
    angle=-arc/2+arc*j/(N-1);radiusw=width-(thickness if inner else 0);radiusd=depth-(thickness if inner else 0);vs.append(tuple(a+(b-a)*t+u*math.sin(angle)*radiusw+w*math.cos(angle)*radiusd))
 K=len(sections)*N;fs=[]
 for skin in [0,1]:
  for k in range(len(sections)-1):
   for j in range(N-1):
    x=skin*K+k*N+j;f=(x,x+1,x+1+N,x+N);fs.append(f if skin==0 else f[::-1])
 for k in [0,len(sections)-1]:
  for j in range(N-1):x=k*N+j;fs.append((x,x+1,x+1+K,x+K))
 for j in [0,N-1]:
  for k in range(len(sections)-1):x=k*N+j;fs.append((x,x+N,x+N+K,x+K))
 return obj(n,vs,fs,bone,material,.005)

def hinge(n,p,r,width,bone):
 p=Vector(p)
 tube(n+'_through_axle',p+Vector((-width,0,0)),p+Vector((width,0,0)),r*.62,r*.62,bone,'Black_innerframe',20)
 for s in [-1,1]:
  x=s*width;tube(n+'_flange',p+Vector((x,0,0)),p+Vector((x+s*.017,0,0)),r,r,bone,'Steel_bearing',24)
  tube(n+'_bronze_retainer',p+Vector((x+s*.018,0,0)),p+Vector((x+s*.027,0,0)),r*.59,r*.59,bone,'Bronze_bushing',20)
  for i in range(6):
   ang=i*math.tau/6;c=p+Vector((x+s*.029,math.cos(ang)*r*.76,math.sin(ang)*r*.76));tube(n+'_fastener',c,c+Vector((s*.01,0,0)),.009,.009,bone,'Black_innerframe',6)

def limb(n,a,b,width,depth,bone):
 a,b=Vector(a),Vector(b);u,w,v=basis(a,b)
 tube(n+'_load_spine',a+(b-a)*.12,b-(b-a)*.12,width*.34,width*.28,bone,'Black_innerframe')
 for s in [-1,1]:tube(n+'_side_link',a+(b-a)*.16+u*s*width*.77,b-(b-a)*.14+u*s*width*.65,.026,.022,bone,'Steel_bearing')
 shell(n+'_formed_plate',a,b,[(.15,width*.83,depth*.80),(.27,width,depth),(.62,width*.87,depth*.92),(.84,width*.58,depth*.64)],bone,'Graphite_enamel')
 shell(n+'_edge_rail',a,b,[(.20,width*.89,depth*.87),(.23,width*.94,depth*.94),(.70,width*.76,depth*.83),(.73,width*.70,depth*.77)],bone,'Steel_bearing',arc=2.72,thickness=.012)
 # Distinct rear frame remains open; no solid cuboid filling the joint gap.
 tube(n+'_rear_bus',a+(b-a)*.23+w*depth*.60,b-(b-a)*.20+w*depth*.62,.028,.021,bone,'Black_innerframe')

for side,s in [('L',-1),('R',1)]:
 for stem,segment,w,d in [('arm','',.18,.15),('arm','_fore',.155,.14),('hind','',.21,.18),('hind','_shin',.175,.16)]:
  name=stem+side+segment;bone=rig.data.bones[name];limb(name,bone.head_local,bone.tail_local,w,d,name)
  hinge(name+'_joint',bone.head_local,w*.66,w*.82,name)
 # Shoulder cowl and knee/elbow strike surface profile are separate from inner frame.
 shoulder=rig.data.bones['arm'+side];shell('Deltoid_cowl',shoulder.head_local,shoulder.tail_local,[(0,.235,.205),(.15,.235,.205),(.30,.18,.16)],shoulder.name,'Graphite_enamel',arc=3.7)
 for stem,seg,r in [('arm','_fore',.14),('hind','_shin',.16)]:
  b=rig.data.bones[stem+side+seg];p=b.head_local; shell('Joint_front_guard',p+Vector((0,-.05,.12)),p+Vector((0,-.07,-.13)),[(0,r*.6,.045),(.30,r,.065),(.7,r*.9,.058),(1,r*.55,.042)],b.name,'Graphite_enamel',arc=2.3)
 hand=rig.data.bones['arm'+side+'_hand'];a,b=hand.head_local,hand.tail_local
 hinge('Wrist_yoke',a,.065,.075,hand.name);limb('Metacarpal',a,b,.105,.050,hand.name)
 for bn in rig.data.bones:
  if bn.name.startswith('arm'+side+'_finger'):
   tube('Articulated_phalanx',bn.head_local,bn.tail_local,.023,.017,bn.name,'Steel_bearing',10);hinge('Digit_pin',bn.head_local,.026,.023,bn.name)
 foot=rig.data.bones['hind'+side+'_foot'];p=foot.head_local;hinge('Ankle_bearing',p,.072,.11,foot.name)
 x=foot.tail_local.x
 # Heel-to-toe spars connect ankle bearing to flat ground pads, rest clearance 4.5mm world.
 for dx in [-.095,.095]:tube('Heel_load_yoke',p+Vector((dx,0,-.01)),(x+dx,.09,.10),.036,.032,foot.name,'Steel_bearing')
 shell('Instep_shell',(x,.14,.12),(x,-.28,.12),[(0,.11,.052),(.30,.16,.060),(.67,.15,.058),(1,.12,.045)],foot.name,'Graphite_enamel',arc=3.1)
 # Foot shell basis for horizontal axis would curve in world Z; sole built explicitly.
 vs=[(x+dx,y,z) for z in [.003,.035] for dx,y in [(-.15,.18),(.15,.18),(.17,-.23),(.11,-.39),(-.11,-.39),(-.17,-.23)]];N=6;fs=[tuple(range(5,-1,-1)),tuple(range(6,12))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)];obj('Ground_pad',vs,fs,foot.name,'Sole_composite',.004)
 for dx in [-.09,0,.09]:tube('Sole_load_rail',(x+dx,.10,.064),(x+dx,-.34,.064),.033,.030,foot.name,'Black_innerframe')
 for dx in [-.09,0,.09]:shell('Toe_cap',(x+dx,-.22,.09),(x+dx,-.38,.08),[(0,.041,.035),(.65,.040,.034),(1,.029,.022)],foot.name,'Steel_bearing',arc=3.2,thickness=.009)
# Load-bearing pelvis and actual waist connection retained through chest interface.
tube('Waist_rotary_column',(0,0,1.53),(0,0,2.07),.15,.13,'pelvis','Black_innerframe',24)
for z in [1.63,1.81,2.01]:tube('Waist_retaining_ring',(0,0,z),(0,0,z+.034),.20,.20,'pelvis','Steel_bearing',24)
for s in [-1,1]:
 p=Vector((s*.28,0,1.5));tube('Hip_suspension_cradle',(0,0,1.65),p,.095,.11,'pelvis','Steel_bearing');shell('Pelvis_flank_armour',p+Vector((0,0,.30)),p-Vector((0,0,.03)),[(0,.10,.13),(.35,.18,.18),(1,.12,.15)],'pelvis','Graphite_enamel',arc=2.7)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join();mesh=bpy.context.object
# Actual topology is changed, with shaped open shells and dedicated joint hardware.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.08,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
folder=P/'bosses/Siege_Sentinel';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Siege_Sentinel_Authoring.blend'))
tri=sum(len(f.vertices)-2 for f in mesh.data.polygons)
if tri>48000:
 d=mesh.modifiers.new('Game_triangle_budget','DECIMATE');d.ratio=47900/tri;bpy.context.view_layer.objects.active=mesh;bpy.ops.object.modifier_apply(modifier=d.name)
images=bake(SimpleNamespace(name='Siege_Sentinel_Batch03',meshobj=mesh),P,2048)
for im in images.values():im.source='FILE';im.filepath=str(P/'textures'/Path(im.filepath_raw).name);im.reload()
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(folder/'Siege_Sentinel.fbx'),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
bpy.ops.export_scene.gltf(filepath=str(folder/'Siege_Sentinel.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS')
for im in images.values():im.filepath='//../../textures/'+Path(im.filepath_raw).name
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Siege_Sentinel.blend'))
for level,ratio in [(1,.55),(2,.28)]:
 d=mesh.modifiers.new('LOD','DECIMATE');d.ratio=ratio;bpy.ops.export_scene.fbx(filepath=str(folder/f'Siege_Sentinel_LOD{level}.fbx'),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y');mesh.modifiers.remove(d)
meta=json.loads((BASE/'bosses/Siege_Sentinel/asset.json').read_text());meta['batch03_changes']=['Replaced every limb rigid component and pelvis with shaped open-section armour, load spars, bearing flanges, joint pins, wrist yokes, segmented fingers, ankle/heel links and ground pads.','Original 52 rest bones and 21 source actions preserved; these are retained actions, not new combat choreography.','New spatial roughness variation and shallow metal grain baked into four 2048 PBR maps.'];meta['triangles']=sum(len(p.vertices)-2 for p in mesh.data.polygons);meta['rig_bones']=len(rig.data.bones);meta['quality_status']='Mechanical limb geometry revision; stylized asset, AAA realism and motion polish unfinished';meta['texture_atlas']={'size':2048,'maps':['textures/Siege_Sentinel_Batch03_'+x+'.png' for x in images]};meta['engine_tested']=False;meta['iphone_tested']=False;(folder/'asset.json').write_text(json.dumps(meta,indent=2))
assert original=={b.name:[list(r) for r in b.matrix_local] for b in rig.data.bones}
print('BUILD_COMPLETE',meta['triangles'],meta['rig_bones'],flush=True)
