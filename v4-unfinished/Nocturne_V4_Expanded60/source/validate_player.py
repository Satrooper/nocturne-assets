import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];F=P/'player_handling';meta=json.load(open(F/'handling_manifest.json'));reports=[];motion=[];QR=Matrix(((-1,0,0),(0,0,-1),(0,-1,0))).to_quaternion()
for path in [F/'Player_With_Firearms.fbx',F/'Player_With_Firearms.glb']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
 if path.suffix=='.glb':bpy.ops.import_scene.gltf(filepath=str(path))
 else:bpy.ops.import_scene.fbx(filepath=str(path))
 r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)];r.animation_data_create();r.animation_data.action=None
 for t in r.animation_data.nla_tracks:t.mute=True
 acts={a.name.split('|')[-1].removesuffix('_'+r.name):a for a in bpy.data.actions};missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];weight=max(abs(sum(g.weight for g in v.groups)-1) for o in meshes for v in o.data.vertices);report={'file':str(path.relative_to(P)),'actions':list(acts),'bones':len(r.data.bones),'skinned_meshes':len(meshes),'missing_textures':missing,'weight_sum_error':weight,'finite_vertices':all(math.isfinite(x) for o in meshes for v in o.data.vertices for x in v.co),'expected_actions_present':all(c['name'] in acts for c in meta['clips']),'engine_tested':False};report['passed']=report['expected_actions_present'] and not missing and report['finite_vertices'] and weight<.002;reports.append(report)
 if path.suffix!='.glb':continue
 bpy.context.scene.render.fps=30
 for clip in meta['clips']:
  r.animation_data.action=acts[clip['name']];first=acts[clip['name']].frame_range[0];samples=[];feet0=None
  for frame in clip['frames']:
   f=first+frame['time_s']*30;bpy.context.scene.frame_set(round(f));bpy.context.view_layer.update();hand=r.matrix_world@r.pose.bones['mixamorig:RightHand'].matrix;held=frame['held'];primary=None;support=None
   if held:
    scale=1 if held=='Pistol' else .82;expected=hand.translation+(hand.to_quaternion()@QR.inverted())@(Vector((0,-.022,-.15))+Vector((0,.014 if held=='Pistol' else .028,0))*scale);actual=r.matrix_world@r.pose.bones['W_'+held+'_grip'].head;primary=(actual-expected).length
    if frame['left_contact']=='support':
     left=r.matrix_world@r.pose.bones['mixamorig:LeftHand'].matrix;lp=left.translation+left.to_quaternion()@Vector((0,.10,0));support=(lp-r.matrix_world@r.pose.bones['W_'+held+'_support'].head).length
   feet=[r.matrix_world@r.pose.bones['mixamorig:'+s+'Foot'].head for s in ['Left','Right']]
   if feet0 is None:feet0=[x.copy() for x in feet]
   samples.append({'time_s':frame['time_s'],'primary_marker_error_m':primary,'support_marker_error_m':support,'feet_joint_drift_m':max((a-b).length for a,b in zip(feet,feet0))})
  motion.append({'clip':clip['name'],'max_primary_marker_error_m':max((s['primary_marker_error_m'] for s in samples if s['primary_marker_error_m'] is not None),default=0),'max_support_marker_error_m':max((s['support_marker_error_m'] for s in samples if s['support_marker_error_m'] is not None),default=0),'max_foot_joint_drift_m':max(s['feet_joint_drift_m'] for s in samples),'samples':samples,'status':'marker measurements; skin collision/finger contact not certified'})
(P/'audit/Player_Export_Validation.json').write_text(json.dumps(reports,indent=2));(P/'audit/Player_Delivered_Contact_Checks.json').write_text(json.dumps(motion,indent=2));print('STRUCTURAL',all(r['passed'] for r in reports));print('MARKERS',[(x['clip'],x['max_primary_marker_error_m'],x['max_support_marker_error_m']) for x in motion]);assert all(r['passed'] for r in reports)
