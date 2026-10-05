from pathlib import Path
import zipfile,json,hashlib,tempfile,subprocess,os
P=Path(__file__).resolve().parents[1];dest=P.parent/'Nocturne_V4_Benchmark_Iteration.zip';tmp=dest.with_suffix('.building');files=sorted(f for f in P.rglob('*') if f.is_file() and '__pycache__' not in f.parts and 'motion_frames' not in f.parts and 'audit_inputs' not in f.parts and f.suffix not in ['.blend1','.blend2'] and not f.name.endswith('_review.png') and f.name!='file_integrity.json')
manifest={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files};(P/'file_integrity.json').write_text(json.dumps(manifest,indent=2));files.append(P/'file_integrity.json')
with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
 for f in files:z.write(f,'nocturne-v4/'+str(f.relative_to(P)))
with tmp.open('rb') as f:os.fsync(f.fileno())
tmp.replace(dest)
with zipfile.ZipFile(dest) as z:
 assert z.testzip() is None
 with tempfile.TemporaryDirectory(prefix='v4-extract-check-',dir=P.parent) as d:
  z.extractall(d)
  for f in files:
   extracted=Path(d)/'nocturne-v4'/f.relative_to(P);assert hashlib.sha256(extracted.read_bytes()).digest()==hashlib.sha256(f.read_bytes()).digest(),f
 result=subprocess.run(['unzip','-tq',str(dest)],capture_output=True,text=True);assert result.returncode==0,result.stdout;entries=len(z.infolist())
sha=hashlib.sha256(dest.read_bytes()).hexdigest();dest.with_suffix('.sha256').write_text(sha+'  '+dest.name+'\n');report={'archive':dest.name,'bytes':dest.stat().st_size,'entries':entries,'all_entries_crc_passed':True,'normal_extraction_passed':True,'all_extracted_bytes_match_source':True,'external_unzip_test_passed':True,'sha256':sha};(P.parent/'V4_Packaging_Validation.json').write_text(json.dumps(report,indent=2));print('V4_ARCHIVE_VALIDATED',json.dumps(report),flush=True)
