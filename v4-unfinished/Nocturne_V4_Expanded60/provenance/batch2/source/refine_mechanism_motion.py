import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
for name in ['Vesper_Pistol','Bastion_Rifle']:
 folder=P/'weapons'/name;bpy.ops.wm.open_mainfile(filepath=str(folder/(name+'.blend')));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data_create();rig.animation_data.action=None
 for t in rig.animation_data.nla_tracks:t.mute=True
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 for clip,duration in [('Mechanical_Fire',.4),('Mechanical_Reload',2.4)]:
  a=bpy.data.actions.new(clip);a.use_fake_user=True;rig.animation_data.action=a
  for i in range(round(duration*30)+1):
   t=i/30
   for b in rig.pose.bones:b.location=(0,0,0);b.rotation_mode='XYZ';b.rotation_euler=(0,0,0)
   def move(bone,v):rig.pose.bones[bone].location=rig.data.bones[bone].matrix_local.to_3x3().inverted()@Vector(v)
   mechanism='slide' if 'Pistol' in name else 'bolt'
   if 'Fire' in clip:
    amount=max(0,1-abs(t-.06)/.06);move(mechanism,(0,.034*amount,0));rig.pose.bones['trigger'].rotation_euler.x=.18*amount
   else:
    amount=max(0,min(1,(t-.25)/.30,(1.85-t)/.35));amount=amount*amount*(3-2*amount);move('magazine',(0,.025*amount,-.16*amount));move(mechanism,(0,.034*max(0,1-abs(t-2.08)/.12),0))
   for b in rig.pose.bones:
    if b.name in ['slide','bolt','magazine','trigger']:b.keyframe_insert('location',frame=i+1);b.keyframe_insert('rotation_euler',frame=i+1)
  for fc in a.fcurves:
   for k in fc.keyframe_points:k.interpolation='LINEAR'
 rig.animation_data.action=None
 for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0)
 bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')));print('MECHANISM_AXES_FIXED',name,flush=True)
