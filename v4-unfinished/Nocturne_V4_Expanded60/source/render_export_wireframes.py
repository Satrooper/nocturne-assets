"""Render actual canonical GLB topology, never concept images."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
catalog=json.loads((P/'asset_manifest.json').read_text())['characters']
out=P/'previews/wireframes';out.mkdir(parents=True,exist_ok=True)
receipts=[]
for c in catalog:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(P/c['canonical_glb']))
    # Restrict to exported geometry, excluding Blender's importer bone-display helpers.
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name!='Icosphere' and not o.name.startswith('Icosphere.')]
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and o not in meshes:o.hide_render=True
    bpy.context.scene.frame_set(1)
    pts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
    lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    center=(lo+hi)/2;span=max(hi-lo)
    mat=bpy.data.materials.new('Exported_triangle_wireframe');mat.use_nodes=True
    nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
    wire=nodes.new('ShaderNodeWireframe');wire.use_pixel_size=True;wire.inputs['Size'].default_value=.65
    mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.7,.73,.76,1);mix.inputs[2].default_value=(.02,.025,.03,1)
    emission=nodes.new('ShaderNodeEmission');output=nodes.new('ShaderNodeOutputMaterial')
    links.new(wire.outputs[0],mix.inputs[0]);links.new(mix.outputs[0],emission.inputs[0]);links.new(emission.outputs[0],output.inputs[0])
    for o in meshes:o.data.materials.clear();o.data.materials.append(mat)
    bpy.ops.object.camera_add(location=center+Vector((1.4,-2.1,1.0))*span)
    cam=bpy.context.object;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=span*1.45
    scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=4
    scene.world=bpy.data.worlds.new('Neutral');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.045,.05,.06,1)
    scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=90
    scene.view_settings.view_transform='Standard';scene.render.filepath=str(out/(c['asset']+'.jpg'))
    bpy.ops.render.render(write_still=True)
    receipts.append({'asset':c['asset'],'source':c['canonical_glb'],'output':str(Path('previews/wireframes')/(c['asset']+'.jpg')),'frame':1,'render':'exported triangles; canonical default, not Experimental; imported current GLB','visual_quality_approved':False})
    (P/'audit/Wireframe_Preview_Mapping.json').write_text(json.dumps(receipts,indent=2))
    print('WIREFRAME_SAVED',c['asset'],flush=True)
