import bpy,math,json,sys,importlib.util,os
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];W=P.parent;sys.path.insert(0,str(Path(__file__).parent));from expansion_roster import ROSTER
spec=importlib.util.spec_from_file_location('primitives',P/'source/mesh_primitives.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
CURRENT='';MECHANICAL=False
def material(palette,part):
    m=bpy.data.materials.new(CURRENT+'_'+part);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
    if part in ['eye','black','tooth']:
        bs.inputs['Base Color'].default_value={'eye':(.32,.18,.04,1),'black':(.006,.004,.006,1),'tooth':(.48,.44,.33,1)}[part];bs.inputs['Roughness'].default_value=.18 if part=='eye' else .6
    else:
        for suffix,inputname in [('BaseColor','Base Color'),('Roughness','Roughness'),('Normal',None)]:
            t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(P/'textures'/(CURRENT+'_'+suffix+'.png')),check_existing=True)
            if suffix!='BaseColor':t.image.colorspace_settings.name='Non-Color'
            if suffix=='Normal':nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.35;l.new(t.outputs[0],nm.inputs[1]);l.new(nm.outputs[0],bs.inputs['Normal'])
            else:l.new(t.outputs[0],bs.inputs[inputname])
        bs.inputs['Metallic'].default_value=.78 if part=='metal' else .0
        if part=='membrane':bs.inputs['Roughness'].default_value=.7
    return m
base.material=material
def add_tube(c,n,points,radii,bone,mat='skin',ellipse=1,sides=20):return c.tube(n,points,radii,[bone]*len(points),mat,sides=sides,sub=5,ellipse=ellipse)
def ring(c,n,center,radius,bone,mat='metal',axis='z',tube=.06):
    pts=[]
    for j in range(33):
        a=j*math.tau/32;q=Vector(center)+ (Vector((math.cos(a)*radius,math.sin(a)*radius,0)) if axis=='z' else Vector((math.cos(a)*radius,0,math.sin(a)*radius)))
        pts.append(q)
    add_tube(c,n,pts,[tube]*len(pts),bone,mat,sides=8)
def plate(c,n,center,w,h,depth,bone,mat='metal'):
    x,y,z=center;poly=[(-.6,-1),(.6,-1),(1,-.55),(1,.55),(.6,1),(-.6,1),(-1,.55),(-1,-.55)];vv=[]
    for shift in [-depth/2,depth/2]:
        vv += [(x+a*w,y+shift,z+b*h) for a,b in poly]
    ff=[tuple(range(7,-1,-1)),tuple(range(8,16))]+[(j,(j+1)%8,(j+1)%8+8,j+8) for j in range(8)]
    c.mesh(n,vv,ff,[(i%8/8,i//8) for i in range(16)],[bone]*16,mat,smooth=False)
def core(c,center=(0,0,1.2),hum=False):
    c.bone('root',(0,0,0),(0,0,.4));c.bone('pelvis',(0,.5,center[2]),center,'root');c.bone('chest',center,(0,-.65,center[2]+.12),'pelvis')
    c.bone('neck1',(0,-.6,center[2]+.1),(0,-1.1,center[2]+.45),'chest');c.bone('neck2',(0,-1.1,center[2]+.45),(0,-1.5,center[2]+.65),'neck1')
def face(c,center,L=1,w=.28,profile='wedge'):
    x,y,z=center;c.bone('head',(x,y+L*.38,z),(x,y-L*.5,z),'neck2');c.bone('jaw',(x,y+L*.25,z-.12),(x,y-L*.55,z-.16),'head')
    if profile=='hammer':
        add_tube(c,'hammer_lateral_skull',[(-w*2,y,z),(0,y-.1,z+.09),(w*2,y,z)],[w*.38,w*.7,w*.38],'head',ellipse=.7)
    elif profile=='mask':plate(c,'fitted_mask',(x,y-.22,z),w,L*.45,.16,'head','metal' if MECHANICAL else 'tooth')
    else:add_tube(c,'profiled_cranium',[(x,y+L*.30,z),(x,y,z+.08),(x,y-L*.35,z),(x,y-L*.66,z-.05)],[w*.6,w,w*.68,w*.30 if profile!='broad' else w*.9],'head',ellipse=.65)
    add_tube(c,'jaw_hinge_and_ramus',[(x,y+L*.22,z-.16),(x,y-L*.22,z-.22),(x,y-L*.62,z-.15)],[w*.70,w*.64,w*.31],'jaw',ellipse=.35)
    c.ell('oral_interior',(x,y-L*.25,z-.10),(w*.65,L*.34,.06),'head','black')
    for s in [-1,1]:
        c.ell('eye_socket',(x+s*w*.89,y-.03,z+.06),(.075,.09,.065),'head','black');c.ell('recessed_eye',(x+s*w*.93,y-.06,z+.065),(.04,.057,.037),'head','eye')
        add_tube(c,'brow_fold',[(x+s*w*.7,y-.2,z+.16),(x+s*w,y-.02,z+.15),(x+s*w*.73,y+.17,z+.1)],[.035,.055,.02],'head',sides=10)
        for j in range(5):
            yy=y-L*(.03+j*.11);ww=w*(.6-j*.065)
            c.horn('upper_tooth',(s*ww,yy,z-.09),(s*ww,yy-.02,z-.19),(s*ww*.9,yy-.03,z-.2),.025,'head')
    c.head_center=Vector(center)
def tail(c,pts,width=.3,mechanical=False):
    weights=[]
    for j in range(len(pts)-1):c.bone('tail'+str(j),pts[j],pts[j+1],'pelvis' if j==0 else 'tail'+str(j-1));weights.append('tail'+str(j))
    c.tube('tapered_tail',pts,[max(.02,width*(1-j/len(pts))) for j in range(len(pts))],weights+[weights[-1]],'metal' if mechanical else 'skin',sides=20,sub=5)
def leg(c,n,hip,knee,ankle,end,thick=.16,mechanical=False):
    if not mechanical:c.limb(n,hip,knee,ankle,end,'chest',thick);return
    c.bone(n,hip,knee,'chest');c.bone(n+'_shin',knee,ankle,n);c.bone(n+'_foot',ankle,end,n+'_shin')
    for suffix,a,b,r,parent in [('upper',hip,knee,thick,n),('lower',knee,ankle,thick*.65,n+'_shin')]:
        add_tube(c,n+'_'+suffix,[a,Vector(a).lerp(Vector(b),.25),Vector(a).lerp(Vector(b),.75),b],[r*.58,r,r*.78,r*.45],parent,'metal',ellipse=.7)
        aa=Vector(a);bb=Vector(b);off=Vector((.08,0,.02));add_tube(c,n+'_actuator',[aa+off,aa.lerp(bb,.40)+off,bb+off],[.035,.048,.025],parent,'metal',sides=10)
    for p,parent in [(hip,n),(knee,n+'_shin'),(ankle,n+'_foot')]:c.ell(n+'_bearing',p,(thick*.8,thick*.65,thick*.8),parent,'black')
    plate(c,n+'_foot_guard',Vector(end)+Vector((0,0,.035)),thick*1.25,thick*.40,thick*2,n+'_foot')
def arm(c,n,shoulder,elbow,wrist,mechanical=False):
    c.bone(n,shoulder,elbow,'chest');c.bone(n+'_fore',elbow,wrist,n);end=Vector(wrist)+Vector((0,-.12,-.22));c.bone(n+'_hand',wrist,end,n+'_fore')
    mat='metal' if mechanical else 'skin';add_tube(c,n+'_upper',[shoulder,elbow],[.16,.115],n,mat);add_tube(c,n+'_forearm',[elbow,Vector(elbow).lerp(Vector(wrist),.5),wrist],[.12,.16,.075],n+'_fore',mat)
    c.ell(n+'_palm',end,(.13,.08,.16),n+'_hand',mat)
    for j in range(4):
        start=end+Vector(((j-1.5)*.065,0,-.10));tip=start+Vector((0,-.025,-.18));bn=n+'_finger'+str(j);c.bone(bn,start,tip,n+'_hand');add_tube(c,bn,[start,tip,tip+Vector((0,-.05,-.04))],[.035,.027,.012],bn,mat,sides=8)
def wing(c,side,attach,span,chord,index=0):
    s=side;n=('wingL' if s<0 else 'wingR')+str(index);a=Vector(attach);el=a+Vector((s*span*.4,-.10,.25));wr=a+Vector((s*span*.7,-.35,.16));c.bone(n,a,el,'chest');c.bone(n+'_fore',el,wr,n)
    c.tube(n+'_arm',[a,el,wr],[.13,.075,.04],[n,n,n+'_fore'],sides=14,sub=5)
    tips=[wr+Vector((s*span*.32,-.15,-.14)),wr+Vector((s*span*.23,chord*.45,-.28)),a+Vector((s*span*.5,chord,-.32)),a+Vector((s*.25,chord*.70,-.3))]
    for j,tip in enumerate(tips[:3]):
        bn=n+'_finger'+str(j);c.bone(bn,wr,tip,n+'_fore');add_tube(c,bn,[wr,wr.lerp(tip,.55),tip],[.042,.027,.008],bn,sides=8)
    for j in range(3):
        vv=[];uv=[];ww=[];ff=[]
        for k in range(13):
            t=k/12
            for l in range(9):
                u=l/8;q=wr.lerp(tips[j].lerp(tips[j+1],u),t);q.z-=math.sin(t*math.pi)*math.sin(u*math.pi)*.09;vv.append(q);uv.append((t,u));ww.append({n+'_fore':1-t*.4,'chest':t*.4})
        for k in range(12):
            for l in range(8):z=k*9+l;ff.append((z,z+1,z+10,z+9))
        c.mesh(n+'_attached_membrane',vv,ff,uv,ww,'membrane')
def tentacle(c,n,pts,parent='chest',mat='skin',width=.15):
    bones=[]
    for j in range(len(pts)-1):bn=n+str(j);c.bone(bn,pts[j],pts[j+1],parent if j==0 else bones[-1]);bones.append(bn)
    c.tube(n,pts,[max(.015,width*(1-j/len(pts))) for j in range(len(pts))],bones+[bones[-1]],mat,sides=14,sub=5)

def build(c,k,idx):
    # Bespoke body plans, not recolours of the old class's dragon/humanoid builders.
    if k in ['coil','leech','eel','slug']:
        core(c,(0,0,.50));pts=[(math.sin(j*.65)*(.55 if k=='coil' else .15),.1+j*.48,.6-(.035*j)) for j in range(10 if k=='coil' else 7)]
        tail(c,pts,.34 if k!='slug' else .65,k=='eel');face(c,(0,-.4,.62),.7,.29,'broad')
        if k=='coil':
            for s in [-1,1]:wing(c,s,(s*.2,-.1,.7),1.1,.6);c.horn('facial_barbel',(s*.2,-.8,.7),(s*.5,-1.2,.9),(s*.6,-1.4,.8),.05,'head')
        elif k=='leech':ring(c,'sucker_jaw',(0,-.95,.59),.27,'jaw','tooth',axis='y',tube=.08)
        elif k=='eel':
            for j in range(6):ring(c,'joint_collar',pts[j],.27*(1-j/9),'tail'+str(j),'metal',axis='y');add_tube(c,'exposed_cable',[Vector(pts[j])+Vector((.2,0,.05)),Vector(pts[j+1])+Vector((.18,0,.06))],[.035,.035],'tail'+str(j),'black',sides=8)
        else:
            for j in range(5):plate(c,'stepped_shell',(0,.5+j*.42,.85+j*.045),.62-j*.035,.30,.50,'tail'+str(j),'tooth')
            for s in [-1,1]:tentacle(c,'eye_stalk'+str(s),[(s*.15,-.55,.7),(s*.26,-.62,1.0),(s*.27,-.7,1.12)],'head',width=.055);c.ell('stalk_eye',(s*.27,-.7,1.12),(.07,.06,.065),'head','eye')
    elif k in ['jelly','anemone','oracle']:
        z=2.4 if k=='jelly' else 1.6 if k=='oracle' else .55;core(c,(0,0,z));face(c,(0,-.1,z+.3),.6,.20,'mask')
        if k=='oracle':
            plate(c,'diamond_torso',(0,0,z),.45,.70,.3,'chest');ring(c,'suspended_halo',(0,0,z+.75),.50,'head','metal',axis='y')
        else:
            c.ell('bell_mantle',(0,0,z),(.85,.85,.38),'chest','membrane');ring(c,'mantle_rim',(0,0,z-.18),.81,'chest','skin',tube=.085)
        count=8 if k=='jelly' else 12 if k=='anemone' else 6
        for j in range(count):
            a=math.tau*j/count;rad=Vector((math.cos(a),math.sin(a),0));start=Vector((0,0,z))+rad*.6
            pts=[start,start+rad*.25+Vector((0,0,-.45 if k=='jelly' else .40)),start+rad*.35+Vector((0,0,-1.45 if k=='jelly' else .8)),start+rad*.1+Vector((0,0,-2.10 if k=='jelly' else .55))]
            tentacle(c,'tentacle'+str(j)+'_',pts,mat='metal' if k=='oracle' else 'skin',width=.12 if k!='oracle' else .07)
    elif k in ['widow','dredger','tick','moth','mole','eightleg']:
        z=1.4 if k in ['widow','dredger'] else .6 if k in ['tick','moth'] else .9;core(c,(0,0,z));mechanical=k in ['widow','dredger']
        bodyrad=(.62,1.0,.35) if k!='dredger' else (.75,.65,.60);c.ell('distinct_body',(0,.25,z),bodyrad,'chest','metal' if mechanical else 'skin');face(c,(.24 if k=='dredger' else 0,-.95,z+.1),.8,.29,'mask' if mechanical else 'broad')
        count={'widow':6,'dredger':3,'tick':4,'moth':6,'mole':6,'eightleg':8}[k]
        for j in range(count):
            a=math.tau*j/count if k in ['widow','dredger'] else math.pi*(j%2)+(j//2-(count/4-.5))*.3;v=Vector((math.cos(a),math.sin(a),0));hip=Vector((0,.2,z))+v*.45;kn=hip+v*(.8 if mechanical else .40)+Vector((0,0,.25));ank=kn+v*.3+Vector((0,0,-z*.9));end=ank+Vector((0,-.15,-.15));leg(c,'leg'+str(j),hip,kn,ank,end,.14 if k!='mole' else .23,mechanical)
        if k=='dredger':
            arm(c,'pincerL',(-.55,-.3,1.6),(-1.1,-.6,1.2),(-1.25,-1,1.3),True);arm(c,'winchR',(.55,-.1,1.7),(1.2,-.3,2),(1.1,-.8,2.2),True);ring(c,'winch_spool',(1.1,-.75,2.2),.28,'winchR_hand','metal',axis='y');plate(c,'offset_cockpit',(.34,-.45,1.95),.3,.24,.26,'chest')
        elif k=='widow':add_tube(c,'optic_mast',[(0,0,z),(0,0,z+.65),(0,-.2,z+.8)],[.16,.12,.18],'chest','metal');ring(c,'sensor_ring',(0,-.2,z+.8),.2,'chest','metal',axis='y')
        elif k=='moth':
            for s in [-1,1]:
                wing(c,s,(s*.3,-.2,z+.1),1.4,.9);wing(c,s,(s*.25,.5,z+.1),1.0,.8,1);tentacle(c,'antenna'+str(s),[(s*.13,-1,z+.2),(s*.3,-1.2,z+.5),(s*.4,-1.4,z+.65)],'head',width=.03)
            c.ell('large_abdomen',(0,1,z),(.40,.65,.4),'pelvis')
        elif k=='tick':c.horn('needle_proboscis',(0,-1.3,z),(0,-1.8,z),(0,-2.25,z),.075,'head','tooth')
        elif k=='mole':
            for s in [-1,1]:c.horn('digging_tusk',(s*.25,-1,z-.1),(s*.38,-1.7,z-.15),(s*.4,-2,z+.2),.12,'head')
        elif k=='eightleg':tail(c,[(0,1,.9),(0,1.8,.7),(.2,2.8,.5),(0,3.4,.45)],.25)
    elif k in ['gorgon','judge','executioner','pilgrim','ram']:
        z=1.9 if k in ['judge','executioner'] else 1.3;core(c,(0,0,z));c.ell('pelvic_structure',(0,0,z-.55),(.30,.25,.36),'pelvis','metal' if k=='executioner' else 'skin')
        c.tube('tapered_torso',[(0,0,z-.55),(0,0,z-.25),(0,0,z+.3),(0,0,z+.55)],[.28,.20,.53 if k=='executioner' else .32,.25],['pelvis','chest','chest','chest'],'metal' if k=='executioner' else 'skin',ellipse=.6,sides=24,sub=6)
        headz=z+1.05 if k=='judge' else z+.85;face(c,(0,-.10,headz),.60,.24,'mask' if k in ['executioner','judge','pilgrim'] else 'broad')
        if k=='gorgon':
            tail(c,[(0,0,z-.6),(.4,.65,.55),(.5,1.5,.30),(-.3,2.0,.25),(-.65,2.8,.3),(0,3.3,.2)],.5)
            for s in [-1,1]:wing(c,s,(s*.2,-.1,z+.6),.65,.9)
        else:
            for s in [-1,1]:leg(c,'hind'+str(s),(s*.24,0,z-.5),(s*.3,-.08,(z-.5)*.5),(s*.3,.06,.25),(s*.32,-.22,.12),.15 if k!='ram' else .25,k=='executioner')
        for s in [-1,1]:
            arm(c,'arm'+str(s),(s*.4,0,z+.37),(s*.66,.06,z-.10),(s*.7,-.12,z-.65),k=='executioner')
            if k=='gorgon':arm(c,'lowarm'+str(s),(s*.33,.05,z-.12),(s*.64,.2,z-.5),(s*.83,-.03,z-.8))
        if k=='judge':ring(c,'ring_head',(0,-.15,headz),.42,'head','tooth',axis='y');tentacle(c,'pendulum_chain',[(-.70,0,z-.6),(-.8,0,z-1.1),(-.9,-.2,.25)],'arm-1_hand','metal',.04)
        if k in ['judge','pilgrim']:
            c.tube('hanging_mantle',[(0,.10,z+.45),(0,.12,z-.2),(0,.13,.20)],[.47,.35,.55],['chest','chest','pelvis'],'membrane',sides=32,sub=3,ellipse=.55)
            if k=='pilgrim':c.ell('enclosed_hood',(0,.05,headz),(.32,.3,.4),'head','membrane');plate(c,'dark_face_aperture',(0,-.255,headz),.14,.22,.025,'head','black')
        if k=='ram':
            for s in [-1,1]:tentacle(c,'curled_horn'+str(s),[(s*.2,-.08,headz+.1),(s*.55,.15,headz+.35),(s*.65,-.20,headz+.05),(s*.35,-.45,headz)],'head','tooth',.13);wing(c,s,(s*.3,.1,z+.40),.8,.6)
            tail(c,[(0,.25,z-.6),(0,1,z-.7),(0,1.7,z-.9),(0,2.3,.3)],.27)
        if k=='executioner':
            plate(c,'wedge_helmet',(0,-.13,headz),.32,.28,.28,'head');plate(c,'integrated_cleaver',(.72,-.12,z-.72),.20,.60,.11,'arm1_hand');ring(c,'open_waist_frame',(0,0,z-.3),.23,'pelvis','metal',tube=.045)
    else:
        # Quadruped, avian, glider and amphibian body plans have individual head/limb/wing construction.
        z={'needle':1.65,'kite':1.45,'choir':1.35,'rook':1.10,'toad':.45,'manta':1.2,'shell':.7,'furnace':1.0}.get(k,1.1);core(c,(0,0,z))
        rad={'manta':(1.2,.9,.18),'shell':(.85,1.1,.38),'toad':(.55,.6,.32),'furnace':(.8,1.0,.58),'needle':(.28,.6,.38),'kite':(.3,.72,.35)}.get(k,(.5,.85,.4))
        c.ell('body_plan',(0,.2,z),rad,'chest','metal' if k in ['furnace','rook'] else 'skin')
        head=(0,-1.2,z+.12);profile='broad' if k=='toad' else 'hammer' if k=='hammer' else 'wedge';length=.85;width=.32
        if k in ['needle','kite','rook']:head=(0,-1.2,z+.7 if k!='needle' else z+1.7);length=1.3;width=.16;add_tube(c,'long_neck',[(0,-.45,z),(0,-.6,z+.5),head],[.16,.12,.10],'neck2','metal' if k=='rook' else 'skin')
        face(c,head,length,width,profile)
        if k=='choir':
            for s in [-1,1]:
                pts=[(s*.25,-.3,z+.3),(s*.6,-.5,z+.8),(s*.75,-.8,z+1.0)];tentacle(c,'choir_neck'+str(s),pts,width=.12);c.ell('secondary_beaked_head',pts[-1],(.14,.30,.17),'choir_neck'+str(s)+'1');c.horn('beak',(s*.75,-1.0,z+1.0),(s*.75,-1.3,z+.94),(s*.75,-1.5,z+.95),.12,'choir_neck'+str(s)+'1','tooth')
        count=0 if k=='manta' else 2 if k in ['kite','sixwing','needle','rook'] else 6 if k=='flipper' else 4
        for j in range(count):
            s=-1 if j%2==0 else 1;yy=-.45+(j//2)*.75;hip=(s*rad[0]*.7,yy,z);knee=(s*(rad[0]+.3),yy+.1,z*.6);ank=(s*(rad[0]+.25),yy-.15,.20);foot=(s*(rad[0]+.28),yy-.4,.08)
            if k=='flipper':
                c.bone('flipper'+str(j),hip,(s*1.3,yy+.2,z-.15),'chest');c.ell('paddle',(s*.9,yy+.15,z-.2),(.6,.25,.06),'flipper'+str(j),'membrane')
            else:leg(c,'hind'+str(j),hip,knee,ank,foot,.18 if k not in ['furnace','shell','toad'] else .25,k in ['furnace','rook'])
        tail(c,[(0,1,z),(0,1.8,z-.15),(.1,2.8,z-.4),(0,3.5,z-.6)],.30 if k!='manta' else .18,k=='rook')
        if k in ['kite','hammer','sixwing','needle','manta','rook']:
            pairs=3 if k=='sixwing' else 2 if k=='needle' else 1
            for j in range(pairs):
                for s in [-1,1]:wing(c,s,(s*rad[0]*.65,-.25+j*.65,z+.25),3.1 if k=='kite' else 2.1 if k=='manta' else .8 if k=='rook' else 1.8 if k=='hammer' else 2.2-j*.25,.9 if k!='manta' else 1.5,j)
        if k in ['shell','furnace']:
            for j in range(5):
                c.ell('segmented_shell',(0,-.65+j*.4,z+.30),(.82,.32,.25),'chest','tooth' if k=='shell' else 'metal')
            if k=='furnace':
                for s in [-1,1]:add_tube(c,'exhaust_stack',[(s*.5,.5,z+.3),(s*.5,.65,z+1.0)],[.12,.12],'chest','metal');plate(c,'ram_shield',(0,-1.1,z+.15),.70,.35,.16,'head')
        if k=='flipper':
            for j in range(7):c.horn('saw_ridge',(0,-.5+j*.45,z+.35),(0,-.45+j*.45,z+.8),(0,-.2+j*.45,z+.48),.1,'chest' if j<4 else 'tail1','tooth')
        if k=='grazer':
            for s in [-1,1]:arm(c,'grasp_arm'+str(s),(s*.24,-.65,z+.4),(s*.5,-.6,z+.6),(s*.5,-1,z+.3))
        if k=='toad':c.ell('expanded_throat',(0,-.9,z-.05),(.46,.45,.28),'jaw','membrane')

def rig_and_motion(c,k,index):
    bpy.ops.object.select_all(action='DESELECT')
    for o in c.parts:o.select_set(True)
    bpy.context.view_layer.objects.active=c.parts[0];bpy.ops.object.join();m=bpy.context.object;m.name=c.name+'_Mesh'
    ad=bpy.data.armatures.new(c.name+'_Skeleton');r=bpy.data.objects.new(c.name+'_Rig',ad);bpy.context.collection.objects.link(r);bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
    for n,(h,t,parent) in c.bones.items():
        b=ad.edit_bones.new(n);b.head=h;b.tail=t
        if (Vector(t)-Vector(h)).length<.001:b.tail=Vector(h)+Vector((0,0,.1))
        if parent:b.parent=ad.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT');m.modifiers.new('Skin','ARMATURE').object=r;m.parent=r
    scale=.5 if c.cat=='enemies' else 1.4 if c.cat=='bosses' else 1.0;r.scale=(scale,)*3;r.animation_data_create();c.rig=r;c.meshobj=m
    specs=[('Idle_Breath',2,True),('Walk_InPlace',1.6,True),('Run_InPlace',.9,True),('Advance_RootMotion',1.3,False),('Start_Forward',.7,False),('Stop_Forward',.75,False),('Turn_Left90_RootMotion',1.0,False),('Turn_Right90_RootMotion',1.1,False),('Defensive_Brace',1.2,False),('Attack_Primary',1.35,False),('Attack_Sweep',1.6,False),('Attack_Charge_RootMotion',1.45,False),('Attack_Special',2.0,False),('React_Front',.7,False),('React_Back',.8,False),('React_Left',.75,False),('React_Right',.75,False),('Stagger',1.1,False),('Knockdown',1.2,False),('GetUp',1.8,False),('Death',2.4,False),('Flight_Cruise_InPlace' if any(n.startswith('wing') for n in c.bones) else 'Swim_Cruise_InPlace' if k in ['eel','flipper','manta','jelly'] else 'Patrol_Scan',2.2,True)]
    records=[];legbones=[n for n in c.bones if n.startswith(('leg','hind')) and not n.endswith(('_shin','_foot'))];specialbones=[n for n in c.bones if n.startswith(('tail','tentacle','choir_neck','flipper'))]
    for ci,(name,dur,loop) in enumerate(specs):
        action=bpy.data.actions.new(c.name+'__'+name);r.animation_data.action=action;last=round(dur*30)+1
        for f in sorted(set(list(range(1,last+1,3))+[last])):
            t=(f-1)/30;u=t/dur;phase=math.tau*u;attack=max(0,math.sin(math.pi*max(0,min(1,(u-.22)/.38)))) if name.startswith('Attack') else 0
            for pb in r.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
            r.pose.bones['chest'].rotation_quaternion=Quaternion((1,0,0),(.025+.002*(index%6))*math.sin(phase))
            r.pose.bones['head'].rotation_quaternion=Quaternion((0,0,1),(.055+.008*(index%4))*math.sin(phase))
            moving=name.startswith(('Walk','Run','Advance','Start','Stop','Attack_Charge'));swimming=name.startswith('Swim');flying=name.startswith('Flight')
            if moving:
                freq=2 if name=='Run_InPlace' else 1
                for j,n in enumerate(legbones):
                    theta=phase*freq+math.tau*j/max(2,len(legbones));amp=.22+.02*(index%5);r.pose.bones[n].rotation_quaternion=Quaternion((1,0,0),amp*math.sin(theta));r.pose.bones[n+'_shin'].rotation_quaternion=Quaternion((1,0,0),-.25*max(0,math.sin(theta)))
                r.pose.bones['chest'].rotation_quaternion=Quaternion((0,0,1),.025*math.sin(phase*2))
            for j,n in enumerate(specialbones):r.pose.bones[n].rotation_quaternion=Quaternion((0,0,1),(.09 if not swimming else .20)*math.sin(phase-j*.55+index*.23))
            for j,n in enumerate(c.bones):
                if n.startswith('wing') and '_finger' not in n:r.pose.bones[n].rotation_quaternion=Quaternion((0,1,0),(.12 if not flying else .4)*math.sin(phase+(0 if 'L' in n else math.pi)+(int(n[-1])*.3 if n[-1].isdigit() else 0)))
                if n.startswith(('arm','pincer','winch','grasp','lowarm')) and not any(s in n for s in ['fore','hand','finger']):r.pose.bones[n].rotation_quaternion=Quaternion((1,0,0),-.35*attack+.07*math.sin(phase+j*.7))
            root=r.pose.bones['root']
            if 'RootMotion' in name:
                if name.startswith('Turn'):root.rotation_quaternion=Quaternion(r.data.bones['root'].matrix_local.to_3x3().inverted()@Vector((0,0,1)),(1 if 'Left' in name else -1)*math.pi/2*(u*u*(3-2*u)))
                else:root.location.y=-(1.2+.06*index)*(u*u*(3-2*u));root.location.z=.04*math.sin(math.pi*u)
            if name.startswith('Attack'):
                r.pose.bones['neck2'].rotation_quaternion=Quaternion((1,0,0),(.16 if k not in ['executioner','judge'] else .06)*attack);r.pose.bones['jaw'].rotation_quaternion=Quaternion((1,0,0),(.36+.015*(index%5))*attack);root.location.z=-.10*attack
                if name=='Attack_Sweep':r.pose.bones['chest'].rotation_quaternion=Quaternion((0,0,1),.45*math.sin(math.tau*u)*math.sin(math.pi*u))
                if name=='Attack_Special':r.pose.bones['chest'].rotation_quaternion=Quaternion((1,0,0),-.20*math.sin(math.pi*u))
            if name.startswith('React') or name=='Stagger':
                env=math.sin(math.pi*u)*math.exp(-2*u);axis=(1,0,0) if name in ['React_Front','React_Back','Stagger'] else (0,1,0);sgn=-1 if name in ['React_Back','React_Right'] else 1;r.pose.bones['chest'].rotation_quaternion=Quaternion(axis,sgn*.3*env)
            if name in ['Knockdown','Death','GetUp']:
                drop=u*u*(3-2*u);drop=1-drop if name=='GetUp' else drop;root.location.z=-.35*drop;r.pose.bones['chest'].rotation_quaternion=Quaternion((0,1,0),.70*drop)
            if name=='Defensive_Brace':root.location.z=-.07*math.sin(math.pi*u);r.pose.bones['head'].rotation_quaternion=Quaternion((1,0,0),-.15*math.sin(math.pi*u))
            root.location=r.data.bones['root'].matrix_local.to_3x3().inverted()@root.location
            for pb in r.pose.bones:
                pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
        for fc in action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
        action.use_fake_user=True;track=r.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(action.name,1,action);track.mute=True
        records.append({'name':action.name,'purpose':name,'duration_s':(last-1)/30,'fps':30,'loop':loop,'motion_kind':'root_motion' if 'RootMotion' in name else 'in_place','root_end_offset_m':[0,(-(1.2+.06*index)*scale if name in ['Advance_RootMotion','Attack_Charge_RootMotion'] else 0),0],'events':[{'time_s':dur*.22,'event':'anticipation_end'},{'time_s':dur*.42,'event':'authored_attack_cue','validated_hit_window':False},{'time_s':dur*.60,'event':'recovery_start'}] if name.startswith('Attack') else [],'contact_validation':'procedural, not approved; foot-contact/clipping review still required','rig':c.name+'_Rig','distinctness':'body-plan-specific channels and index-dependent timing/amplitude; procedural shared framework, not motion capture'})
    r.animation_data.action=None
    for pb in r.pose.bones:pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
    return records

ONLY=sys.argv[-1] if '--' in sys.argv else 'all';progress=P/'audit/Build_Progress.json';done=json.loads(progress.read_text()) if progress.exists() else []
for idx,(cat,name,kind,description) in enumerate(ROSTER):
    if ONLY=='all' and any(x['asset']==name for x in done) and os.environ.get('NOCTURNE_FORCE_REBUILD')!='1':continue
    if ONLY!='all' and ONLY!=name:continue
    CURRENT=name;MECHANICAL=kind in ['dredger','widow','furnace','executioner','eel','rook'];bpy.ops.wm.read_factory_settings(use_empty=True)
    c=base.Creature((cat,name,kind,'expansion'),idx);build(c,kind,idx);clips=rig_and_motion(c,kind,idx)
    folder=P/cat/name;folder.mkdir(parents=True,exist_ok=True);bpy.context.scene.render.fps=30
    for im in bpy.data.images:
        if im.source=='FILE':im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')),compress=True)
    bpy.ops.object.select_all(action='DESELECT');c.rig.select_set(True);c.meshobj.select_set(True);bpy.context.view_layer.objects.active=c.rig
    saved_rig_name=c.rig.name;c.rig.name='Rig';saved_action_names=[(a,a.name) for a in list(bpy.data.actions)]
    for a,n in saved_action_names:a.name=n.split('__')[-1]
    bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,object_types={'MESH','ARMATURE'},add_leaf_bones=False,axis_forward='-Z',axis_up='Y',bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True)
    c.rig.name=saved_rig_name
    for a,n in saved_action_names:a.name=n
    bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_frame_range=False,export_force_sampling=True,export_def_bones=True)
    data={'asset':name,'category':cat,'body_plan':kind,'design':description,'status':'new_distinct_procedural_prototype_not_cinematic','canonical_glb':str((folder/(name+'.glb')).relative_to(P)),'canonical_fbx':str((folder/(name+'.fbx')).relative_to(P)),'editable_source':str((folder/(name+'.blend')).relative_to(P)),'vertices':len(c.meshobj.data.vertices),'bones':len(c.rig.data.bones),'clips':clips,'source':'original body construction using reusable mesh primitives; no copied franchise art','texture_resolution':2048,'texture_painting':'procedural UV textures, not hand-painted anatomy','sockets':{'mouth':'head','effect_socket':'chest','root_motion':'root','feet':[n for n in c.bones if n.endswith('_foot')]},'engine_tested':False,'iphone_tested':False,'remaining':['Cinematic anatomy/material refinement','Contact/clipping and motion polish','Engine integration']}
    (folder/'asset.json').write_text(json.dumps(data,indent=2));done=[x for x in done if x['asset']!=name]+[data];progress.write_text(json.dumps(done,indent=2))
    for f in folder.iterdir():
        if f.is_file():
            with f.open('rb') as h:os.fsync(h.fileno())
    print('CHARACTER_EXPORTED',name,len(clips),len(c.meshobj.data.vertices),flush=True)
