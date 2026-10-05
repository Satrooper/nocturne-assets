import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];report=[]
paths=[f for cat in ['dragons','bosses','enemies','weapons'] for f in (P/cat).glob('*/*.blend')]+list((P/'player_animation').glob('*.blend'))+list((P/'player_handling').glob('*.blend'))
for f in paths:
 bpy.ops.wm.open_mainfile(filepath=str(f));missing=[];changed=0
 for im in bpy.data.images:
  if im.source!='FILE' or im.packed_file:continue
  path=Path(bpy.path.abspath(im.filepath))
  if not path.exists():
   replacement=P/'textures'/Path(im.filepath).name
   if replacement.exists():im.filepath=str(replacement);im.reload();changed+=1
   else:missing.append(im.filepath)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(f),compress=True);report.append({'file':str(f.relative_to(P)),'fixed_paths':changed,'missing_images':missing,'packed':not missing})
(P/'audit/Editable_Source_Texture_Checks.json').write_text(json.dumps(report,indent=2));print('SOURCE_PACKING',len(report),sum(not x['missing_images'] for x in report))
