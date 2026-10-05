import bpy,math,json
from mathutils import Vector
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
