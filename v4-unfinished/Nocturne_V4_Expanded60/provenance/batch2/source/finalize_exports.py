import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for meta in P.glob('*/*/asset.json'):
 m=json.loads(meta.read_text());name=m['name'];folder=meta.parent;bpy.ops.wm.open_mainfile(filepath=str(folder/(name+'.blend')));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(mod.type=='ARMATURE' for mod in o.modifiers))
 if name=='Siege_Sentinel':
  from mathutils import Vector
  for side,sign in [('L',-1),('R',1)]:
   point=Vector((sign*.48,-.557,2.716));anchor=m['effect_anchors']['muzzle_'+side];bone=rig.data.bones[anchor['bone']];anchor['rest_point_armature_local']=list(point);anchor['offset_bone_local_authoring_units']=list(bone.matrix_local.inverted()@point);anchor['status']='Updated for batch02 muzzle geometry; engine direction/playback untested'
  m['texture_atlas']={'size':2048,'maps':['textures/Siege_Sentinel_Batch02_'+t+'.png' for t in ['basecolor','normal','roughness','metallic']]};m['visual_status']='Partial geometry revision; realistic full-body target unfinished';meta.write_text(json.dumps(m,indent=2))
 if meta.parent.parent.name=='weapons':
  for a in bpy.data.actions:a.name=a.name.replace(name+'_','')
  for c in m['clips']:c['name']=c['name'].replace(name+'_','')
  meta.write_text(json.dumps(m,indent=2))
 for im in bpy.data.images:
  path=P/'textures'/Path(im.filepath).name
  if path.exists():im.filepath=str(path)
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
 bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS')
 for im in bpy.data.images:
  if (P/'textures'/Path(im.filepath).name).exists():im.filepath='//../../textures/'+Path(im.filepath).name
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')))
 for level,ratio in [(1,.55 if name=='Siege_Sentinel' else .6),(2,.28 if name=='Siege_Sentinel' else .3)]:
  d=mesh.modifiers.new('LOD','DECIMATE');d.ratio=ratio
  for im in bpy.data.images:
   path=P/'textures'/Path(im.filepath).name
   if path.exists():im.filepath=str(path)
  bpy.ops.export_scene.fbx(filepath=str(folder/(name+'_LOD'+str(level)+'.fbx')),use_selection=True,path_mode='COPY',embed_textures=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y');mesh.modifiers.remove(d)
 authoring=folder/(name+'_Authoring.blend');bpy.ops.wm.open_mainfile(filepath=str(authoring));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(authoring));print('FINALIZED',name,flush=True)
