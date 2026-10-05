import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for cat,name in [('dragons','Cinder_Crown'),('bosses','Siege_Sentinel')]:
 f=P/'source/v3_baselines'/cat/name/(name+'.blend');bpy.ops.wm.open_mainfile(filepath=str(f));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.animation_data_clear()
 for o in list(bpy.data.objects):
  if o!=rig:bpy.data.objects.remove(o,do_unlink=True)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 bpy.data.orphans_purge(do_recursive=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True)
print('BASELINE_RIG_SOURCES_PREPARED',flush=True)
