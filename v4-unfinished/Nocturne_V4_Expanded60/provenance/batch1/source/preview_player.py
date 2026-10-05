import bpy,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'player_animation/Player_Moves_With_Existing_Mannequin.glb'));rig=next(o for o in scene.objects if o.type=='ARMATURE');meshes=[o for o in scene.objects if o.type=='MESH' and any(mod.type=='ARMATURE' for mod in o.modifiers)]
for o in list(scene.objects):
 if o.type=='MESH' and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
for t in rig.animation_data.nla_tracks:t.mute=True
rig.animation_data.action=None
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-.06));g=bpy.context.object;m=bpy.data.materials.new('Neutral_ground');m.diffuse_color=(.16,.16,.16,1);g.data.materials.append(m)
for pos,power in [((3,-4,5),450),((-3,-2,3),300),((1,3,4),400)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.size=4;l.rotation_euler=(Vector((0,0,.9))-l.location).to_track_quat('-Z','Y').to_euler()
scene.world=bpy.data.worlds.new('Neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
bpy.ops.object.camera_add(location=(3,-4,2.6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,-.35,.8))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.9;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=4;scene.cycles.use_denoising=False;scene.render.use_persistent_data=True;scene.render.resolution_x=480;scene.render.resolution_y=360;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
actions={a.name.split('|')[-1].removesuffix('_'+rig.name):a for a in bpy.data.actions};meta=json.loads((P/'player_animation/animation_manifest.json').read_text())
clips=['Pistol_Reload_Empty','Sword_Light_Combo_2_RootMotion','Sword_Heavy_Combo_1_RootMotion','Dodge_Forward_RootMotion','Swim_Crawl_RootMotion','GetUp_From_Back']
for clip in clips:
 rig.animation_data.action=actions[clip];first,last=actions[clip].frame_range;out=P/'previews/motion_frames'/('Player_'+clip);out.mkdir(parents=True,exist_ok=True)
 for i in range(24):
  f=first+(last-first)*i/23;scene.frame_set(int(f),subframe=f-int(f));scene.render.filepath=str(out/(str(i).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
 print('PLAYER_PREVIEW',clip,flush=True)
# Both delivered paired clips, on copies of the delivered mannequin, share a clock.
second=rig.copy();second.data=rig.data.copy();bpy.context.collection.objects.link(second);second.animation_data_clear();second.animation_data_create()
for mesh in meshes:
 ob=mesh.copy();ob.data=mesh.data.copy();bpy.context.collection.objects.link(ob);ob.parent=second
 for mod in ob.modifiers:
  if mod.type=='ARMATURE':mod.object=second
clip='Paired_Backstab_Attacker';rig.animation_data.action=actions[clip];second.animation_data.action=actions['Paired_Backstab_Victim'];first,last=actions[clip].frame_range;out=P/'previews/motion_frames/Player_Paired_Backstab';out.mkdir(parents=True,exist_ok=True)
for i in range(24):
 f=first+(last-first)*i/23;scene.frame_set(int(f),subframe=f-int(f));scene.render.filepath=str(out/(str(i).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
print('PLAYER_ACTUAL_EXPORT_PREVIEWS_DONE',flush=True)
