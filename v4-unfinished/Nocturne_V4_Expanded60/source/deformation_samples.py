import bpy,json,os,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];rows=json.loads((P/'asset_manifest.json').read_text())['characters'];report=[]
for row in rows:
 f=P/row['category']/row['asset']/(row['asset']+'.glb');bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(f));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data_create()
 for tr in rig.animation_data.nla_tracks:tr.mute=True
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)];clips=[]
 for a in bpy.data.actions:
  for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
  rig.animation_data.action=a;lo,hi=a.frame_range;samples=[]
  for t in [0,.5,1]:
   frame=lo+(hi-lo)*t;bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));dg=bpy.context.evaluated_depsgraph_get();bounds=[];finite=True
   for o in meshes:
    e=o.evaluated_get(dg);m=e.to_mesh();co=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',co);co=co.reshape(-1,3);mat=np.array(e.matrix_world);world=co@mat[:3,:3].T+mat[:3,3];finite=finite and bool(np.isfinite(world).all());bounds.append([world.min(axis=0).tolist(),world.max(axis=0).tolist()]);e.to_mesh_clear()
   samples.append({'frame':frame,'finite_deformed_vertices':finite,'world_bounds':bounds})
  clips.append({'clip':a.name,'samples':samples,'ground_penetration_requires_review':any(b[0][2]<-.03 for s in samples for b in s['world_bounds']),'clipping_or_contact_approved':False})
 report.append({'asset':row['asset'],'source':str(f.relative_to(P)),'clips':clips,'structural_deformation_samples_passed':all(s['finite_deformed_vertices'] for c in clips for s in c['samples']),'visual_deformation_approval':False,'engine_tested':False})
 with (P/'audit/Deformed_Geometry_Samples.json').open('w') as h:json.dump(report,h,indent=2);h.flush();os.fsync(h.fileno())
 print('DEFORMATION_SAMPLED',row['asset'],len(clips),flush=True)
assert all(r['structural_deformation_samples_passed'] for r in report)
