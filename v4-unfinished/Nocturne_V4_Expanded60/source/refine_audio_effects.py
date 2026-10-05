"""Original deterministic asset revisions; no recorded samples or licensed external media."""
from pathlib import Path
import json, hashlib, wave, os
import numpy as np
from scipy.signal import butter,sosfilt,lfilter
from PIL import Image, ImageDraw, ImageFilter
P=Path(__file__).resolve().parents[1];BASE=P.parent/'Nocturne_V4_Full_Pack'
def savejson(p,v):
 with p.open('w') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
rows=json.loads((BASE/'audio/audio_manifest.json').read_text())
for row in rows:
 name=row['asset'];src=BASE/row['file'];rng=np.random.default_rng(int(hashlib.sha256(name.encode()).hexdigest()[:8],16))
 with wave.open(str(src)) as w:rate=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
 t=np.arange(len(x))/rate;n=rng.normal(0,1,len(x));low=sosfilt(butter(2,110,fs=rate,output='sos'),n)
 if any(a in name.lower() for a in ['roar','growl','call']):
  f=42+rng.uniform(0,70);phase=2*np.pi*(f*t+6*np.sin(t*5));throat=(np.sin(phase)+.4*np.sin(phase*2.03))*(np.sin(np.pi*t/max(t[-1],.01))**.7);air=sosfilt(butter(2,[230,1700],fs=rate,btype='bandpass',output='sos'),n)*.10;y=.60*x+.23*throat+.20*air*np.sin(np.pi*t/max(t[-1],.01));change='Added frequency-modulated throat resonance and band-limited breath layer; deterministic synthetic creature voice.'
 elif any(a in name.lower() for a in ['impact','hit','footstep','fire','crack','fracture']):
  transient=sosfilt(butter(2,[900,6800],fs=rate,btype='bandpass',output='sos'),n)*np.exp(-t/0.018);body=(np.sin(2*np.pi*(90*t+12*(1-np.exp(-t/.035))))+.4*low)*np.exp(-t/.11);y=.78*x+.22*transient+.23*body;change='Reshaped attack transient and added low-frequency impact body; synthetic layers.'
 else:
  y=.83*x+.13*sosfilt(butter(2,[500,4200],fs=rate,btype='bandpass',output='sos'),n)*np.sin(np.pi*t/max(t[-1],.01));change='Added controlled band-limited movement/air layer; synthetic layers.'
 y=sosfilt(butter(2,30,fs=rate,btype='highpass',output='sos'),y);fade=min(240,len(y)//10);y[:fade]*=np.linspace(0,1,fade);y[-fade:]*=np.linspace(1,0,fade);y=np.tanh(y*1.15);y*=.86/max(np.max(np.abs(y)),1e-6)
 dest=P/row['file'];q=np.round(y*32767).astype('<i2')
 with wave.open(str(dest),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(q.tobytes())
 row.update(status='revised_synthetic_sound_design_pending_listening',changes=change,peak_linear=float(np.max(np.abs(q))/32768),rms_linear=float(np.sqrt(np.mean(y*y))),auditory_review=False,playback={'spatialization':'mono 3D emitter; creature mouth, weapon muzzle, or contact anchor','gain_db':-6,'pitch_variation_semitones':[-1,1]},remaining=['Listening and in-game mix approval','Recorded foley/vocal realism where desired']);print('AUDIO_REVISED',name,flush=True)
savejson(P/'audio/audio_manifest.json',rows)
fx=json.loads((BASE/'effects/effects_manifest.json').read_text())
for row in fx:
 name=row['name'];rng=np.random.default_rng(int(hashlib.sha256(name.encode()).hexdigest()[:8],16));frames=[];paths=[]
 for j in range(90):
  ang=rng.uniform(0,np.pi*2);vel=rng.uniform(30,120);paths.append((ang,vel,rng.uniform(1,4),rng.uniform(.05,.9)))
 for k in range(16):
  t=k/15;im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im)
  if name=='lightning_arc':
   pts=[(128+np.sin(j*1.7+t*17)*18+rng.uniform(-8,8),240-j*12) for j in range(19)];d.line(pts,fill=(110,160,255,int(255*(1-t)**.35)),width=7);d.line(pts,fill=(230,245,255,int(255*(1-t)**.35)),width=2)
   for j in [5,10,14]:a=pts[j];d.line([a,(a[0]+rng.uniform(-45,45),a[1]-25)],fill=(120,175,255,int(160*(1-t))),width=2)
  elif name in ['flame_plume','toxic_cloud','shadow_smoke','blood_mist','dust_impact']:
   color={'flame_plume':(255,125,24),'toxic_cloud':(105,145,55),'shadow_smoke':(65,61,83),'blood_mist':(138,16,22),'dust_impact':(120,101,76)}[name]
   for idx,(a,v,r,delay) in enumerate(paths[:38]):
    f=max(0,t-delay*.35);rad=(7+f*22)*(1-delay*.5);x=128+np.cos(a)*v*f*.65;y=190-v*f*(1.1 if name=='flame_plume' else .6)+np.sin(a)*f*30;alpha=int(85*np.sin(np.pi*min(1,f/0.8))*(1-t*.65));d.ellipse((x-rad,y-rad,x+rad,y+rad),fill=(*color,max(0,alpha)))
   im=im.filter(ImageFilter.GaussianBlur(3))
  elif name=='lunar_pulse':
   radius=8+t*110;d.ellipse((128-radius,128-radius,128+radius,128+radius),outline=(140,185,255,int(220*(1-t))),width=max(1,int(8*(1-t))));d.ellipse((128-radius*.85,128-radius*.85,128+radius*.85,128+radius*.85),outline=(190,145,250,int(100*(1-t))),width=2)
  else:
   color={'ember_burst':(255,117,20),'metal_sparks':(255,207,96),'frost_shatter':(151,220,247),'water_splash':(133,196,226),'spore_burst':(174,189,91)}[name]
   for a,v,r,delay in paths:
    f=max(0,t-delay*.08);x=128+np.cos(a)*v*f;y=128+np.sin(a)*v*f+38*f*f;alpha=int(255*(1-t)**.7);length=(5 if name=='metal_sparks' else 2)*(1-t)+1
    if name=='frost_shatter':d.polygon([(x,y-r*2),(x-r,y),(x+r,y+r)],fill=(*color,alpha))
    else:d.line([(x,y),(x-np.cos(a)*length,y-np.sin(a)*length)],fill=(*color,alpha),width=max(1,int(r*(1-t*.55))))
  frames.append(im)
 atlas=Image.new('RGBA',(1024,1024))
 for i,im in enumerate(frames):atlas.paste(im,((i%4)*256,(i//4)*256))
 atlas.save(P/'effects'/row['file']);row.update(revision='directional_layered_procedural_iteration',changes='Distinct effect-specific silhouettes, propagation and decay; redesigned pixels rather than larger atlas.',engine_tested=False,quality_status='procedural flipbook; not production volumetric simulation',blend='alpha blend' if name in ['toxic_cloud','shadow_smoke','blood_mist','dust_impact','water_splash','frost_shatter','spore_burst'] else 'additive')
 frames[0].save(P/'effects'/(name+'_first_frame.png'))
 frames[0].save(P/'previews'/(name+'_Motion.gif'),save_all=True,append_images=frames[1:],duration=42,loop=0,disposal=2)
 print('EFFECT_REVISED',name,flush=True)
savejson(P/'effects/effects_manifest.json',fx)
