import bpy,json,math,struct,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
paths=sorted(P.glob('*/*/asset.json'))
resume='--remaining' in args
if args and not resume:paths=[p for p in paths if p.parent.name==args[0]]
results=json.loads((P/'validation.json').read_text()) if resume and (P/'validation.json').exists() else []
if resume:
 done={r['name'] for r in results if r['passed']}
 paths=[p for p in paths if p.parent.name not in done]
for meta in paths:
 m=json.loads(meta.read_text());folder=meta.parent;name=m['name'];expected={a['name'] for a in m['clips']}
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 bpy.ops.import_scene.fbx(filepath=str(folder/(name+'.fbx')))
 rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];actions=list(bpy.data.actions)
 names={a.name.split('|')[-1] for a in actions};finite=all(math.isfinite(x) for o in meshes for v in o.data.vertices for x in v.co)
 movement=[]
 if len(rigs)==1 and len(meshes)==1:
  rig=rigs[0];mesh=meshes[0]
  for a in actions:
   rig.animation_data.action=a;sample=[]
   for frac in [0,.37,.64]:
    bpy.context.scene.frame_set(int(a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*frac));bpy.context.view_layer.update()
    ob=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ob.to_mesh();sample.append([ob.matrix_world @ me.vertices[i].co for i in range(0,len(me.vertices),max(1,len(me.vertices)//200))]);ob.to_mesh_clear()
   movement.append(max((x-y).length for a0 in sample[1:] for x,y in zip(sample[0],a0))>1e-6)
  weight_error=max(abs(sum(g.weight for g in v.groups)-1) for v in mesh.data.vertices)
 else:weight_error=999
 data=(folder/(name+'.glb')).read_bytes();ln,typ=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+ln]);glbnames={a.get('name') for a in doc.get('animations',[])}
 # .blend source must locate all texture images after relocation by relative paths.
 texture_files=[p for p in (P/'textures').glob('*.png')];textures_present=len(texture_files)==51
 lod_ok=all((folder/(name+'_LOD'+str(j)+'.fbx')).stat().st_size>10000 for j in [1,2])
 # glTF images must be embedded and every bufferView lie within the declared buffer.
 images_embedded=all('bufferView' in im for im in doc.get('images',[])) and len(doc.get('images',[]))>0
 buffers_valid=all(v.get('byteOffset',0)+v['byteLength']<=doc['buffers'][v.get('buffer',0)]['byteLength'] for v in doc.get('bufferViews',[]))
 r={'name':name,'fbx_meshes':len(meshes),'fbx_rigs':len(rigs),'fbx_clips':len(actions),'glb_clips':len(glbnames),'expected_clips':len(expected),'all_names_match':names==expected and glbnames==expected,'moving_clips':sum(movement),'finite_mesh':finite,'max_weight_sum_error':weight_error,'embedded_pbr_images':images_embedded,'buffer_bounds_valid':buffers_valid,'texture_files_present':textures_present,'lod_files_present':lod_ok}
 bpy.ops.wm.open_mainfile(filepath=str(folder/(name+'.blend')))
 source_images=[im for im in bpy.data.images if im.source=='FILE'];r['source_textures_resolve']=bool(source_images) and all(Path(bpy.path.abspath(im.filepath)).is_file() for im in source_images)
 r['passed']=len(rigs)==1 and len(meshes)==1 and names==expected and glbnames==expected and all(movement) and len(movement)==len(expected) and finite and weight_error<.001 and images_embedded and buffers_valid and textures_present and lod_ok and r['source_textures_resolve']
 results.append(r);print(json.dumps(r),flush=True)
(P/('validation_'+args[0]+'.json' if args and not resume else 'validation.json')).write_text(json.dumps(results,indent=2))
if not all(r['passed'] for r in results):raise RuntimeError('Asset validation failed')
