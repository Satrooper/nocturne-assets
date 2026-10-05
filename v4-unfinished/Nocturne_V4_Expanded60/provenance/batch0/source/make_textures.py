from pathlib import Path
import sys
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1]/'textures';P.mkdir(exist_ok=True)
N=1024;rng=np.random.default_rng(5812)
y,x=np.mgrid[0:N,0:N].astype(np.float32)/N
palettes={'cinder':(.23,.115,.062),'frost':(.34,.43,.46),'storm':(.125,.145,.205),'thorn':(.15,.19,.105),'obsidian':(.10,.085,.079),'crimson':(.25,.045,.052),'abyss':(.07,.15,.145),'dune':(.39,.265,.12),'moon':(.225,.23,.255),'iron':(.19,.205,.215),'bone':(.57,.49,.34),'leather':(.145,.091,.052),'bark':(.18,.13,.075),'metal':(.23,.245,.26),'chitin':(.105,.066,.04),'flesh':(.27,.14,.135),'cloth':(.095,.075,.11)}
noise=gaussian_filter(rng.random((N,N)).astype('f'),2,mode='wrap');noise=(noise-.5)*1.8
large=gaussian_filter(rng.random((N,N)).astype('f'),24,mode='wrap');large=(large-large.min())/(large.max()-large.min())
sites=np.array([((i+rng.uniform(-.28,.28))/18,(j+rng.uniform(-.28,.28))/22) for j in range(22) for i in range(18)])
periodic=np.concatenate([sites+[u,v] for u in [-1,0,1] for v in [-1,0,1]])
dists,indices=cKDTree(periodic).query(np.column_stack((x.ravel(),y.ravel())),k=2)
edge=(dists[:,1]-dists[:,0]).reshape(N,N)
cellmottles=rng.uniform(.7,1.25,len(periodic))[indices[:,0]].reshape(N,N)
for name,col in palettes.items():
 row=np.floor(y*22);u=(x*18+(row%2)*.5)%1;v=(y*22)%1
 dist=np.sqrt(((u-.5)*1.65)**2+((v-.48)*1.05)**2)
 h=np.clip(edge*150,0,1)**.45*cellmottles
 h*=.82+.18*np.cos(v*np.pi)
 if name in ('bark','leather','cloth','metal','bone'):
  if name=='bark':h=.5+.2*np.sin(x*180+np.sin(y*30)*2)+noise*.6
  elif name=='cloth':h=.5+.1*np.sin(x*700)*np.sin(y*700)+noise*.05
  elif name=='metal':h=.5+gaussian_filter(noise,(.6,8),mode='wrap')*.5
  elif name=='bone':h=.5+gaussian_filter(noise,(6,1),mode='wrap')*.2
  else:h=gaussian_filter(noise,1,mode='wrap')+.5
 h=gaussian_filter(h, .65,mode='wrap')+noise*.09
 stain=.65+.38*large+.22*h+noise*.1
 rgb=np.clip(np.array(col)[None,None,:]*stain[:,:,None]*.94,0,1)
 if name=='metal':rgb=rgb*(.85+.15*large[:,:,None]);rgb[:,:,0]+=.09*np.clip(large-.58,0,1)
 rough=np.clip(.61+.21*large-.20*h+noise*.1,.22,.96)
 gx=(np.roll(h,-1,1)-np.roll(h,1,1))*3;gy=(np.roll(h,-1,0)-np.roll(h,1,0))*3
 normal=np.dstack((-gx,-gy,np.ones_like(h)));normal/=np.linalg.norm(normal,axis=2)[:,:,None]
 for typ,arr in [('basecolor',rgb),('normal',normal*.5+.5),('roughness',rough)]:
  if '--repair' in sys.argv and name+'_'+typ+'.png' not in ['storm_basecolor.png','moon_normal.png']:continue
  im=Image.fromarray((np.clip(arr,0,1)*255).astype('uint8'));im=im.resize((2048,2048),Image.Resampling.LANCZOS);im.save(P/(name+'_'+typ+'.png'))
print('17 PBR surface sets, 2048x2048')
