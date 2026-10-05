import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];folder=P/'enemies'/'Cinder_Hound';name='Cinder_Hound'
bpy.ops.wm.open_mainfile(filepath=str(folder/(name+'.blend')))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
rig.animation_data.action=None
for a in list(bpy.data.actions):
 if a.name.startswith('Flight_'):bpy.data.actions.remove(a);continue
 for fc in list(a.fcurves):
  if 'wingL' in fc.data_path or 'wingR' in fc.data_path:a.fcurves.remove(fc)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for b in list(rig.data.edit_bones):
 if b.name.startswith('wing'):rig.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT')
for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
for im in bpy.data.images:
 if im.source=='FILE':im.filepath=str(P/'textures'/Path(im.filepath).name)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=.1,path_mode='RELATIVE')
rig.animation_data.action=list(bpy.data.actions)[0]
bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS')
rig.animation_data.action=None
for im in bpy.data.images:
 if im.source=='FILE':im.filepath='//../../textures/'+Path(im.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')),relative_remap=False)
m=json.loads((folder/'asset.json').read_text());m['clips']=[c for c in m['clips'] if not c['name'].startswith('Flight_')];m['bones']=len(rig.data.bones);(folder/'asset.json').write_text(json.dumps(m,indent=2))
# Rebuild both LODs so skeletons match the revised base rig exactly.
original=mesh.data.copy()
for level,ratio in [(1,.55),(2,.28)]:
 mesh.data=original.copy();bpy.context.view_layer.objects.active=mesh;mod=mesh.modifiers.new('LOD','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.ops.export_scene.fbx(filepath=str(folder/(name+'_LOD'+str(level)+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE')
print('Hound rig corrected; no flight bank or unused wing bones')
