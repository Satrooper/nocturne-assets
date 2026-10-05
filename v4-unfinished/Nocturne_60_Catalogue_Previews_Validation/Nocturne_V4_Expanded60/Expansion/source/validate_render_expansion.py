import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P.parent
rows=json.loads((P/'audit/Build_Progress.json').read_text());results=[];progress=P/'audit/Export_Validation.json'
def load(f):
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
    if f.suffix=='.fbx':bpy.ops.import_scene.fbx(filepath=str(f))
    else:bpy.ops.import_scene.gltf(filepath=str(f))
    r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');r.animation_data_create();r.animation_data.action=None
    for tr in r.animation_data.nla_tracks:tr.mute=True
    for pb in r.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
    mesh=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
    for o in list(bpy.context.scene.objects):
        if o.type=='MESH' and o not in mesh:bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.view_layer.update();pts=[o.matrix_world@v.co for o in mesh for v in o.data.vertices]
    assert pts and all(math.isfinite(x) for v in pts for x in v)
    lo=Vector(tuple(min(v[i] for v in pts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in pts) for i in range(3)))
    return r,mesh,lo,hi
def studio(lo,hi):
    sc=bpy.context.scene;center=(lo+hi)/2;extent=max(hi-lo);sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.use_persistent_data=True;sc.render.resolution_x=512;sc.render.resolution_y=512
    sc.render.image_settings.file_format='JPEG';sc.render.image_settings.quality=92;sc.view_settings.view_transform='AgX';sc.world=bpy.data.worlds.new('Neutral');sc.world.color=(.2,.2,.2)
    bpy.ops.mesh.primitive_plane_add(size=extent*30,location=(0,0,lo.z-.003));floor=bpy.context.object;mat=bpy.data.materials.new('neutral_ground');mat.diffuse_color=(.14,.14,.14,1);floor.data.materials.append(mat)
    for delta,power in [((1,-1,2),140),((-1,-.5,1),110),((.2,1,1.5),160)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(delta)*extent);l=bpy.context.object;l.data.energy=power*extent**2;l.data.size=extent*1.2;l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';sc.camera=cam
    return sc,cam,center,extent
def aim(cam,center,extent,direction,pts,close=False):
    cam.location=center+Vector(direction).normalized()*extent*3;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();inv=cam.rotation_euler.to_matrix().transposed();pr=[inv@(v-center) for v in pts]
    xmin,xmax=min(v.x for v in pr),max(v.x for v in pr);ymin,ymax=min(v.y for v in pr),max(v.y for v in pr);cam.data.ortho_scale=max(xmax-xmin,ymax-ymin)*1.18
    if not close:cam.location+=cam.rotation_euler.to_matrix()@Vector(((xmin+xmax)/2,(ymin+ymax)/2,0))
    if close:cam.data.ortho_scale=extent*.45
for row in rows:
    name=row['asset'];folder=P/'previews/characters'/name;folder.mkdir(parents=True,exist_ok=True);rec={'asset':name,'source_glb':row['canonical_glb'],'source_fbx':row['canonical_fbx'],'structural':{},'visual_approved':False,'engine_tested':False}
    for fmt,key in [('fbx','canonical_fbx'),('glb','canonical_glb')]:
        r,meshes,lo,hi=load(P/row[key]);actions=list(bpy.data.actions);assert len(actions)==22,(name,fmt,len(actions));assert len(r.data.bones)==row['bones'];rec['structural'][fmt]={'reimport_passed':True,'bones':len(r.data.bones),'clips':len(actions),'bounds_m':[list(lo),list(hi)],'finite_vertices':True}
    sc,cam,center,extent=studio(lo,hi);pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
    for view,direction in [('Threequarter',(1,-1,.35)),('Front',(0,-1,.14)),('Side',(1,0,.14)),('Back',(0,1,.14)),('Closeup',(1,-1,.2))]:
        target=r.matrix_world@r.data.bones['head'].head_local if view=='Closeup' else center
        aim(cam,target,extent,direction,pts,view=='Closeup');sc.render.filepath=str(folder/(view+'.jpg'));bpy.ops.render.render(write_still=True)
    aim(cam,center,extent,(1,-1,.35),pts)
    material=bpy.data.materials.new('triangulated_export_wire');material.use_nodes=True;N=material.node_tree.nodes;L=material.node_tree.links;bs=N.get('Principled BSDF');wire=N.new('ShaderNodeWireframe');wire.use_pixel_size=True;wire.inputs[0].default_value=.60;mix=N.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.60,.63,.66,1);mix.inputs[2].default_value=(.012,.017,.02,1);L.new(wire.outputs[0],mix.inputs[0]);L.new(mix.outputs[0],bs.inputs['Base Color'])
    old=[]
    for o in meshes:old.append(list(o.data.materials));o.data.materials.clear();o.data.materials.append(material)
    sc.render.filepath=str(folder/'Wireframe.jpg');bpy.ops.render.render(write_still=True)
    for o,mats in zip(meshes,old):
        o.data.materials.clear()
        for m in mats:o.data.materials.append(m)
    clips=[a for a in bpy.data.actions if any(x in a.name for x in ['Flight_Cruise','Swim_Cruise','Walk_InPlace'])];action=clips[-1];r.animation_data.action=action;frames=[];sc.cycles.samples=4
    for i in range(8):
        f=action.frame_range.x+(action.frame_range.y-action.frame_range.x)*i/7;sc.frame_set(int(f));sc.render.filepath=str(folder/('Motion_'+str(i)+'.jpg'));bpy.ops.render.render(write_still=True);frames.append(str(Path(sc.render.filepath).relative_to(P)))
    rec['motion_preview']={'action':action.name,'frames':frames,'duration_s':float(action.frame_range.y-action.frame_range.x)/30,'source':'canonical GLB reimport','collision_contact_approved':False}
    # Sample every clip independently for finite deformation, loop/root bookkeeping.
    samples=[];dg=bpy.context.evaluated_depsgraph_get()
    for a in bpy.data.actions:
        r.animation_data.action=a
        for f in [a.frame_range.x,(a.frame_range.x+a.frame_range.y)/2,a.frame_range.y]:
            sc.frame_set(round(f));dg.update()
            for o in meshes:
                ev=o.evaluated_get(dg);me=ev.to_mesh();assert all(math.isfinite(x) for v in me.vertices for x in v.co);ev.to_mesh_clear()
        samples.append(a.name)
    rec['deformation_samples']={'clips':len(samples),'frames_per_clip':3,'finite':True,'does_not_establish':'No all-frame clipping, foot-contact, loop-quality or choreography approval.'};results.append(rec);progress.write_text(json.dumps(results,indent=2));print('VALIDATED_RENDERED',name,flush=True)
# Reimport actual player and weapon exports separately, without claiming contact approval.
other=[]
for f in list((P/'player_handling').glob('*.glb'))+list((P/'player_animation').glob('*.glb'))+list((P/'weapons').glob('*/*.glb')):
    r,m,lo,hi=load(f);other.append({'file':str(f.relative_to(P)),'bones':len(r.data.bones),'clips':len(bpy.data.actions),'reimport_passed':True,'engine_tested':False})
(P/'audit/Player_Weapon_Validation.json').write_text(json.dumps(other,indent=2));print('ALL_EXPANSION_VALIDATED',len(results),flush=True)
