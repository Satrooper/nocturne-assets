import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];mode=sys.argv[-1];results=[]
def load(path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
 if path.suffix=='.glb':bpy.ops.import_scene.gltf(filepath=str(path))
 else:bpy.ops.import_scene.fbx(filepath=str(path))
 rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];rig=rigs[0];meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 for o in list(bpy.context.scene.objects):
  if o.type=='MESH' and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
 rig.animation_data_create()
 for t in rig.animation_data.nla_tracks:t.mute=True
 rig.animation_data.action=None
 for b in rig.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
 bpy.context.scene.frame_set(1);return rig,meshes
if mode=='validate':
 for meta in sorted(P.glob('*/*/asset.json')):
  m=json.loads(meta.read_text());expected={c['name'] for c in m['clips']}
  for path in sorted(meta.parent.glob('*.fbx'))+sorted(meta.parent.glob('*.glb')):
   rig,meshes=load(path);names={a.name.split('|')[-1].removesuffix('_'+rig.name) for a in bpy.data.actions};finite=all(math.isfinite(x) for o in meshes for v in o.data.vertices for x in v.co);err=max((abs(sum(g.weight for g in v.groups)-1) for o in meshes for v in o.data.vertices),default=1);tri=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons);missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];motion=[]
   if 'LOD' not in path.name:
    for a in bpy.data.actions:
     rig.animation_data.action=a;first,last=a.frame_range;poses=[]
     for t in [0,.15,.5,.85,1]:
      f=first+(last-first)*t;bpy.context.scene.frame_set(int(f),subframe=f-int(f));poses.append([list(rig.matrix_world@b.head) for b in rig.pose.bones])
     motion.append({'name':a.name,'sampled_joint_movement_m':max(math.dist(p[j],poses[0][j]) for p in poses for j in range(len(p)))})
   passed=finite and err<.002 and not missing and (not expected or 'LOD' in path.name or expected<=names)
   results.append({'file':str(path.relative_to(P)),'rig_bones':len(rig.data.bones),'mesh_count':len(meshes),'triangles':tri,'finite_vertices':finite,'max_weight_sum_error':err,'missing_texture_paths':missing,'action_names':sorted(names),'expected_actions_present':expected<=names if 'LOD' not in path.name else None,'sampled_motion':motion,'structural_passed':passed,'engine_tested':False});print('VALIDATED',path.name,passed,flush=True)
 (P/'audit/Export_Reimport_Validation.json').write_text(json.dumps(results,indent=2));assert all(r['structural_passed'] for r in results)
else:
 def studio(rig,meshes,camera_position,target,scale,width=800,height=800):
  scene=bpy.context.scene;scene.world=bpy.data.worlds.new('Neutral_world');scene.world.color=(.17,.17,.17);scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.resolution_x=width;scene.render.resolution_y=height;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX'
  for loc,power,size in [((4,-4,8),1000,5),((-5,-3,4),700,5),((0,5,7),1100,4)]:
   bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add(location=camera_position);cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.camera=cam
  return scene
 for label,path in [('Before',P.parent/'nocturne-v4/bosses/Siege_Sentinel/Siege_Sentinel.glb'),('After',P/'bosses/Siege_Sentinel/Siege_Sentinel.glb')]:
  for view,loc,target,scale in [('Front',(0,-12,2.5),(0,0,2.5),5.9),('Side',(12,0,2.5),(0,0,2.5),5.9),('Back',(0,12,2.5),(0,0,2.5),5.9),('Closeup',(4,-8,5.2),(0,0,4.25),2.8)]:
   output=P/'previews'/('Sentinel_'+label+'_'+view+'.png')
   if output.exists():continue
   rig,meshes=load(path);scene=studio(rig,meshes,loc,target,scale);scene.render.filepath=str(output);bpy.ops.render.render(write_still=True)
 for meta in P.glob('weapons/*/asset.json'):
  name=meta.parent.name;rig,meshes=load(meta.parent/(name+'.glb'));pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);center=(lo+hi)/2;size=max(hi-lo);scene=studio(rig,meshes,center+Vector((2,-.6,1.2)),center,size*1.3,1100,720);cam=scene.camera;inv=cam.rotation_euler.to_matrix().transposed();projected=[inv@(p-center) for p in pts];cam.data.ortho_scale=max(max(v.x for v in projected)-min(v.x for v in projected),(max(v.y for v in projected)-min(v.y for v in projected))*1100/720)*1.20;scene.render.filepath=str(P/'previews'/(name+'_Neutral.png'));bpy.ops.render.render(write_still=True)
 for name,path,keyword in [('Sentinel',P/'bosses/Siege_Sentinel/Siege_Sentinel.glb','Walk_InPlace'),('Rifle',P/'weapons/Bastion_Rifle/Bastion_Rifle.glb','Mechanical_Reload')]:
  rig,meshes=load(path);act=next(a for a in bpy.data.actions if keyword in a.name);rig.animation_data.action=act
  if name=='Sentinel':scene=studio(rig,meshes,(7,-10,4),(0,0,2.5),6.1,480,480)
  else:scene=studio(rig,meshes,(2,-.6,1.3),(0,-.12,.04),1.5,480,360)
  scene.cycles.samples=4;scene.render.use_persistent_data=True;folder=P/'previews'/('frames_'+name);folder.mkdir(exist_ok=True);first,last=act.frame_range
  for i in range(16):
   f=first+(last-first)*i/15;scene.frame_set(int(f),subframe=f-int(f));scene.render.filepath=str(folder/(str(i).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
 rig,meshes=load(P/'bosses/Siege_Sentinel/Siege_Sentinel.glb');scene=studio(rig,meshes,(6,-10,3.8),(0,0,2.5),6.2,1100,800)
 for i,o in enumerate(o for o in scene.objects if o.type=='LIGHT'):o.data.color=[(1,.68,.38),(.30,.54,1),(.42,.68,1)][i]
 scene.world.color=(.025,.028,.04);scene.cycles.samples=24;scene.render.filepath=str(P/'previews/Sentinel_Additional_Presentation.png');bpy.ops.render.render(write_still=True)
 print('PREVIEWS_FINISHED',flush=True)
