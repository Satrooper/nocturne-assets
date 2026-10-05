from pathlib import Path
import json,hashlib,wave,io,os
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import butter,sosfilt
from PIL import Image,ImageDraw,ImageFilter
from expansion_roster import ROSTER
W=Path(__file__).resolve().parents[1];P=W/'Nocturne_Expansion_60'
def savepng(im,path):
    buffer=io.BytesIO();im.save(buffer,format='PNG');payload=buffer.getvalue()
    Image.open(io.BytesIO(payload)).load()
    tmp=path.with_suffix('.writing')
    with tmp.open('wb') as h:
        for start in range(0,len(payload),32768):h.write(payload[start:start+32768])
        h.flush();os.fsync(h.fileno())
    assert tmp.stat().st_size==len(payload);Image.open(tmp).load();os.replace(tmp,path)
for d in ['textures','audio','effects','previews','source','audit']: (P/d).mkdir(parents=True,exist_ok=True)
(P/'source/expansion_roster.py').write_text(Path(__file__).with_name('expansion_roster.py').read_text())
(P/'source/generate_expansion_media.py').write_text(Path(__file__).read_text())
for index,(cat,name,kind,description) in enumerate(ROSTER):
    rng=np.random.default_rng(91300+index);N=2048
    grain=rng.normal(size=(N,N)).astype(np.float32);macro=gaussian_filter(rng.normal(size=(N,N)).astype(np.float32),22);macro/=max(macro.std(),1e-5)
    y,x=np.mgrid[:N,:N].astype(np.float32)/N
    mechanical=kind in ['dredger','widow','furnace','executioner','eel','rook']
    relief=.20*gaussian_filter(grain,1.5)+.035*macro
    if mechanical: relief+=.07*np.sin(x*180)+.1*(np.mod(y*8,1)<.04)
    else: relief+=.12*np.sin(x*(50+index%7)*np.pi)*np.sin(y*(37+index%11)*np.pi)+.035*np.sin(y*250+x*90)
    palettes=[(.22,.13,.075),(.18,.20,.23),(.09,.13,.15),(.27,.24,.18),(.11,.16,.095),(.23,.11,.09),(.10,.13,.20),(.30,.28,.21),(.16,.15,.18),(.095,.17,.15)]
    color=np.array(palettes[index%10]);lum=np.clip(1+.12*macro+.12*grain+.25*relief,.35,1.65)
    rgb=np.clip(color[None,None,:]*lum[:,:,None]*255,0,255).astype('uint8');savepng(Image.fromarray(rgb),P/'textures'/(name+'_BaseColor.png'))
    dy,dx=np.gradient(relief);normal=np.dstack((-dx*12,-dy*12,np.ones_like(dx)));normal/=np.sqrt((normal*normal).sum(axis=2))[:,:,None]
    savepng(Image.fromarray(np.clip((normal*.5+.5)*255,0,255).astype('uint8')),P/'textures'/(name+'_Normal.png'))
    rough=np.clip((.40 if mechanical else .63)+.075*macro+.055*grain,.15,.9)
    savepng(Image.fromarray((rough*255).astype('uint8')),P/'textures'/(name+'_Roughness.png'))
    # Lossless 16-bit authoring height carries the actual procedural relief used in normals.
    savepng(Image.fromarray(np.uint16(np.clip((relief+.5)*65535,0,65535))),P/'textures'/(name+'_Height_Source16.png'))
    print('TEXTURES',name,flush=True)

sound_specs=[]
for i,(_,name,kind,_) in enumerate(ROSTER):
    sound_specs += [(name+'_Call','call',2.1+(i%5)*.27,i),(name+'_Movement','movement',.8+(i%4)*.16,i)]
for i,n in enumerate(['Blade_Shear','Heavy_Cleaver_Impact','Cable_Tension','Pincer_Snap','Servo_Start','Servo_Stop','Wing_Canopy','Shell_Scrape','Acid_Drip','Stone_Resonance']):sound_specs.append((n,'special',.7+i*.11,i+30))
records=[]
for name,kind,dur,seed in sound_specs:
    rng=np.random.default_rng(4100+seed*3+(kind=='movement'));sr=48000;t=np.arange(int(sr*dur))/sr;n=rng.normal(0,1,len(t));env=np.sin(np.pi*t/dur)**.7
    if kind=='call':
        fundamental=34+(seed%10)*11;phase=2*np.pi*(fundamental*t+(3+seed%5)*np.sin(t*(3+seed%4)))
        y=sum(np.sin(phase*k)/(k**1.35) for k in range(1,6));y+=sosfilt(butter(2,[180+seed*8,2000+seed*20],btype='bandpass',fs=sr,output='sos'),n)*.30
        y*=env*(.7+.3*np.sin(t*(8+seed%6))**2)
    elif kind=='movement':
        y=np.zeros(len(t));count=2+seed%5
        for j in range(count):
            tau=t-(j+.15)*dur/count;mask=tau>=0;decay=np.exp(-np.maximum(tau,0)/(.05+.012*(seed%4)))*mask
            y+=(np.sin(2*np.pi*(80+seed*7)*np.maximum(tau,0))+.45*n)*decay
        y=sosfilt(butter(2,4200,fs=sr,output='sos'),y)
    else:y=(sosfilt(butter(2,[220+seed*4,6000],btype='bandpass',fs=sr,output='sos'),n)+.5*np.sin(2*np.pi*(120+seed*5)*t))*np.exp(-t/(.12+seed*.003))
    y=np.tanh(y);fade=min(300,len(y)//10);y[:fade]*=np.linspace(0,1,fade);y[-fade:]*=np.linspace(1,0,fade);y*=.8/max(abs(y).max(),1e-6)
    q=np.round(y*32767).astype('<i2');f=P/'audio'/(name+'.wav')
    with wave.open(str(f),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(q.tobytes())
    records.append({'asset':name,'file':'audio/'+f.name,'source':'original deterministic synthesis; not recorded','duration_s':len(q)/sr,'sample_rate':sr,'channels':1,'peak_linear':float(abs(q.astype(float)).max()/32768),'gain_db':-6,'spatial_anchor':'mouth' if kind=='call' else 'contact','listening_approved':False,'engine_tested':False,'seed':seed})
(P/'audio/audio_manifest.json').write_text(json.dumps(records,indent=2))

fxnames=['gravity_well','acid_ribbon','sonic_cone','sand_vortex','plasma_lattice','bone_fragments','oil_spray','bioluminescent_trail','shield_hex_break','steam_vent','ink_ring','electric_tether'];fx=[]
for idx,name in enumerate(fxnames):
    rng=np.random.default_rng(5500+idx);frames=[];paths=rng.uniform(size=(50,4))
    for k in range(24):
        t=k/23;im=Image.new('RGBA',(256,256));d=ImageDraw.Draw(im);alpha=int(255*(1-t));col=[(137,93,222),(118,194,49),(150,213,243),(192,156,105),(101,196,250),(218,207,170),(72,57,43),(59,223,182),(144,182,229),(180,194,208),(50,48,67),(192,223,255)][idx]
        if idx==0:
            for j in range(3):
                r=105*(1-t)+j*6;d.ellipse((128-r,128-r*.4,128+r,128+r*.4),outline=(*col,alpha),width=3)
        elif idx in [1,7,11]:
            pts=[(12+j*8,128+np.sin(j*.55+t*13)*(15+idx*2)) for j in range(30)];d.line(pts,fill=(*col,alpha),width=5 if idx==1 else 2)
            if idx==11:
                for j in range(0,29,4):d.line([pts[j],(pts[j][0]+4,pts[j][1]-22)],fill=(*col,alpha),width=1)
        elif idx==2:
            for j in range(4):
                r=(t*170-j*17);d.arc((128-r,128-r,128+r,128+r),195,345,fill=(*col,alpha),width=3) if r>0 else None
        elif idx==3:
            for j in range(8):
                r=(j+1)*9*(.3+t);a=j*.8+t*10;px=128+np.cos(a)*r;py=230-j*21;d.ellipse((px-r*.5,py-7,px+r*.5,py+7),outline=(*col,int(alpha*.6)),width=3)
        elif idx in [4,8]:
            for j in range(12):
                a=j*np.pi/6;r=25+t*90;cx=128+np.cos(a)*r;cy=128+np.sin(a)*r
                points=[(cx+np.cos(a+q*np.pi/3)*(6+10*t),cy+np.sin(a+q*np.pi/3)*(6+10*t)) for q in range(6)]
                d.line(points+[points[0]],fill=(*col,alpha),width=2)
                if idx==4:d.line([(128,128),(cx,cy)],fill=(*col,int(alpha*.45)),width=1)
        elif idx==10:
            r=t*114;d.ellipse((128-r,128-r,128+r,128+r),outline=(*col,alpha),width=12)
        else:
            for a,b,c,e in paths:
                theta=a*np.pi*2;r=(20+b*100)*t;px=128+np.cos(theta)*r;py=128+np.sin(theta)*r+(30*t*t if idx!=9 else -100*t);rad=2+c*6 if idx!=9 else 9+t*20
                if idx==5:d.polygon([(px,py-rad),(px+rad,py),(px-2,py+rad)],fill=(*col,alpha))
                else:d.ellipse((px-rad,py-rad,px+rad,py+rad),fill=(*col,int(alpha*(.45 if idx==9 else .8))))
            if idx==9:im=im.filter(ImageFilter.GaussianBlur(4))
        frames.append(im)
    atlas=Image.new('RGBA',(1536,1024))
    for j,im in enumerate(frames):atlas.paste(im,((j%6)*256,(j//6)*256))
    atlas.save(P/'effects'/(name+'.png'));frames[0].save(P/'previews'/(name+'.gif'),save_all=True,append_images=frames[1:],duration=40,loop=0,disposal=2)
    fx.append({'name':name,'file':'effects/'+name+'.png','frames':24,'columns':6,'rows':4,'frame_px':256,'fps':25,'duration_s':.96,'blend':'alpha' if idx in [1,3,5,6,9,10] else 'additive','loop':False,'anchor':'effect_socket','source':'procedural original flipbook','engine_tested':False})
(P/'effects/effects_manifest.json').write_text(json.dumps(fx,indent=2))
print('MEDIA_DONE',len(records),len(fx),flush=True)
