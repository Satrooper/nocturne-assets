import bpy,json,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_creatures import Creature,ROSTER,P,clear,render
from animation_library import animate
records=[]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
start=int(args[0]) if args else 0;stop=int(args[1]) if len(args)>1 else len(ROSTER)
for i in range(start,stop):
 clear();c=Creature(ROSTER[i],i);c.construct();clips=animate(c);folder=P/c.cat/c.name;folder.mkdir(parents=True,exist_ok=True)
 scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=120;scene.render.fps=30
 # Keep texture paths relative for the editable source and FBX bundle.
 for im in bpy.data.images:
  if im.source=='FILE':im.filepath=str(P/'textures'/Path(im.filepath).name)
 c.rig.animation_data.action=None
 for pb in c.rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 bpy.ops.object.select_all(action='DESELECT');c.meshobj.select_set(True);c.rig.select_set(True);bpy.context.view_layer.objects.active=c.rig
 bpy.ops.export_scene.fbx(filepath=str(folder/(c.name+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=.1,path_mode='RELATIVE',use_mesh_modifiers=True)
 c.rig.animation_data.action=list(bpy.data.actions)[0]
 bpy.ops.export_scene.gltf(filepath=str(folder/(c.name+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_materials='EXPORT')
 c.rig.animation_data.action=None
 for pb in c.rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 triangles=sum(len(p.vertices)-2 for p in c.meshobj.data.polygons)
 # Save source with portable texture references.
 for im in bpy.data.images:
  if im.source=='FILE':im.filepath='//../../textures/'+Path(im.filepath).name
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/(c.name+'.blend')),relative_remap=False)
 # Lower detail FBXs retain the same skeleton, without duplicated animation banks.
 lods=[];original=c.meshobj.data.copy()
 for level,ratio in [(1,.55),(2,.28)]:
  c.meshobj.data=original.copy();bpy.context.view_layer.objects.active=c.meshobj
  mod=c.meshobj.modifiers.new('LOD','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name)
  tris=sum(len(p.vertices)-2 for p in c.meshobj.data.polygons);lods.append({'level':level,'triangles':tris})
  bpy.ops.export_scene.fbx(filepath=str(folder/(c.name+'_LOD'+str(level)+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',use_mesh_modifiers=True)
 c.meshobj.data=original
 # Restore absolute paths for render after saving the portable project.
 for im in bpy.data.images:
  if im.source=='FILE':im.filepath=str(P/'textures'/Path(im.filepath).name)
 render(c,c.name+'.png')
 if i==0:render(c,c.name+'_closeup.png',True)
 record={'name':c.name,'category':c.cat,'body_type':c.kind,'triangles':triangles,'bones':len(c.bones),'materials':len(c.meshobj.data.materials),'clips':clips,'lods':lods,'textures':'2048px basecolor/normal/roughness; original procedural PBR','skin_weights':'interpolated along anatomical tubes; rigid detail attachments','provenance':'original procedural artwork; not extracted franchise content','quality_status':'requires artistic and engine review; not photorealistic or motion-captured'}
 (folder/'asset.json').write_text(json.dumps(record,indent=2));records.append(record);print('FINISHED_ASSET',c.name,triangles,len(clips),flush=True)
(P/('manifest_'+str(start)+'_'+str(stop)+'.json')).write_text(json.dumps(records,indent=2))
