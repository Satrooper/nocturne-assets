from pathlib import Path
import zipfile,json,hashlib,os,subprocess,shutil
W=Path('/workspace/scratch/c638d9b24e22');out=W/'Nocturne_V4_All30_Revision_Checkpoint.zip';dest=W/'work/revision_clean_extraction';shutil.rmtree(dest,ignore_errors=True);dest.mkdir(exist_ok=True)
def sha(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(f,s):
 with f.open('w') as h:h.write(s);h.flush();os.fsync(h.fileno())
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None;entries=len(z.infolist());print('ALL_ENTRY_CRC_PASS',entries,flush=True)
r=subprocess.run(['unzip','-q',str(out),'-d',str(dest)],capture_output=True,text=True);assert r.returncode==0,r.stderr;print('NORMAL_UNZIP_SUCCESS',flush=True)
p=dest/'Nocturne_V4_Full_Pack';data=json.loads((p/'audit/File_Integrity.json').read_text());bad=[]
for row in data['files']:
 f=p/row['path']
 if not f.exists() or f.stat().st_size!=row['size_bytes'] or sha(f)!=row['sha256']:bad.append(row['path'])
assert not bad,bad
actual=sorted(str(x.relative_to(dest)) for x in dest.rglob('*') if x.is_file())
with zipfile.ZipFile(out) as z:assert sorted(z.namelist())==actual
checksum=sha(out);report={'archive':out.name,'size_bytes':out.stat().st_size,'sha256':checksum,'entries':entries,'every_entry_crc_passed':True,'normal_unzip_exit_code':r.returncode,'clean_extraction_file_list_matches':True,'per_file_size_sha256_checked':len(data['files']),'per_file_size_sha256_passed':True,'scope_complete':False,'note':'Packaging integrity does not establish artwork, animation or engine/device completion.'}
save(W/'Nocturne_V4_All30_Archive_Validation.json',json.dumps(report,indent=2));save(W/'Nocturne_V4_All30_Revision_Checkpoint.sha256',checksum+'  '+out.name+'\n');print(json.dumps(report),flush=True)
# Rebuilt player checkpoint integrity checked independently after producing tool returned.
with zipfile.ZipFile(W/'Nocturne_V4_Player_Handling_Checkpoint.zip') as z:assert z.testzip() is None;print('PLAYER_CHECKPOINT_PASS',len(z.infolist()),flush=True)
