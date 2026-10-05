import bpy,bmesh,sys,json,math,random
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_creatures import Creature,ROSTER,P,render
OLD=P.parent/'nocturne-dark-fantasy-v2'

def flatmat(c,n,color,metal=0,rough=.5,emission=0):
 m=bpy.data.materials.new(n);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 if emission:bs.inputs['Emission Color'].default_value=(*color,1);bs.inputs['Emission Strength'].default_value=emission
 # Image roughness and normal retain export-compatible material detail.
 if not emission:
  for typ in ['roughness','normal']:
   t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'textures'/('metal_'+typ+'.png')),check_existing=True);t.image.colorspace_settings.name='Non-Color'
   if typ=='normal':
    nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.22;m.node_tree.links.new(t.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
   else:m.node_tree.links.new(t.outputs['Color'],bs.inputs['Roughness'])
 c.mats[n]=m

def plate(c,n,center,size,bone,mat='paint',rotation=(0,0,0)):
 # Bevelled eight-corner plate, with chamfered edges and separate front panel.
 x,y,z=[v/2 for v in size];cut=min(x,z)*.24;outline=[(-x+cut,-z), (x-cut,-z),(x,-z+cut),(x,z-cut),(x-cut,z),(-x+cut,z),(-x,z-cut),(-x,-z+cut)]
 rot=Matrix.Rotation(rotation[0],3,'X')@Matrix.Rotation(rotation[1],3,'Y')@Matrix.Rotation(rotation[2],3,'Z');vs=[]
 for depth,scale in [(y,.94),(-y+.025,1),(-y,.85)]:
  for a,b in outline:vs.append(Vector(center)+rot@Vector((a*scale,depth,b*scale)))
 vs.append(Vector(center)+rot@Vector((0,-y-min(x,z)*.17,0)))
 ff=[tuple(range(7,-1,-1))]+[(16+i,16+(i+1)%8,24) for i in range(8)]
 for j in range(2):
  for i in range(8):ff.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
 return c.mesh(n,vs,ff,[(v[0]*2,v[2]*2) for v in vs],[bone]*25,mat,False)

def tile(c,n,center,u,v,w,l,h,bone,mat='skin'):
 p=Vector(center);u=Vector(u).normalized();v=Vector(v).normalized();normal=u.cross(v).normalized()
 vs=[p-u*w*.5-v*l*.4,p+u*w*.5-v*l*.4,p+u*w*.4+v*l*.3,p+v*l*.62,p-u*w*.4+v*l*.3,p+normal*h]
 ff=[(0,1,5),(1,2,5),(2,3,5),(3,4,5),(4,0,5),(4,3,2,1,0)]
 c.mesh(n,vs,ff,[(0,0),(1,0),(1,.7),(.5,1),(0,.7),(.5,.5)],[bone]*6,mat,False)

def rivet(c,p,bone,mat='trim',r=.018):c.ell('Rivet',p,(r,r*.6,r),bone,mat,rings=4,sides=6)
def strip(c,n,pts,width,bone,mat='trim'):c.tube(n,pts,[width]*len(pts),[bone]*len(pts),mat,sides=6,sub=2)

def scale_path(c,points,radii,weights,rows=24,around=14):
 pts=[Vector(v) for v in points]
 for j in range(rows):
  t=(j+.5)/rows*(len(pts)-1);idx=min(len(pts)-2,int(t));f=t-idx;p0=pts[max(0,idx-1)];p1=pts[idx];p2=pts[idx+1];p3=pts[min(len(pts)-1,idx+2)]
  def point(q):return .5*(2*p1+(-p0+p2)*q+(2*p0-5*p1+4*p2-p3)*q*q+(-p0+3*p1-3*p2+p3)*q*q*q)
  center=point(f);tang=(point(min(1,f+.02))-point(max(0,f-.02))).normalized();up=Vector((0,1,0)) if abs(tang.z)>.94 else Vector((0,0,1));u=tang.cross(up).normalized();v=tang.cross(u).normalized();radius=radii[idx]*(1-f)+radii[idx+1]*f
  bone=weights[idx] if f<.5 else weights[idx+1]
  for k in range(around):
   a=(k+(j%2)*.5)*2*pi/around;normal=u*cos(a)+v*sin(a)*.85;pos=center+normal*(radius+.005);across=tang.cross(normal).normalized()
   tile(c,'Overlapping_scale',pos,across,tang,max(.035,radius*2*pi/around*.91),.17,.018,bone,'trim' if c.index==9 and j%4==0 else 'skin')

def dragon_details(c):
 idx=c.index%10;heavy=1.4 if idx==4 else 1
 scale_path(c,[(0,1.4,1.45),(0,.65,1.65),(0,-.2,1.72),(0,-.85,1.88),(0,-1.5,2.1),(0,-2.4,2.4)],[.22,.65*heavy,.75*heavy,.5,.34,.22],['pelvis','pelvis','chest','chest','neck1','neck2'],rows=33,around=18)
 # Smaller scales on load-bearing limbs.
 for pre in ['hindL','hindR','frontL','frontR']:
  if pre not in c.rig.data.bones:continue
  a=c.rig.data.bones[pre];b=c.rig.data.bones[pre+'_shin'];thick=.30*heavy if pre.startswith('hind') else .22*heavy
  scale_path(c,[a.head_local,a.head_local.lerp(a.tail_local,.45),a.tail_local,b.tail_local],[thick,thick*1.15,thick*.65,thick*.45],[pre,pre,pre+'_shin',pre+'_shin'],rows=16,around=10)
 # Broad articulated ventral shields rather than a smooth belly.
 for j in range(17):
  y=-2.16+j*.20;z=2.20 if y<-1.2 else 1.78 if y<-.6 else 1.16;w=.29 if y<-1.2 else .53 if y<-.6 else .68*heavy
  b='neck2' if y<-1.7 else 'neck1' if y<-.9 else 'chest' if y<.5 else 'pelvis'
  tile(c,'Ventral_shield',(0,y,z),(1,0,0),(0,1,0),w,.25,.035,b,'trim' if idx==9 else 'belly')
 for s in [-1,1]:
  for j in range(10):tile(c,'Cheek_scale',(s*(.31-j*.007),-2.58-j*.08,2.47),(0,1,0),(0,0,s),.11,.12,.018,'head','skin')
  for j in range(7):
   y=-.8+j*.35;z=2.20-max(0,y)*.14
   tile(c,'Shoulder_scute',(s*.46,y,z),(s*.7,0,.4),(0,1,0),.38,.45,.10,'chest' if j<4 else 'pelvis','paint' if idx==9 else 'skin')
 if idx in (0,4):
  for s in [-1,1]:
   for j in range(6):c.horn('Neck_crown',(s*.25,-2.30+j*.24,2.55),(s*(.65+j*.035),-2.07+j*.24,2.80),(s*(.58+j*.05),-1.92+j*.24,3.0),.075,'head' if j<2 else 'neck1','skin')
 if idx in (1,3,8):
  for s in [-1,1]:
   for j in range(12):
    p=Vector((s*.32,-2.3+j*.18,2.56-j*.04));c.horn('Branching_crest',p,p+Vector((s*.25,.15,.18)),p+Vector((s*.36,.30,.36)),.045,'neck1' if j>3 else 'head','trim' if idx==1 else 'skin')
 if idx in (2,5,7,8):
  for s in [-1,1]:
   for j in range(11):
    x=s*(1.0+j*.25);y=.20+j*.11;z=2.50-j*.055
    c.horn('Wing_trailing_barb',(x,y,z),(x+s*.08,y+.3,z-.1),(x+s*.05,y+.48,z-.18),.045,'wingL_fore' if s<0 else 'wingR_fore','tooth' if idx==7 else 'skin')
 if idx==6:
  for j in range(16):
   y=1.3+j*.45;x=sin((y-1.2)/.9*.55)*.65;z=1.4-(y-1.2)/.9*.10;b='tail'+str(min(9,int((y-1.2)/.9)))
   for s in [-1,1]:c.horn('Abyss_fin',(x+s*.2,y,z),(x+s*.72,y+.22,z+.5),(x+s*.55,y+.70,z+.3),.09,b,'skin')
 if idx==9:
  for s in [-1,1]:
   strip(c,'Hydraulic_line',[(s*.64,.8,1.8),(s*.86,.35,1.9),(s*.68,-.4,2.15)],.05,'chest','black')
   for j in range(4):plate(c,'Heat_sink',(s*.43,-.2+j*.28,2.33),(.48,.17,.22),'chest','paint',rotation=(pi/2,0,0))
 # Species proportions applied consistently to bind mesh and skeleton later.
 c.warp=lambda v:Vector((v.x*([1.05,.85,.86,1.05,1.28,.82,.83,.91,.88,1.03][idx]),v.y*([1,1.07,.96,.94,.91,1.08,1.04,1.1,1.08,.96][idx]),v.z*([1.02,1.16,1.04,.96,.86,1.02,1.06,.95,1.11,1.02][idx])))

def boot(c,s):
 b='hindL_foot' if s<0 else 'hindR_foot';plate(c,'Armoured_boot',(s*.35,-.12,.16),(.40,.58,.29),b,'paint')
 for j in range(3):plate(c,'Boot_lame',(s*.35,-.37,.15+j*.065),(.34,.10,.10),b,'trim')

def cape(c,bone='chest',length=1.9,mat='fabric'):
 vs=[];uv=[];ws=[];ff=[]
 for j in range(13):
  t=j/12
  for i in range(17):
   u=i/16;x=(u-.5)*(1.2+t*.6);z=2.55-t*length;y=.33+.25*t+.09*cos(u*pi*10)*(t*.7+.3)
   vs.append((x,y,z));uv.append((u,t));ws.append({bone:1-t*.7,'pelvis':t*.7})
 for j in range(12):
  for i in range(16):q=j*17+i;ff.append((q,q+1,q+18,q+17))
 c.mesh('Pleated_mantle',vs,ff,uv,ws,mat)

def cuirass(c):
 vs=[];uv=[];ff=[]
 for j in range(9):
  t=j/8;z=1.98+t*.63;radius=.40+.17*sin(t*pi*.72)
  for i in range(15):
   a=-pi*.60+i/14*pi*1.20;vs.append((sin(a)*radius,-cos(a)*(.29+.07*sin(pi*t)),z));uv.append((i/14,t))
 for j in range(8):
  for i in range(14):q=j*15+i;ff.append((q,q+1,q+16,q+15))
 c.mesh('Forged_curved_cuirass',vs,ff,uv,['chest']*len(vs),'paint',True)
 for side in [-1,1]:
  strip(c,'Cuirass_gilt_edge',[(side*.40,-.29,2.05),(side*.48,-.29,2.32),(side*.46,-.26,2.58)],.024,'chest','trim')
 for j in range(7):
  z=2.05+j*.075;strip(c,'Central_flute',[(0,-.36,z),(0,-.365,z+.067)],.013,'chest','trim')

def helmet(c,style):
 c.ell('Forged_helmet_dome',(0,.02,3.24),(.285,.25,.32),'head','paint',rings=12,sides=20)
 plate(c,'Face_mask',(0,-.255,3.14),(.46,.11,.49),'head','paint')
 for s in [-1,1]:
  plate(c,'Helm_cheek',(s*.19,-.20,3.10),(.14,.25,.46),'head','paint',rotation=(0,0,s*.2))
  plate(c,'Temple',(s*.24,-.04,3.24),(.10,.32,.35),'head','trim')
 if style=='tactical':
  plate(c,'Optical_visor',(0,-.33,3.23),(.39,.08,.16),'head','black')
  for s in [-1,1]:
   c.ell('Respirator_filter',(s*.17,-.335,3.02),(.07,.06,.07),'head','black',rings=6,sides=10)
   strip(c,'Helmet_rail',[(s*.24,-.15,3.38),(s*.24,.07,3.42)],.025,'head','trim')
 else:
  for s in [-1,1]:plate(c,'Eye_slit',(s*.10,-.32,3.23),(.13,.016,.032),'head','black')
  plate(c,'Nasal_guard',(0,-.33,3.16),(.054,.033,.31),'head','trim')
  for j in range(6):plate(c,'Breathing_slot',((j-2.5)*.053,-.319,3.055),(.017,.016,.08),'head','black')
  strip(c,'Helm_ridge',[(0,-.22,3.4),(0,0,3.56),(0,.23,3.38)],.038,'head','trim')

def armour(c,style='gothic'):
 # Faceted, shaped plates with articulated waist/shoulder guards and visible trim.
 cuirass(c) if style=='gothic' else plate(c,'Breastplate',(0,-.26,2.30),(1.06,.25,.72),'chest','paint')
 for s in [-1,1]:
  for j in range(3):plate(c,'Shoulder_lame',(s*(.61+j*.06),-.015,2.68-j*.10),(.49,.58,.16),'armL' if s<0 else 'armR','paint',rotation=(0,s*.17,0))
  for j in range(3):plate(c,'Abdominal_lame',(s*.20,-.26,1.94-j*.13),(.40,.17,.20),'pelvis' if j>0 else 'chest','paint')
  plate(c,'Vambrace',(s*.995,-.10,1.67),(.28,.31,.44),'armL_fore' if s<0 else 'armR_fore','paint',rotation=(0,s*.08,0))
  plate(c,'Knee_guard',(s*.355,-.18,.87),(.33,.18,.29),'hindL_shin' if s<0 else 'hindR_shin','paint')
  plate(c,'Shin_guard',(s*.33,-.105,.56),(.31,.27,.48),'hindL_shin' if s<0 else 'hindR_shin','paint')
  boot(c,s)
  for j in range(3):
   b='armL' if s<0 else 'armR';rivet(c,(s*(.48+j*.13),-.31,2.65),b)
   rivet(c,(s*.48,-.4,2.06+j*.18),'chest')
  strip(c,'Chest_trim',[(s*.46,-.405,2.56),(s*.50,-.405,2.12),(s*.12,-.405,1.96)],.017,'chest')
  plate(c,'Hip_guard',(s*.39,-.04,1.53),(.32,.44,.43),'pelvis','paint',rotation=(0,s*.17,0))
 plate(c,'Gorget',(0,-.04,2.69),(.64,.57,.16),'chest','trim')
 helmet(c,'tactical' if style=='tactical' else 'gothic')
 if style=='gothic':
  cape(c)
  # Replace the v2 spherical hammer head with a cast bell and embossed ribs.
  vs=[];ff=[];uv=[]
  for j,(r,z) in enumerate([(.18,3.52),(.24,3.45),(.28,3.25),(.43,3.05),(.44,3.0),(.36,3.0),(.20,3.32)]):
   for i in range(25):a=i/24*2*pi;vs.append((1.05+r*cos(a),-.12+r*sin(a),z));uv.append((i/24,j/6))
  for j in range(6):
   for i in range(24):q=j*25+i;ff.append((q,q+1,q+26,q+25))
  c.mesh('Cast_bell_hammer',vs,ff,uv,['armR_hand']*len(vs),'trim')
  for j in range(12):
   a=j/12*2*pi;strip(c,'Bell_rib',[(1.05+.24*cos(a),-.12+.24*sin(a),3.42),(1.05+.30*cos(a),-.12+.30*sin(a),3.25),(1.05+.43*cos(a),-.12+.43*sin(a),3.05)],.018,'armR_hand','paint')
  for s in [-1,1]:
   for j in range(4):c.horn('Crown_spire',(s*(.10+j*.05),.03,3.5),(s*(.12+j*.1),.07,3.76+j*.06),(s*(.10+j*.11),.06,3.82+j*.07),.032,'head','trim')
  for s in [-1,1]:
   for j in range(4):plate(c,'Fauld',(s*(.1+j*.11),-.13,1.4),(.16,.10,.48),'pelvis','paint',rotation=(0,s*.17,0))
 if style=='tactical':
  for s in [-1,1]:
   strip(c,'Harness',[(s*.37,-.41,2.59),(s*.30,-.425,2.18),(s*.24,-.35,1.75)],.032,'chest','fabric')
   for j in range(3):plate(c,'Magazine_pouch',(s*(.1+j*.135),-.43,2.12),(.125,.14,.25),'chest','fabric')
   plate(c,'Thigh_pouch',(s*.53,0,1.19),(.24,.32,.29),'hindL' if s<0 else 'hindR','fabric')
  plate(c,'Pack',(0,.37,2.29),(.62,.32,.70),'chest','fabric')
  plate(c,'Pack_flap',(0,.555,2.43),(.54,.04,.28),'chest','paint')
  strip(c,'Antenna',[(.28,.45,2.52),(.28,.45,3.03)],.013,'chest','black')
  # Attached rifle, aligned along the forearm; reuse hand bone for animation.
  plate(c,'Rifle_receiver',(1.05,-.34,1.35),(.17,.35,.17),'armR_hand','black')
  strip(c,'Rifle_barrel',[(1.05,-.45,1.37),(1.05,-1.0,1.37)],.037,'armR_hand','black')
  plate(c,'Rifle_magazine',(1.05,-.40,1.20),(.10,.13,.20),'armR_hand','black')
  plate(c,'Rifle_stock',(1.05,-.01,1.37),(.15,.28,.17),'armR_hand','paint')

def mechanical(c):
 armour(c,'tactical' if c.name=='Siege_Sentinel' else 'industrial')
 for s in [-1,1]:
  a='armL' if s<0 else 'armR';f=a+'_fore'
  for j in range(4):plate(c,'Cooling_fin',(s*.76,.12,2.45-j*.09),(.24,.35,.044),a,'trim')
  strip(c,'Hydraulic_piston',[(s*.92,.14,2.14),(s*1.01,.14,1.58)],.043,f,'trim')
  strip(c,'Arm_cable',[(s*.73,.2,2.35),(s*.97,.21,2),(s*1.09,.16,1.50)],.033,f,'black')
  for z,b in [(2.5,a),(.85,'hindL_shin' if s<0 else 'hindR_shin')]:
   c.ell('Joint_bearing',(s*(.68 if z>2 else .43),0,z),(.08,.13,.13),b,'trim',rings=6,sides=12)
 plate(c,'Core_housing',(0,-.41,2.32),(.33,.08,.36),'chest','black')
 for j in range(4):plate(c,'Reactor_lit_slit',(0,-.458,2.22+j*.065),(.25,.012,.025),'chest','glow')


def details(c):
 k=c.kind;idx=c.index
 flatmat(c,'trim',(.26,.16,.061) if c.name not in ['Siege_Sentinel','Iron_Seraph','Scrapling'] else (.37,.41,.44),.82,.32)
 colors={'Cathedral_Bellwarden':(.09,.075,.052),'Furnace_Titan':(.095,.085,.065),'Siege_Sentinel':(.11,.135,.10),'Neon_Reaper':(.028,.045,.055),'Mirror_Colossus':(.35,.52,.59),'Iron_Seraph':(.17,.22,.23),'Scrapling':(.16,.18,.17)}
 flatmat(c,'paint',colors.get(c.name,(.095,.082,.065)),.7,.44)
 flatmat(c,'fabric',(.025,.032,.039),0,.84);flatmat(c,'belly',(.20,.15,.10),.05,.73);flatmat(c,'glow',(.02,.42,.62),.1,.35,1.7)
 c.warp=lambda v:v
 if c.cat=='dragons':dragon_details(c)
 elif k in ['construct','mech']:mechanical(c)
 elif k=='knight':armour(c)
 elif k=='wraith':
  armour(c,'tactical');cape(c,length=2.10)
  for s in [-1,1]:strip(c,'Coat_light_piping',[(s*.46,.42,2.45),(s*.6,.54,.60)],.017,'chest','glow')
 elif k=='demon':
  for s in [-1,1]:
   for j in range(4):plate(c,'Bone_spaulder',(s*(.56+j*.05),-.015,2.64-j*.08),(.46,.51,.14),'armL' if s<0 else 'armR','tooth',rotation=(0,s*.18,0))
   plate(c,'War_bracer',(s*1.0,-.08,1.65),(.29,.30,.40),'armL_fore' if s<0 else 'armR_fore','paint')
   for j in range(7):rivet(c,(s*.32,-.25,1.64+j*.06),'pelvis','trim',.024)
  cape(c,length=1.15);plate(c,'Belt_buckle',(0,-.26,1.67),(.16,.07,.18),'pelvis','trim')
 elif k=='ent':
  rng=random.Random(idx)
  for j in range(75):
   z=rng.uniform(1.35,2.60);a=rng.uniform(0,2*pi);r=.42 if z<2 else .61
   tile(c,'Bark_shingle',(cos(a)*r,sin(a)*r*.6,z),(-sin(a),cos(a),0),(0,0,1),.13,.28,.05,'chest' if z>1.9 else 'pelvis','skin')
  for j in range(35):
   a=j*2.39;z=2.75+(j%5)*.19;x=cos(a)*(.7+(j%3)*.13);y=sin(a)*.23
   tile(c,'Canopy_leaf',(x,y,z),(1,0,.2),(0,.4,1),.23,.43,.027,'chest','skin')
 elif k in ['spider','centipede','crab']:
  for j in range(9 if k=='centipede' else 5):
   y=-.4+j*.22
   for s in [-1,1]:tile(c,'Dorsal_shell',(s*.21,y,1.45 if y<.3 else 1.70),(s*.7,0,.35),(0,1,0),.46,.30,.08,'chest' if y<.3 else 'pelvis','paint' if k=='crab' else 'skin')
  for b in c.rig.data.bones:
   if b.name.startswith('leg') and b.name.endswith('_shin'):
    strip(c,'Leg_armour_ridge',[b.head_local,b.head_local.lerp(b.tail_local,.5),b.tail_local],.042,b.name,'trim' if k=='crab' else 'skin')
 elif k=='fish':
  scale_path(c,[(0,-1.9,1.3),(0,-1.2,1.4),(0,-.45,1.35),(0,.6,1.22),(0,1.5,1.25),(0,2.35,1.25)],[.13,.44,.6,.42,.19,.06],['head','head','chest','pelvis','tail0','tail1'],rows=30,around=16)
  for s in [-1,1]:
   for j in range(6):strip(c,'Gill',[(s*.48,-.6+j*.065,1.13),(s*.57,-.6+j*.065,1.41),(s*.45,-.6+j*.065,1.65)],.018,'chest','black')
 elif k=='hound':
  for s in [-1,1]:
   for j in range(14):tile(c,'Hound_scute',(s*.5,-.4+j*.13,2.03),(0,1,0),(s*.7,0,.5),.22,.31,.045,'chest' if j<7 else 'pelvis','skin')
  c.warp=lambda v:Vector((v.x,v.y*.82,v.z*.74))
 elif k=='mantis':
  # Re-author body as a upright mantis; retain existing humanoid animation rig.
  c.parts.remove(c.meshobj);bpy.data.objects.remove(c.meshobj,do_unlink=True);c.meshobj=None
  c.tube('Insect_thorax',[(0,0,1.40),(0,.03,1.95),(0,0,2.60)],[.2,.27,.21],['pelvis','chest','chest'],sides=14,sub=4)
  c.ell('Abdomen',(0,.27,1.55),(.33,.48,.57),'pelvis',rings=12,sides=16)
  c.tube('Flexible_neck',[(0,0,2.48),(0,-.03,2.80),(0,-.06,3.17)],[.11,.08,.10],['chest','neck1','head'],sides=12,sub=3)
  for s in [-1,1]:
   c.tube('Shoulder_link',[(s*.18,0,2.50),(s*.38,0,2.50),(s*.58,0,2.5)],[.09,.08,.10],['chest','chest','armL' if s<0 else 'armR'],sides=10,sub=3)
   side='hindL' if s<0 else 'hindR'
   c.tube('Middle_leg',[(s*.24,.26,1.8),(s*.70,.55,1.12),(s*.78,.64,.24),(s*.84,.55,.10)],[.07,.06,.037,.012],['pelvis',side,side+'_shin',side+'_foot'],sides=10,sub=3)
   c.ell('Folded_wing',(s*.20,.37,2.04),(.17,.16,.64),'chest','membrane',rings=12,sides=16)
   c.limb('visual_leg',(s*.22,0,1.5),(s*.36,-.07,.86),(s*.32,.08,.27),(s*.35,-.23,.10),'pelvis',.08,False)
   # visual_leg introduces names with no rig: replace their vertex weights below.
   arm='armL' if s<0 else 'armR';c.tube('Raptorial_arm',[(s*.58,0,2.5),(s*.95,-.01,1.94),(s*1.02,-.10,1.39)],[.11,.07,.05],[arm,arm+'_fore',arm+'_hand'],sides=10,sub=4)
   for j in range(7):c.horn('Forearm_teeth',(s*(.95+j*.01),-.10,1.50+j*.065),(s*(.89+j*.01),-.22,1.49+j*.065),(s*(.88+j*.01),-.23,1.55+j*.065),.028,arm+'_fore','tooth')
   c.ell('Compound_eye',(s*.22,-.08,3.18),(.14,.13,.15),'head','black',rings=8,sides=12)
   strip(c,'Antenna',[(s*.10,0,3.3),(s*.25,-.12,3.63),(s*.39,-.3,3.78)],.014,'head','skin')
  c.mesh('Triangular_head',[(-.3,0,3.28),(.3,0,3.28),(0,-.12,2.98),(-.24,-.15,3.24),(.24,-.15,3.24),(0,-.25,3.05)],[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],[(0,0)]*6,['head']*6,'skin',False)
  for o in c.parts:
   for g in o.vertex_groups:
    if g.name.startswith('visual_leg'):
     side='hindL' if sum(v.co.x for v in o.data.vertices)<0 else 'hindR';g.name=side+('_shin' if g.name.endswith('_shin') else '_foot' if g.name.endswith('_foot') else '')
 elif k=='wisp':
  c.parts.remove(c.meshobj);bpy.data.objects.remove(c.meshobj,do_unlink=True);c.meshobj=None
  for j in range(5):c.ell('Floating_core',(0,0,2.0+j*.12),(.30-j*.025,.22, .17),'chest','glow',rings=8,sides=12)
  for j in range(9):
   a=j*2*pi/9;strip(c,'Orbital_tendril',[(cos(a)*.3,sin(a)*.3,2.35),(cos(a)*.58,sin(a)*.58,1.65),(cos(a)*.3,sin(a)*.3,.6)],.035,'pelvis','fabric')
  for j in range(12):a=j*2*pi/12;plate(c,'Orbit_shard',(cos(a)*.51,sin(a)*.51,2.18),(.10,.12,.32),'chest','paint',rotation=(0,a*.3,a))
 elif k=='bat':
  for s in [-1,1]:
   for j in range(8):c.horn('Ruff',(s*.25,-2.45+j*.12,2.6),(s*.47,-2.42+j*.12,2.79),(s*.58,-2.36+j*.12,2.88),.045,'neck1','skin')
  c.warp=lambda v:Vector((v.x*1.08,v.y*.69,v.z*.93))
 if c.meshobj and c.kind in ['knight','construct','mech','wraith']:
  # Remove old exposed toe claws and round breast/helmet shell; new plates replace them.
  bm=bmesh.new();bm.from_mesh(c.meshobj.data);dl=bm.verts.layers.deform.active;groups={g.index:g.name for g in c.meshobj.vertex_groups}
  doomed=[]
  for v in bm.verts:
   w=dict(v[dl].items()) if dl else {};dominant=groups.get(max(w,key=w.get),'') if w else ''
   if ((dominant.endswith('_foot') and v.co.z<.20 and v.co.y<-.22) or (dominant in ['head','jaw'] and v.co.y<-.23 and v.co.z<3.27) or ((dominant!='armR_hand' or (c.kind=='knight' and v.co.z>2.82)) and any(c.meshobj.data.materials[f.material_index].name.split('.')[0].endswith('_metal') for f in v.link_faces))):doomed.append(v)
  bmesh.ops.delete(bm,geom=doomed,context='VERTS');bm.to_mesh(c.meshobj.data);bm.free()

def finalize(c):
 for o in c.parts:
  if o!=c.meshobj:o.parent=c.rig
 bpy.ops.object.select_all(action='DESELECT')
 for o in c.parts:o.select_set(True)
 bpy.context.view_layer.objects.active=c.meshobj or c.parts[0];bpy.ops.object.join();c.meshobj=bpy.context.object;c.meshobj.name='CreatureMesh'
 if not any(m.type=='ARMATURE' for m in c.meshobj.modifiers):c.meshobj.modifiers.new('Skin','ARMATURE').object=c.rig
 for v in c.meshobj.data.vertices:v.co=c.warp(v.co)
 bpy.context.view_layer.objects.active=c.rig;bpy.ops.object.mode_set(mode='EDIT')
 for b in c.rig.data.edit_bones:b.head=c.warp(b.head);b.tail=c.warp(b.tail)
 bpy.ops.object.mode_set(mode='OBJECT')
 # Nondeforming unused bones remain for clip compatibility; every mesh weight must use the exported rig.
 assert all(g.name in c.rig.data.bones for g in c.meshobj.vertex_groups if any(g.index in [q.group for q in v.groups] for v in c.meshobj.data.vertices)), 'missing weighted bone'

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
start=int(args[0]) if args else 0;stop=int(args[1]) if len(args)>1 else 30
for idx in range(start,stop):
 entry=ROSTER[idx];cat,name,kind,pal=entry
 if '--only' in args and name not in args[args.index('--only')+1:]:continue
 old=OLD/cat/name;bpy.ops.wm.open_mainfile(filepath=str(old/(name+'.blend')))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');rig.animation_data.action=None
 for tr in rig.animation_data.nla_tracks:tr.mute=True
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
 bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 c=Creature(entry,idx);c.rig=rig;c.meshobj=mesh;c.parts=[mesh];c.bones={b.name:(tuple(b.head_local),tuple(b.tail_local),b.parent.name if b.parent else None) for b in rig.data.bones}
 for im in bpy.data.images:
  if im.source=='FILE':
   im.filepath=str(P/'textures'/Path(im.filepath).name)
   if im.packed_file:im.unpack(method='REMOVE')
   im.reload()
 details(c);finalize(c)
 if kind=='wisp':
  # Adapt invisible limb-only walk/run and jaw-only threat tracks to visible floating-core motion.
  for action in bpy.data.actions:
   if action.name not in ['Locomotion_Walk','Locomotion_Run','Threat_Roar']:continue
   rig.animation_data.action=action;first,last=action.frame_range
   for frame in range(int(first),int(last)+1,2):
    t=(frame-first)/(last-first);bpy.context.scene.frame_set(frame)
    h=(.09 if action.name=='Locomotion_Walk' else .17)*sin(t*2*pi) if action.name!='Threat_Roar' else .14*sin(pi*t)**2
    rig.pose.bones['root'].location=rig.data.bones['root'].matrix_local.to_3x3().inverted()@Vector((0,0,h));rig.pose.bones['root'].keyframe_insert('location',frame=frame)
    if action.name=='Threat_Roar':rig.pose.bones['chest'].scale=(1+.15*sin(pi*t)**2,)*3;rig.pose.bones['chest'].keyframe_insert('scale',frame=frame)
   for fc in action.fcurves:
    for kp in fc.keyframe_points:kp.interpolation='LINEAR'
  rig.animation_data.action=None
  for pb in rig.pose.bones:pb.scale=(1,1,1)
 folder=P/cat/name;folder.mkdir(parents=True,exist_ok=True)
 tris=sum(len(q.vertices)-2 for q in c.meshobj.data.polygons)
 if tris>=50000:
  bpy.context.view_layer.objects.active=c.meshobj;mod=c.meshobj.modifiers.new('Budget','DECIMATE');mod.ratio=48000/tris;bpy.ops.object.modifier_apply(modifier=mod.name);tris=sum(len(q.vertices)-2 for q in c.meshobj.data.polygons)
 render(c,name+'.png')
 if idx==0 and '--review' in args:
  render(c,name+'_closeup.png',True);bpy.ops.wm.save_as_mainfile(filepath=str(P/(name+'_review.blend')));print('V3_REVIEW',name,tris,flush=True);break
 # Render resets animation state. Export exactly the same motion bank as v2 onto revised meshes.
 for im in bpy.data.images:
  if im.source=='FILE':im.filepath=str(P/'textures'/Path(im.filepath).name)
 bpy.ops.object.select_all(action='DESELECT');c.rig.select_set(True);c.meshobj.select_set(True);bpy.context.view_layer.objects.active=c.rig
 bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=.1,path_mode='RELATIVE')
 c.rig.animation_data.action=list(bpy.data.actions)[0];bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_materials='EXPORT')
 c.rig.animation_data.action=None
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
 for im in bpy.data.images:
  if im.source=='FILE':im.filepath='//../../textures/'+Path(im.filepath).name
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')),relative_remap=False)
 original=c.meshobj.data.copy();lods=[]
 for level,ratio in [(1,.55),(2,.28)]:
  c.meshobj.data=original.copy();bpy.context.view_layer.objects.active=c.meshobj;mod=c.meshobj.modifiers.new('LOD','DECIMATE');mod.ratio=ratio;bpy.ops.object.modifier_apply(modifier=mod.name)
  lods.append({'level':level,'triangles':sum(len(p.vertices)-2 for p in c.meshobj.data.polygons)})
  bpy.ops.export_scene.fbx(filepath=str(folder/(name+'_LOD'+str(level)+'.fbx')),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE')
 m=json.loads((old/'asset.json').read_text());m.update({'revision':3,'triangles':tris,'bones':len(rig.data.bones),'materials':len(c.meshobj.data.materials),'lods':lods,'animation_revision':'v2 motion bank retained; wisp walk/run/threat adapted for floating core; not new mocap','quality_status':'Detailed procedural stylised art; does not equal AAA realistic production art','geometry_changes':'shaped plates, layered surfaces, anatomical/species proportions and accessories'})
 (folder/'asset.json').write_text(json.dumps(m,indent=2));print('V3_EXPORTED',name,tris,len(m['clips']),flush=True)
