import bpy,bmesh,sys,json
from pathlib import Path
from mathutils import Vector
from types import SimpleNamespace
P=Path(__file__).resolve().parents[1];BASE=P.parent/'nocturne-v4';sys.path.insert(0,str(P/'source'));from texture_bake import bake
bpy.ops.wm.open_mainfile(filepath=str(BASE/'bosses/Siege_Sentinel/Siege_Sentinel_Authoring.blend'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers));rig.animation_data.action=None
for t in rig.animation_data.nla_tracks:t.mute=True
for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
bpy.context.scene.frame_set(1)
# Remove actual chest/head rigid components, retaining limb mesh and original rig.
removed_groups={g.index for g in mesh.vertex_groups if g.name in ['head','chest','neck1','turretL','turretR','turretL_recoil','turretR_recoil']};indices={v.index for v in mesh.data.vertices if any(g.group in removed_groups and g.weight>.98 for g in v.groups)};bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in indices],context='VERTS');bm.to_mesh(mesh.data);bm.free()
mats={m.name:m for m in mesh.data.materials};parts=[mesh]
def mat(key,color,metal,rough):
 m=bpy.data.materials.new(key);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;mats[key]=m
mat('Graphite_coating',(.028,.034,.037),.65,.39);mat('Machined_titanium',(.13,.15,.17),.95,.28);mat('Dark_mechanism',(.010,.014,.017),.8,.48);mat('Sensor_glass',(.055,.10,.115),.3,.12);mat('Oxide_warning',(.29,.077,.022),.4,.47)
def prism(name,poly,xwidth,bone,material,x=0):
 vs=[(x+s*xwidth/2,y,z) for s in [-1,1] for y,z in poly];
 if name=='Angled_sensor_cranium':vs=[(vx*(.45+.55*max(0,1-abs(vz-3.24)/.20)),vy,vz) for vx,vy,vz in vs]
 if name=='Pectoral_carapace':vs=[(x+(vx-x)*(.57+.43*max(0,min(1,(vz-2.13)/.50))),vy,vz) for vx,vy,vz in vs]
 if bone=='head':vs=[(vx,vy,vz-.10) for vx,vy,vz in vs]
 n=len(poly);ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];me=bpy.data.meshes.new(name);me.from_pydata(vs,[],ff);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.matrix_world=mesh.matrix_world.copy();o.data.materials.append(mats[material]);o.vertex_groups.new(name=bone).add(list(range(len(vs))),1,'REPLACE');bpy.context.view_layer.objects.active=o;be=o.modifiers.new('Forged_edge','BEVEL');be.width=.008;be.segments=3;bpy.ops.object.modifier_apply(modifier=be.name);parts.append(o);return o
# Continuous neck linkage reconnects the removed chassis and sensor head.
prism('Cervical_gimbal',[(-.10,2.64),(-.10,2.975),(.105,2.975),(.12,2.64)],.17,'neck1','Dark_mechanism')
prism('Neck_base_collar',[(-.15,2.64),(-.15,2.76),(.16,2.76),(.16,2.64)],.27,'chest','Machined_titanium')
prism('Waist_interface',[(-.12,2.035),(-.12,2.18),(.14,2.18),(.14,2.035)],.24,'chest','Dark_mechanism')
# Sloped helmet and integrated jaw cowl: no anthropomorphic button eyes.
prism('Angled_sensor_cranium',[(-.22,3.07),(-.27,3.24),(-.13,3.43),(.13,3.37),(.15,3.13),(.05,3.05)],.38,'head','Graphite_coating')
prism('Recessed_sensor_band',[(-.28,3.22),(-.285,3.255),(-.257,3.28),(-.241,3.225)],.325,'head','Dark_mechanism')
prism('Continuous_optic',[(-.290,3.235),(-.291,3.25),(-.271,3.263),(-.262,3.240)],.27,'head','Sensor_glass')
prism('Mandibular_impact_cowl',[(-.22,3.065),(-.28,3.12),(-.264,3.17),(-.175,3.155),(-.07,3.065)],.29,'head','Machined_titanium')
for s in [-1,1]:
 prism('Temporal_shield',[(-.15,3.30),(.13,3.29),(.14,3.14),(-.09,3.11)],.058,'head','Machined_titanium',s*.205)
 # Pectoral carapace has a broad shoulder slope, undercut lower edge and central opening.
 prism('Pectoral_carapace',[(-.27,2.13),(-.385,2.31),(-.29,2.66),(-.08,2.67),(.07,2.43),(-.06,2.19)],.39,'chest','Graphite_coating',s*.27)
 prism('Rib_underframe',[(-.09,2.09),(-.20,2.25),(-.10,2.57),(.12,2.54),(.16,2.14)],.27,'chest','Dark_mechanism',s*.22)
 for j in range(6):
  z=2.22+j*.051;prism('Intake_louver',[(-.337,z),(-.362,z+.023),(-.283,z+.032),(-.267,z+.007)],.195,'chest','Machined_titanium',s*.285)
 prism('Scapular_mount',[(-.04,2.54),(-.07,2.72),(.26,2.78),(.32,2.59)],.26,'chest','Machined_titanium',s*.46)
 prism('Back_heat_exchanger',[(.27,2.18),(.36,2.19),(.35,2.61),(.27,2.65)],.19,'chest','Dark_mechanism',s*.27)
 for j in range(8):
  z=2.22+j*.049;prism('Rear_radiator_fin',[(.33,z),(.42,z),(.42,z+.014),(.33,z+.014)],.24,'chest','Machined_titanium',s*.27)
prism('Sternal_spine',[(-.15,2.12),(-.22,2.3),(-.17,2.57),(.08,2.63),(.14,2.30),(.10,2.12)],.13,'chest','Machined_titanium')
prism('Sternal_recess',[(-.224,2.28),(-.225,2.47),(-.194,2.50),(-.191,2.26)],.057,'chest','Dark_mechanism')
prism('Rear_power_core',[(.18,2.19),(.42,2.19),(.40,2.55),(.20,2.65)],.24,'chest','Graphite_coating')
# Existing turret bones are retained for compatibility but shoulder barrels are replaced with single recoil assembly.
for s in [-1,1]:
 turret='turretL_recoil' if s<0 else 'turretR_recoil'
 prism('Recoil_sled',[(-.02,2.67),(.20,2.67),(.18,2.80),(-.07,2.77)],.17,turret,'Dark_mechanism',s*.48)
 prism('Armoured_barrel_shroud',[(-.54,2.67),(-.54,2.76),(-.01,2.78),(.01,2.66)],.11,turret,'Graphite_coating',s*.48)
 prism('Muzzle_recess',[(-.552,2.685),(-.552,2.747),(-.535,2.747),(-.535,2.685)],.075,turret,'Dark_mechanism',s*.48)
 for j in range(4):prism('Shroud_vent',[(-.12-j*.08,2.77),(-.16-j*.08,2.77),(-.16-j*.08,2.778),(-.12-j*.08,2.778)],.067,turret,'Machined_titanium',s*.48)
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join();mesh=bpy.context.object;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.08,island_margin=.012);bpy.ops.object.mode_set(mode='OBJECT')
folder=P/'bosses/Siege_Sentinel';folder.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Siege_Sentinel_Authoring.blend'))
c=SimpleNamespace(name='Siege_Sentinel_Batch02',meshobj=mesh);images=bake(c,P,2048)
for im in images.values():im.filepath='//../../textures/'+Path(im.filepath_raw).name
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(folder/'Siege_Sentinel.fbx'),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
bpy.ops.export_scene.gltf(filepath=str(folder/'Siege_Sentinel.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS')
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Siege_Sentinel.blend'))
for level,ratio in [(1,.55),(2,.28)]:
 d=mesh.modifiers.new('LOD','DECIMATE');d.ratio=ratio;bpy.ops.export_scene.fbx(filepath=str(folder/('Siege_Sentinel_LOD'+str(level)+'.fbx')),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y');mesh.modifiers.remove(d)
meta=json.loads((BASE/'bosses/Siege_Sentinel/asset.json').read_text());meta['batch02_changes']=['Replaced chest/head rigid geometry with sloped helmet and split pectoral carapace.','Removed button-eye lenses; recessed continuous sensor band.','Reshaped scapular mounts, radiator and single-barrel recoil shrouds.','Existing limb mesh and 21 animation clips retained; not a whole-body motion upgrade.'];meta['quality_status']='partial geometry revision; realism target unfinished';meta['triangles']=sum(len(p.vertices)-2 for p in mesh.data.polygons);
for side,sign in [('L',-1),('R',1)]:
 point=Vector((sign*.48,-.557,2.716));anchor=meta['effect_anchors']['muzzle_'+side];bone=rig.data.bones[anchor['bone']];anchor['rest_point_armature_local']=list(point);anchor['offset_bone_local_authoring_units']=list(bone.matrix_local.inverted()@point);anchor['status']='updated for batch02 muzzle geometry; engine direction/playback untested'
meta['texture_atlas']={'size':2048,'maps':[str(Path('textures')/('Siege_Sentinel_Batch02_'+t+'.png')) for t in ['basecolor','normal','roughness','metallic']]}
meta['visual_status']='Partial geometry revision; realistic full-body quality target unfinished'
(folder/'asset.json').write_text(json.dumps(meta,indent=2))
print('SENTINEL_REVISED',meta['triangles'],flush=True)
