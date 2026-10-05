import bpy,math,json,sys,random
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi
P=Path(__file__).resolve().parents[1]
PALETTES=['cinder','frost','storm','thorn','obsidian','crimson','abyss','dune','moon','iron']
ROSTER=[('dragons','Cinder_Crown','dragon','cinder'),('dragons','Frost_Antler','dragon','frost'),('dragons','Storm_Wyvern','wyvern','storm'),('dragons','Thornback','dragon','thorn'),('dragons','Obsidian_Bastion','dragon','obsidian'),('dragons','Crimson_Vesper','wyvern','crimson'),('dragons','Sunken_Leviathan','serpent','abyss'),('dragons','Dune_Glasswing','wyvern','dune'),('dragons','Moonveil','dragon','moon'),('dragons','Iron_Seraph','dragon','iron'),('bosses','Cathedral_Bellwarden','knight','metal'),('bosses','Furnace_Titan','construct','iron'),('bosses','Root_Matriarch','ent','bark'),('bosses','Crypt_Arachnarch','spider','chitin'),('bosses','Horned_Regent','demon','crimson'),('bosses','Siege_Sentinel','mech','metal'),('bosses','Abyss_Maw','fish','abyss'),('bosses','Neon_Reaper','wraith','cloth'),('bosses','Mirror_Colossus','crystal','frost'),('bosses','Hundredleg','centipede','chitin'),('enemies','Cinder_Hound','hound','cinder'),('enemies','Crypt_Skitter','spider','chitin'),('enemies','Bamboo_Mantis','mantis','thorn'),('enemies','Scrapling','construct','iron'),('enemies','Crimson_Imp','demon','crimson'),('enemies','Razorfin','fish','abyss'),('enemies','Sporeling','ent','bark'),('enemies','Moon_Bat','bat','moon'),('enemies','Shard_Crab','crab','frost'),('enemies','Neon_Wisp','wisp','storm')]

def material(palette,part):
 m=bpy.data.materials.new(palette+'_'+part);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.55
 if part=='eye':
  bs.inputs['Base Color'].default_value=(.6,.21,.015,1);bs.inputs['Emission Color'].default_value=(.6,.10,.002,1);bs.inputs['Emission Strength'].default_value=.5;bs.inputs['Roughness'].default_value=.18
 elif part=='black':bs.inputs['Base Color'].default_value=(.008,.004,.004,1);bs.inputs['Roughness'].default_value=.28
 else:
  texname='bone' if part=='tooth' else 'leather' if part=='membrane' else 'metal' if part=='metal' else palette
  for typ,inputname in [('basecolor','Base Color'),('roughness','Roughness'),('normal',None)]:
   tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'textures'/(texname+'_'+typ+'.png')),check_existing=True);tex.extension='REPEAT'
   if typ!='basecolor':tex.image.colorspace_settings.name='Non-Color'
   if typ=='normal':
    nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.55 if part!='membrane' else .25;l.new(tex.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],bs.inputs['Normal'])
   else:l.new(tex.outputs['Color'],bs.inputs[inputname])
  if part=='metal' or palette=='metal':bs.inputs['Metallic'].default_value=.82
  if part=='membrane':bs.inputs['Roughness'].default_value=.65
 return m

class Creature:
 def __init__(self,entry,index):
  self.cat,self.name,self.kind,self.palette=entry;self.index=index;self.bones={};self.parts=[];self.tags={};self.mats={k:material(self.palette,k) for k in ['skin','tooth','membrane','eye','black','metal']};self.poses=[]
 def bone(self,n,h,t,parent=None):self.bones[n]=(tuple(h),tuple(t),parent);return n
 def mesh(self,n,verts,faces,uvs,weights,mat='skin',smooth=True):
  me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);me.materials.append(self.mats[mat]);uv=me.uv_layers.new(name='UVMap')
  for poly in me.polygons:
   poly.use_smooth=smooth
   for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
  groups={}
  for i,w in enumerate(weights):
   if isinstance(w,str):w={w:1}
   for b,val in w.items():
    if val<=0:continue
    if b not in groups:groups[b]=o.vertex_groups.new(name=b)
    groups[b].add([i],val,'REPLACE')
  self.parts.append(o);return o
 def ell(self,n,c,r,b,mat='skin',rings=12,sides=20,rotation=0):
  vv=[];uv=[];ff=[]
  for j in range(rings+1):
   ph=pi*j/rings
   for i in range(sides+1):
    a=math.tau*i/sides;x=r[0]*sin(ph)*cos(a);y=r[1]*sin(ph)*sin(a)
    vv.append((c[0]+x*cos(rotation)-y*sin(rotation),c[1]+x*sin(rotation)+y*cos(rotation),c[2]+r[2]*cos(ph)));uv.append((i/sides*2,j/rings))
  for j in range(rings):
   for i in range(sides):a=j*(sides+1)+i;ff.append((a,a+sides+1,a+sides+2,a+1))
  return self.mesh(n,vv,ff,uv,[b]*len(vv),mat)
 def tube(self,n,points,radii,weights,mat='skin',sides=12,sub=3,ellipse=1):
  # Catmull-Rom interpolation provides smooth anatomical curves.
  pts=[Vector(p) for p in points];vv=[];uv=[];ww=[];centers=[];rad=[];bw=[]
  for j in range(len(pts)-1):
   p0=pts[max(0,j-1)];p1=pts[j];p2=pts[j+1];p3=pts[min(len(pts)-1,j+2)]
   for k in range(sub):
    t=k/sub;q=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);centers.append(q);rad.append(radii[j]*(1-t)+radii[j+1]*t)
    wa=weights[j] if isinstance(weights[j],dict) else {weights[j]:1};wb=weights[j+1] if isinstance(weights[j+1],dict) else {weights[j+1]:1};bw.append({b:wa.get(b,0)*(1-t)+wb.get(b,0)*t for b in wa.keys()|wb.keys()})
  centers.append(pts[-1]);rad.append(radii[-1]);bw.append(weights[-1] if isinstance(weights[-1],dict) else {weights[-1]:1})
  for j,c in enumerate(centers):
   tang=(centers[min(j+1,len(centers)-1)]-centers[max(0,j-1)]).normalized();up=Vector((0,0,1))
   if abs(tang.dot(up))>.94:up=Vector((0,1,0))
   u=tang.cross(up).normalized();v=tang.cross(u).normalized()
   for i in range(sides+1):
    a=math.tau*i/sides;q=c+rad[j]*(cos(a)*u+sin(a)*v*ellipse);vv.append(q);uv.append((i/sides*2,j/max(1,len(centers)-1)*4));ww.append(bw[j])
  ff=[]
  for j in range(len(centers)-1):
   for i in range(sides):a=j*(sides+1)+i;ff.append((a,a+1,a+sides+2,a+sides+1))
  ff += [tuple(range(sides,-1,-1)),tuple((len(centers)-1)*(sides+1)+i for i in range(sides+1))]
  return self.mesh(n,vv,ff,uv,ww,mat)
 def horn(self,n,a,b,c,r,bone,mat='tooth'):
  self.tube(n,[a,b,c],[r,r*.55,.004],[bone]*3,mat,sides=10,sub=5)
 def wing(self,side,attach,span,length=2.8):
  s=side;root=Vector(attach);elbow=root+Vector((s*span*.36,-.25,span*.18));wrist=root+Vector((s*span*.62,-.7,span*.22))
  a='wingL' if s<0 else 'wingR';f=a+'_fore';self.bone(a,root,elbow,'chest');self.bone(f,elbow,wrist,a)
  self.tube(a,[root,elbow,wrist],[.17,.11,.075],['chest',a,f],sub=6)
  tips=[wrist+Vector((s*span*.40,.25,-span*.11)),wrist+Vector((s*span*.30,length*.48,-span*.25)),wrist+Vector((s*span*.12,length*.90,-span*.32)),root+Vector((s*.55,length*.76,-.5)),root+Vector((0,length*.45,-.4))]
  for j,tip in enumerate(tips[:4]):self.tube(f+'_finger'+str(j),[wrist,(wrist+tip)/2+Vector((0,-.1,.12)),tip],[.055,.034,.007],[f]*3,'skin',sides=8,sub=4)
  self.horn(a+'_thumb',wrist,wrist+Vector((s*.12,-.35,.3)),wrist+Vector((s*.06,-.46,.18)),.08,f)
  for j in range(4):
   vs=[];uv=[];ws=[];faces=[];ta,tb=tips[j],tips[j+1]
   for k in range(13):
    t=k/12
    for l in range(9):
     u=l/8;edge=ta.lerp(tb,u);edge+=(wrist-edge).normalized()*(sin(pi*u)*.18)
     pos=wrist.lerp(edge,t);pos.z-=sin(pi*t)*sin(pi*u)*.12
     vs.append(pos);uv.append((t*1.5,u));ws.append({f:.85,a:.15} if j<3 else {f:1-t*.55,'chest':t*.55})
   for k in range(12):
    for l in range(8):q=k*9+l;faces.append((q,q+1,q+10,q+9))
   self.mesh(a+'_sail',vs,faces,uv,ws,'membrane')
 def limb(self,prefix,hip,knee,ankle,foot,parent='chest',thick=.2,claws=True):
  a=prefix;b=prefix+'_shin';c=prefix+'_foot';self.bone(a,hip,knee,parent);self.bone(b,knee,ankle,a);self.bone(c,ankle,foot,b)
  self.tube(prefix,[hip,Vector(hip).lerp(Vector(knee),.45),knee,ankle,foot],[thick,thick*1.15,thick*.65,thick*.45,thick*.35],[{parent:.25,a:.75},a,{a:.5,b:.5},{b:.7,c:.3},c],sub=4)
  if claws:
   for j in (-1,0,1):
    start=Vector(foot)+Vector((j*thick*.7,0,0));mid=start+Vector((j*.06,-.20,-.04));end=mid+Vector((0,-.18,-.03));self.tube(c+'_toe',[start,mid,end],[thick*.18,thick*.15,.008],[c]*3,sides=8,sub=3)
    self.horn(c+'_claw',mid,end,end+Vector((0,-.10,.07)),thick*.14,c)
 def dragon(self):
  idx=self.index%10;wyv=self.kind in ('wyvern','bat');serp=self.kind=='serpent';heavy=1.4 if idx==4 else 1
  self.bone('root',(0,0,0),(0,0,.5));self.bone('pelvis',(0,.6,1.6),(0,0,1.7),'root');self.bone('chest',(0,0,1.7),(0,-.9,1.85),'pelvis')
  self.bone('neck1',(0,-.9,1.85),(0,-1.65,2.15),'chest');self.bone('neck2',(0,-1.65,2.15),(0,-2.4,2.45),'neck1');self.bone('head',(0,-2.4,2.45),(0,-3.4,2.3),'neck2');self.bone('jaw',(0,-2.5,2.18),(0,-3.45,2.11),'head')
  self.tube('torso_neck',[(0,1.4,1.45),(0,.65,1.65),(0,-.2,1.72),(0,-.85,1.88),(0,-1.5,2.1),(0,-2.4,2.4)],[.22,.65*heavy,.75*heavy,.50,.34,.22],['pelvis','pelvis','chest','chest',{'neck1':.65,'neck2':.35},'neck2'],sides=24,sub=6,ellipse=.85)
  # cheeks, long wedge-like muzzle, nostrils, recessed eye sockets and jaw.
  self.tube('skull',[(0,-2.35,2.45),(0,-2.7,2.52),(0,-3.08,2.40),(0,-3.52,2.35)],[.20,.34,.23,.17],['head']*4,sides=20,sub=5,ellipse=.78)
  self.tube('mandible',[(0,-2.45,2.18),(0,-2.85,2.09),(0,-3.3,2.10),(0,-3.55,2.14)],[.22,.22,.15,.10],['jaw']*4,sides=16,sub=4,ellipse=.48)
  self.ell('mouth_cavity',(0,-2.96,2.18),(.205,.49,.065),'head','black')
  for s in (-1,1):
   self.ell('socket',(s*.29,-2.73,2.55),(.065,.11,.045),'head','black');self.ell('eye',(s*.328,-2.78,2.57),(.027,.048,.027),'head','eye',rings=10,sides=14)
   self.ell('pupil',(s*.350,-2.80,2.57),(.008,.012,.025),'head','black',rings=8,sides=10)
   self.tube('brow',[(s*.18,-2.9,2.62),(s*.32,-2.67,2.67),(s*.29,-2.4,2.67)],[.075,.085,.015],['head']*3,sides=10,sub=4)
   self.ell('nostril',(s*.14,-3.4,2.44),(.045,.075,.025),'head','black',rings=8,sides=12)
   for j in range(11):
    y=-2.66-j*.075;wid=.2-(j/11)*.06;self.horn('fang',(s*wid,y,2.23),(s*wid,y-.015,2.10),(s*wid,y-.04,2.07),.018,'head')
    if j%2==0:self.horn('lower_fang',(s*wid,y,2.15),(s*wid,y-.02,2.25),(s*wid,y-.035,2.28),.018,'jaw')
   self.horn('main_horn',(s*.24,-2.38,2.61),(s*.48,-1.96,3.06),(s*.47,-1.69,3.36),.13,'head')
   self.horn('cheek_spur',(s*.30,-2.49,2.41),(s*.58,-2.10,2.55),(s*.66,-1.95,2.49),.095,'head')
  tailpts=[(0,1.22,1.48),(0,1.9,1.35),(.1,2.65,1.12),(.18,3.35,.82),(.1,4.0,.55),(-.08,4.7,.4),(-.2,5.4,.48)]
  if serp:tailpts=[(sin(j*.55)*.65,1.2+j*.9,1.4-j*.10) for j in range(11)]
  tw=[]
  for j in range(len(tailpts)-1):self.bone('tail'+str(j),tailpts[j],tailpts[j+1],'pelvis' if j==0 else 'tail'+str(j-1));tw.append('tail'+str(j))
  self.tube('tail',tailpts,[max(.018,.34*(1-j/(len(tailpts)-1))) for j in range(len(tailpts))],tw+[tw[-1]],sides=16,sub=4)
  if not serp:
   for s in (-1,1):
    self.limb('hindL' if s<0 else 'hindR',(s*.45,.85,1.6),(s*.84,1.0,.95),(s*.75,1.55,.38),(s*.80,1.02,.13),'pelvis',.30*heavy)
    if not wyv:self.limb('frontL' if s<0 else 'frontR',(s*.56,-.50,1.72),(s*.95,-.18,.95),(s*.88,-.7,.30),(s*.9,-1.02,.12),'chest',.22*heavy)
    self.wing(s,(s*.50,-.35,2.05),4.5 if idx!=4 else 3.5,2.8)
  for j in range(14):
   y=-1.2+j*.40
   if y<1.2:
    z=2.30-abs(y+.2)*.11;b='neck1' if y<-.8 else 'chest' if y<.5 else 'pelvis'
   else:
    ti=min(len(tailpts)-2,max(0,int((y-1.22)/.75)));frac=max(0,min(1,(y-tailpts[ti][1])/(tailpts[ti+1][1]-tailpts[ti][1])));center=Vector(tailpts[ti]).lerp(Vector(tailpts[ti+1]),frac);z=center.z+max(.03,.34*(1-(ti+frac)/(len(tailpts)-1)))*.85;b='tail'+str(ti)
   self.horn('dorsal_spine',(0,y,z-.055),(0,y+.09,z+.16),(0,y+.27,z+.24+(j%3)*.05),.085,b,'skin')
  if idx==1:
   for s in (-1,1):
    for j in range(4):self.horn('antler',(s*(.3+j*.035),-2.3+j*.12,2.8+j*.13),(s*(.75+j*.1),-2.2+j*.2,3.25+j*.18),(s*(.9+j*.1),-2.1+j*.24,3.55+j*.15),.065,'head')
  if idx in (3,4,9):
   for row in range(7):
    y=-.8+row*.30
    for s in (-1,1):self.ell('armour_scute',(s*.32,y,2.23-(max(0,y)*.12)),(.30,.23,.11),'chest' if row<4 else 'pelvis','metal' if idx==9 else 'skin',rings=6,sides=10)
  if idx==3:
   for s in (-1,1):
    for j in range(5):self.horn('thorns',(s*.6,-.5+j*.36,1.9),(s*.95,-.3+j*.36,2.15),(s*1.1,-.2+j*.36,2.30),.10,'chest' if j<3 else 'pelvis')
  if idx==7:
   self.tube('nasal_crest',[(0,-3.3,2.5),(0,-2.9,2.75),(0,-2.55,2.9),(0,-2.15,2.65)],[.02,.1,.14,.01],['head']*4,'tooth',sides=10,sub=4)
  if serp:
   for s in (-1,1):self.wing(s,(s*.3,-.2,1.9),2.2,1.9)
  if self.kind=='bat':
   for s in (-1,1):self.horn('ear',(s*.28,-2.5,2.65),(s*.62,-2.35,3.0),(s*.52,-2.48,3.6),.19,'head','membrane')
 def humanoid(self):
  k=self.kind
  self.bone('root',(0,0,0),(0,0,.5));self.bone('pelvis',(0,0,1.45),(0,0,1.9),'root');self.bone('chest',(0,0,1.9),(0,0,2.65),'pelvis');self.bone('neck1',(0,0,2.65),(0,-.05,2.92),'chest');self.bone('head',(0,-.05,2.92),(0,-.12,3.40),'neck1');self.bone('jaw',(0,-.2,3.04),(0,-.36,3.01),'head')
  broad=1.3 if k in ('construct','crystal') else .9 if k=='wraith' else 1.0
  self.tube('torso',[(0,0,1.3),(0,0,1.6),(0,0,1.95),(0,0,2.35),(0,0,2.63)],[.28,.40,.32,.62*broad,.40],['pelvis','pelvis',{'pelvis':.5,'chest':.5},'chest','chest'],sides=24,sub=5,ellipse=.55)
  self.tube('neck',[(0,0,2.56),(0,-.02,2.80),(0,-.05,3.06)],[.21,.15,.20],['chest','neck1','head'],sides=16,sub=3)
  self.ell('cranium',(0,-.04,3.14),(.23,.22,.34),'head',rings=18,sides=24)
  self.ell('jaw',(0,-.14,2.98),(.20,.16,.13),'jaw')
  for s in (-1,1):
   self.limb('hindL' if s<0 else 'hindR',(s*.28,0,1.5),(s*.36,-.07,.86),(s*.32,.08,.27),(s*.35,-.23,.10),'pelvis',.22 if k!='construct' else .3)
   a='armL' if s<0 else 'armR';sh=(s*.58,0,2.5);el=(s*.95,-.01,1.94);wr=(s*1.02,-.10,1.39)
   self.bone(a,sh,el,'chest');self.bone(a+'_fore',el,wr,a);self.bone(a+'_hand',wr,(s*1.05,-.12,1.12),a+'_fore')
   self.tube(a,[sh,(s*.80,.03,2.26),el,wr,(s*1.04,-.12,1.16)],[.24,.25,.16,.105,.12],['chest',a,{a:.5,a+'_fore':.5},a+'_fore',a+'_hand'],sides=16,sub=4)
   for j in range(4):self.tube('finger',[(s*(.97+j*.055),-.12,1.22),(s*(.99+j*.055),-.16,1.03),(s*(.99+j*.05),-.22,.96)],[.032,.027,.011],[a+'_hand']*3,sides=6,sub=2)
   self.ell('eye_socket',(s*.092,-.227,3.20),(.075,.031,.056),'head','black',rings=10,sides=12);self.ell('eye',(s*.092,-.25,3.20),(.031,.018,.023),'head','eye',rings=8,sides=12)
   self.tube('brow',[(s*.03,-.24,3.27),(s*.1,-.252,3.26),(s*.18,-.19,3.22)],[.035,.04,.018],['head']*3,sub=3,sides=8)
  self.tube('nose',[(0,-.20,3.24),(0,-.31,3.12),(0,-.29,3.08)],[.055,.065,.03],['head']*3,sub=3,sides=10)
  if k in ('knight','construct','mech'):
   for s in (-1,1):
    self.ell('pauldron',(s*.62,.0,2.55),(.39,.33,.24),'armL' if s<0 else 'armR','metal',rings=10,sides=16)
    self.ell('cuirass',(s*.24,-.22,2.30),(.31,.17,.40),'chest','metal',rings=12,sides=16)
    self.ell('greave',(s*.33,-.07,.58),(.18,.15,.35),'hindL_shin' if s<0 else 'hindR_shin','metal')
   self.ell('helmet',(0,.00,3.19),(.29,.25,.38),'head','metal',rings=18,sides=20)
   self.ell('visor',(0,-.246,3.21),(.21,.025,.025),'head','black',rings=8,sides=16)
   if k=='knight':
    self.tube('great_hammer',[(1.05,-.12,1.15),(1.05,-.12,2),(1.05,-.12,3.2)],[.045,.045,.045],['armR_hand']*3,'metal',sides=10,sub=3)
    self.ell('bell_hammer',(1.05,-.12,3.18),(.40,.34,.42),'armR_hand','metal',rings=12,sides=16)
   else:
    for s in (-1,1):
     for j in range(3):self.tube('barrel',[(s*.70,.02,2.55+j*.07),(s*.70,-.45,2.55+j*.07),(s*.70,-.75,2.55+j*.07)],[.055,.055,.065],['chest']*3,'metal',sub=2,sides=10)
     self.tube('exhaust',[(s*.25,.24,2.1),(s*.25,.25,2.85),(s*.25,.32,3.15)],[.11,.11,.13],['chest']*3,'metal',sides=10,sub=3)
  if k in ('demon','wraith'):
   for s in (-1,1):
    self.horn('crown_horn',(s*.16,.02,3.38),(s*.45,.05,3.68),(s*.25,-.03,3.98),.105,'head')
    for j in range(4):self.horn('shoulder_spike',(s*(.4+j*.08),.06,2.63),(s*(.57+j*.1),.07,2.91),(s*(.67+j*.10),.1,3.05),.065,'chest')
  if k=='wraith':
   self.tube('robe',[(0,.12,2.48),(0,.12,1.8),(0,.12,1.1),(0,.1,.30)],[.59,.43,.50,.74],['chest','pelvis','pelvis','pelvis'],'membrane',sides=30,sub=5,ellipse=.55)
   self.tube('scythe_shaft',[(1.06,-.15,.6),(1.06,-.15,2),(1.06,-.15,3.7)],[.045,.045,.045],['armR_hand']*3,'metal',sides=10,sub=3)
   self.horn('scythe_blade',(1.06,-.15,3.7),(.1,-.15,3.70),(-.6,-.15,3.20),.2,'armR_hand','metal')
  if k=='ent':
   for s in (-1,1):
    for j in range(5):self.horn('branch',(s*.35,.1,2.35+j*.12),(s*(.65+j*.15),.1+j*.08,3.0+j*.18),(s*(.75+j*.22),.05+j*.12,3.65+j*.19),.13,'chest','skin')
   for j in range(7):
    a=j*math.tau/7;self.horn('root',(cos(a)*.2,sin(a)*.2,1.45),(cos(a)*.7,sin(a)*.7,.6),(cos(a)*1.05,sin(a)*1.05,.1),.14,'pelvis','skin')
   if self.cat=='enemies':self.ell('mushroom_cap',(0,0,3.38),(.71,.63,.15),'head','skin',rings=12,sides=30)
  if k=='crystal':
   for j in range(18):
    a=j*2.39;z=1.6+(j%6)*.2;s=1 if j%2 else -1;self.horn('crystal',(s*.32,.08,z),(s*(.6+j%3*.15),.15,z+.5),(s*(.7+j%3*.2),.1,z+.8),.13,'chest' if z>1.9 else 'pelvis','metal')
 def arthropod(self):
  k=self.kind;count=10 if k=='centipede' else 8 if k in ('spider','mech') else 6
  self.bone('root',(0,0,0),(0,0,.3));self.bone('pelvis',(0,.5,.9),(0,0,1.0),'root');self.bone('chest',(0,0,1.0),(0,-.55,1.1),'pelvis');self.bone('neck1',(0,-.55,1.1),(0,-.85,1.1),'chest');self.bone('head',(0,-.85,1.1),(0,-1.1,1.05),'neck1');self.bone('jaw',(0,-1,1.05),(0,-1.3,.9),'head')
  self.ell('thorax',(0,0,1.05),(.55,.65,.42),'chest');self.ell('abdomen',(0,.8,1.1),(.66,.87,.59),'pelvis');self.ell('head',(0,-.72,1.02),(.35,.33,.27),'head')
  for j in range(count):
   s=-1 if j%2==0 else 1;y=-.45+(j//2)*.37;pre='leg'+str(j)
   self.limb(pre,(s*.38,y,1.13),(s*(1.0+abs(y)*.1),y-.14,1.6),(s*1.62,y-.38,.44),(s*1.7,y-.45,.07),'chest' if y<.4 else 'pelvis',.11,claws=False)
   for q in range(5):
    z=.4+q*.18;self.horn('leg_barb',(s*1.55,y-.3,z),(s*1.70,y-.3,z+.07),(s*1.77,y-.3,z+.03),.035,pre+'_shin','skin')
  for s in (-1,1):
   self.horn('mandible',(s*.20,-.93,1.06),(s*.43,-1.30,.97),(s*.12,-1.43,.80),.10,'jaw','tooth')
   for j in range(4):self.ell('eye',(s*(.07+j*.055),-.97,1.16+(j%2)*.07),(.041,.029,.043),'head','eye',rings=8,sides=10)
  if k=='centipede':
   for j in range(5):self.ell('segment',(0,.45+j*.36,1.12),(.52,.29,.40),'pelvis')
  if k=='crab':
   for s in (-1,1):
    self.bone('armL' if s<0 else 'armR',(s*.4,-.2,1.1),(s*1.0,-1.0,.85),'chest');a='armL' if s<0 else 'armR';self.ell('pincer',(s*1.05,-1,.85),(.31,.47,.25),a)
    for q in (-1,1):self.horn('claw',(s*1.05+q*.12,-1.2,.87),(s*1.05+q*.24,-1.62,.85),(s*1.05+q*.02,-1.86,.88),.13,a)
 def fish(self):
  self.bone('root',(0,0,0),(0,0,.5));self.bone('pelvis',(0,.5,1.25),(0,0,1.25),'root');self.bone('chest',(0,0,1.25),(0,-.7,1.25),'pelvis');self.bone('neck1',(0,-.7,1.25),(0,-1.1,1.25),'chest');self.bone('head',(0,-1.1,1.25),(0,-1.8,1.3),'neck1');self.bone('jaw',(0,-1.1,1.15),(0,-1.8,1.10),'head')
  pts=[(0,-1.9,1.3),(0,-1.2,1.4),(0,-.45,1.35),(0,.6,1.22),(0,1.5,1.25),(0,2.35,1.25)];self.bone('tail0',pts[3],pts[4],'pelvis');self.bone('tail1',pts[4],pts[5],'tail0')
  self.tube('body',pts,[.13,.44,.60,.42,.19,.06],['head','head','chest','pelvis','tail0','tail1'],sides=24,sub=6,ellipse=1.25)
  self.ell('jaw',(0,-1.55,1.07),(.32,.45,.12),'jaw')
  for s in (-1,1):
   self.ell('eye',(s*.34,-1.20,1.59),(.052,.07,.062),'head','eye')
   self.horn('pectoral',(s*.35,-.3,1.1),(s*1.1,.15,1.15),(s*1.45,.75,1.0),.20,'chest','skin')
   for j in range(9):self.horn('tooth',(s*.23,-1.18-j*.055,1.16),(s*.21,-1.19-j*.055,1.32),(s*.19,-1.2-j*.055,1.34),.032,'jaw')
  self.horn('dorsal',(0,.1,1.65),(0,.25,2.35),(0,.9,1.85),.22,'chest','skin')
  for s in (-1,1):self.horn('caudal',(0,2.2,1.25),(0,2.7,1.25+s*.65),(0,3.05,1.25+s*.93),.17,'tail1','skin')
 def hound(self):
  # Wingless, low-slung dragon anatomy with canine skull proportions.
  self.dragon()
  for o in list(self.parts):
   if o.name.startswith(('wingL','wingR')):self.parts.remove(o);bpy.data.objects.remove(o,do_unlink=True)
  self.bones={n:b for n,b in self.bones.items() if not n.startswith('wing')}
 def wisp(self):
  self.humanoid()
  for j in range(9):
   a=j*math.tau/9;self.tube('wisp_tendril',[(cos(a)*.2,sin(a)*.2,1.5),(cos(a)*.6,sin(a)*.6,.8),(cos(a)*.35,sin(a)*.35,.1)],[.10,.06,.006],['pelvis']*3,'membrane',sides=8,sub=6)
 def construct(self):
  if self.kind in ('dragon','wyvern','serpent','bat'):self.dragon()
  elif self.kind=='hound':self.hound()
  elif self.kind in ('spider','crab','centipede'):self.arthropod()
  elif self.kind=='fish':self.fish()
  elif self.kind=='wisp':self.wisp()
  else:self.humanoid()
  # Consolidate into a skinned mesh with smoothly interpolated tube weights.
  bpy.ops.object.select_all(action='DESELECT')
  for o in self.parts:o.select_set(True)
  bpy.context.view_layer.objects.active=self.parts[0];bpy.ops.object.join();self.meshobj=bpy.context.object;self.meshobj.name='CreatureMesh'
  ad=bpy.data.armatures.new('Skeleton');self.rig=bpy.data.objects.new('Rig',ad);bpy.context.collection.objects.link(self.rig);bpy.context.view_layer.objects.active=self.rig;bpy.ops.object.mode_set(mode='EDIT')
  for n,(h,t,parent) in self.bones.items():
   b=ad.edit_bones.new(n);b.head=h;b.tail=t
   if parent:b.parent=ad.edit_bones[parent]
  bpy.ops.object.mode_set(mode='OBJECT');mod=self.meshobj.modifiers.new('Skin','ARMATURE');mod.object=self.rig;self.meshobj.parent=self.rig
  scale=.42 if self.cat=='enemies' else 1.5 if self.cat=='bosses' else 1
  self.rig.scale=(scale,)*3
  self.rig.animation_data_create()

def render(creature,filename,close=False):
 scene=bpy.context.scene
 for tr in creature.rig.animation_data.nla_tracks:tr.mute=True
 creature.rig.animation_data.action=None
 for pb in creature.rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
 bpy.context.view_layer.update()
 corners=[creature.meshobj.matrix_world@v.co for v in creature.meshobj.data.vertices]
 mn=Vector(tuple(min(p[i] for p in corners) for i in range(3)));mx=Vector(tuple(max(p[i] for p in corners) for i in range(3)));center=(mn+mx)/2;span=max(mx-mn)
 studio=[]
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.03));floor=bpy.context.object;studio.append(floor);m=bpy.data.materials.new('Studio');m.diffuse_color=(.045,.052,.06,1);floor.data.materials.append(m)
 bpy.ops.object.camera_add();cam=bpy.context.object;studio.append(cam);cam.data.type='ORTHO';cam.data.ortho_scale=span*1.13;cam.location=center+Vector((1,-1.3,.7))*span;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
 aspect=900/700
 inv=cam.rotation_euler.to_matrix().transposed();projected=[inv@(v-center) for v in corners]
 xmin,xmax=min(v.x for v in projected),max(v.x for v in projected);ymin,ymax=min(v.y for v in projected),max(v.y for v in projected)
 cam.data.ortho_scale=max(xmax-xmin,(ymax-ymin)*aspect)*1.15
 basis=cam.rotation_euler.to_matrix();cam.location+=basis@Vector(((xmin+xmax)/2,(ymin+ymax)/2,0))
 if close:
  target=Vector((0,-2.65,2.4))*creature.rig.scale.x;cam.location=target+Vector((3,-4,1.8));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=3.2*creature.rig.scale.x
 for pos,power,color,sz in [((1,-1,1.7),1700,(1,.84,.68),.8),((-1,-.4,.9),1200,(.60,.75,1),.8),((.3,1,1.3),2100,(.85,.9,1),.6)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(pos)*span*.65);o=bpy.context.object;studio.append(o);o.data.energy=power*(span/5)**2;o.data.color=color;o.data.shape='DISK';o.data.size=span*sz;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
 scene.world.color=(.15,.15,.15);scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8 if not close else 48;scene.cycles.use_denoising=True
 scene.render.resolution_x=1100 if close else 900;scene.render.resolution_y=850 if close else 700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(P/'previews'/filename);scene.view_settings.view_transform='AgX';bpy.ops.render.render(write_still=True)
 for o in studio:bpy.data.objects.remove(o,do_unlink=True)

def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)

if __name__=='__main__':
 clear();c=Creature(ROSTER[0],0);c.construct();render(c,'Cinder_Crown_review.png');render(c,'Cinder_Crown_closeup.png',True)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'Cinder_Crown_review.blend'))
 print('REVIEW_COMPLETE',flush=True)
