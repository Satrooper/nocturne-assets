from pathlib import Path
import json,subprocess,hashlib
P=Path(__file__).resolve().parents[1];out=P/'previews/motion';out.mkdir(exist_ok=True);records=[]
for group,cat in [('Cinder_Crown','dragons'),('Siege_Sentinel','bosses'),('Player',None)]:
 meta=json.loads((P/cat/group/'asset.json').read_text()) if cat else json.loads((P/'player_animation/animation_manifest.json').read_text());dur={c['name']:c['duration'] for c in meta['clips']};parts=[]
 for d in sorted((P/'previews/motion_frames').iterdir()):
  if not d.name.startswith(group+'_'):continue
  assert len(list(d.glob('*.png')))==24,d
  clip=d.name[len(group)+1:];duration=2.4 if clip=='Paired_Backstab' else dur[clip];dest=out/(d.name+'.mp4');title=d.name.replace('_',' ')
  vf="drawbox=x=0:y=0:w=iw:h=30:color=black@0.6:t=fill,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='"+title+"':x=8:y=8:fontsize=12:fontcolor=white,format=yuv420p"
  subprocess.run(['ffmpeg','-xerror','-hide_banner','-loglevel','error','-y','-framerate',str(24/duration),'-i',str(d/'%03d.png'),'-vf',vf,'-r','30','-c:v','libx264','-preset','medium','-crf','18',str(dest)],check=True);parts.append(dest);records.append({'asset':group,'clip':clip,'duration_s':duration,'render_frames':24,'file':str(dest.relative_to(P)),'source':'Actual delivered GLB imported into Blender, not concept art. Player has no weapon props.'})
 concat=out/(group+'_concat.txt');concat.write_text(''.join("file '"+f.name+"'\n" for f in parts));subprocess.run(['ffmpeg','-xerror','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(out/(group+'_Motion_Preview.mp4'))],check=True);concat.unlink()
 assetfile=P/cat/group/(group+'.glb') if cat else P/'player_animation/Player_Moves_With_Existing_Mannequin.glb';records.append({'asset':group,'rendered_model_sha256':hashlib.sha256(assetfile.read_bytes()).hexdigest(),'preview_file':str((out/(group+'_Motion_Preview.mp4')).relative_to(P))})
(P/'previews/preview_manifest.json').write_text(json.dumps(records,indent=2));print('MOTION_VIDEOS_ENCODED',len(records),flush=True)
