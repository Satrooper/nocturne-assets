"""CPU-renderable offline presentation of the delivered GLB. Not an engine performance test."""
import bpy,json,math,sys,random
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent));from studio_helpers import load,studio,aim
P=Path(__file__).resolve().parents[1];rows=json.loads((P/'audit/Repair_Progress.json').read_text());ONLY=sys.argv[-1] if '--' in sys.argv else 'all';progress=P/'audit/Cinematic_Preview_Progress.json';records=json.loads(progress.read_text()) if progress.exists() else []
for row in rows:
 name=row['asset']
 if ONLY!='all' and ONLY!=name:continue
 folder=P/'cinematics'/name;folder.mkdir(parents=True,exist_ok=True);r,meshes,lo,hi=load(P/row['canonical_glb']);sc,cam,center,extent=studio(lo,hi)
 sc.render.resolution_x=640;sc.render.resolution_y=480;sc.cycles.samples=12;sc.world.color=(.015,.019,.027);sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=-.35
 lights=[o for o in sc.objects if o.type=='LIGHT']
 for light,color,power in zip(lights,[(.90,.77,.64),(.28,.41,.65),(.52,.72,1.0)],[115,28,150]):light.data.color=color;light.data.energy=power*extent**2
 floor=next(o for o in sc.objects if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers));floor.data.materials[0].use_nodes=True;bs=floor.data.materials[0].node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.045,.052,.061,1);bs.inputs['Roughness'].default_value=.62
 pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];aim(cam,center,extent,(1,-1,.24),pts);cam.data.type='PERSP';cam.data.lens=52;cam.location=center+Vector((1,-1,.22)).normalized()*extent*1.75;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.dof.use_dof=True;cam.data.dof.focus_distance=(center-cam.location).length;cam.data.dof.aperture_fstop=7
 # Editable camera push-in, deliberately restrained; no camera jitter concealing deformation.
 sc.frame_start=1;sc.frame_end=61;sc.render.fps=30
 start=cam.location.copy()
 for f,t in [(1,0),(31,.045),(61,.09)]:cam.location=start.lerp(center,t);cam.keyframe_insert('location',frame=f)
 cam.location=start
 actions=list(bpy.data.actions);chosen=next((a for a in actions if any(n in a.name for n in ['Idle_Breath','Idle','Breathe'])),actions[0] if actions else None)
 if chosen:r.animation_data.action=chosen
 sc.use_nodes=True;nodes=sc.node_tree.nodes;nodes.clear();rl=nodes.new('CompositorNodeRLayers');glare=nodes.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.quality='LOW';glare.threshold=2;glare.mix=-.90;comp=nodes.new('CompositorNodeComposite');sc.node_tree.links.new(rl.outputs['Image'],glare.inputs['Image']);sc.node_tree.links.new(glare.outputs['Image'],comp.inputs[0]);sc.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Presentation.blend'),compress=True);sc.render.filepath=str(folder/'Cinematic.jpg');bpy.ops.render.render(write_still=True)
 rec={'asset':name,'delivered_model':row['canonical_glb'],'scene':str((folder/'Presentation.blend').relative_to(P)),'render':str((folder/'Cinematic.jpg').relative_to(P)),'animation':chosen.name if chosen else None,'presentation':'Actual GLB reimport, three lights, perspective lens, mild DOF and glow, editable camera push-in','rendering':'Blender Cycles CPU offline; not a GPU/mobile benchmark','cinematic_asset_quality_approved':False}
 records=[x for x in records if x['asset']!=name];records.append(rec);(P/'audit/Cinematic_Preview_Progress.json').write_text(json.dumps(records,indent=2));print('CINEMATIC_PRESENTATION_SAVED',name,flush=True)
