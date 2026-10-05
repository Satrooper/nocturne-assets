from pathlib import Path
import json,hashlib,zipfile,tempfile,subprocess,os,shutil,wave
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];ROOT=P.parent
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
# Verify all PNGs after renderer completion; never encode partially written frames.
for p in list((P/'previews').rglob('*.png'))+list((P/'textures').glob('*.png')):
 with Image.open(p) as im:im.verify()
 with Image.open(p) as im:im.load()
for name,duration in [('Sentinel',2.0),('Rifle',2.4)]:
 frames=P/'previews'/('frames_'+name);assert len(list(frames.glob('*.png')))==16
 out=P/'previews'/(name+'_Delivered_Model_Motion.mp4');r=subprocess.run(['ffmpeg','-y','-v','error','-framerate',str(16/duration),'-i',str(frames/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(out)],capture_output=True,text=True);assert r.returncode==0 and not r.stderr,r.stderr
 r=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(out),'-f','null','-'],capture_output=True,text=True);assert r.returncode==0 and not r.stderr,r.stderr
sheet=Image.new('RGB',(1600,930),(22,25,28));d=ImageDraw.Draw(sheet)
for row,label in enumerate(['Before','After']):
 for col,view in enumerate(['Front','Side','Back','Closeup']):
  im=Image.open(P/'previews'/('Sentinel_'+label+'_'+view+'.png')).convert('RGB').resize((400,400));sheet.paste(im,(col*400,50+row*440));d.text((col*400+12,10+row*440),label+' — '+view,font=font,fill=(235,235,235))
d.text((12,900),'Same lighting/cameras. Before: prior V4 benchmark. Partial geometry revision; realism target unfinished.',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18),fill=(230,230,230));sheet.save(ROOT/'Nocturne_V4_Batch02_Before_After.jpg',quality=93)
weapons=Image.new('RGB',(1500,1110),(22,25,28));d=ImageDraw.Draw(weapons)
for i,name in enumerate(['Vesper_Pistol','Bastion_Rifle','Gravesong_Sword']):
 im=Image.open(P/'previews'/(name+'_Neutral.png')).convert('RGB');im.thumbnail((1100,340));weapons.paste(im,((1500-im.width)//2,30+i*365));d.text((20,8+i*365),name.replace('_',' '),font=font,fill=(235,235,235))
weapons.save(ROOT/'Nocturne_V4_Batch02_Weapons.jpg',quality=93)
shutil.copy(ROOT/'Nocturne_V4_Batch02_Before_After.jpg',P/'previews/Before_After.jpg');shutil.copy(ROOT/'Nocturne_V4_Batch02_Weapons.jpg',P/'previews/Weapons.jpg')
validation=json.loads((P/'audit/Export_Reimport_Validation.json').read_text());assert len(validation)==16 and all(v['structural_passed'] for v in validation)
for meta in P.glob('*/*/asset.json'):
 m=json.loads(meta.read_text());name=m['name'];m['lods']=[{'level':level,'file':name+('_LOD'+str(level) if level else '')+'.fbx','triangles':next(v['triangles'] for v in validation if v['file']==str(meta.parent.relative_to(P)/(name+('_LOD'+str(level) if level else '')+'.fbx')))} for level in [0,1,2]];meta.write_text(json.dumps(m,indent=2))
(P/'batch_manifest.json').write_text(json.dumps({'name':'Nocturne V4 Batch02','delivery_scope':'Incremental prototypes, not full V4','models':['Siege_Sentinel','Vesper_Pistol','Bastion_Rifle','Gravesong_Sword'],'retained_creature_clips':21,'new_weapon_mechanism_clips':4,'new_player_animation_clips':0,'new_synthesized_audio_files':4,'structural_validation':'16/16 export reimports passed','visual_review':'partial revisions reviewed; realism target unfinished','engine_testing':False,'iphone_performance_measured':False,'full_collection_complete':False},indent=2))
shutil.copy(P/'README.md',ROOT/'Nocturne_V4_Batch02_Report.md')
files=sorted(f for f in P.rglob('*') if f.is_file() and not any(x.startswith('frames_') or x=='__pycache__' or x.endswith('.fbm') for x in f.parts) and f.suffix not in ['.blend1','.blend2','.log'] and f.name!='file_integrity.json')
(P/'file_integrity.json').write_text(json.dumps({str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},indent=2));files.append(P/'file_integrity.json');dest=ROOT/'Nocturne_V4_Batch02.zip';tmp=dest.with_suffix('.building')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
 for f in files:z.write(f,P.name+'/'+str(f.relative_to(P)))
with tmp.open('rb') as f:os.fsync(f.fileno())
tmp.replace(dest)
with zipfile.ZipFile(dest) as z:
 assert z.testzip() is None
 with tempfile.TemporaryDirectory(dir=ROOT,prefix='batch02-extract-') as d:
  z.extractall(d)
  for f in files:assert hashlib.sha256((Path(d)/P.name/f.relative_to(P)).read_bytes()).digest()==hashlib.sha256(f.read_bytes()).digest()
 entries=len(z.infolist())
r=subprocess.run(['unzip','-tq',str(dest)],capture_output=True,text=True);assert r.returncode==0,r.stdout
sha=hashlib.sha256(dest.read_bytes()).hexdigest();dest.with_suffix('.sha256').write_text(sha+'  '+dest.name+'\n');report={'archive':dest.name,'bytes':dest.stat().st_size,'entries':entries,'sha256':sha,'every_entry_crc_passed':True,'normal_extraction_passed':True,'every_extracted_file_matches_source':True,'external_unzip_test_passed':True};(ROOT/'Nocturne_V4_Batch02_Packaging_Validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
