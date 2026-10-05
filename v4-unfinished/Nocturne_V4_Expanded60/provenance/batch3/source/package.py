from pathlib import Path
import json,hashlib,zipfile,os,shutil,subprocess
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];root=P.parent
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
views=['Front','Side','Back','Limbs','Hand','Feet'];out=Image.new('RGB',(1200,6*650),(22,24,27));d=ImageDraw.Draw(out)
for i,v in enumerate(views):
 for j,label in enumerate(['Before','After']):
  im=Image.open(P/'previews'/f'Sentinel_{label}_{v}.png');im.load();out.paste(im.convert('RGB'),(j*600,i*650+50));d.text((j*600+18,i*650+13),f'{label}: {v}',font=font,fill=(235,235,235))
out.save(P/'previews/Sentinel_Before_After.jpg',quality=92)
# Verify every frame has finished writing; playback length follows each clip's source duration.
meta=json.load(open(P/'bosses/Siege_Sentinel/asset.json'));clips={x['name']:x for x in meta['clips']}
for name in ['Walk_InPlace','Piston_Punch_Right','Brace']:
 folder=P/'previews'/('frames_'+name)
 for f in sorted(folder.glob('*.png')):
  im=Image.open(f);im.verify();im=Image.open(f);im.load()
 assert len(list(folder.glob('*.png')))==16
 dur=clips[name].get('exported_duration_s',clips[name].get('duration',1));dest=P/'previews'/f'Sentinel_{name}.mp4'
 subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(16/float(dur)),'-i',str(folder/'%03d.png'),'-vf','fps=30','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(dest)],check=True)
 subprocess.run(['ffmpeg','-v','error','-i',str(dest),'-f','null','-'],check=True)
status=json.load(open(root/'restored/nocturne-v4-batch02/audit/Collection_Status.json'));status['scope']='Entire collection; batch03 is Sentinel limb/contact revision only; full realistic V4 unfinished'
for c in status['creatures']:
 if c['name']=='Siege_Sentinel':
  c.update(status='partially upgraded',reason='Rebuilt limb and pelvis geometry; preserved 52 bones and 21 clips; 19 clips received leg/contact correction.',weaknesses=['Stylized head/chest and narrow neck still lack mature cinematic design.','Automatic UVs and budget decimation; no manual sculpt/retopology. Visible atlas seams and simplified surfaces remain.','Death and Ground_Slam foot penetration unresolved; full-body collision review and artistic combat polish unfinished.','Joint bearing articulation is kinematic; no physical mechanism simulation.'])
status['batch03_player_status']='unfinished: player handling not created in this batch; prior lost work is not a delivered asset';status['batch03_audio_effects_status']='retained in prior packs, no changes this batch';status['engine_tested']=False;status['iphone_tested']=False
(P/'audit/Collection_Status.json').write_text(json.dumps(status,indent=2))
# Every packaged payload gets a digest. Exclude transient frames, backup scenes and process logs.
files=[f for f in sorted(P.rglob('*')) if f.is_file() and f.suffix not in ['.log','.blend1','.blend2'] and '__pycache__' not in f.parts and not any(x.startswith('frames_') or x.endswith('.fbm') for x in f.parts) and f.name!='file_integrity.json']
digests={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files};(P/'file_integrity.json').write_text(json.dumps(digests,indent=2));files.append(P/'file_integrity.json')
zipname=root/'Nocturne_V4_Sentinel_Limbs_Batch03.zip';tmp=zipname.with_suffix('.tmp')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,6) as z:
 for f in files:z.write(f,str(f.relative_to(root)))
with open(tmp,'rb') as f:os.fsync(f.fileno())
os.replace(tmp,zipname)
extract=root/'batch03-extraction-check';shutil.rmtree(extract,ignore_errors=True)
with zipfile.ZipFile(zipname) as z:
 assert z.testzip() is None;z.extractall(extract);entries=len(z.infolist())
for f in files:
 p=extract/f.relative_to(root);assert p.read_bytes()==f.read_bytes()
subprocess.run(['unzip','-tq',str(zipname)],check=True)
sha=hashlib.sha256(zipname.read_bytes()).hexdigest();(root/'Nocturne_V4_Sentinel_Limbs_Batch03.sha256').write_text(sha+'  '+zipname.name+'\n')
report={'archive':zipname.name,'sha256':sha,'bytes':zipname.stat().st_size,'entries':entries,'every_entry_crc_passed':True,'normal_extraction_passed':True,'all_extracted_bytes_match':True,'unzip_test_passed':True,'engine_tested':False,'iphone_tested':False};(root/'Nocturne_V4_Sentinel_Limbs_Batch03_Validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
