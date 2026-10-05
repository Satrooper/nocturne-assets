import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['Cinder_Crown'];name=args[0];cat='dragons' if name=='Cinder_Crown' else 'bosses';folder=P/cat/name;m=json.loads((folder/'asset.json').read_text());bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(folder/(name+'.glb')));rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH' and any(mod.type=='ARMATURE' for mod in o.modifiers));
for helper in list(scene.objects):
 if helper.type=='MESH' and helper!=mesh:bpy.data.objects.remove(helper,do_unlink=True)
rig.animation_data.action=None
for track in rig.animation_data.nla_tracks:track.mute=True
for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
bpy.context.view_layer.update();verts=[mesh.matrix_world@v.co for v in mesh.data.vertices];mn=Vector([min(p[i] for p in verts) for i in range(3)]);mx=Vector([max(p[i] for p in verts) for i in range(3)]);center=(mn+mx)/2;span=max(mx-mn)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.045));ground=bpy.context.object;gm=bpy.data.materials.new('Neutral_ground');gm.use_nodes=True;bs=gm.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.12,.12,.12,1);bs.inputs['Roughness'].default_value=.9;ground.data.materials.append(gm)
for v,power,size in [((.7,-.7,1.5),1400,1.0),((-.9,-.5,.8),900,1.0),((.1,.9,1.1),1000,.7)]:
 bpy.ops.object.light_add(type='AREA',location=center+Vector(v)*span*.7);light=bpy.context.object;light.data.energy=power*(span/5)**2;light.data.size=span*size;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Neutral_world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.use_persistent_data=True;scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
def camera(direction,target=None,width=None):
 target=center if target is None else target;cam.location=target+Vector(direction).normalized()*span*2;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();inv=cam.rotation_euler.to_matrix().transposed();points=[inv@(v-target) for v in verts];xr=2*max(abs(v.x) for v in points);yr=2*max(abs(v.y) for v in points);cam.data.ortho_scale=width or max(xr,yr*900/700)*1.17
if '--only-motion' not in args:
 for view,vec in [('front',(0,-1,.12)),('side',(1,0,.10)),('back',(0,1,.12)),('threequarter',(1,-1.3,.65))]:
  camera(vec);scene.render.filepath=str(P/'previews'/(name+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
 target=rig.matrix_world@Vector((0,-2.85,2.43) if name=='Cinder_Crown' else (0,-.08,2.96));camera((1,-1,.27),target,width=2.0 if name=='Cinder_Crown' else 1.9);scene.render.filepath=str(P/'previews'/(name+'_closeup.png'));bpy.ops.render.render(write_still=True)
if '--motion' in args:
 scene.render.resolution_x=480;scene.render.resolution_y=360;scene.cycles.samples=4;camera((1,-1.3,.62));cam.data.ortho_scale*=1.22
 clipnames=['Walk_RootMotion','Bite_Lunge_RootMotion','Flight_Takeoff_RootMotion','Swim_Cruise_InPlace'] if name=='Cinder_Crown' else ['Walk_RootMotion','Piston_Punch_Right','Cannon_Burst','Ground_Slam']
 if '--clip' in args:clipnames=[args[args.index('--clip')+1]]
 for clipname in clipnames:
  a=next(a for a in bpy.data.actions if a.name.split('|')[-1].removesuffix('_'+rig.name)==clipname);rig.animation_data.action=a;first,last=a.frame_range;out=P/'previews'/'motion_frames'/(name+'_'+clipname);out.mkdir(parents=True,exist_ok=True)
  for i in ([int(args[args.index('--frame')+1])] if '--frame' in args else range(24)):
   f=first+(last-first)*i/23;scene.frame_set(int(f),subframe=f-int(f));scene.render.filepath=str(out/(str(i).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
  print('MOTION_FRAMES',name,clipname,flush=True)
print('ACTUAL_EXPORT_PREVIEWS_DONE',name,flush=True)
