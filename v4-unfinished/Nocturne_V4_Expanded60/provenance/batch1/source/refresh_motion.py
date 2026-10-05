import bpy,sys,json,struct
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parent));from benchmark_motion import animate_benchmark
P=Path(__file__).resolve().parents[1];name=sys.argv[sys.argv.index('--')+1];folder=P/('dragons' if name=='Cinder_Crown' else 'bosses')/name
for suffix in ['_Authoring','']:
 f=folder/(name+suffix+'.blend');bpy.ops.wm.open_mainfile(filepath=str(f));bpy.context.preferences.filepaths.save_version=0;rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 clips=animate_benchmark(SimpleNamespace(name=name,rig=rig));bpy.context.scene.render.fps=30
 for im in bpy.data.images:
  if im.source=='FILE':im.filepath='//../../textures/'+Path(im.filepath).name
 bpy.ops.wm.save_as_mainfile(filepath=str(f),relative_remap=False,compress=True)
 if not suffix:
  bpy.ops.object.select_all(action='DESELECT')
  for ob in bpy.context.scene.objects:
   if ob.type in ['MESH','ARMATURE']:ob.select_set(True)
  bpy.context.view_layer.objects.active=rig
  dest=folder/(name+'_temp.fbx');bpy.ops.export_scene.fbx(filepath=str(dest),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='RELATIVE');d=dest.read_bytes();off=27
  while off+13<len(d):
   end,_,_,_=struct.unpack_from('<IIIB',d,off)
   if not end:break
   assert off<end<=len(d),'Malformed FBX export';off=end
  dest.replace(folder/(name+'.fbx'));rig.animation_data.action=list(bpy.data.actions)[0];dest=folder/(name+'_temp.glb');bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS');dest.replace(folder/(name+'.glb'));rig.animation_data.action=None
m=json.loads((folder/'asset.json').read_text());m['clips']=clips;(folder/'asset.json').write_text(json.dumps(m,indent=2));print('MOTION_REFRESH_DONE',name,flush=True)
