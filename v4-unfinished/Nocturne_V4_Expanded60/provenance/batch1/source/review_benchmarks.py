import sys,bpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from benchmark_models import build,P
from build_creatures import render
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Cinder_Crown']
c=build(args[0]);render(c,c.name+'_review.png');bpy.ops.wm.save_as_mainfile(filepath=str(P/(c.name+'_working.blend')));print('V4_MODEL_REVIEW',c.name,len(c.meshobj.data.vertices),flush=True)
