from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
P=Path(__file__).resolve().parents[1];d=P/'textures';d.mkdir(exist_ok=True);n=256;y,x=np.mgrid[:n,:n]/n;rng=np.random.default_rng(4621)
nearest=np.full((n,n),100.0)
for j in range(-1,6):
 for i in range(-1,6):
  cx=(i+.5+rng.uniform(-.22,.22))/4;cy=(j+.5+rng.uniform(-.22,.22))/4;dist=((x-cx)**2+(y-cy)**2*1.4)**.5;nearest=np.minimum(nearest,dist)
h=gaussian_filter(np.maximum(0,.070-nearest),.8)+gaussian_filter(rng.normal(0,.001,(n,n)),.6)
for name,height,strength in [('skin_micro_normal',h,14),('metal_micro_normal',gaussian_filter(rng.normal(0,.001,(n,n)),(.5,4)),18)]:
 gy,gx=np.gradient(height);v=np.stack([-gx*strength,-gy*strength,np.ones_like(gx)],axis=-1);v/=np.linalg.norm(v,axis=-1,keepdims=True);Image.fromarray(((v*.5+.5)*255).astype('uint8'),'RGB').save(d/(name+'.png'))
print('MICRO_SURFACES_WRITTEN')
