from pathlib import Path
import wave,json,hashlib,os
import numpy as np
from PIL import Image
P=Path('Nocturne_V4_Visual_Revision');results=[]
for row in json.loads((P/'audio/audio_manifest.json').read_text()):
 f=P/row['file']
 with wave.open(str(f)) as w:
  data=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2');result={'file':row['file'],'sample_rate':w.getframerate(),'channels':w.getnchannels(),'sample_width_bytes':w.getsampwidth(),'frames':len(data),'peak':float(np.max(np.abs(data.astype(float)))/32768),'decoded':True,'auditory_review':False}
 assert result['sample_rate']==48000 and result['channels']==1 and result['peak']<.999;results.append(result)
fx=[]
for row in json.loads((P/'effects/effects_manifest.json').read_text()):
 f=P/'effects'/row['file'];im=Image.open(f);im.load();assert im.mode=='RGBA' and im.size==(1024,1024);fx.append({'file':str(f.relative_to(P)),'size':list(im.size),'mode':im.mode,'frame_layout_matches_manifest':True,'engine_playback_checked':False})
with (P/'audit/Audio_Effect_Structural_Checks.json').open('w') as h:json.dump({'audio':results,'effects':fx,'sound_design_listening_approved':False,'volumetric_fx_approved':False},h,indent=2);h.flush();os.fsync(h.fileno())
print('AUDIO_EFFECT_STRUCTURAL_PASS',len(results),len(fx),flush=True)
