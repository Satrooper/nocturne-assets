import bpy,json,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from studio_helpers import load,studio
P=Path(__file__).resolve().parents[1]
rows=json.loads((P/'audit/Repair_Progress.json').read_text())
row=next(x for x in rows if x['asset']=='Iron_Executioner')
r,meshes,lo,hi=load(P/row['canonical_glb']);sc,cam,center,extent=studio(lo,hi)
sc.render.resolution_x=384;sc.render.resolution_y=384;sc.cycles.samples=6
cam.location=center+Vector((1,-1,.35)).normalized()*extent*3;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=extent*1.3
act=next(a for a in bpy.data.actions if 'Walk_InPlace' in a.name);r.animation_data.action=act
folder=P/'previews'/'Iron_Executioner';frames=[]
for i in range(12):
 f=round(act.frame_range.x+(act.frame_range.y-act.frame_range.x)*i/12);sc.frame_set(f);file=folder/('Motion_%02d.jpg'%i);sc.render.filepath=str(file);bpy.ops.render.render(write_still=True);frames.append({'frame':f,'image':str(file.relative_to(P))})
(folder/'Motion.json').write_text(json.dumps({'source':row['canonical_glb'],'animation':act.name,'fps':30,'duration_s':(act.frame_range.y-act.frame_range.x)/30,'frames':frames,'contact_clipping_approved':False},indent=2))
print('MOTION_FRAMES_SAVED',flush=True)
