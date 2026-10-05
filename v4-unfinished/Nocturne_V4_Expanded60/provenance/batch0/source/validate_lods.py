import bpy,json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];results=[]
for mp in sorted(P.glob('*/*/asset.json')):
 m=json.loads(mp.read_text())
 for level in [1,2]:
  bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
  p=mp.parent/(m['name']+'_LOD'+str(level)+'.fbx');bpy.ops.import_scene.fbx(filepath=str(p))
  rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=sum(len(q.vertices)-2 for o in meshes for q in o.data.polygons)
  weights=max([abs(sum(g.weight for g in v.groups)-1) for o in meshes for v in o.data.vertices],default=999)
  r={'asset':m['name'],'lod':level,'triangles':tri,'bones':len(rigs[0].data.bones) if len(rigs)==1 else -1,'max_weight_sum_error':weights,'passed':len(rigs)==1 and len(meshes)==1 and len(rigs[0].data.bones)==m['bones'] and tri<m['triangles'] and weights<.001}
  results.append(r);print(r,flush=True)
(P/'lod_validation.json').write_text(json.dumps(results,indent=2))
assert len(results)==60 and all(r['passed'] for r in results)
