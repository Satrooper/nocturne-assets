from pathlib import Path
import numpy as np,wave,json
from scipy.signal import butter,sosfilt
P=Path(__file__).resolve().parents[1];out=P/'audio';out.mkdir(exist_ok=True);sr=48000;rng=np.random.default_rng(4027);records=[]
def filtered(n,lo,hi):return sosfilt(butter(3,[lo,hi],btype='bandpass',fs=sr,output='sos'),rng.normal(0,1,n))
def tick(length=.15,f=1800):
 t=np.arange(round(length*sr))/sr;return .5*filtered(len(t),1000,14000)*np.exp(-t*100)+.12*np.sin(2*np.pi*f*t)*np.exp(-t*45)
def save(name,x,cues,notes):
 x=x*np.minimum(1,.75/max(1e-12,np.abs(x).max()));x[-240:]*=np.linspace(1,0,min(240,len(x)));pcm=np.rint(np.clip(x,-1,1)*32767).astype('<i2')
 with wave.open(str(out/(name+'.wav')),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())
 records.append({'file':name+'.wav','status':'new_synthesized_weapon_prototype','source':'original deterministic DSP synthesis; not recorded foley or gunfire; no external samples','sample_rate':sr,'bits':16,'channels':1,'duration_s':len(x)/sr,'peak_dbfs':float(20*np.log10(max(1e-12,np.abs(x).max()))),'cues':cues,'notes':notes,'engine_integration_required':'Spatialize dry mono sound at muzzle/mechanism; game determines occlusion, distance attenuation and environmental reflection.','perceptual_quality':'Auditory quality review remains unfinished.'})
for name,duration,body,brightness in [('Vesper_Pistol_Fire',.8,120,1),('Bastion_Rifle_Fire',1.1,80,1.2)]:
 t=np.arange(round(duration*sr))/sr;n=len(t);attack=1-np.exp(-t*2500);crack=filtered(n,1800,17000)*np.exp(-t*120)*brightness;blast=filtered(n,60,1800)*np.exp(-t*14);pressure=np.sin(2*np.pi*(body*t+18*(1-np.exp(-t*10))))*np.exp(-t*19);x=attack*(.8*crack+1.1*blast+.32*pressure)
 a=tick(.15);i=int(.065*sr);x[i:i+len(a)]+=.14*a
 save(name,x,[{'time_s':0,'event':'shot'},{'time_s':.065,'event':'mechanical_return'}],'Dry close-range synthetic impulse. No environment tail. Prototype requires listening and mix calibration.')
for name,events in [('Weapon_Magazine_Service',[(.00,2100),(.12,1100),(.72,2700),(1.04,1200)]),('Weapon_Action_Rack',[(.00,1100),(.16,2600)])]:
 x=np.zeros(round((events[-1][0]+.3)*sr))
 for ts,f in events:a=tick(.2,f);i=round(ts*sr);x[i:i+len(a)]+=a
 save(name,x,[{'time_s':ts,'event':'mechanical_tick'} for ts,f in events],'Separate service sound; align selected cues to animation metadata rather than playing blindly from clip start.')
(out/'audio_manifest.json').write_text(json.dumps(records,indent=2));print('AUDIO_CREATED',len(records))
