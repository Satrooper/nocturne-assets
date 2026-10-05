import bpy,json,math,importlib.util
from pathlib import Path
from mathutils import Vector,Quaternion
W=Path(__file__).resolve().parents[1];P=W/'Nocturne_Expansion_60';BASE=W/'Nocturne_V4_Visual_Revision'
spec=importlib.util.spec_from_file_location('base',P/'source/mesh_primitives.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def mat(palette,part):
    m=bpy.data.materials.new(part);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value={'metal':(.13,.15,.17,1),'skin':(.065,.075,.07,1),'black':(.012,.014,.017,1),'tooth':(.35,.37,.39,1),'eye':(.12,.24,.29,1),'membrane':(.075,.043,.027,1)}[part];bs.inputs['Metallic'].default_value=.85 if part in ['metal','tooth'] else 0;bs.inputs['Roughness'].default_value=.32 if part=='metal' else .60;return m
base.material=mat
weapon_rows=[]
for name,kind in [('Sable_Revolver','revolver'),('Helix_Carbine','carbine'),('Tidebreaker_Poleaxe','poleaxe')]:
    bpy.ops.wm.read_factory_settings(use_empty=True);c=base.Creature(('weapons',name,kind,'metal'),0);c.bone('root',(0,0,0),(0,0,.1));c.bone('muzzle',(0,-.48,.10),(0,-.60,.10),'root');c.bone('grip',(0,.02,0),(0,.02,-.10),'root');c.bone('support',(0,-.20,.05),(0,-.30,.05),'root')
    if kind=='revolver':
        c.bone('cylinder',(0,-.12,.10),(0,-.23,.10),'root');c.bone('hammer',(0,.02,.15),(0,.05,.21),'root')
        c.tube('profiled_barrel',[(0,-.15,.1),(0,-.35,.10),(0,-.49,.10)],[.042,.028,.026],['root']*3,'metal',sides=8,sub=2)
        for j in range(6):
            a=math.tau*j/6;x=math.cos(a)*.037;z=.10+math.sin(a)*.037;c.tube('cylinder_chamber',[(x,-.12,z),(x,-.225,z)],[.022,.022],['cylinder']*2,'metal',sides=10,sub=1)
        c.tube('curved_grip',[(0,.01,.04),(0,.05,-.06),(0,.08,-.17)],[.033,.042,.037],['root']*3,'membrane',ellipse=.65)
        c.tube('frame_bridge',[(0,.04,.13),(0,-.10,.17),(0,-.26,.15)],[.024,.026,.023],['root']*3,'skin',sides=8)
        c.ell('hammer',(.0,.025,.18),(.018,.035,.025),'hammer','metal')
    elif kind=='carbine':
        c.bone('bolt',(0,-.10,.13),(0,-.22,.13),'root');c.bone('magazine',(0,.12,-.05),(0,.15,-.17),'root')
        c.tube('bullpup_receiver',[(0,.26,.07),(0,.18,.09),(0,-.15,.10),(0,-.31,.10)],[.053,.065,.060,.035],['root']*4,'skin',sides=8,ellipse=1.4)
        c.tube('exposed_forward_barrel',[(0,-.25,.1),(0,-.49,.1),(0,-.58,.10)],[.025,.025,.027],['root']*3,'metal',sides=12)
        c.tube('magazine',[(0,.14,.015),(0,.17,-.19)],[.043,.041],['magazine']*2,'metal',sides=6,ellipse=.75)
        c.tube('pistol_grip',[(0,-.01,.04),(0,.015,-.11)],[.034,.027],['root']*2,'membrane',sides=8,ellipse=.75)
        c.tube('optic_mount',[(0,-.07,.16),(0,-.13,.20)],[.02,.02],['root']*2,'metal');c.tube('optic_tube',[(0,-.02,.22),(0,-.22,.22)],[.036,.033],['root']*2,'black')
        c.tube('stock_plate',[(0,.27,-.02),(0,.29,.16)],[.027,.027],['root']*2,'membrane',sides=8,ellipse=.7)
    else:
        c.bones['grip']=((0,0,-.15),(0,0,.10),'root');c.bones['support']=((0,0,.42),(0,0,.60),'root');c.bones['muzzle']=((0,0,1.1),(0,0,1.2),'root')
        c.tube('long_shaft',[(0,0,-.65),(0,0,.8),(0,0,1.18)],[.025,.025,.021],['root']*3,'membrane',sides=12,sub=1)
        vv=[(0,-.035,.70),(.40,-.035,.75),(.56,-.035,1.1),(.35,-.035,1.35),(0,-.035,1.14),(0,.035,.70),(.40,.035,.75),(.56,.035,1.1),(.35,.035,1.35),(0,.035,1.14)]
        ff=[(0,1,2,3,4),(9,8,7,6,5)]+[(j,(j+1)%5,(j+1)%5+5,j+5) for j in range(5)];c.mesh('crescent_cleaver_head',vv,ff,[(v[0],v[2]) for v in vv],['root']*10,'tooth',False)
        c.horn('rear_pick',(0,0,1.1),(-.25,0,1.17),(-.4,0,1.10),.06,'root','metal');c.horn('top_spike',(0,0,1.15),(0,0,1.45),(0,0,1.58),.055,'root','metal')
    bpy.ops.object.select_all(action='DESELECT')
    for o in c.parts:o.select_set(True)
    bpy.context.view_layer.objects.active=c.parts[0];bpy.ops.object.join();mesh=bpy.context.object;mesh.name=name+'_Mesh'
    ad=bpy.data.armatures.new(name+'_Skeleton');r=bpy.data.objects.new(name+'_Rig',ad);bpy.context.collection.objects.link(r);bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
    for n,(h,t,parent) in c.bones.items():b=ad.edit_bones.new(n);b.head=h;b.tail=t;b.parent=ad.edit_bones.get(parent) if parent else None
    bpy.ops.object.mode_set(mode='OBJECT');mesh.modifiers.new('Skin','ARMATURE').object=r;mesh.parent=r;r.animation_data_create();clips=[]
    if kind!='poleaxe':
        for actionname,dur in [('Fire_Cycle',.50),('Reload_Mechanism',2.0)]:
            a=bpy.data.actions.new(name+'__'+actionname);r.animation_data.action=a
            for f in range(1,int(dur*30)+2):
                t=(f-1)/30;u=t/dur
                for pb in r.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0)
                if kind=='revolver':r.pose.bones['cylinder'].rotation_quaternion=Quaternion((0,1,0),math.pi/3*u if actionname=='Fire_Cycle' else math.pi*2*u);r.pose.bones['hammer'].rotation_quaternion=Quaternion((1,0,0),-.4*math.sin(math.pi*u))
                elif actionname=='Fire_Cycle':r.pose.bones['bolt'].location.y=.07*math.sin(math.pi*u)**2
                else:r.pose.bones['magazine'].location.z=-.18*math.sin(math.pi*u)
                for pb in r.pose.bones:pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
            a.use_fake_user=True;tr=r.animation_data.nla_tracks.new();tr.strips.new(a.name,1,a);tr.mute=True;clips.append({'name':a.name,'duration_s':dur,'player_handling':False,'loop':False})
    r.animation_data.action=None
    for pb in r.pose.bones:pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0)
    folder=P/'weapons'/name;folder.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(folder/(name+'.blend')),compress=True);bpy.ops.object.select_all(action='DESELECT');r.select_set(True);mesh.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(folder/(name+'.fbx')),use_selection=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
    bpy.ops.export_scene.gltf(filepath=str(folder/(name+'.glb')),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_frame_range=False)
    rec={'asset':name,'kind':kind,'status':'new_weapon_prototype','glb':str((folder/(name+'.glb')).relative_to(P)),'fbx':str((folder/(name+'.fbx')).relative_to(P)),'clips':clips,'sockets':['grip','support','muzzle'],'engine_tested':False};(folder/'asset.json').write_text(json.dumps(rec,indent=2));weapon_rows.append(rec)
(P/'weapons/weapon_manifest.json').write_text(json.dumps(weapon_rows,indent=2))

bpy.ops.wm.open_mainfile(filepath=str(BASE/'player_animation/Player_Moves.blend'));r=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');r.animation_data.action=None
for tr in list(r.animation_data.nla_tracks):r.animation_data.nla_tracks.remove(tr)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
names=['Light_Slash_Left','Light_Slash_Right','Light_Thrust','Heavy_Overhead','Heavy_Sweep','Heavy_Thrust','Charge_Loop','Charge_Release','Run_Slash','Jump_Slam','Backhand_Cut','Spin_Cut','Shield_Raise','Shield_Lower','Shield_Bash','Parry_High','Parry_Low','GuardBreak','Riposte_Thrust','Finisher_Attacker_A','Finisher_Victim_A','Finisher_Attacker_B','Finisher_Victim_B','Dodge_Forward','Dodge_Back','Dodge_Left','Dodge_Right','Roll_Forward','Roll_Back','Step_Left','Step_Right','React_FrontHigh','React_FrontLow','React_BackHigh','React_BackLow','React_Left','React_Right','Knockdown_Front','Knockdown_Back','Getup_Front','Getup_Back','Swim_Freestyle','Swim_Backstroke','Swim_Dive','Land_Heavy','Climb_Mantle']
assert len(names)==46;rows=[];prefix='mixamorig:'
def rot(n,axis,value):
    pb=r.pose.bones.get(prefix+n)
    if pb:pb.rotation_quaternion=Quaternion(axis,value)
root=r.pose.bones.get('NocturneRoot') or r.pose.bones[prefix+'Hips'];wm=r.matrix_world.copy();wi=wm.to_3x3().inverted()
for idx,name in enumerate(names):
    dur=2.1 if name.startswith(('Swim','Finisher','Climb')) else .70+idx%5*.15;end=round(dur*30)+1;a=bpy.data.actions.new('Expansion_Body__'+name);r.animation_data.action=a
    for f in range(1,end+1):
        u=(f-1)/(end-1);phase=u*math.tau;env=math.sin(math.pi*u)
        for pb in r.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0)
        if name.startswith(('Light','Heavy','Charge','Run','Jump','Backhand','Spin','Riposte','Finisher')):
            amp=.85 if name.startswith('Heavy') else .6;rot('RightArm',(1,0,0),-amp*env);rot('RightForeArm',(0,0,1),.45*env);rot('LeftArm',(1,0,0),-.3*env);rot('Spine2',(0,1,0),(.25 if 'Left' in name else -.25)*env);rot('Hips',(0,1,0),.12*math.sin(phase));rot('RightHand',(0,0,1),.17*math.sin(phase+idx*.3))
            if 'Thrust' in name:rot('RightArm',(0,0,1),-.55*env);rot('RightForeArm',(0,0,1),.2*(1-env))
            if 'Overhead' in name or 'Jump' in name:rot('RightArm',(0,0,1),1.3*env);root.location=wi@Vector((0,0,.28*env if 'Jump' in name else -.10*env))
            if 'Victim' in name:rot('Spine2',(1,0,0),.65*env);root.location=wi@Vector((0,.10*env,-.35*env))
        elif name.startswith(('Shield','Parry','Guard')):
            rot('LeftArm',(1,0,0),-.65*env);rot('LeftForeArm',(0,0,1),.70*env);rot('RightArm',(1,0,0),-.28*env);rot('Spine2',(1,0,0),-.20*env if name=='GuardBreak' else .08*env)
        elif name.startswith(('Dodge','Roll','Step')):
            d=Vector((-.7 if 'Left' in name else .7 if 'Right' in name else 0,.9 if 'Back' in name else -.9 if 'Forward' in name else 0,0));root.location=wi@(d*(u*u*(3-2*u))+Vector((0,0,.11*env)));rot('Hips',(1,0,0),math.tau*u if name.startswith('Roll') else -.15*env);rot('LeftUpLeg',(1,0,0),.3*env);rot('RightUpLeg',(1,0,0),-.3*env)
        elif name.startswith('React'):
            sg=-1 if any(s in name for s in ['Back','Right']) else 1;rot('Spine2',(1,0,0) if 'Left' not in name and 'Right' not in name else (0,1,0),sg*.32*env);rot('Head',(1,0,0),-.12*env)
        elif name.startswith(('Knockdown','Getup')):
            e=u*u*(3-2*u);e=1-e if name.startswith('Getup') else e;sg=-1 if 'Back' in name else 1;rot('Hips',(1,0,0),sg*1.25*e);root.location=wi@Vector((0,sg*.20*e,-.70*e));rot('LeftLeg',(1,0,0),-.50*e);rot('RightLeg',(1,0,0),-.4*e)
        elif name.startswith('Swim'):
            rot('Hips',(1,0,0),-math.pi/2 if 'Backstroke' not in name else math.pi/2);rot('LeftArm',(0,0,1),.80*math.sin(phase));rot('RightArm',(0,0,1),.80*math.sin(phase+math.pi));rot('LeftUpLeg',(1,0,0),.22*math.sin(phase*2));rot('RightUpLeg',(1,0,0),-.22*math.sin(phase*2))
        elif name=='Land_Heavy':root.location=wi@Vector((0,0,-.30*env));rot('LeftLeg',(1,0,0),-.6*env);rot('RightLeg',(1,0,0),-.6*env)
        else:root.location=wi@Vector((0,-.65*u,.8*u));rot('LeftArm',(1,0,0),-.75*env);rot('RightArm',(1,0,0),-.75*env)
        for pb in r.pose.bones:pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
    a.use_fake_user=True;tr=r.animation_data.nla_tracks.new();tr.strips.new(a.name,1,a);tr.mute=True
    rows.append({'name':a.name,'duration_s':(end-1)/30,'fps':30,'loop':name in ['Charge_Loop','Swim_Freestyle','Swim_Backstroke'],'motion_kind':'root_motion' if name.startswith(('Dodge','Roll','Step','Climb')) else 'in_place','status':'procedural body prototype; weapon/grip/contact approval unfinished','events':[{'time_s':dur*.45,'event':'authored_attack_cue','validated_damage_window':False}] if name.startswith(('Light','Heavy','Riposte')) else [],'paired_alignment':{'pair':name[-1],'attacker_world':[0,0,0],'victim_world':[0,-.9,0],'victim_yaw_degrees':180,'validated':False} if name.startswith('Finisher') else None})
folder=P/'player_animation';folder.mkdir(exist_ok=True);r.animation_data.action=None
for pb in r.pose.bones:pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0)
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'Expanded_Player_Moves.blend'),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type in ['ARMATURE','MESH']:o.select_set(True)
bpy.ops.export_scene.fbx(filepath=str(folder/'Expanded_Player_Moves.fbx'),use_selection=True,add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,axis_forward='-Z',axis_up='Y')
bpy.ops.export_scene.gltf(filepath=str(folder/'Expanded_Player_Moves.glb'),export_format='GLB',use_selection=True,export_animation_mode='ACTIONS',export_frame_range=False)
(folder/'animation_manifest.json').write_text(json.dumps({'clips':rows,'status':'new procedural body bank; not polished production choreography','engine_tested':False},indent=2));print('EXPANDED_BODY_AND_WEAPONS_DONE',len(rows),len(weapon_rows),flush=True)
