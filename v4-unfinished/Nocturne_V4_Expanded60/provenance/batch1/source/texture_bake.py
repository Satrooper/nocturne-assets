import bpy
from pathlib import Path

def bake(c,P,size=2048):
 scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=2;scene.render.bake.margin=12;scene.render.bake.use_clear=True
 bpy.ops.object.select_all(action='DESELECT');c.meshobj.select_set(True);bpy.context.view_layer.objects.active=c.meshobj
 materials=list(c.meshobj.data.materials);saved=[]
 for m in materials:
  n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF');out=n.get('Material Output');saved.append((m,bs,out))
 images={}
 for typ in ['basecolor','roughness','metallic','normal']:
  im=bpy.data.images.new(c.name+'_'+typ,width=size,height=size,alpha=False);im.generated_color=(.5,.5,1,1) if typ=='normal' else (0,0,0,1);im.colorspace_settings.name='sRGB' if typ=='basecolor' else 'Non-Color';images[typ]=im
  temporary=[]
  for m,bs,out in saved:
   nodes=m.node_tree.nodes;links=m.node_tree.links;tex=nodes.new('ShaderNodeTexImage');tex.image=im;nodes.active=tex;temporary.append((m,tex))
   for link in list(out.inputs['Surface'].links):links.remove(link)
   if typ=='normal':links.new(bs.outputs[0],out.inputs['Surface'])
   else:
    socket=bs.inputs['Base Color' if typ=='basecolor' else 'Roughness' if typ=='roughness' else 'Metallic'];em=nodes.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1;temporary.append((m,em))
    if socket.is_linked:links.new(socket.links[0].from_socket,em.inputs['Color'])
    else:
     value=socket.default_value;em.inputs['Color'].default_value=tuple(value) if typ=='basecolor' else (value,value,value,1)
    links.new(em.outputs[0],out.inputs['Surface'])
  bpy.ops.object.bake(type='NORMAL' if typ=='normal' else 'EMIT');im.filepath_raw=str(P/'textures'/(c.name+'_'+typ+'.png'));im.file_format='PNG';im.save()
  for m,node in temporary:m.node_tree.nodes.remove(node)
  for m,bs,out in saved:m.node_tree.links.new(bs.outputs[0],out.inputs['Surface'])
  print('BAKED',c.name,typ,flush=True)
 m=bpy.data.materials.new(c.name+'_Baked_PBR');m.use_nodes=True;nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF')
 for typ,im in images.items():
  tex=nodes.new('ShaderNodeTexImage');tex.image=im
  if typ=='normal':nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=1;links.new(tex.outputs[0],nm.inputs['Color']);links.new(nm.outputs[0],bs.inputs['Normal'])
  else:links.new(tex.outputs[0],bs.inputs['Base Color' if typ=='basecolor' else 'Roughness' if typ=='roughness' else 'Metallic'])
 c.meshobj.data.materials.clear();c.meshobj.data.materials.append(m)
 for poly in c.meshobj.data.polygons:poly.material_index=0
 return images
