import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];r=[]
for f in sorted(P.glob('*/*/*_LOD*.fbx')):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(f));rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];mesh=meshes[0];w=max(abs(sum(g.weight for g in v.groups)-1) for v in mesh.data.vertices);missing=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists():missing.append(im.filepath)
 item={'file':str(f.relative_to(P)),'rigs':len(rigs),'meshes':len(meshes),'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'finite_vertices':all(math.isfinite(x) for v in mesh.data.vertices for x in v.co),'max_weight_sum_error':w,'missing_external_textures':missing};item['passed']=len(rigs)==1 and len(meshes)==1 and item['finite_vertices'] and w<.001 and not missing;r.append(item);print('LOD_REIMPORT',f.name,item['passed'],flush=True)
(P/'lod_validation.json').write_text(json.dumps(r,indent=2))
