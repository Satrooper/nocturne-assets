import bpy,sys,json,math,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];BASE=P.parent/'Nocturne_V4_Full_Pack';ONLY=sys.argv[-1] if '--' in sys.argv else 'all'
rows=json.loads((BASE/'asset_manifest.json').read_text())['characters']
def load(file):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(file));r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');r.animation_data_create();r.animation_data.action=None
 for t in r.animation_data.nla_tracks:t.mute=True
 for b in r.pose.bones:b.rotation_quaternion=(1,0,0,0);b.rotation_euler=(0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
 bpy.context.view_layer.update();meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 for extra in list(bpy.context.scene.objects):
  if extra.type=='MESH' and extra not in meshes:bpy.data.objects.remove(extra,do_unlink=True)
 pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];lo=Vector(tuple(min(v[i] for v in pts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in pts) for i in range(3)))
 return r,lo,hi
progress=P/'audit/Neutral_Preview_Progress.json';done=json.loads(progress.read_text()) if progress.exists() else []
for row in rows:
 name=row['asset'];cat=row['category']
 if ONLY=='all' and name in done:continue
 if ONLY!='all' and name!=ONLY:continue
 directory=P/'previews/roster'/name;directory.mkdir(parents=True,exist_ok=True)
 r,lo,hi=load(BASE/cat/name/(name+'.glb'));r,lo2,hi2=load(P/cat/name/(name+'.glb'));lo=Vector(tuple(min(lo[i],lo2[i]) for i in range(3)));hi=Vector(tuple(max(hi[i],hi2[i]) for i in range(3)));center=(lo+hi)/2;size=(hi-lo).length;extent=max(hi.x-lo.x,hi.y-lo.y,hi.z-lo.z)
 for rev,root in [('Before',BASE),('After',P)]:
  r,local_lo,local_hi=load(root/cat/name/(name+'.glb'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=2;sc.cycles.use_denoising=True;sc.render.use_persistent_data=True;sc.render.resolution_x=512;sc.render.resolution_y=512;sc.world=bpy.data.worlds.new('Neutral');sc.world.color=(.2,.2,.2);sc.view_settings.view_transform='AgX'
  bpy.ops.mesh.primitive_plane_add(size=extent*30,location=(0,0,local_lo.z-.002));ground=bpy.context.object;mat=bpy.data.materials.new('Neutral_grey');mat.diffuse_color=(.12,.12,.12,1);ground.data.materials.append(mat)
  for delta,power in [((1,-1,2),150),((-1,-.4,1),100),((.1,1,1.5),160)]:
   bpy.ops.object.light_add(type='AREA',location=center+Vector(delta)*extent);o=bpy.context.object;o.data.energy=power*extent**2;o.data.size=extent*1.2;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';sc.camera=camera
  for view,direction in [('Threequarter',(1,-1,.32)),('Front',(0,-1,.16)),('Side',(1,0,.16)),('Back',(0,1,.16)),('Closeup',(1,-1,.14))]:
   target=center.copy();scale=extent*1.2
   if view=='Closeup':
    h=r.data.bones.get('head');target=r.matrix_world@((h.head_local+h.tail_local)*.5) if h else center;scale= max((hi.z-lo.z)*.40,.2)
   camera.location=target+Vector(direction).normalized()*extent*3;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;sc.render.filepath=str(directory/(rev+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
   with Path(sc.render.filepath).open('rb') as h:os.fsync(h.fileno())
 done.append(name)
 with progress.open('w') as h:json.dump(done,h);h.flush();os.fsync(h.fileno())
 print('VISUAL_REVIEW_READY',name,flush=True)
