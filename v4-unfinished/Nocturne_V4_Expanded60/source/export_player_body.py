import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];F=P/'player_handling';bpy.ops.wm.open_mainfile(filepath=str(F/'Player_Handling.blend'));r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');r.animation_data.action=None
for a in bpy.data.actions:
 for fc in list(a.fcurves):
  if fc.data_path.startswith('pose.bones["W_'):a.fcurves.remove(fc)
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for b in list(r.data.edit_bones):
 if b.name.startswith('W_'):r.data.edit_bones.remove(b)
bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.object.select_all(action='DESELECT');r.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(F/'Player_Handling_BodyOnly.fbx'),use_selection=True,object_types={'ARMATURE'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y');print('BODY_EXPORT',len(r.data.bones))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.fbx(filepath=str(F/'Player_Handling_BodyOnly.fbx'));r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');assert len(r.data.bones)==66 and len(bpy.data.actions)==18;print('BODY_REIMPORT_PASS')
