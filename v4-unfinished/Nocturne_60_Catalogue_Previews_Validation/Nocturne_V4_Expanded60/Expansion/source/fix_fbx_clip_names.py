import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P.parent;records=[]
for f in sorted(P.rglob('*.blend')):
    dest=f.with_suffix('.fbx')
    if f.name=='Player_Handling.blend':dest=f.parent/'Player_With_Firearms.fbx'
    if not dest.exists():continue
    bpy.ops.wm.open_mainfile(filepath=str(f));bpy.context.scene.render.fps=30
    rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    for i,r in enumerate(rigs):r.name='Rig' if i==0 else 'Rig'+str(i)
    names=[]
    for a in list(bpy.data.actions):
        old=a.name;short=old.split('__')[-1]
        if len(short)>45:short=short[-45:]
        a.name=short;names.append({'source_action':old,'fbx_action':a.name})
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type in {'MESH','ARMATURE'}:o.select_set(True)
    if rigs:bpy.context.view_layer.objects.active=rigs[0]
    bpy.ops.export_scene.fbx(filepath=str(dest),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True)
    records.append({'file':str(dest.relative_to(P)),'action_name_map':names,'fps':30,'bone_names_preserved':True});print('FBX_NAMES',f.parent.name,len(names),flush=True)
(P/'audit/FBX_Action_Name_Map.json').write_text(json.dumps(records,indent=2))
print('FBX_NAMES_COMPLETE',len(records),flush=True)
