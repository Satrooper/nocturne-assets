import bpy,sys,json
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_creatures import P,render
for meta in sorted(P.glob('*/*/asset.json')):
 m=json.loads(meta.read_text());folder=meta.parent;bpy.ops.wm.open_mainfile(filepath=str(folder/(m['name']+'.blend')))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
 render(SimpleNamespace(rig=rig,meshobj=mesh),m['name']+'.png')
 print('PREVIEW',m['name'],flush=True)
