import bpy,json,hashlib,os,ast,math
from mathutils import Euler
from pathlib import Path
P=Path(__file__).resolve().parents[1];tex=P/'textures';lookup={hashlib.sha256(f.read_bytes()).hexdigest():f for f in tex.rglob('*') if f.is_file()};report=[]
paths=[f for cat in ['dragons','bosses','enemies','weapons'] for f in (P/cat).glob('*/*.blend')]+list((P/'player_animation').glob('*.blend'))+list((P/'player_handling').glob('*.blend'))
tree=ast.parse((P/'source/visual_revision.py').read_text());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='normalize_action_rotations');exec(compile(ast.Module(body=[fn],type_ignores=[]),'normalize','exec'))
for f in paths:
 bpy.ops.wm.open_mainfile(filepath=str(f));refs=[]
 if f.name.endswith('_Authoring.blend'):
  rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');normalize_action_rotations(rig)
 for im in bpy.data.images:
  if im.source!='FILE':continue
  target=lookup.get(hashlib.sha256(bytes(im.packed_file.data)).hexdigest()) if im.packed_file else None
  if target:
   im.unpack(method='REMOVE');im.filepath='//'+os.path.relpath(target,f.parent);im.reload();refs.append({'image':im.name,'path':str(target.relative_to(P)),'exists':True})
  elif not im.packed_file:
   path=Path(bpy.path.abspath(im.filepath));assert path.is_file(),str(path)
   if not path.is_relative_to(P):path=lookup[hashlib.sha256(path.read_bytes()).hexdigest()]
   im.filepath='//'+os.path.relpath(path,f.parent);refs.append({'image':im.name,'path':str(path.relative_to(P)),'exists':True})
 bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True)
 with f.open('rb') as h:os.fsync(h.fileno())
 report.append({'file':str(f.relative_to(P)),'shared_texture_references':refs,'remaining_embedded_images':sum(bool(im.packed_file) for im in bpy.data.images),'missing_images':[]})
with (P/'audit/Editable_Source_Texture_Checks.json').open('w') as h:json.dump(report,h,indent=2);h.flush();os.fsync(h.fileno())
print('SOURCES_EXTERNALIZED',len(report),flush=True)
