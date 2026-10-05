"""Preserve every previous source; make explicit alternate body-plan revisions for repetitive families."""
import bpy,json,math,importlib.util
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P.parent;BASE=W
rows=json.loads((BASE/'asset_manifest.json').read_text())['characters'];byname={x['asset']:x for x in rows}
# Regional proportions plus new structural anatomy; these are prototypes, not cinematic approval.
config={'Hundredleg':('bosses',(.58,2.10,.68),'Long narrow segmented crawler with radial leg reach; no longer the compact arachnarch shape.'),'Crypt_Skitter':('enemies',(1.35,.65,.58),'Broad flattened four-forward-feeding silhouette and raised frontal sensory ridges.'),'Razorfin':('enemies',(.58,1.65,.72),'Narrow needlefish body and elongated snout; distinct from broad Abyss Maw.'),'Crimson_Imp':('enemies',(.77,.90,1.10),'Lean long-armed imp with curling balance tail; distinct from heavy Horned Regent.'),'Sporeling':('enemies',(1.05,.85,.62),'Low mushroom-bodied enemy with broad fleshy umbrella crown; distinct from Root Matriarch.'),'Scrapling':('enemies',(.75,.90,.73),'Low compact worker robot with large independent forearm grippers and elevated dorsal sensor mast.'),'Furnace_Titan':('bosses',(1.4,1.16,.86),'Broad low-headed furnace frame with paired rear exhaust chambers; distinct from upright Siege Sentinel.')}
results=[]
for name,(cat,scales,description) in config.items():
    row=byname[name];bpy.ops.wm.open_mainfile(filepath=str(BASE/row['editable_source']));r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');r.animation_data.action=None
    for tr in r.animation_data.nla_tracks:tr.mute=True
    for pb in r.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.rotation_euler=(0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    def warp(p):
        q=Vector((p.x*scales[0],p.y*scales[1],p.z*scales[2]))
        if name=='Crimson_Imp':q.x*=1+.25*max(0,min(1,(abs(p.x)-.35)/.55))
        if name=='Furnace_Titan':q.x*=1+.18*max(0,min(1,(p.z-1.2)/1.5))
        return q
    for m in meshes:
        for v in m.data.vertices:v.co=warp(v.co)
    bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
    for b in r.data.edit_bones:b.head=warp(b.head);b.tail=warp(b.tail)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Add actual structural parts, with the existing bone names and material separation.
    def sphere(n,center,scale,bone,material):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=center);o=bpy.context.object;o.name=n;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.ops.object.transform_apply(location=True,rotation=False,scale=False);o.matrix_world=r.matrix_world.copy();o.data.materials.append(material);o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE');o.modifiers.new('Skin','ARMATURE').object=r;o.parent=r;meshes.append(o);return o
    mats=[ma for m in meshes for ma in m.data.materials if ma];skin=mats[0]
    for im in bpy.data.images:
        if im.source=='FILE' and not im.packed_file:
            f=BASE/'textures'/Path(im.filepath).name
            if f.exists():im.filepath=str(f);im.reload();im.pack()
    if name=='Sporeling':
        h=r.data.bones['head'].head_local;sphere('fleshy_umbrella_crown',h+Vector((0,0,.15)),(.85,.68,.19),'head',skin)
        for s in [-1,1]:sphere('gill_lobe',h+Vector((s*.35,.1,.07)),(.33,.38,.12),'head',skin)
    elif name=='Crimson_Imp':
        pts=[Vector((0,.2,.9)),Vector((.25,.6,.65)),Vector((.55,.95,.8)),Vector((.7,.8,1.1)),Vector((.55,.55,1.2))];vv=[];ff=[]
        for j,p in enumerate(pts):
            for a in range(16):q=p+Vector((math.cos(a*math.tau/16),0,math.sin(a*math.tau/16)))*(.09*(1-j/len(pts)));vv.append(q)
        for j in range(len(pts)-1):
            for a in range(16):i=j*16+a;ff.append((i,j*16+(a+1)%16,(j+1)*16+(a+1)%16,i+16))
        me=bpy.data.meshes.new('curl_tail');me.from_pydata(vv,[],ff);me.materials.append(skin);o=bpy.data.objects.new('curled_balance_tail',me);bpy.context.collection.objects.link(o);o.vertex_groups.new(name='pelvis').add(list(range(len(vv))),1,'REPLACE');o.modifiers.new('Skin','ARMATURE').object=r;o.parent=r;o.matrix_world=r.matrix_world.copy();meshes.append(o)
    elif name=='Furnace_Titan':
        for s in [-1,1]:sphere('rear_exhaust_chamber',(s*.35,.38,2.12),(.15,.22,.42),'chest',skin)
    elif name=='Scrapling':
        for s in [-1,1]:
            n='armL_hand' if s<0 else 'armR_hand';b=r.data.bones.get(n)
            if b:sphere('industrial_gripper_housing',b.head_local,(.22,.14,.17),n,skin)
        sphere('dorsal_sensor_mast',(0,.28,2.55),(.11,.11,.35),'chest',skin)
    folder=P/'legacy_distinct_variants'/name;folder.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'_Distinct.blend')),compress=True);bpy.ops.object.select_all(action='DESELECT');r.select_set(True)
    for m in meshes:m.select_set(True)
    bpy.context.view_layer.objects.active=r
    bpy.ops.export_scene.fbx(filepath=str(folder/(name+'_Distinct.fbx')),use_selection=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
    bpy.ops.export_scene.gltf(filepath=str(folder/(name+'_Distinct.glb')),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_frame_range=False)
    results.append({'asset':name,'category':cat,'original_preserved':row['canonical_glb'],'candidate_glb':str((folder/(name+'_Distinct.glb')).relative_to(P)),'candidate_fbx':str((folder/(name+'_Distinct.fbx')).relative_to(P)),'changes':description,'status':'alternate_prototype_requires_visual_and_animation_review','canonical_replaced':False,'clips_choreography':'retained; changed proportions require contact and clipping review','cinematic_approved':False});(folder/'asset.json').write_text(json.dumps(results[-1],indent=2));(P/'audit/Legacy_Distinct_Variants.json').write_text(json.dumps(results,indent=2));print('LEGACY_VARIANT',name,flush=True)
