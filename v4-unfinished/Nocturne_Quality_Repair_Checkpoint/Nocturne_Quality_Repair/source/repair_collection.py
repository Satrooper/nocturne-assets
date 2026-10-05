import bpy,bmesh,math,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.noise import noise_vector,noise
W=Path(__file__).resolve().parents[2];P=W/'Nocturne_Quality_Repair';BASE=W/'Nocturne_V4_Visual_Revision';EXP=W/'Nocturne_Expansion_60'
old=json.loads((BASE/'asset_manifest.json').read_text())['characters'];new=json.loads((EXP/'audit/Build_Progress.json').read_text());rows=[dict(c,added=False,base=str(BASE)) for c in old]+[dict(c,added=True,base=str(EXP)) for c in new]
mechanical={'Iron_Executioner','Harbour_Dredger','Vector_Widow','Molten_Ram','Cable_Eel','Ratchet_Rook','Siege_Sentinel','Furnace_Titan','Scrapling'}
ONLY=sys.argv[-1] if '--' in sys.argv else 'all';progress=P/'audit/Repair_Progress.json';done=json.loads(progress.read_text()) if progress.exists() else []

def meshpart(name,verts,faces,bone,material,parts):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(material);o.vertex_groups.new(name=bone).add(list(range(len(verts))),1,'REPLACE');parts.append(o);return o

def newmat(name,color,metal=0,rough=.6):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;return m

def segment_panel(a,b,bone,width,mat,parts):
 axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized()
 if u.length<.5:u=axis.cross(Vector((1,0,0))).normalized()
 v=axis.cross(u).normalized();verts=[];faces=[]
 # Two side shells: tapered, faceted and open-backed rather than a box or padded cylinder.
 for side in [-1,1]:
  start=len(verts)
  for t,k in [(.14,.65),(.26,1.0),(.67,.82),(.84,.42)]:
   for angle in [-.95,-.50,0,.50,.95]:verts.append(a.lerp(b,t)+u*(side*width*math.cos(angle)*k)+v*(width*.68*math.sin(angle)*k))
  for j in range(3):
   for k in range(4):z=start+j*5+k;faces.append((z,z+1,z+6,z+5))
 o=meshpart('profiled_open_limb_shell',verts,faces,bone,mat,parts);sol=o.modifiers.new('Armour thickness','SOLIDIFY');sol.thickness=width*.11;bev=o.modifiers.new('Machined edges','BEVEL');bev.width=width*.045;bev.segments=2;bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 return u,v

def rod(a,b,bone,radius,mat,parts):
 axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
 if u.length<.1:u=axis.cross(Vector((0,1,0)))
 u.normalize();v=axis.cross(u);verts=[];faces=[]
 for q,r in [(a,radius),(a.lerp(b,.08),radius),(a.lerp(b,.60),radius),(b,radius*.58)]:
  for i in range(12):verts.append(q+(u*math.cos(i*math.tau/12)+v*math.sin(i*math.tau/12))*r)
 for j in range(3):
  for i in range(12):faces.append((j*12+i,j*12+(i+1)%12,(j+1)*12+(i+1)%12,(j+1)*12+i))
 faces.extend([tuple(range(11,-1,-1)),tuple(range(36,48))]);return meshpart('actuator_body_and_rod',verts,faces,bone,mat,parts)

def bearing(center,axis,bone,radius,steel,rubber,parts):
 axis.normalize();u=axis.cross(Vector((0,0,1)))
 if u.length<.1:u=axis.cross(Vector((0,1,0)))
 u.normalize();v=axis.cross(u);vv=[];ff=[]
 for d,r in [(-radius*.36,radius*.84),(-radius*.20,radius),(radius*.20,radius),(radius*.36,radius*.84)]:
  for i in range(16):vv.append(center+axis*d+(u*math.cos(i*math.tau/16)+v*math.sin(i*math.tau/16))*r)
 for j in range(3):
  for i in range(16):ff.append((j*16+i,j*16+(i+1)%16,(j+1)*16+(i+1)%16,(j+1)*16+i))
 ff.extend([tuple(range(15,-1,-1)),tuple(range(48,64))]);meshpart('recessed_hinge_motor',vv,ff,bone,steel,parts)
 rod(center-axis*radius*.4,center+axis*radius*.4,bone,radius*.42,rubber,parts)

def helmet(m,r,name,parts,paint,steel,rubber):
 if name not in {'Iron_Executioner','Siege_Sentinel'}:return False
 head=r.data.bones.get('head');jaw=r.data.bones.get('jaw');groups={g.index:g.name for g in m.vertex_groups};selected=[]
 for v in m.data.vertices:
  if any(groups[g.group] in {'head','jaw'} and g.weight>.70 for g in v.groups):selected.append(v.co.copy())
 if not selected:return False
 lo=Vector(tuple(min(v[i] for v in selected) for i in range(3)));hi=Vector(tuple(max(v[i] for v in selected) for i in range(3)));center=(lo+hi)/2;size=hi-lo
 # Remove the old generic head's geometry, preserving the skeleton and animations.
 bm=bmesh.new();bm.from_mesh(m.data);layer=bm.verts.layers.deform.active
 doomed=[v for v in bm.verts if layer and any(groups.get(k) in {'head','jaw'} and w>.70 for k,w in v[layer].items())];bmesh.ops.delete(bm,geom=doomed,context='VERTS');bm.to_mesh(m.data);bm.free()
 width=max(.25,min(.42,size.x*.48));height=max(.30,min(.62,size.z*.52));depth=max(.22,min(.40,size.y*.5));center.x=head.head_local.x;center.y=head.head_local.y-.02;center.z=(head.head_local.z+head.tail_local.z)/2 if name=='Siege_Sentinel' else head.head_local.z
 shape=[(-.58,1),(.58,1),(1,.52),(.86,-.40),(.48,-.95),(-.48,-.95),(-.86,-.40),(-1,.52)]
 verts=[]
 for y,k in [(depth*.70,.82),(-depth*.25,1),(-depth*.90,.85)]:
  for x,z in shape:verts.append(center+Vector((x*width,y,z*height)))
 faces=[]
 for ring in range(2):
  for j in range(8):faces.append((ring*8+j,ring*8+(j+1)%8,(ring+1)*8+(j+1)%8,(ring+1)*8+j))
 # Offset brow and cheek plates around a deliberately recessed sensor cavity.
 faces.append(tuple(range(7,-1,-1)));meshpart('split_faceted_cranium',verts,faces,'head',paint,parts)
 front=center+Vector((0,-depth*.87,0))
 for s in [-1,1]:
  vv=[front+Vector((s*x*width,y,z*height)) for x,y,z in [(.07,-.035,.38),(.78,.00,.51),(.83,.015,.18),(.12,-.065,.12)]];meshpart('slanted_brow',vv,[(0,1,2,3)],'head',steel,parts)
  vv=[front+Vector((s*x*width,y,z*height)) for x,y,z in [(.15,.03,-.08),(.75,.015,.04),(.68,-.01,-.48),(.24,-.045,-.54)]];meshpart('fitted_cheek',vv,[(0,1,2,3)],'head',paint,parts)
 # Dark optical cavity, lower jaw attached to its actual jaw bone.
 vv=[front+Vector((x*width,.055,z*height)) for x,z in [(-.74,.25),(.74,.25),(.66,-.18),(-.66,-.18)]];meshpart('recessed_optical_aperture',vv,[(0,1,2,3)],'head',rubber,parts)
 jawcenter=front+Vector((0,-.01,-height*.60));vv=[jawcenter+Vector((x*width,y,z*height)) for x,y,z in [(-.50,.04,.17),(.50,.04,.17),(.32,-.07,-.10),(-.32,-.07,-.10)]];meshpart('articulated_mandibular_guard',vv,[(0,1,2,3)],'jaw' if jaw else 'head',steel,parts)
 for s in [-1,1]:rod(front+Vector((s*width*.40,.015,height*.045)),front+Vector((s*width*.18,.015,height*.045)),'head',height*.018,newmat(name+'_sensor',(.28,.045,.014),0,.24),parts)
 return True

def armour(m,r,name):
 parts=[];paint=newmat(name+'_armour_paint',(.075,.090,.105),.35,.48);steel=newmat(name+'_machined_steel',(.20,.22,.24),.95,.30);rubber=newmat(name+'_seal_rubber',(.009,.012,.013),0,.78)
 for b in r.data.bones:
  n=b.name.lower()
  if any(s in n for s in ['finger','toe','hand','foot','wing','tail','root','neck','head','jaw','pelvis','chest']):continue
  if not any(s in n for s in ['arm','leg','hind','shin','fore','pincer','winch']):continue
  a=b.head_local.copy();end=b.tail_local.copy();L=(end-a).length
  if L<.25:continue
  radii=[]
  group=m.vertex_groups.get(b.name)
  if group:
   for vert in m.data.vertices:
    if any(g.group==group.index and g.weight>.65 for g in vert.groups):
     t=(vert.co-a).dot((end-a).normalized())/L
     if .12<t<.82:radii.append((vert.co-a.lerp(end,t)).length)
  radius=sorted(radii)[int(len(radii)*.78)] if radii else L*.18
  width=min(.32,max(.055,L*.21,radius*1.14));u,v=segment_panel(a,end,b.name,width,paint,parts)
  bearing(a,u.copy(),b.name,width*.61,steel,rubber,parts)
  rod(a.lerp(end,.20)+v*width*.57,a.lerp(end,.81)+v*width*.57,b.name,width*.13,steel,parts)
  rod(a.lerp(end,.17)-v*width*.46,a.lerp(end,.77)-v*width*.46,b.name,width*.07,rubber,parts)
 changedhead=helmet(m,r,name,parts,paint,steel,rubber)
 if name=='Iron_Executioner':
  groups={g.index:g.name for g in m.vertex_groups};bm=bmesh.new();bm.from_mesh(m.data);layer=bm.verts.layers.deform.active
  remove=[v for v in bm.verts if layer and any(groups.get(k) in {'chest','pelvis'} and w>.85 for k,w in v[layer].items())];bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(m.data);bm.free()
  z=r.data.bones['chest'].head_local.z
  for side in [-1,1]:
   pts=[(side*x,y,z+dz) for x,y,dz in [(.045,-.28,.48),(.37,-.20,.42),(.50,-.08,.16),(.30,-.24,-.36),(.06,-.31,-.24)]]
   plate=meshpart('shaped_pectoral_armour',pts,[(0,1,2,3,4)],'chest',paint,parts);solid=plate.modifiers.new('Purposeful plate thickness','SOLIDIFY');solid.thickness=.035;bpy.context.view_layer.objects.active=plate;bpy.ops.object.modifier_apply(modifier=solid.name)
   rod(Vector((side*.23,.06,z+.4)),Vector((side*.15,.06,z-.43)),'chest',.05,steel,parts)
   for j in range(3):rod(Vector((side*.12,.06,z-.05-j*.13)),Vector((side*.34,-.10,z-.08-j*.13)),'chest',.025,rubber,parts)
  rod(Vector((0,.12,z-.6)),Vector((0,.12,z+.4)),'chest',.075,steel,parts)
  for side in [-1,1]:
   pts=[(side*x,y,z+dz) for x,y,dz in [(.045,-.18,-.49),(.27,-.12,-.46),(.34,-.08,-.66),(.24,-.20,-.82),(.06,-.24,-.76)]];meshpart('paired_iliac_guards',pts,[(0,1,2,3,4)],'pelvis',paint,parts)

 if parts:
  bpy.ops.object.select_all(action='DESELECT');m.select_set(True)
  for o in parts:o.matrix_world=m.matrix_world.copy();o.select_set(True)
  bpy.context.view_layer.objects.active=m;bpy.ops.object.join()
 return {'new_parts':len(parts),'head_rebuilt':changedhead,'geometry_change':'Tapered open armour shells, machined motor housings, rigid segment actuators and cable runs on existing articulated bones.'}

def fuse_flesh(m,r):
 groups={g.index:g.name for g in m.vertex_groups};skinindices={i for i,mat in enumerate(m.data.materials) if mat and mat.name.lower().endswith('_skin')};eligible=[]
 for p in m.data.polygons:
  if p.material_index not in skinindices:continue
  gnames={groups[g.group].lower() for i in p.vertices for g in m.data.vertices[i].groups if g.weight>.30}
  if any(n not in {'chest','pelvis','head','jaw','neck1','neck2'} and not n.startswith('tail') for n in gnames):continue
  eligible.append(p.index)
 if not eligible:return {'flesh_fused':False}
 # Preserve detailed extremities, membranes, teeth and eyes while fusing bulk flesh.
 bpy.ops.object.select_all(action='DESELECT');m.select_set(True);bpy.context.view_layer.objects.active=m
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.context.tool_settings.mesh_select_mode=(False,False,True)
 bm=bmesh.from_edit_mesh(m.data);bm.faces.ensure_lookup_table()
 for i in eligible:bm.faces[i].select_set(True)
 bmesh.update_edit_mesh(m.data);bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
 bulk=next(o for o in bpy.context.selected_objects if o!=m);bulk.modifiers.clear();saved_matrix=m.matrix_world.copy();bulk.parent=None;bulk.matrix_world=saved_matrix
 originalverts=[v.co.copy() for v in bulk.data.vertices];originalweights=[[(groups.get(g.group,bulk.vertex_groups[g.group].name),g.weight) for g in v.groups] for v in bulk.data.vertices]
 kd=KDTree(len(originalverts))
 for i,co in enumerate(originalverts):kd.insert(co,i)
 kd.balance();bbox=[Vector(c) for c in bulk.bound_box];extent=max(max(v[k] for v in bbox)-min(v[k] for v in bbox) for k in range(3));vox=max(.007,min(.025,extent/190))
 bpy.context.view_layer.objects.active=bulk;mod=bulk.modifiers.new('Fused anatomical surface','REMESH');mod.mode='VOXEL';mod.voxel_size=vox;mod.use_remove_disconnected=False;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name)
 if len(bulk.data.vertices)>100000:
  dec=bulk.modifiers.new('Controlled surface density','DECIMATE');dec.ratio=100000/len(bulk.data.vertices);bpy.ops.object.modifier_apply(modifier=dec.name)
 smooth=bulk.modifiers.new('Seam relaxation','SMOOTH');smooth.factor=.35;smooth.iterations=2;bpy.ops.object.modifier_apply(modifier=smooth.name)
 for g in list(bulk.vertex_groups):bulk.vertex_groups.remove(g)
 created={b.name:bulk.vertex_groups.new(name=b.name) for b in r.data.bones}
 for v in bulk.data.vertices:
  accum={}
  for co,i,dist in kd.find_n(v.co,3):
   factor=1/max(dist,.0005)**2
   for n,w in originalweights[i]:accum[n]=accum.get(n,0)+w*factor
  total=sum(accum.values())
  for n,w in accum.items():
   if n in created and w/total>.001:created[n].add([v.index],w/total,'REPLACE')
  # Broad anatomical relief is kept subtle; avoid spiky random displacement.
  v.co+=v.normal*(noise(v.co*12)*vox*.11)
 bpy.ops.object.select_all(action='DESELECT');m.select_set(True);bulk.select_set(True);bpy.context.view_layer.objects.active=m;bpy.ops.object.join()
 return {'flesh_fused':True,'voxel_size_m':vox,'weight_transfer':'Inverse-square blend of three nearby source skin weights; detailed extremities retained','topology':'Voxel triangles/quads, not manually retopologized cinematic topology'}

def surface_materials(m,name,added):
 if not added:
  # Preserve previous authored/baked detail. Adjust severe normal amplification only.
  changes=0
  for mat in m.data.materials:
   if not mat or not mat.use_nodes:continue
   for node in mat.node_tree.nodes:
    if node.type=='NORMAL_MAP' and node.inputs['Strength'].default_value>.50:node.inputs['Strength'].default_value=.42;changes+=1
  return {'old_art_preserved':True,'normal_maps_restrained':changes}
 # Replace stretched noise textures with local-space detail carried by COLOR_0 in the game export.
 palette=[(.075,.063,.048),(.040,.060,.067),(.082,.039,.031),(.060,.074,.051),(.054,.055,.071),(.105,.078,.047)]
 index=int(hashlib.sha256(name.encode()).hexdigest()[:4],16)%len(palette);skin=palette[index];m.data.update()
 attr=m.data.color_attributes.get('SurfaceDetail') or m.data.color_attributes.new(name='SurfaceDetail',type='FLOAT_COLOR',domain='CORNER');m.data.color_attributes.active_color=attr
 kinds=[]
 for mat in m.data.materials:
  n=mat.name.lower();kind='metal' if any(s in n for s in ['metal','steel']) else 'paint' if 'paint' in n else 'black' if any(s in n for s in ['black','rubber']) else 'eye' if any(s in n for s in ['eye','sensor']) else 'tooth' if 'tooth' in n else 'membrane' if 'membrane' in n else 'skin';
  if name in mechanical and n.endswith('_metal'):kind='paint'
  if name in mechanical and n.endswith('_skin'):kind='black'
  kinds.append(kind)
  mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='SurfaceDetail';mat.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(bs.outputs[0],out.inputs[0]);bs.inputs['Metallic'].default_value=.90 if kind=='metal' else .28 if kind=='paint' else 0;bs.inputs['Roughness'].default_value={'metal':.34,'paint':.48,'black':.75,'skin':.64,'tooth':.40,'eye':.16,'membrane':.72}[kind]
  if kind=='eye':bs.inputs['Emission Color'].default_value=(.05,.006,.001,1);bs.inputs['Emission Strength'].default_value=.08
  if kind not in {'eye','black','tooth'}:
   tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'textures'/('metal_micro_normal.png' if kind in {'metal','paint'} else 'skin_micro_normal.png')),check_existing=True);tex.image.colorspace_settings.name='Non-Color';nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.16 if kind in {'skin','membrane'} else .09;mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs[0],bs.inputs['Normal'])
  mat.diffuse_color=(.1,.1,.1,1)
 uv=m.data.uv_layers.active or m.data.uv_layers.new(name='SurfaceTileUV')
 groups={g.index:g.name for g in m.vertex_groups}
 for p in m.data.polygons:
  axis=max(range(3),key=lambda i:abs(p.normal[i]));pair=[i for i in range(3) if i!=axis];names={groups[g.group].lower() for vi in p.vertices for g in m.data.vertices[vi].groups if g.weight>.65};tile=.075 if kinds[p.material_index] in {'skin','membrane'} else .25
  if any('head' in x or 'jaw' in x for x in names):tile*=.30
  elif any('arm' in x or 'leg' in x or 'shin' in x for x in names):tile*=.55
  for li in p.loop_indices:
   co=m.data.vertices[m.data.loops[li].vertex_index].co;uv.data[li].uv=(co[pair[0]]/tile,co[pair[1]]/tile)
 colors={'skin':skin,'metal':(.16,.18,.20),'paint':(.040,.054,.063),'black':(.008,.010,.012),'tooth':(.22,.185,.13),'eye':(.018,.010,.003),'membrane':tuple(x*.68 for x in skin)}
 for p in m.data.polygons:
  kind=kinds[p.material_index];base=Vector(colors[kind])
  for li in p.loop_indices:
   vert=m.data.vertices[m.data.loops[li].vertex_index];co=vert.co;macro=noise(co*3.7);micro=noise(co*65);variation=max(.65,min(1.22,.96+macro*.16+micro*.06));c=base*variation
   # Restrained exposed-edge wear on metal, organic variation stays subdued.
   if kind in ['metal','paint']:
    edge=min(1,(vert.normal-p.normal).length*1.3);c=c.lerp(Vector((.25,.26,.27)),edge*.23)
   attr.data[li].color=(*c,1)
 return {'new_surface':'Local-space vertex colour variation exported as COLOR_0; neutral metal/paint/rubber/skin/eye separation','stretched_texture_removed':True,'export_texture_dependency':'Two small original micro-normal tiles embedded in GLB and packed in Blender; old texture sources preserved in base pack','UV_method':'Tiling object-space box projection with smaller facial/limb scale; not unique painted UVs','vertex_colour_attribute':'SurfaceDetail'}

def export_asset(row):
 name=row['asset'];folder=P/'models'/row['category']/name;folder.mkdir(parents=True,exist_ok=True);source=Path(row['base'])/row.get('editable_source',str(Path(row['canonical_glb']).with_suffix('.blend')))
 bpy.ops.wm.open_mainfile(filepath=str(source));r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(md.type=='ARMATURE' for md in o.modifiers)];m=meshes[0];r.animation_data_create();r.animation_data.action=None
 for tr in r.animation_data.nla_tracks:tr.mute=True
 for pb in r.pose.bones:pb.location=(0,0,0);pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.scale=(1,1,1)
 bpy.context.view_layer.update();bones=[b.name for b in r.data.bones];actions=len(bpy.data.actions);oldverts=len(m.data.vertices);geo={}
 if row['added'] and name not in mechanical:geo=fuse_flesh(m,r)
 if name in mechanical and (row['added'] or name=='Siege_Sentinel'):geo=armour(m,r,name)
 surf=surface_materials(m,name,row['added']);bpy.context.scene.render.fps=30
 for mat in list(bpy.data.materials):
  if mat.users==0:bpy.data.materials.remove(mat)
 for im in list(bpy.data.images):
  if im.users==0:bpy.data.images.remove(im)
  elif im.source=='FILE' and not im.packed_file:im.pack()
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')),compress=True);bpy.ops.object.select_all(action='DESELECT');r.select_set(True)
 for o in meshes:o.select_set(True)
 bpy.context.view_layer.objects.active=r
 # Bone names and original action names preserved in editable and GLB files.
 bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_frame_range=False,export_force_sampling=True,export_def_bones=True)
 rig_name=r.name;r.name='Rig';saved=[(a,a.name) for a in list(bpy.data.actions)]
 for a,n in saved:a.name=(n.split('__')[-1])[-44:]
 bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True)
 r.name=rig_name
 for a,n in saved:a.name=n
 rec={'asset':name,'category':row['category'],'original_source':str(source.relative_to(W)),'added_to_60_pack':row['added'],'canonical_glb':str((folder/(name+'.glb')).relative_to(P)),'canonical_fbx':str((folder/(name+'.fbx')).relative_to(P)),'editable_source':str((folder/(name+'.blend')).relative_to(P)),'bones':bones,'clips':actions,'vertices_before':oldverts,'vertices_after':len(m.data.vertices),'geometry_changes':geo,'material_changes':surf,'status':'candidate_repair_requires_visual_deformation_review','cinematic_quality_approved':False,'engine_tested':False,'iphone_tested':False,'remaining':['Individual anatomical sculpting and final art review','All-frame weight/contact/clipping polish','Runtime integration'], 'fbx_action_names':[{'source':n,'export':n.split('__')[-1][-44:]} for a,n in saved]}
 (folder/'repair.json').write_text(json.dumps(rec,indent=2));return rec
for row in rows:
 if ONLY!='all' and row['asset']!=ONLY:continue
 if any(x['asset']==row['asset'] for x in done):continue
 rec=export_asset(row);done.append(rec);progress.write_text(json.dumps(done,indent=2));print('QUALITY_REPAIR_SAVED',row['asset'],rec['vertices_after'],flush=True)
