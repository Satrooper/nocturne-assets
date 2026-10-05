import bpy,bmesh,json,math,os,sys,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Euler
from mathutils.kdtree import KDTree
from types import SimpleNamespace
P=Path(__file__).resolve().parents[1];BASE=P.parent/'Nocturne_V4_Full_Pack';sys.path.insert(0,str(P/'provenance/batch2/source'))
from texture_bake import bake
ONLY=sys.argv[-1] if '--' in sys.argv else 'all'
ROSTER=json.loads((BASE/'asset_manifest.json').read_text())['characters']
COLORS={'Cinder_Crown':(.115,.073,.046),'Frost_Antler':(.24,.28,.28),'Storm_Wyvern':(.055,.068,.082),'Thornback':(.095,.12,.066),'Obsidian_Bastion':(.045,.046,.043),'Crimson_Vesper':(.14,.055,.045),'Sunken_Leviathan':(.055,.085,.085),'Dune_Glasswing':(.24,.17,.095),'Moonveil':(.105,.12,.145),'Iron_Seraph':(.10,.115,.12),'Root_Matriarch':(.105,.074,.040),'Horned_Regent':(.13,.072,.058),'Mirror_Colossus':(.14,.17,.17),'Cinder_Hound':(.10,.062,.036),'Crimson_Imp':(.12,.064,.048),'Sporeling':(.12,.11,.078),'Crypt_Arachnarch':(.050,.041,.032),'Crypt_Skitter':(.082,.061,.038),'Hundredleg':(.11,.083,.054),'Shard_Crab':(.16,.17,.145),'Abyss_Maw':(.065,.082,.08),'Razorfin':(.10,.12,.095),'Bamboo_Mantis':(.10,.13,.065),'Moon_Bat':(.11,.085,.075)}
def persist(f,data):
 with f.open('w') as h:json.dump(data,h,indent=2);h.flush();os.fsync(h.fileno())
def reset(r):
 r.animation_data.action=None
 for t in r.animation_data.nla_tracks:t.mute=True
 for b in r.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
 bpy.context.view_layer.update()
def meshpart(n,vs,fs,bone,mat,template,parts):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.matrix_world=template.matrix_world.copy();me.materials.append(mat)
 o.vertex_groups.new(name=bone).add(list(range(len(vs))),1,'REPLACE')
 for p in me.polygons:p.use_smooth=True
 parts.append(o);return o

def organic_material(n,c,kind='skin'):
 m=bpy.data.materials.new(n);m.use_nodes=True;N=m.node_tree.nodes;L=m.node_tree.links;bs=N.get('Principled BSDF');bs.inputs['Metallic'].default_value=.0;bs.inputs['Roughness'].default_value=.56
 coord=N.new('ShaderNodeTexCoord');noise=N.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=5;L.new(coord.outputs['Object'],noise.inputs['Vector']);r=N.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.22;r.color_ramp.elements[0].color=tuple(v*.48 for v in c)+(1,);r.color_ramp.elements[1].position=.80;r.color_ramp.elements[1].color=tuple(min(.65,v*1.45) for v in c)+(1,);L.new(noise.outputs['Fac'],r.inputs[0]);L.new(r.outputs[0],bs.inputs['Base Color'])
 pores=N.new('ShaderNodeTexNoise');pores.inputs['Scale'].default_value=135 if kind=='flesh' else 85;pores.inputs['Detail'].default_value=3;L.new(coord.outputs['Object'],pores.inputs['Vector']);bump=N.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.004 if kind=='flesh' else .012;L.new(pores.outputs['Fac'],bump.inputs['Height'])
 if kind in ['scale','bark','chitin']:
  cell=N.new('ShaderNodeTexVoronoi');cell.feature='DISTANCE_TO_EDGE';cell.inputs['Scale'].default_value=14 if kind=='scale' else 6;L.new(coord.outputs['Object'],cell.inputs['Vector']);ramp=N.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.025;ramp.color_ramp.elements[0].color=(.25,.25,.25,1);ramp.color_ramp.elements[1].position=.08;ramp.color_ramp.elements[1].color=(.65,.65,.65,1);L.new(cell.outputs[0],ramp.inputs[0]);macro=N.new('ShaderNodeBump');macro.inputs['Strength'].default_value=.4;macro.inputs['Distance'].default_value=.012;L.new(ramp.outputs[0],macro.inputs['Height']);L.new(bump.outputs[0],macro.inputs['Normal']);L.new(macro.outputs[0],bs.inputs['Normal'])
 else:L.new(bump.outputs[0],bs.inputs['Normal'])
 rr=N.new('ShaderNodeMapRange');rr.inputs['To Min'].default_value=.37;rr.inputs['To Max'].default_value=.72;L.new(pores.outputs['Fac'],rr.inputs[0]);L.new(rr.outputs[0],bs.inputs['Roughness'])
 return m

def loft(n,a,b,sections,side,mat,template,parts):
 a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=Vector((1,0,0));u=(u-axis*u.dot(axis)).normalized();v=u.cross(axis).normalized();vs=[];fs=[];N=24
 for t,w,h in sections:
  center=a.lerp(b,t)
  for j in range(N):
   angle=math.tau*j/N;z=math.sin(angle)*h
   if z<0:z*=.72
   vs.append(center+u*(math.cos(angle)*w)+v*z)
 for k in range(len(sections)-1):
  for j in range(N):i=k*N+j;fs.append((i,k*N+(j+1)%N,(k+1)*N+(j+1)%N,i+N))
 fs += [tuple(range(N-1,-1,-1)),tuple((len(sections)-1)*N+j for j in range(N))]
 return meshpart(n,vs,fs,side,mat,template,parts)

def components(me):
 parent=list(range(len(me.vertices)))
 def root(a):
  while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
  return a
 for e in me.edges:
  a,b=map(root,e.vertices);parent[b]=a
 out={}
 for v in me.vertices:out.setdefault(root(v.index),[]).append(v.index)
 return list(out.values())

def organic(m,r,name,cat):
 changes=[];mats=list(m.data.materials);skin={i for i,ma in enumerate(mats) if any(t in ma.name for t in ['skin','dermis','belly']) and 'wing' not in ma.name};flesh=organic_material(name+'_Anatomical_surface',COLORS.get(name,(.11,.105,.09)),'scale' if cat=='dragons' or name in ['Cinder_Hound','Moon_Bat'] else 'bark' if name in ['Root_Matriarch','Sporeling'] else 'chitin' if any(t in name for t in ['Crypt','Hundred','Crab','Mantis']) else 'flesh')
 vmat={}
 for poly in m.data.polygons:
  for vi in poly.vertices:vmat.setdefault(vi,poly.material_index)
 groups={g.index:g.name for g in m.vertex_groups};comp=components(m.data);remove=set();wing=set();head=r.data.bones.get('head');jaw=r.data.bones.get('jaw');dragon=cat=='dragons' or name in ['Cinder_Hound','Moon_Bat']
 for ids in comp:
  mi=vmat.get(ids[0],0);coords=[m.data.vertices[i].co for i in ids];cent=sum(coords,Vector())/len(coords);diag=(Vector(tuple(max(v[a] for v in coords) for a in range(3)))-Vector(tuple(min(v[a] for v in coords) for a in range(3)))).length
  weights={}
  for i in ids:
   for g in m.data.vertices[i].groups:weights[groups[g.group]]=weights.get(groups[g.group],0)+g.weight
  dominant=max(weights,key=weights.get) if weights else ''
  if mi in skin and len(ids)<=12 and diag<.72:remove.update(ids)
  if any(g.startswith('wing') for g in weights):wing.update(ids)
  if dragon and head and mi in skin and dominant in ['head','jaw'] and len(ids)>35:
   bone=head if dominant=='head' else jaw;axis=(bone.tail_local-bone.head_local).normalized();t=(cent-bone.head_local).dot(axis);span=max((v-bone.head_local).dot(axis) for v in coords)-min((v-bone.head_local).dot(axis) for v in coords)
   if t>bone.length*.12 and span>bone.length*.50:remove.update(ids)
  if dragon and dominant=='head' and any(t in mats[mi].name for t in ['black','eye']):remove.update(ids)
 # Remove angular overlay scales and obsolete orbital/skull pieces.
 bm=bmesh.new();bm.from_mesh(m.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(m.data);bm.free();parts=[m]
 changes.append('Removed '+str(len(remove))+' vertices of angular overlay scales/obsolete skull and socket components; source silhouette-specific horns retained.')
 if dragon and head and jaw:
  a=head.head_local;b=head.tail_local;L=head.length;factor={'Obsidian_Bastion':1.28,'Dune_Glasswing':.83,'Crimson_Vesper':.88,'Moonveil':.92,'Cinder_Hound':.88,'Sunken_Leviathan':.92}.get(name,1)
  loft('Orbital_cranium_and_nasal_bridge',a,b,[(0,.21*L,.17*L),(.18,.29*L*factor,.22*L),(.36,.34*L*factor,.19*L),(.55,.28*L*factor,.14*L),(.77,.21*L*factor,.115*L),(1.10,.15*L,.09*L)],'head',flesh,m,parts)
  loft('Mandible_hinge_and_ramus',jaw.head_local,jaw.tail_local,[(0,.23*L,.085*L),(.18,.245*L,.105*L),(.42,.23*L,.065*L),(.75,.175*L,.048*L),(1.08,.12*L,.035*L)],'jaw',flesh,m,parts)
  dark=organic_material(name+'_Oral_tissue',(.026,.009,.008),'flesh');axis=(b-a).normalized();center=a+axis*L*.58;center.z=(jaw.head_local.z+a.z)/2
  loft('Oral_palate',center-axis*L*.34,center+axis*L*.46,[(0,.15*L,.035*L),(.5,.20*L,.04*L),(1,.1*L,.02*L)],'head',dark,m,parts)
  eye=bpy.data.materials.new(name+'_Corneal_surface');eye.use_nodes=True;bs=eye.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.22,.115,.032,1);bs.inputs['Roughness'].default_value=.11
  for s in [-1,1]:
   p=a+axis*L*.28+Vector((s*.345*L,0,.14*L))
   bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1);o=bpy.context.object;o.name='Recessed_orbital_eye';o.data.transform(Matrix.Translation(p)@Matrix.Diagonal((.062*L,.069*L,.055*L,1)));o.matrix_world=m.matrix_world;o.data.materials.append(eye);o.vertex_groups.new(name='head').add(list(range(len(o.data.vertices))),1,'REPLACE');parts.append(o)
   # Eyelid ring is an actual local skin fold, open around the eye rather than a button sphere.
   vs=[];fs=[];N=32
   for k in range(2):
    for j in range(N):
     q=math.tau*j/N;vs.append(p+Vector((s*(.018 if k==0 else -.008)*L,math.cos(q)*(.080 if k==0 else .065)*L,math.sin(q)*(.063 if k==0 else .049)*L)))
   for j in range(N):fs.append((j,(j+1)%N,(j+1)%N+N,j+N))
   meshpart('Upper_and_lower_eyelid',vs,fs,'head',flesh,m,parts)
  changes.append('Rebuilt muzzle/orbital cranium and mandibular ramus as profiled surfaces, with mouth tissue and skin eyelids; preserved jaw bone and teeth.')
 # Join added anatomy before transferring source weights to a fused skin volume.
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=m;bpy.ops.object.join();m=bpy.context.object
 # Replace all old skin shader slots with regional microdetail; wing and hard material slots retain separation.
 for i,ma in enumerate(list(m.data.materials)):
  if any(t in ma.name for t in ['skin','dermis','belly']) and 'wing' not in ma.name:m.data.materials[i]=flesh
 # Sculpt muscles and joint folds into underlying vertices according to skeletal region.
 for v in m.data.vertices:
  dominant=max(v.groups,key=lambda g:g.weight).group if v.groups else None;bn=m.vertex_groups[dominant].name if dominant is not None else '';bone=r.data.bones.get(bn)
  if not bone or any(t in bn for t in ['wing','foot','finger','jaw','head','tail']):continue
  if bn.startswith(('hind','front','arm')):
   a,b=bone.head_local,bone.tail_local;axis=b-a;t=(v.co-a).dot(axis)/max(axis.length_squared,1e-9);c=a+axis*max(0,min(1,t));rad=v.co-c
   if .12<t<.78 and rad.length<bone.length*.60:v.co=c+rad*(1+.16*math.sin(math.pi*(t-.12)/.66))
 changes.append('Resculpted proximal limb volume and joint transitions using bone-aligned regional profiles; resting skeleton unchanged.')
 # Fuse major body/limb skin components, leaving membrane, horns, teeth and equipment distinct.
 skinindex={i for i,ma in enumerate(m.data.materials) if ma==flesh};vv=[];ff=[];chosen=[];idxmap={};keep=[]
 for poly in m.data.polygons:
  groups_here={m.vertex_groups[g.group].name for vi in poly.vertices for g in m.data.vertices[vi].groups if g.weight>.1}
  if poly.material_index in skinindex and not any(g.startswith('wing') for g in groups_here):chosen.append(poly.index)
 if chosen:
  selected={vi for pi in chosen for vi in m.data.polygons[pi].vertices};kd=KDTree(len(selected));src=[]
  for i,vi in enumerate(selected):v=m.data.vertices[vi];kd.insert(v.co,i);src.append([(m.vertex_groups[g.group].name,g.weight) for g in v.groups])
  kd.balance()
  for pi in chosen:
   face=[]
   for vi in m.data.polygons[pi].vertices:
    if vi not in idxmap:idxmap[vi]=len(vv);vv.append(m.data.vertices[vi].co.copy())
    face.append(idxmap[vi])
   ff.append(face)
  body=meshpart('Continuous_anatomical_skin',vv,ff,'root',flesh,m,[]);body.vertex_groups.clear();bpy.context.view_layer.objects.active=body
  rem=body.modifiers.new('Volume_sculpt_union','REMESH');rem.mode='VOXEL';rem.voxel_size=.028 if cat=='dragons' else .020;rem.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=rem.name)
  smooth=body.modifiers.new('Skin_transition_relax','SMOOTH');smooth.factor=.45;smooth.iterations=2;bpy.ops.object.modifier_apply(modifier=smooth.name)
  tri=sum(len(p.vertices)-2 for p in body.data.polygons)
  if tri>27000:d=body.modifiers.new('Surface_budget','DECIMATE');d.ratio=27000/tri;bpy.ops.object.modifier_apply(modifier=d.name)
  vg={}
  for v in body.data.vertices:
   # Three-neighbour weighted transfer preserves bend transitions better than rigid closest-bone binding.
   near=kd.find_n(v.co,3);weights={};total=0
   for co,ix,dist in near:
    w=1/max(dist,.005)**2;total+=w
    for bn,bw in src[ix]:weights[bn]=weights.get(bn,0)+w*bw
   norm=sum(weights.values())
   for bn,val in weights.items():
    if val/norm<.005:continue
    if bn not in vg:vg[bn]=body.vertex_groups.new(name=bn)
    vg[bn].add([v.index],val/norm,'REPLACE')
  bm=bmesh.new();bm.from_mesh(m.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in chosen],context='FACES');bm.to_mesh(m.data);bm.free()
  bpy.ops.object.select_all(action='DESELECT');body.select_set(True);m.select_set(True);bpy.context.view_layer.objects.active=m;bpy.ops.object.join();m=bpy.context.object;changes.append('Fused body/limb skin into a continuous voxel-sculpt surface, relaxed transitions, rebuilt UVs and transferred nearest-surface skin weights. This is automated surface reconstruction, not manual production retopology.')
 return m,changes

def mechanical(m,r,name):
 # Reuse tested open-section limb construction; rebuild whole torso and helmet instead of adding decoration to boxes.
 source=(P/'provenance/batch3/source/sentinel_limbs.py').read_text();section=source[source.index('parts=[mesh]'):source.index('for side,s in')];env={'bpy':bpy,'bmesh':bmesh,'math':math,'Vector':Vector,'mesh':m,'rig':r};exec(section,env)
 mats=env['materials'];
 for key,c,metal in [('Graphite_enamel',(.009,.014,.019),.22),('Steel_bearing',(.085,.11,.13),.82),('Black_innerframe',(.005,.006,.008),.6)]:
  bs=mats[key].node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Metallic'].default_value=metal
  for node in mats[key].node_tree.nodes:
   if node.type=='VALTORGB':node.color_ramp.elements[0].color=(.43,.43,.43,1);node.color_ramp.elements[1].color=(.68,.68,.68,1)
 parts=env['parts'];obj=env['obj'];tube=env['tube'];shell=env['shell'];hinge=env['hinge'];limb=env['limb']
 # Drop previous generic boxes and casing; preserve skeleton and action bank.
 m.data.clear_geometry();heavy=1.23 if name=='Furnace_Titan' else .88 if name=='Scrapling' else 1.06
 for side,s in [('L',-1),('R',1)]:
  for stem,seg,w,d in [('arm','',.18,.16),('arm','_fore',.16,.145),('hind','',.23,.20),('hind','_shin',.185,.17)]:
   bn=stem+side+seg;b=r.data.bones.get(bn)
   if b:limb(bn,b.head_local,b.tail_local,w*heavy,d*heavy,bn);hinge(bn+'_bearing',b.head_local,w*.65,w*.84,bn)
  hand=r.data.bones['arm'+side+'_hand'];limb('Metacarpal_frame',hand.head_local,hand.tail_local,.105,.06,hand.name);hinge('Wrist_trunnion',hand.head_local,.076,.09,hand.name)
  fingers=[b for b in r.data.bones if b.name.startswith('arm'+side+'_finger')]
  if fingers:
   for b in fingers:tube('Phalanx',b.head_local,b.tail_local,.023,.017,b.name,'Steel_bearing',10);hinge('Finger_pin',b.head_local,.025,.023,b.name)
  else:
   for j in range(4):
    a=hand.tail_local+Vector((s*(j-1.5)*.038,0,.07));b=a+Vector((0,-.025,-.14));tube('Digit_proximal',a,b,.024,.019,hand.name,'Steel_bearing');tube('Digit_distal',b,b+Vector((0,-.045,-.09)),.018,.013,hand.name,'Black_innerframe')
  foot=r.data.bones['hind'+side+'_foot'];p=foot.head_local;hinge('Ankle_trunnion',p,.086,.12,foot.name);x=foot.tail_local.x
  for dx in [-.10,.10]:tube('Heel_to_instep_link',p+Vector((dx,0,0)),(x+dx,-.13,.09),.034,.030,foot.name,'Steel_bearing')
  vs=[(x+dx,y,z) for z in [.008,.055] for dx,y in [(-.17,.19),(.17,.19),(.18,-.23),(.11,-.41),(-.11,-.41),(-.18,-.23)]];fs=[tuple(range(5,-1,-1)),tuple(range(6,12))]+[(i,(i+1)%6,(i+1)%6+6,i+6) for i in range(6)];obj('Ground_contact_sole',vs,fs,foot.name,'Sole_composite',.008)
  shell('Instep_carapace',(x,.13,.14),(x,-.31,.11),[(0,.12,.06),(.32,.18,.075),(.7,.15,.06),(1,.10,.04)],foot.name,'Graphite_enamel',arc=3.1)
  a=r.data.bones['arm'+side];shell('Overlapping_deltoid_cowl',a.head_local,a.tail_local,[(0,.29*heavy,.23),(.13,.30*heavy,.24),(.33,.20*heavy,.16)],a.name,'Graphite_enamel',arc=3.8)
 # Custom tapering torso with split armour rather than rectangular chest blocks.
 def hull(n,profiles,bone,material,xoff=0):
  vs=[];fs=[];N=12
  for z,w,d,y in profiles:
   for j in range(N):q=math.tau*j/N;vs.append((xoff+math.sin(q)*w,y-math.cos(q)*d,z))
  for k in range(len(profiles)-1):
   for j in range(N):i=k*N+j;fs.append((i,k*N+(j+1)%N,(k+1)*N+(j+1)%N,i+N))
  fs += [tuple(range(N-1,-1,-1)),tuple((len(profiles)-1)*N+j for j in range(N))];return obj(n,vs,fs,bone,material,.006)
 hull('Thoracic_inner_frame',[(1.92,.26,.18,0),(2.10,.37,.22,0),(2.38,.55*heavy,.26,0),(2.61,.42*heavy,.21,0)],'chest','Black_innerframe')
 for s in [-1,1]:
  hull('Formed_pectoral_carapace',[(2.05,.15,.12,-.10),(2.21,.24*heavy,.16,-.08),(2.46,.30*heavy,.18,-.04),(2.64,.23*heavy,.13,.015)],'chest','Graphite_enamel',s*.26*heavy)
  tube('Scapular_load_strut',(s*.30,.14,2.11),(s*.58*heavy,.05,2.58),.064,.050,'chest','Steel_bearing')
  for j in range(6):tube('Rear_radiator_louver',(s*.10,.30,2.16+j*.064),(s*.42,.30,2.16+j*.064),.014,.014,'chest','Steel_bearing',8)
  tube('Neck_load_column',(s*.115,.07,2.57),(s*.115,.035,3.01),.046,.035,'neck1','Steel_bearing')
  tube('Neck_service_line',(s*.08,.11,2.57),(s*.07,.10,3.07),.025,.019,'neck1','Black_innerframe')
 hull('Waist_suspension',[(1.45,.19,.15,0),(1.64,.32,.22,0),(1.86,.26,.19,0),(2.04,.23,.17,0)],'pelvis','Black_innerframe')
 for s in [-1,1]:hull('Iliac_armour',[(1.42,.115,.12,0),(1.56,.20,.19,0),(1.80,.18,.20,.01)],'pelvis','Graphite_enamel',s*.25)
 # Helmet has a projecting brow, recessed continuous sensor band, cheek structure and protected jaw.
 hull('Cranial_armour',[(3.04,.16,.17,-.025),(3.18,.265,.245,-.045),(3.34,.255,.25,-.012),(3.48,.17,.19,.025),(3.54,.08,.10,.035)],'head','Graphite_enamel')
 hull('Mandibular_casing',[(2.98,.115,.125,-.09),(3.04,.19,.18,-.06),(3.14,.225,.185,-.045)],'head','Steel_bearing')
 shell('Recessed_sensor_band',(-.23,-.285,3.26),(.23,-.285,3.26),[(0,.04,.022),(.12,.044,.025),(.85,.044,.025),(1,.028,.02)],'head','Black_innerframe',arc=3.0)
 for s in [-1,1]:tube('Temple_service_port',(s*.254,-.01,3.21),(s*.272,-.01,3.21),.07,.07,'head','Steel_bearing',20)
 for j in range(5):tube('Jaw_exhaust_slit',(-.11,-.235,3.025+j*.022),(.11,-.235,3.025+j*.022),.006,.006,'head','Black_innerframe',8)
 for bn in [b for b in r.data.bones if b.name.startswith('turret') and b.name.endswith('recoil')]:
  a=bn.head_local;b=a+Vector((0,-.72,0));tube('Cannon_outer_shroud',a,b,.115,.095,bn.name,'Graphite_enamel',20);tube('Cannon_bore',b,b+Vector((0,-.07,0)),.067,.065,bn.name,'Black_innerframe',20)
 if name=='Furnace_Titan':
  for s in [-1,1]:tube('Thermal_stack',(s*.28,.31,2.21),(s*.28,.37,2.95),.11,.085,'chest','Black_innerframe',16)
 hull('Armoured_cervical_collar',[(2.58,.27,.19,.04),(2.70,.28,.20,.04),(2.88,.21,.18,.03)],'neck1','Graphite_enamel')
 for s in [-1,1]:
  for j in range(7):tube('Thoracic_recessed_vent',(s*.16,-.256,2.22+j*.038),(s*.35,-.256,2.22+j*.038),.009,.009,'chest','Black_innerframe',6)
  tube('Protected_sternal_power_bus',(s*.064,-.28,2.12),(s*.064,-.25,2.55),.025,.020,'chest','Bronze_bushing',8)
 for o in parts:
  if any(g.name=='head' for g in o.vertex_groups) and o!=m:
   for v in o.data.vertices:v.co.z-=.20
  if any(t in o.name for t in ['carapace','armour','casing']):
   for face in o.data.polygons:face.use_smooth=False
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=m;bpy.ops.object.join();m=bpy.context.object
 return m,['Rebuilt complete mechanical body: tapered split thorax, integrated neck load columns, shaped cranial armour and protected jaw; old box torso/head removed.','Open C-section limbs, bearings, load links, wrist/digit construction and ankle-to-ground load paths; skeleton rest transforms preserved.','Distinct material regions for enamel, titanium/steel, inner frame, bushings and composite soles; material wear baked into UV atlas.']

def normalize_action_rotations(r):
 converted=0
 for action in bpy.data.actions:
  paths={}
  for fc in action.fcurves:
   if fc.data_path.startswith('pose.bones[') and fc.data_path.endswith('rotation_euler'):
    bone=fc.data_path.split('"')[1];paths.setdefault(bone,{})[fc.array_index]=fc
  for bone,curves in paths.items():
   qpath='pose.bones["'+bone+'"].rotation_quaternion'
   if any(fc.data_path==qpath for fc in action.fcurves):
    for fc in curves.values():action.fcurves.remove(fc)
    continue
   first,last=map(int,action.frame_range);samples=[];prev=None
   for fr in range(first,last+1):
    q=Euler(tuple(curves[i].evaluate(fr) if i in curves else 0 for i in range(3)),'XYZ').to_quaternion()
    if prev is not None and prev.dot(q)<0:q.negate()
    prev=q.copy();samples.append((fr,q.copy()))
   for fc in curves.values():action.fcurves.remove(fc)
   for i in range(4):
    fc=action.fcurves.new(qpath,index=i,action_group=bone);fc.keyframe_points.add(len(samples))
    for kp,(fr,q) in zip(fc.keyframe_points,samples):kp.co=(fr,q[i]);kp.interpolation='LINEAR'
   converted+=1
 for b in r.pose.bones:b.rotation_mode='QUATERNION'
 return converted

def run(row):
 name=row['asset'];cat=row['category'];folder=P/cat/name;src=BASE/cat/name/(name+'_Authoring.blend') if name in ['Cinder_Crown','Siege_Sentinel'] else BASE/cat/name/(name+'.blend');bpy.ops.wm.open_mainfile(filepath=str(src));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');m=next(o for o in bpy.data.objects if o.type=='MESH' and any(x.type=='ARMATURE' for x in o.modifiers));reset(r);rest={b.name:b.matrix_local.copy() for b in r.data.bones};old=len(m.data.vertices)
 if name in ['Siege_Sentinel','Furnace_Titan','Scrapling']:m,changes=mechanical(m,r,name)
 else:m,changes=organic(m,r,name,cat)
 # Remove orphan vertices, normalize deform weights and recalculate normals before UV work.
 bm=bmesh.new();bm.from_mesh(m.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(m.data);bm.free()
 for v in m.data.vertices:
  total=sum(g.weight for g in v.groups)
  if not total:m.vertex_groups.get('root').add([v.index],1,'REPLACE')
  elif abs(total-1)>1e-6:
   for g in list(v.groups):m.vertex_groups[g.group].add([v.index],g.weight/total,'REPLACE')
 bpy.ops.object.select_all(action='DESELECT');m.select_set(True);bpy.context.view_layer.objects.active=m;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.05,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
 if not any(x.type=='ARMATURE' for x in m.modifiers):mod=m.modifiers.new('Deform','ARMATURE');mod.object=r
 m.parent=r;m.matrix_world=r.matrix_world.copy()
 assert all(r.data.bones[n].matrix_local==v for n,v in rest.items())
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'_Authoring.blend')),compress=True)
 # Real game atlas captures local material separation and surface response.
 tris=sum(len(p.vertices)-2 for p in m.data.polygons)
 if tris>48000:d=m.modifiers.new('Game_surface_budget','DECIMATE');d.ratio=47900/tris;bpy.ops.object.modifier_apply(modifier=d.name)
 converted=normalize_action_rotations(r);changes.append('Converted '+str(converted)+' Euler bone/action channels into continuity-correct quaternion samples to make FBX/GLB playback consistent; retained original choreography.')
 images=bake(SimpleNamespace(name=name+'_Visual4',meshobj=m),P,1024)
 for im in images.values():im.source='FILE';im.filepath=str(P/'textures'/Path(im.filepath_raw).name);im.reload()
 bpy.ops.object.select_all(action='DESELECT');m.select_set(True);r.select_set(True);bpy.context.view_layer.objects.active=r
 bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
 reset(r)
 bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_optimize_animation_size=False)
 reset(r)
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file:
   path=Path(bpy.path.abspath(im.filepath));im.filepath='//'+os.path.relpath(path,folder)
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')),compress=True)
 for level,ratio in [(1,.55),(2,.28)]:
  d=m.modifiers.new('LOD','DECIMATE');d.ratio=ratio;bpy.ops.export_scene.fbx(filepath=str(folder/(name+'_LOD'+str(level)+'.fbx')),use_selection=True,path_mode='RELATIVE',embed_textures=False,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y');m.modifiers.remove(d)
 meta=json.loads((folder/'asset.json').read_text());meta['revision']='v4_full_roster_visual_iteration';meta['visual_changes']=changes;meta['vertices_before']=old;meta['vertices_after']=len(m.data.vertices);meta['triangles']=sum(len(p.vertices)-2 for p in m.data.polygons);meta['quality_status']='Actual geometry/material revision; cinematic realism, complete animation refinement and all-frame collision approval remain unproven';meta['texture_atlas']={'size':1024,'maps':[str((P/'textures'/Path(im.filepath_raw).name).relative_to(P)) for im in images.values()]};meta['rig_rest_transforms_preserved']=True;meta['engine_tested']=False;persist(folder/'asset.json',meta)
 for f in folder.iterdir():
  if f.is_file():
   with f.open('rb') as h:os.fsync(h.fileno())
 progress=P/'audit/Visual_Revision_Progress.json';done=json.loads(progress.read_text()) if progress.exists() else [];done=[x for x in done if x['asset']!=name];done.append({'asset':name,'files':[str((folder/(name+ext)).relative_to(P)) for ext in ['.blend','.fbx','.glb']],'changes':changes,'rest_rig_preserved':True,'status':'geometry_and_materials_changed_pending_visual_export_review','animations':'Existing bank retained; no motion upgrade claimed by this modelling pass.'});persist(progress,done);print('CREATURE_REVISED',name,len(done),flush=True)
for row in ROSTER:
 if ONLY!='all' and row['asset']!=ONLY:continue
 run(row)
