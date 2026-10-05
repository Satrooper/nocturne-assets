import bpy,sys,json
from pathlib import Path
from mathutils import Vector
P=Path('/workspace/scratch/c638d9b24e22/Nocturne_Expansion_60');F=P/'previews/player';F.mkdir(parents=True,exist_ok=True);mode=sys.argv[-1]
def load(before=False):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;path=P/'player_animation/Player_Moves_With_Existing_Mannequin.glb' if before else P/'player_handling/Player_With_Firearms.glb';bpy.ops.import_scene.gltf(filepath=str(path));r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 for o in list(bpy.context.scene.objects):
  if o.type=='MESH' and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
 r.animation_data_create()
 for t in r.animation_data.nla_tracks:t.mute=True
 sc=bpy.context.scene;sc.render.fps=30;sc.render.engine='CYCLES';sc.cycles.samples=5;sc.cycles.use_denoising=True;sc.render.resolution_x=520;sc.render.resolution_y=520;sc.render.resolution_percentage=100;sc.world=bpy.data.worlds.new('Neutral_world');sc.world.color=(.15,.15,.15)
 bpy.ops.mesh.primitive_plane_add(size=200);m=bpy.data.materials.new('Ground');m.diffuse_color=(.10,.10,.10,1);bpy.context.object.data.materials.append(m)
 for loc,power in [((3,-3,5),650),((-3,-2,4),450),((0,3,4),800)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.size=4;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add(location=(2,-4,2.2));cam=bpy.context.object;cam.rotation_euler=(Vector((0,-.05,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.25;sc.camera=cam
 return r,sc
if mode=='neutral':
 for label,before in [('Before',True),('After',False)]:
  r,sc=load(before);a=next(a for a in bpy.data.actions if ('Pistol_Fire_Hip' if before else 'Pistol_Aim_Idle') in a.name);r.animation_data.action=a;sc.frame_set(int(a.frame_range[0])+2);sc.render.filepath=str(F/(label+'_Pistol.png'));bpy.ops.render.render(write_still=True)
 for clip,t in [('Rifle_Aim_Idle',.1),('Pistol_Reload_Crouched',.95),('Rifle_Fire_Burst3',1.1),('Rifle_Draw_LowReady',1.5)]:
  r,sc=load();a=next(a for a in bpy.data.actions if clip in a.name);r.animation_data.action=a;sc.frame_set(int(a.frame_range[0])+round(t*30));sc.render.filepath=str(F/(clip+'.png'));bpy.ops.render.render(write_still=True)
else:
 meta=json.load(open(P/'player_handling/handling_manifest.json'))
 for clip in ['Pistol_Fire_Hip','Pistol_Reload_Crouched','Rifle_Fire_Burst3','Rifle_Draw_LowReady']:
  r,sc=load();a=next(a for a in bpy.data.actions if clip in a.name);r.animation_data.action=a;sc.render.resolution_x=360;sc.render.resolution_y=360;sc.cycles.samples=3;sc.render.use_persistent_data=True;folder=F/('frames_'+clip);folder.mkdir(exist_ok=True);first,last=a.frame_range
  for i in range(16):
   f=first+(last-first)*i/15;sc.frame_set(int(f),subframe=f-int(f));sc.render.filepath=str(folder/f'{i:03d}.png');bpy.ops.render.render(write_still=True)
print('PLAYER_PREVIEWS_COMPLETE',mode)
