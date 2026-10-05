from pathlib import Path
import struct,json,hashlib,os
P=Path(__file__).resolve().parents[1];tex=P/'textures';maps={hashlib.sha256(f.read_bytes()).hexdigest():f for f in tex.rglob('*') if f.is_file()};report=[]
for f in sorted(P.rglob('*.glb')):
 raw=f.read_bytes();magic,version,total=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and total==len(raw)
 off=12;chunks=[]
 while off<len(raw):
  n,typ=struct.unpack_from('<II',raw,off);chunks.append((typ,raw[off+8:off+8+n]));off+=8+n
 d=json.loads(next(b for t,b in chunks if t==0x4e4f534a));binary=next((b for t,b in chunks if t==0x004e4942),b'');views=d.get('bufferViews',[]);imageviews=set();rows=[]
 for im in d.get('images',[]):
  if 'bufferView' not in im:continue
  idx=im['bufferView'];v=views[idx];assert v.get('buffer',0)==0;data=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];h=hashlib.sha256(data).hexdigest();target=maps.get(h)
  if target is None:
   ext='.jpg' if im.get('mimeType')=='image/jpeg' else '.png';target=tex/'embedded'/('Image_'+h+ext);target.parent.mkdir(exist_ok=True)
   with target.open('wb') as fh:fh.write(data);fh.flush();os.fsync(fh.fileno())
   maps[h]=target
  im.pop('bufferView');im.pop('mimeType',None);im['uri']=os.path.relpath(target,f.parent).replace(os.sep,'/');imageviews.add(idx);rows.append({'texture':str(target.relative_to(P)),'image_sha256':h,'preserved_image_bytes':True})
 if not imageviews:continue
 # Retain all non-image buffer views, remapping every bufferView reference recursively.
 mapping={};newviews=[];buf=bytearray()
 for i,v in enumerate(views):
  if i in imageviews:continue
  assert v.get('buffer',0)==0
  mapping[i]=len(newviews);buf.extend(b'\0'*((-len(buf))%4));nv=dict(v);nv['byteOffset']=len(buf);buf.extend(binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]);newviews.append(nv)
 def remap(x):
  if isinstance(x,dict):
   for k,v in x.items():
    if k=='bufferView':x[k]=mapping[v]
    else:remap(v)
  elif isinstance(x,list):
   for v in x:remap(v)
 remap(d);d['bufferViews']=newviews;d['buffers'][0]['byteLength']=len(buf);js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf.extend(b'\0'*((-len(buf))%4));out=struct.pack('<III',magic,2,12+8+len(js)+8+len(buf))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf
 with f.open('wb') as fh:fh.write(out);fh.flush();os.fsync(fh.fileno())
 report.append({'file':str(f.relative_to(P)),'old_bytes':len(raw),'new_bytes':len(out),'images':rows,'geometry_animation_buffer_views_preserved':True})
with (P/'audit/GLB_Texture_Packaging.json').open('w') as h:json.dump(report,h,indent=2);h.flush();os.fsync(h.fileno())
print('EXTERNALIZED',len(report),'SAVED_BYTES',sum(x['old_bytes']-x['new_bytes'] for x in report),'NEW_TEXTURE_FILES',len(list((tex/'embedded').glob('*'))))
