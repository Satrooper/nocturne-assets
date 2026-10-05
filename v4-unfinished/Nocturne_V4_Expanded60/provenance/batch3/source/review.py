import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];M=P/'bosses/Siege_Sentinel';mode=sys.argv[-1]
def load(path):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 if path.suffix=='.glb':bpy.ops.import_scene.gltf(filepath=str(path))
 else:bpy.ops.import_scene.fbx(filepath=str(path))
 rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];r=rigs[0];meshes=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 for o in list(bpy.context.scene.objects):
  if o.type=='MESH' and o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
 r.animation_data_create();r.animation_data.action=None
 for t in r.animation_data.nla_tracks:t.mute=True
 for b in r.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.location=(0,0,0);b.scale=(1,1,1)
 bpy.context.scene.render.fps=30;bpy.context.scene.frame_set(1);return r,meshes
if mode=='validate':
 reports=[];checks=[];meta=json.loads((M/'asset.json').read_text());expected={a['name'] for a in meta['clips']}
 for path in list(M.glob('*.fbx'))+list(M.glob('*.glb')):
  r,meshes=load(path);names={a.name.split('|')[-1].removesuffix('_'+r.name) for a in bpy.data.actions};finite=all(math.isfinite(c) for o in meshes for v in o.data.vertices for c in v.co);err=max(abs(sum(g.weight for g in v.groups)-1) for o in meshes for v in o.data.vertices);missing=[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).exists()];tri=sum(len(p.vertices)-2 for o in meshes for p in o.data.polygons);passed=finite and err<.002 and not missing and len(r.data.bones)==52 and ('LOD' in path.name or expected<=names)
  reports.append({'file':path.name,'rig_bones':len(r.data.bones),'actions':sorted(names),'triangles':tri,'finite_vertices':finite,'max_weight_sum_error':err,'missing_textures':missing,'structural_passed':passed,'engine_tested':False});print('VALIDATED',path.name,passed,flush=True)
  if path.suffix!='.glb':continue
  rest=r.matrix_world.copy();restWM={b.name:rest@b.matrix_local for b in r.data.bones};sources={}
  for side in ['L','R']:
   bn='hind'+side+'_foot';o=meshes[0];g=o.vertex_groups[bn].index;pts=[o.matrix_world@v.co for v in o.data.vertices if any(x.group==g and x.weight>.95 for x in v.groups)];sources[bn]=pts
  for a in bpy.data.actions:
   r.animation_data.action=a;first,last=map(int,a.frame_range);record={'clip':a.name,'samples':[]};root=[]
   for f in range(first,last+1):
    bpy.context.scene.frame_set(f);bpy.context.view_layer.update();feet={}
    for bn,pts in sources.items():
     skin=r.matrix_world@r.pose.bones[bn].matrix@restWM[bn].inverted();p=[skin@v for v in pts];feet[bn]={'min_z_m':min(v.z for v in p),'joint_m':list(r.matrix_world@r.pose.bones[bn].head)}
    root.append(list(r.matrix_world@r.pose.bones['root'].head));record['samples'].append({'time_s':(f-first)/30,'feet':feet})
   record['minimum_foot_geometry_z_m']=min(x['min_z_m'] for s in record['samples'] for x in s['feet'].values());record['root_delta_m']=list(Vector(root[-1])-Vector(root[0]));record['note']='Foot sole geometry sampled from weighted vertices; contact and sliding are findings, not automatic approval.';checks.append(record)
 (P/'audit/Export_Reimport_Validation.json').write_text(json.dumps(reports,indent=2));(P/'audit/Foot_Geometry_Motion_Check.json').write_text(json.dumps(checks,indent=2));assert all(x['structural_passed'] for x in reports)
else:
 def studio(loc,target,scale,res=600):
  sc=bpy.context.scene;sc.world=bpy.data.worlds.new('Neutral');sc.world.color=(.17,.17,.17);sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.resolution_x=res;sc.render.resolution_y=res;sc.render.resolution_percentage=100;sc.view_settings.view_transform='AgX'
  bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.002));o=bpy.context.object;m=bpy.data.materials.new('Neutral_ground');m.diffuse_color=(.12,.12,.12,1);o.data.materials.append(m)
  for pos,power in [((4,-4,8),1100),((-5,-3,4),850),((0,5,7),1000)]:
   bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=5;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
  bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;sc.camera=cam;return sc
 if mode=='neutral':
  for label,path in [('Before',P.parent/'restored/nocturne-v4-batch02/bosses/Siege_Sentinel/Siege_Sentinel.glb'),('After',M/'Siege_Sentinel.glb')]:
   for view,loc,target,scale in [('Front',(0,-12,2.5),(0,0,2.5),6),('Side',(12,0,2.5),(0,0,2.5),6),('Back',(0,12,2.5),(0,0,2.5),6),('Limbs',(5,-10,2),(0,0,1.85),3.9),('Hand',(-4,-8,2),(-1.53,-.15,1.75),1.45),('Feet',(4,-8,1), (0,-.10,.40),1.7)]:
    out=P/'previews'/f'Sentinel_{label}_{view}.png'
    if out.exists():continue
    r,meshes=load(path);sc=studio(loc,target,scale);sc.render.filepath=str(out);bpy.ops.render.render(write_still=True)
 else:
  for keyword in ['Walk_InPlace','Piston_Punch_Right','Brace']:
   r,meshes=load(M/'Siege_Sentinel.glb');act=next(a for a in bpy.data.actions if keyword in a.name);r.animation_data.action=act;sc=studio((7,-10,3.8),(0,0,2.5),6.1,360);sc.cycles.samples=3;sc.render.use_persistent_data=True;folder=P/'previews'/('frames_'+keyword);folder.mkdir(exist_ok=True);first,last=act.frame_range
   for i in range(16):
    f=first+(last-first)*i/15;sc.frame_set(int(f),subframe=f-int(f));sc.render.filepath=str(folder/f'{i:03d}.png');bpy.ops.render.render(write_still=True)
 print('REVIEW_COMPLETE',mode,flush=True)
