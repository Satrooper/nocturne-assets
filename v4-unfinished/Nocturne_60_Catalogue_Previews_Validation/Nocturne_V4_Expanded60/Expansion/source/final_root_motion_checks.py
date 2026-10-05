import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P.parent;receipts=[];rows=json.loads((P/'audit/Build_Progress.json').read_text())
for i,row in enumerate(rows):
    rec={'asset':row['asset'],'revision':'world-to-bone root translation and world-Z yaw corrected','formats':{}}
    for fmt in ['fbx','glb']:
        f=P/row['canonical_'+fmt];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
        if fmt=='fbx':bpy.ops.import_scene.fbx(filepath=str(f))
        else:bpy.ops.import_scene.gltf(filepath=str(f))
        r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');r.animation_data_create()
        for tr in r.animation_data.nla_tracks:tr.mute=True
        assert len(bpy.data.actions)==22;checks=[]
        for clip in ['Advance_RootMotion','Attack_Charge_RootMotion','Turn_Left90_RootMotion','Turn_Right90_RootMotion']:
            a=next(a for a in bpy.data.actions if clip in a.name);r.animation_data.action=a;points=[];directions=[]
            for frame in [a.frame_range.x,a.frame_range.y]:
                bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update();mat=r.matrix_world@r.pose.bones['root'].matrix;points.append(mat.translation.copy());directions.append(mat.to_3x3()@Vector((1,0,0)))
            delta=points[-1]-points[0]
            if clip.startswith(('Advance','Attack')):
                meta=next(c for c in row['clips'] if c['purpose']==clip);expected=Vector(meta['root_end_offset_m']);assert (delta-expected).length<.005,(row['asset'],fmt,clip,list(delta),list(expected))
                checks.append({'clip':clip,'end_displacement_m':list(delta),'expected_m':list(expected),'unwanted_end_snapback':False,'translation_axis_passed':True})
            else:
                u,v=directions;angle=math.degrees(math.atan2(u.x*v.y-u.y*v.x,u.x*v.x+u.y*v.y));expected=90 if 'Left' in clip else -90;assert abs(angle-expected)<.1,(row['asset'],fmt,angle)
                checks.append({'clip':clip,'yaw_degrees':angle,'world_Z_yaw_passed':True})
        rec['formats'][fmt]={'reimport_passed':True,'clips':22,'bones':len(r.data.bones),'root_checks':checks}
    receipts.append(rec);(P/'audit/Final_Root_Motion_Checks.json').write_text(json.dumps(receipts,indent=2));print('ROOT_CHECK',row['asset'],flush=True)
others=[]
for f in list((P/'player_animation').glob('*.glb'))+list((P/'player_handling').glob('*.glb'))+list((P/'weapons').glob('*/*.glb')):
    expected=46 if 'player_animation' in f.parts else 18 if 'player_handling' in f.parts else 0 if 'Poleaxe' in f.name else 2
    for fmt in ['glb','fbx']:
        ff=f.with_suffix('.'+fmt);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
        if fmt=='fbx':bpy.ops.import_scene.fbx(filepath=str(ff))
        else:bpy.ops.import_scene.gltf(filepath=str(ff))
        assert len(bpy.data.actions)==expected,(ff,len(bpy.data.actions),expected);others.append({'file':str(ff.relative_to(P)),'format':fmt,'clips':expected,'reimport_passed':True})
(P/'audit/Final_Player_Weapon_Reimports.json').write_text(json.dumps(others,indent=2));print('FINAL_MOTION_CHECKS_COMPLETE',len(receipts),len(others),flush=True)
