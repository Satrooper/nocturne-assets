import bpy,json,math
from pathlib import Path
from mathutils import Vector
import sys
sys.path.insert(0,str(Path(__file__).parent))
from studio_helpers import load,studio,aim
W=Path(__file__).resolve().parents[2];P=W/'Nocturne_Quality_Repair';rows=json.loads((P/'audit/Repair_Progress.json').read_text());results=[];progress=P/'audit/Repair_Validation.json';oldrows={c['asset']:c for c in json.loads((W/'Nocturne_V4_Visual_Revision/asset_manifest.json').read_text())['characters']};newrows={c['asset']:c for c in json.loads((W/'Nocturne_Expansion_60/audit/Build_Progress.json').read_text())}
if progress.exists():results=json.loads(progress.read_text())
for row in rows:
 name=row['asset']
 if '--' in sys.argv and sys.argv[-1]!=name:continue
 if any(x['asset']==name for x in results):continue
 base=W/('Nocturne_Expansion_60' if row['added_to_60_pack'] else 'Nocturne_V4_Visual_Revision');original=(newrows if row['added_to_60_pack'] else oldrows)[name];before=base/original['canonical_glb'];after=P/row['canonical_glb'];folder=P/'previews'/name;folder.mkdir(parents=True,exist_ok=True)
 r,mesh,lo,hi=load(before);r,mesh,lo2,hi2=load(after);unionlo=Vector(tuple(min(lo[i],lo2[i]) for i in range(3)));unionhi=Vector(tuple(max(hi[i],hi2[i]) for i in range(3)));rec={'asset':name,'before_glb':str(before.relative_to(W)),'after_glb':row['canonical_glb'],'neutral_lighting_and_framing_identical':True,'formats':{},'cinematic_quality_approved':False,'visual_review':'Candidate; no automatic quality approval from polygon count or rendering','engine_tested':False}
 for label,file in [('Before',before),('After',after)]:
  r,meshes,lo,hi=load(file);rec[label+'_clips']=len(bpy.data.actions);sc,cam,center,extent=studio(unionlo,unionhi);pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];sc.render.resolution_x=512;sc.render.resolution_y=512
  for view,direction in [('Threequarter',(1,-1,.35)),('Front',(0,-1,.14))]:
   cam.location=center+Vector(direction).normalized()*extent*3;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=extent*1.16;sc.render.filepath=str(folder/(label+'_'+view+'.jpg'));bpy.ops.render.render(write_still=True)
  if label=='After':
   aim(cam,r.matrix_world@r.data.bones['head'].head_local,extent,(1,-1,.20),pts,True);sc.render.filepath=str(folder/'After_Closeup.jpg');bpy.ops.render.render(write_still=True)
   sampled=[];dg=bpy.context.evaluated_depsgraph_get();actions=list(bpy.data.actions)
   for a in actions:
    r.animation_data.action=a
    for frame in [a.frame_range.x,(a.frame_range.x+a.frame_range.y)/2,a.frame_range.y]:
     sc.frame_set(round(frame));dg.update()
     for o in meshes:
      ev=o.evaluated_get(dg);me=ev.to_mesh();assert all(math.isfinite(c) for v in me.vertices for c in v.co);ev.to_mesh_clear()
    sampled.append(a.name)
   rec['sampled_deformation']={'clips':len(sampled),'frames_per_clip':3,'finite':True,'clipping_contact_approved':False}
   rec['formats']['glb']={'reimport_passed':True,'bones':len(r.data.bones),'clips':len(actions),'bone_names_match':set(b.name for b in r.data.bones)==set(row['bones'])};assert rec['formats']['glb']['bone_names_match'];assert len(actions)==row['clips']
 r,meshes,lo,hi=load(P/row['canonical_fbx']);assert set(b.name for b in r.data.bones)==set(row['bones']);assert len(bpy.data.actions)==row['clips'];rec['formats']['fbx']={'reimport_passed':True,'bones':len(r.data.bones),'clips':len(bpy.data.actions),'bone_names_match':True};results.append(rec);progress.write_text(json.dumps(results,indent=2));print('QUALITY_REVIEW_RENDERED',name,flush=True)
