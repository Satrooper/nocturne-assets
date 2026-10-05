import bpy,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from benchmark_models import build,P
from benchmark_motion import animate_benchmark
from texture_bake import bake
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Cinder_Crown']
name=args[0];c=build(name);clips=animate_benchmark(c);cat='dragons' if name=='Cinder_Crown' else 'bosses';folder=P/cat/name;folder.mkdir(parents=True,exist_ok=True);bpy.context.scene.render.fps=30
for im in bpy.data.images:
 if im.source=='FILE':im.filepath=str(P/'textures'/Path(im.filepath).name)
# Artist-editable material/mesh source before flattening material graphs into texture atlases.
bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'_Authoring.blend')),compress=True)
bake(c,P)
for pb in c.rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
c.rig.animation_data.action=None;bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT');c.meshobj.select_set(True);c.rig.select_set(True);bpy.context.view_layer.objects.active=c.rig
bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='RELATIVE')
c.rig.animation_data.action=list(bpy.data.actions)[0];bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_materials='EXPORT')
c.rig.animation_data.action=None
for pb in c.rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
for im in bpy.data.images:
 if im.source=='FILE':im.filepath='//../../textures/'+Path(im.filepath).name
bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')),relative_remap=False,compress=True)
triangles=sum(len(p.vertices)-2 for p in c.meshobj.data.polygons);original=c.meshobj.data.copy();lods=[]
for level,ratio in [(1,.55),(2,.28)]:
 c.meshobj.data=original.copy();bpy.context.view_layer.objects.active=c.meshobj;mod=c.meshobj.modifiers.new('LOD','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name);lods.append({'level':level,'triangles':sum(len(p.vertices)-2 for p in c.meshobj.data.polygons)})
 bpy.ops.export_scene.fbx(filepath=str(folder/(name+'_LOD'+str(level)+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE')
c.meshobj.data=original
meta={'name':name,'revision':4,'category':cat,'triangles':triangles,'bones':len(c.rig.data.bones),'clips':clips,'lods':lods,'texture_atlas':{'resolution':2048,'maps':['basecolor','normal','roughness','metallic'],'uv':'non-overlapping smart-projected atlas; margin baked at 12px; artist cleanup still required'},'engine_tested':False,'visual_status':'review required; procedural modelling/volume reconstruction, not a manual production sculpt or quad retopology','sockets':{'root':'root','weapon_hand_L':'armL_hand' if name=='Siege_Sentinel' else 'frontL_foot','weapon_hand_R':'armR_hand' if name=='Siege_Sentinel' else 'frontR_foot','mouth':'head','breath_origin_local':[0,-3.64,2.34] if name=='Cinder_Crown' else None,'muzzle_L':'turretL_recoil' if name=='Siege_Sentinel' else None,'muzzle_R':'turretR_recoil' if name=='Siege_Sentinel' else None},'hit_windows_status':'authoring contact cues; not validated damage windows','contacts_status':'IK target-derived bone stance samples, to be checked on exported skeleton; not engine collision data'}
(folder/'asset.json').write_text(json.dumps(meta,indent=2));print('V4_BENCHMARK_EXPORTED',name,triangles,len(clips),flush=True)
