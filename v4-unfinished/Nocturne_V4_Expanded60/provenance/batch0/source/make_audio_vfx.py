from pathlib import Path
import numpy as np,json,wave,math
from scipy.signal import butter,sosfilt
from scipy.ndimage import gaussian_filter
from PIL import Image
P=Path(__file__).resolve().parents[1];A=P/'audio';V=P/'effects';A.mkdir(exist_ok=True);V.mkdir(exist_ok=True)
SR=48000;records=[]
def filt(x,low=None,high=None):
 if low and high:return sosfilt(butter(3,[low,high],btype='band',fs=SR,output='sos'),x)
 return sosfilt(butter(3,high or low,btype='low' if high else 'high',fs=SR,output='sos'),x)
def save(name,x,category):
 x=x.astype('f');x-=x.mean();fade=min(480,len(x)//10);x[:fade]*=np.linspace(0,1,fade);x[-fade:]*=np.linspace(1,0,fade)
 peak=float(np.max(np.abs(x)));x=x/max(peak,1e-9)*.82
 with wave.open(str(A/(name+'.wav')),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(SR);f.writeframes((x*32767).astype('<i2').tobytes())
 records.append({'file':name+'.wav','category':category,'sample_rate':SR,'channels':1,'bits':16,'duration':len(x)/SR,'peak_dbfs':float(20*np.log10(np.max(np.abs(x)))),'source':'original layered synthesis; not field-recorded or franchise audio'})
def roar(seed,small=False):
 rng=np.random.default_rng(seed);d=1.3 if small else 3.2;t=np.arange(int(SR*d))/SR;base=120+seed%45 if small else 38+seed%32
 frequency=base*(1+.35*np.sin(t*1.7)+.04*np.sin(t*41));phase=np.cumsum(frequency)/SR*math.tau
 voice=np.sin(phase)+.4*np.sin(phase*2.01)+.21*np.sin(phase*3.005);voice=np.tanh(voice*2)
 noise=rng.normal(size=len(t));rasp=filt(noise,150,2100)*(.5+.5*np.sin(t*math.tau*27)**2)
 throat=filt(voice,70,650)+.5*filt(voice,700,1300);air=filt(noise,900,4000)*.15
 env=(1-np.exp(-t*12))*np.exp(-t/(d*.48))*(.7+.3*np.sin(t*math.pi/d)**2)
 return (throat*.8+rasp*.35+air)*env
for i in range(10):save('dragon_roar_'+str(i+1).zfill(2),roar(70+i),'dragon vocal')
for i in range(10):save('boss_growl_'+str(i+1).zfill(2),roar(220+i),'boss vocal')
for i in range(10):save('enemy_call_'+str(i+1).zfill(2),roar(470+i,True),'enemy vocal')
for cat in ['heavy_footstep','claw_scrape','wing_whoosh','bone_impact','armour_hit','blade_swing','blade_impact','fire_breath','ice_fracture','lightning_crack','water_burst','magic_pulse']:
 for variation in range(3):
  seed=sum(map(ord,cat))+variation*71;rng=np.random.default_rng(seed);d=1.7 if cat in ('fire_breath','wing_whoosh','water_burst') else .85;t=np.arange(int(SR*d))/SR;n=rng.normal(size=len(t));low=filt(n,None,160);mid=filt(n,120,1600);high=filt(n,1800,9500)
  if 'whoosh' in cat or 'swing' in cat:
   env=np.sin(np.pi*t/d)**4;x=(mid*.5+high*.13+low)*env
  elif cat=='fire_breath':x=(filt(n,50,1800)*.7+low*2)*(1-np.exp(-t*12))*np.exp(-t*.65)
  elif cat=='magic_pulse':x=(np.sin(2*np.pi*(110*t-35*t*t))*.22+filt(n,100,2200)*.45)*np.exp(-t*6)
  else:
   ring=np.sin(2*np.pi*(370+variation*53)*t)*np.exp(-t*18)+np.sin(2*np.pi*1073*t)*np.exp(-t*23)
   sub=np.sin(2*np.pi*(70*t-20*t*t))*np.exp(-t*13)
   x=(low*2+mid*.6)*np.exp(-t*18)+high*np.exp(-t*65)*.25+sub*.7
   if cat in ('blade_impact','armour_hit','ice_fracture'):x+=ring*.18
   if cat=='claw_scrape':x+=high*np.exp(-t*4)*.12*(.4+.6*np.sin(t*120)**2)
   if cat=='lightning_crack':x+=high*np.exp(-t*9)*.5
   if cat=='water_burst':x=filt(n,100,2600)*np.exp(-t*3)+low*np.exp(-t*5)
  # Sparse room reflections retain a clear attack.
  for delay,gain in [(.037,.15),(.083,.09),(.137,.05)]:
   sh=int(delay*SR)
   if sh<len(x):x[sh:]+=x[:-sh].copy()*gain
  save(cat+'_'+str(variation+1).zfill(2),x,cat)
(A/'audio_manifest.json').write_text(json.dumps(records,indent=2))
# Transparent 16-frame effect atlases: each frame is 256px; row-major 4x4.
fx={'ember_burst':(1,.29,.025),'flame_plume':(1,.16,.015),'frost_shatter':(.36,.72,1),'lightning_arc':(.50,.67,1),'blood_mist':(.45,.012,.025),'toxic_cloud':(.30,.52,.06),'dust_impact':(.42,.28,.12),'water_splash':(.22,.55,.75),'lunar_pulse':(.52,.50,1),'shadow_smoke':(.10,.065,.15),'metal_sparks':(1,.66,.20),'spore_burst':(.48,.50,.19)}
fxrec=[]
for fi,(name,col) in enumerate(fx.items()):
 rng=np.random.default_rng(400+fi);n=256;yy,xx=np.mgrid[-1:1:complex(n),-1:1:complex(n)];r=np.sqrt(xx*xx+yy*yy);ang=np.arctan2(yy,xx);noise=gaussian_filter(rng.random((n,n)),4);noise=(noise-noise.min())/(noise.max()-noise.min())
 atlas=np.zeros((n*4,n*4,4),np.uint8)
 for frame in range(16):
  t=frame/15;radius=.14+t*.70;envelope=(1-t)**.7
  if name in ('lunar_pulse','water_splash','dust_impact'):
   intensity=np.exp(-((r-radius)/(.035+.08*t))**2)*(noise*.7+.3)*envelope
  elif name=='lightning_arc':
   line=np.sin(yy*18+fi)*.17+np.sin(yy*47+t*7)*.07;intensity=np.exp(-((xx-line)/(.008+.02*t))**2)*(1-abs(yy))*envelope
  elif name in ('flame_plume','ember_burst','metal_sparks'):
   drift=.25*np.sin(yy*9+t*8)*(1-abs(yy));rr=np.sqrt((xx-drift)**2+(yy+.25-t*.4)**2*.45)
   intensity=np.clip(1-rr/(.3+t*.5),0,1)**1.3*(noise*.8+.2)*envelope
   intensity+=np.exp(-((np.sin(ang*11+fi)*.18+radius-r)/.025)**2)*.18*envelope
  else:intensity=np.exp(-(r/(.18+t*.7))**2)*(noise*.85+.15)*envelope
  alpha=np.clip(intensity*1.5,0,1);rgb=np.zeros((n,n,3));rgb[:]=col;rgb*=.7+np.clip(intensity,0,1)[:,:,None]*.3
  rgba=np.dstack((rgb,alpha));tile=(np.clip(rgba,0,1)*255).astype('uint8');atlas[(frame//4)*n:(frame//4+1)*n,(frame%4)*n:(frame%4+1)*n]=tile
 Image.fromarray(atlas,'RGBA').save(V/(name+'_atlas.png'))
 fxrec.append({'name':name,'file':name+'_atlas.png','frames':16,'columns':4,'rows':4,'frame_size':256,'fps':24,'duration':16/24,'frame_order':'row-major, top-left first','alpha':'straight','blend':'additive suggested' if name in ('lightning_arc','lunar_pulse','metal_sparks','flame_plume','ember_burst') else 'alpha blend','loop':False,'type':'2D transparent flipbook; requires engine particle/billboard material'})
(V/'effects_manifest.json').write_text(json.dumps(fxrec,indent=2))
print('Created',len(records),'WAV files and',len(fxrec),'effect atlases')
