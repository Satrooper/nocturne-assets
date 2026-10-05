import bpy,sys,json,struct
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for folder in [P/'dragons/Cinder_Crown',P/'bosses/Siege_Sentinel']:
 name=folder.name
 for suffix in ['', '_Authoring']:
  filepath=folder/(name+suffix+'.blend');bpy.ops.wm.open_mainfile(filepath=str(filepath));bpy.context.preferences.filepaths.save_version=0
  for im in bpy.data.images:
   if im.source=='FILE':im.filepath='//../../textures/'+Path(im.filepath).name
  bpy.ops.wm.save_as_mainfile(filepath=str(filepath),relative_remap=False,compress=True)
  if name=='Cinder_Crown' and not suffix:
   bpy.ops.object.select_all(action='DESELECT')
   for o in bpy.context.scene.objects:
    if o.type in ['ARMATURE','MESH']:o.select_set(True)
   rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');bpy.context.view_layer.objects.active=rig;rig.animation_data.action=None
   bpy.ops.export_scene.fbx(filepath=str(folder/(name+'_fresh.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='RELATIVE')
   dest=folder/(name+'_fresh.fbx');data=dest.read_bytes();off=27
   while off+13<len(data):
    end,_,_,_=struct.unpack_from('<IIIB',data,off)
    if not end:break
    assert off<end<=len(data),'Malformed FBX export';off=end
   dest.replace(folder/(name+'.fbx'));print('FRESH_FBX_SIZE',len(data),flush=True)
