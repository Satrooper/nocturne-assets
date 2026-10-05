import bpy,json,math,struct,io,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];results=[]
for meta in sorted(P.glob('*/*/asset.json')):
 m=json.loads(meta.read_text());folder=meta.parent;expected={c['name'] for c in m['clips']};r={'asset':m['name'],'structural':{},'kinematic':{},'engine_tested':False}
 for ext in ['fbx','glb']:
  bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
  bpy.ops.import_scene.fbx(filepath=str(folder/(m['name']+'.fbx'))) if ext=='fbx' else bpy.ops.import_scene.gltf(filepath=str(folder/(m['name']+'.glb')))
  rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render and any(mod.type=='ARMATURE' for mod in o.modifiers)];actions=list(bpy.data.actions);names={a.name.split('|')[-1] for a in actions};rig=rigs[0];mesh=meshes[0]
  names={a.name.split('|')[-1].removesuffix('_'+rig.name) for a in actions}
  for track in rig.animation_data.nla_tracks:track.mute=True
  weight_error=max(abs(sum(g.weight for g in v.groups)-1) for v in mesh.data.vertices);finite=all(math.isfinite(x) for v in mesh.data.vertices for x in v.co)
  r['structural'][ext]={'rigs':len(rigs),'meshes':len(meshes),'clips':len(actions),'names_match':names==expected,'finite_vertices':finite,'max_weight_sum_error':weight_error,'passed':len(rigs)==1 and len(meshes)==1 and names==expected and finite and weight_error<.001}
  if ext=='glb':
   reviews=[]
   for clip in m['clips']:
    act=next(a for a in actions if a.name.split('|')[-1].removesuffix('_'+rig.name)==clip['name']);rig.animation_data_create();rig.animation_data.action=act;start,last=act.frame_range;positions=[];vertex=[]
    for f in [start,start+(last-start)*.4,last]:
     bpy.context.scene.frame_set(int(f));bpy.context.view_layer.update();positions.append({b.name:list(rig.matrix_world@b.head) for b in rig.pose.bones});ob=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ob.to_mesh();vertex.append([ob.matrix_world@me.vertices[i].co for i in range(0,len(me.vertices),max(1,len(me.vertices)//300))]);ob.to_mesh_clear()
    delta=[positions[2]['root'][i]-positions[0]['root'][i] for i in range(3)];expected_delta=clip['root_displacement_m'];root_error=math.dist(delta,expected_delta);loop_error=0
    if clip['loop']:
     for n in positions[0]:loop_error=max(loop_error,math.dist([positions[0][n][i]-positions[0]['root'][i] for i in range(3)],[positions[2][n][i]-positions[2]['root'][i] for i in range(3)]))
    moving=max((x-y).length for va in vertex[1:] for x,y in zip(vertex[0],va))>1e-5
    contacts={}
    for pre,data in clip['contacts'].items():
     drift=[]
     for a,b in data['stance_intervals']:
      sample=[]
      for ts in [a+.075,b-.075]:
       if ts<a or ts>b:continue
       f=start+ts*30;bpy.context.scene.frame_set(int(f),subframe=f-int(f));bpy.context.view_layer.update();point=rig.matrix_world@rig.pose.bones[data['bone']].head
       if clip['name'] in ['Walk_InPlace','Run_InPlace']:
        point.y-=clip.get('in_place_speed_mps',0)*ts
       sample.append(point)
      if len(sample)==2:drift.append((sample[-1]-sample[0]).length)
     contacts[pre]={'max_stance_anchor_drift_m':max(drift,default=0),'note':'bone endpoint measurement; not sole mesh/engine collision'}
    reviews.append({'clip':clip['name'],'moving':moving,'root_delta_error_m':root_error,'loop_pose_error_m':loop_error,'contacts':contacts,'loop_pose_passed':not clip['loop'] or loop_error<.01,'root_delta_passed':root_error<.015})
   r['kinematic']={'clips':reviews,'all_moving':all(c['moving'] for c in reviews),'all_root_delta_passed':all(c['root_delta_passed'] for c in reviews),'all_loop_pose_passed':all(c['loop_pose_passed'] for c in reviews)}
 r['structural_passed']=all(v['passed'] for v in r['structural'].values());results.append(r);print('REIMPORT',m['name'],r['structural_passed'],r['kinematic']['all_moving'],r['kinematic']['all_root_delta_passed'],r['kinematic']['all_loop_pose_passed'],flush=True)
(P/'benchmark_validation.json').write_text(json.dumps(results,indent=2))
