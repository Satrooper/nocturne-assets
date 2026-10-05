from pathlib import Path
import struct,json,io
from PIL import Image
P=Path(__file__).resolve().parents[1]
results=[]
for f in sorted((P/'textures').glob('*.png')):
 with Image.open(f) as im:im.verify()
 results.append({'file':str(f.relative_to(P)),'passed':True})
for f in sorted(P.glob('*/*/*.glb')):
 data=f.read_bytes();length,_=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+length]);binst=20+length+8;count=0
 for im in doc.get('images',[]):
  view=doc['bufferViews'][im['bufferView']];start=binst+view.get('byteOffset',0);raw=data[start:start+view['byteLength']]
  with Image.open(io.BytesIO(raw)) as image:image.verify()
  count+=1
 results.append({'file':str(f.relative_to(P)),'embedded_images_verified':count,'passed':True})
(P/'content_validation.json').write_text(json.dumps(results,indent=2));print('CONTENT_VERIFIED',len(results),'files')
