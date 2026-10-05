import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=str(Path('restored/nocturne-v4-batch02/bosses/Siege_Sentinel/Siege_Sentinel_Authoring.blend').resolve()))
r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
r.animation_data.action=None
for t in r.animation_data.nla_tracks:t.mute=True
for b in r.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
bpy.context.view_layer.update()
d={'rig':r.name,'matrix':list(map(list,r.matrix_world)),'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in r.data.bones},'actions':[(a.name,list(a.frame_range)) for a in bpy.data.actions],'meshes':[(o.name,len(o.data.vertices),[g.name for g in o.vertex_groups]) for o in bpy.context.scene.objects if o.type=='MESH']}
Path('nocturne-v4-batch03/audit/rest_inspection.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
