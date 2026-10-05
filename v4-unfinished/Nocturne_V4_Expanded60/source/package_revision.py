from pathlib import Path
import os,json,hashlib,zipfile,shutil
W=Path('/workspace/scratch/c638d9b24e22');P=W/'Nocturne_V4_Visual_Revision';out=W/'Nocturne_V4_All30_Revision_Checkpoint.zip'
def skip(f):
 rel=f.relative_to(P)
 return not f.is_file() or f.name.endswith(('.blend1','.blend2','.pyc')) or any(x.startswith('.') or x=='__pycache__' or x.endswith('.fbm') or x.startswith('frames_') for x in rel.parts)
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(f,s):
 with f.open('w') as h:h.write(s);h.flush();os.fsync(h.fileno())
files=[f for f in sorted(P.rglob('*')) if not skip(f) and f.name!='File_Integrity.json'];integrity=[]
for f in files:
 with f.open('rb') as h:os.fsync(h.fileno())
 integrity.append({'path':str(f.relative_to(P)),'size_bytes':f.stat().st_size,'sha256':sha(f)})
write(P/'audit/File_Integrity.json',json.dumps({'scope_complete':False,'files':integrity,'excluded':'Transient Blender backups, import-created fbm texture copies, render-frame intermediates, pycache. Historical sources/previews preserved under provenance.'},indent=2))
files.append(P/'audit/File_Integrity.json');tmp=out.with_suffix('.tmp')
with tmp.open('wb') as h:
 with zipfile.ZipFile(h,'w',zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
  for i,f in enumerate(files):
   z.write(f,str(Path('Nocturne_V4_Full_Pack')/f.relative_to(P)))
   if i%100==0:print('PACK',i,len(files),flush=True)
 h.flush();os.fsync(h.fileno())
os.replace(tmp,out);fd=os.open(W,os.O_DIRECTORY);os.fsync(fd);os.close(fd)
print('ARCHIVE_WRITTEN',out.stat().st_size,sha(out),flush=True)
