import bpy,math,json
from math import sin
from mathutils import Vector
# Each row defines eight distinct staged moves, composed from reusable motion primitives.
# These are authored procedural sequences, not motion capture.
MOVESETS=[
'Hooked Bite|Furnace Inhale|Floor Flame Sweep|Alternating Claw Combo|Rear Tail Sweep|Overhead Wing Slam|Ember Pounce|Charge And Bite',
'Antler Rake|Double Horn Thrust|Frost Exhale|Freezing Stomp|Sidestep Bite|Horn Lift|Tail Crush|Glacial Dive',
'Lightning Dive|Crosswind Buffet|Banking Talon Rake|Ground Thunder Peck|Wing Shield Counter|Spiral Descent|Storm Takeoff|Triple Snap',
'Thorn Shoulder Ram|Rooted Tail Lash|Thorn Fan Cast|Claw Hook Pull|Bramble Stomp|Vine Neck Snare|Burrowing Strike|Backplate Shudder',
'Magma Belly Slam|Armour Brace|Seismic Double Stomp|Obsidian Headbutt|Furnace Vent|Heavy Tail Hammer|Slow Crushing Bite|Eruption Rear',
'Blood Screech|Twin Fang Lunge|Crimson Wing Cross|Leaping Neck Bite|Backward Wing Cut|Blood Cone|Hanging Talon Sweep|Batwing Feint',
'Tidal Coil|Undertow Bite|Lateral Fin Strike|Deepwater Ascend|Corkscrew Rush|Whirlpool Cast|Coil Constriction|Surface Breach',
'Sandblast Exhale|Raking Wing Dive|Buried Ambush|Sand Tail Fan|Hooked Talon Drag|Dust Wingbeat|Snapping Retreat|Mirage Sidestep',
'Lunar Bow|Crescent Tail Cut|Moon Halo Pulse|Delayed Neck Thrust|Floating Wing Cross|Lunar Pounce|Halfmoon Turn Bite|Veil Unfurl',
'Iron Wing Scissor|Armoured Shoulder Charge|Blade Tail Spear|Steel Jaw Clamp|Wing Guard Reversal|Mechanical Dive|Quill Volley|Landing Wing Sweep',
'Bell Overhead Smash|Backhand Bell Swing|Bell Drag Sweep|Shielding Kneel|Double Hammer Combo|Bell Toll Cast|Charging Bell Ram|Execution Downstroke',
'Furnace Punch|Back Vent Discharge|Piston Uppercut|Overheat Stomp|Steam Guard Break|Double Piston Combo|Grate Slam|Cooling Kneel',
'Root Hand Sweep|Branch Spear|Entangling Reach|Trunk Body Slam|Root Fan Cast|Bark Guard|Uprooting Heave|Canopy Rake',
'Front Fang Lunge|Left Leg Cage|Right Leg Cage|Web Spit|Abdomen Slam|Silk Retreat|Eight Leg Surge|Crossed Fang Clamp',
'Royal Cleave|Horned Headbutt|Left Hook Right Crush|Regal Stomp|Blood Hand Cast|Grab And Throw|Kneeling Eruption|Delayed Execution',
'Gatling Brace|Missile Launch Pose|Hydraulic Backhand|Targeting Pivot|Shockwave Stomp|Core Overload|Armoured Rush|Mechanical Uppercut',
'Vortex Inhale|Crushing Maw|Fin Backhand|Deep Dive Feint|Tailfin Reversal|Jaw Triple Snap|Spiral Ascend|Breach And Plunge',
'Scythe Reap|Reverse Scythe Cut|Hook And Pull|Spectral Reach|Scythe Vault|Double Reaping Arc|Teleport Arrival Pose|Soul Harvest Kneel',
'Crystal Fist Crush|Prism Chest Cast|Shard Shoulder Sweep|Glass Guard Break|Mirror Stomp|Shard Rain Summon|Crystal Uppercut|Splinter Collapse',
'Coiling Fang Strike|Sequential Leg Rake|Venom Spit|Segment Tail Sweep|Low Burrowing Lunge|Rearing Crush|Spiral Guard|Rolling Surge',
'Low Throat Bite|Running Pounce|Left Flank Snap|Right Flank Snap|Rear Kick|Pack Howl|Bite And Shake|Retreating Snap',
'Quick Fang Stab|Sideways Leap|Web Pellet|Leg Hook Trip|Double Fang Snap|Low Skitter Rush|Defensive Curl|Rear Leg Kick',
'Left Scythe Cut|Right Scythe Cut|Cross Scythe Combo|Leaping Pierce|Parry Riposte|Antenna Threat|Low Scythe Sweep|Double Overhead Cut',
'Scrap Fist Jab|Metal Backhand|Arm Burst Brace|Scrap Throw Pose|Low Ram|Shock Discharge|Two Hit Scrap Combo|Defensive Vent',
'Claw Jab|Blood Spit|Leaping Scratch|Horn Jab|Double Claw Rake|Crouched Cast|Tail Feint|Angry Stomp',
'Quick Fin Dash|Side Bite|Tailfin Slap|Dive And Return|Surface Snap|Rolling Bite|Territorial Circle|Forward Jaw Lunge',
'Spore Release|Root Slap|Cap Headbutt|Branch Jab|Root Trip|Spore Guard|Low Root Sweep|Seed Throw Pose',
'Sonic Pulse|Airborne Bite|Left Wing Slap|Right Wing Slap|Talon Dive|Backward Flutter|Hanging Snap|Swoop And Rise',
'Left Claw Crush|Right Claw Crush|Double Claw Clamp|Shell Brace|Sideways Charge|Claw Uppercut|Ground Claw Scrape|Shell Slam',
'Pulse Charge|Pulse Release|Spectral Swipe|Orbital Swoop|Tendril Reach|Blink Arrival Pose|Spiral Ascend|Dissipation Fall']
COMMON=['Idle_Breathe','Locomotion_Walk','Locomotion_Run','Turn_Left','Turn_Right','Dodge_Left','Dodge_Right','Hit_Front','Hit_Back','Stagger','Death','Threat_Roar']

def pulse(t,a,b):
 if t<=a or t>=b:return 0
 return math.sin(math.pi*(t-a)/(b-a))**2

def rot(pb,axis,value):pb.rotation_euler[axis]+=value

def apply_primitive(rig,kind,amp,t,phase,side):
 p=pulse(t,phase[0],phase[1]);snap=pulse(t,phase[0]+(phase[1]-phase[0])*.27,phase[1]);hold=math.sin(math.pi*max(0,min(1,(t-phase[0])/(phase[1]-phase[0])))) if phase[0]<t<phase[1] else 0
 for pb in rig.pose.bones:
  n=pb.name;left=n.endswith('L') or 'L_' in n;sgn=-1 if left else 1
  if kind=='bite':
   if n in ('neck1','neck2','head'):rot(pb,0,-amp*p*(.5 if n=='head' else .25))
   if n=='jaw':rot(pb,0,amp*(p-.7*snap))
   if n=='root':pb.location+=Vector((0,0,0))
  elif kind=='sweep':
   if n in ('chest','neck1','neck2'):rot(pb,1,side*amp*p*.45)
   if n.startswith('tail'):rot(pb,2,side*amp*p*.25)
   if n.startswith('arm'):rot(pb,1,side*amp*p*(.7 if 'fore' in n else .5))
  elif kind=='slam':
   if n=='chest':rot(pb,0,-amp*p*.35+amp*snap*.7)
   if n.startswith('arm'):rot(pb,0,-amp*p+amp*snap*.8)
   if n.startswith('front'):rot(pb,0,amp*p*.4)
  elif kind=='cast':
   if n=='neck1':rot(pb,0,-amp*p*.4)
   if n=='jaw':rot(pb,0,amp*p*.55)
   if n.startswith('arm'):rot(pb,0,-amp*p*.65);rot(pb,2,sgn*amp*p*.25)
   if n.startswith('wing'):rot(pb,0,sgn*amp*p*.25)
  elif kind=='lunge':
   if n in ('chest','neck1'):rot(pb,0,amp*(p*.35-snap*.7))
   if n.startswith(('hind','front','leg')):rot(pb,0,amp*p*(.6 if 'shin' not in n else -.4))
  elif kind=='guard':
   if n=='chest':rot(pb,0,amp*p*.12)
   if n.startswith('arm'):rot(pb,0,-amp*p*.55);rot(pb,2,-sgn*amp*p*.55)
   if n.startswith('wing'):rot(pb,1,-sgn*amp*p*.4)
   if n.startswith(('leg','hind')):rot(pb,0,amp*p*.25)
  elif kind=='wing':
   if n.startswith('wing'):rot(pb,1,sgn*amp*math.sin((t-phase[0])*math.pi*4)*p)
   if n in ('chest','neck1'):rot(pb,0,amp*p*.12)
  elif kind=='coil':
   if n.startswith('tail'):rot(pb,2,side*amp*p*.4)
   if n in ('chest','pelvis','neck1'):rot(pb,1,side*amp*p*.25)
  elif kind=='jab':
   if n.startswith('arm') and ((side<0)==left):rot(pb,0,-amp*p*.8);rot(pb,1,amp*snap*.4)
   if n=='head':rot(pb,0,amp*p*.20)
   if n=='chest':rot(pb,1,side*amp*p*.25)
  elif kind=='stomp':
   if n.startswith('hind') and ((side<0)==left):rot(pb,0,-amp*p*.5+amp*snap*.35)
   if n=='chest':rot(pb,0,amp*p*.20)
   if n.startswith('leg') and int(n[3:].split('_')[0])%2==(0 if side<0 else 1):rot(pb,0,amp*p*.5)
  elif kind=='rise':
   if n=='chest':rot(pb,0,-amp*p*.6)
   if n in ('neck1','neck2'):rot(pb,0,amp*p*.2)
   if n.startswith('arm'):rot(pb,0,-amp*p*.5)
  elif kind=='shake':
   if n in ('head','neck1'):rot(pb,1,math.sin(t*math.pi*14)*amp*p*.2)
   if n=='jaw':rot(pb,0,amp*p*.3)

def choose_recipe(label,i,creature):
 s=label.lower()
 if any(x in s for x in ['bite','fang','jaw','snap','maw']):a='bite'
 elif any(x in s for x in ['wing','flutter','swoop','dive','flight','talon']):a='wing'
 elif any(x in s for x in ['cast','spit','pulse','breath','exhale','release','vent','volley','toll','discharge','spore','summon','inhale','screech','howl']):a='cast'
 elif any(x in s for x in ['guard','brace','parry','curl']):a='guard'
 elif any(x in s for x in ['stomp','kick','trip']):a='stomp'
 elif any(x in s for x in ['sweep','cut','cleave','rake','scythe','reap','slap','swipe']):a='sweep'
 elif any(x in s for x in ['coil','spiral','circle','constriction']):a='coil'
 elif any(x in s for x in ['slam','smash','crush','execution','uppercut','downstroke']):a='slam'
 elif any(x in s for x in ['jab','punch','thrust','spear','pierce']):a='jab'
 else:a='lunge'
 secondary=['bite','sweep','slam','cast','lunge','guard','wing','coil','jab','stomp','rise','shake'][(creature.index*5+i*3)%12]
 # The action order, side, timing and magnitude are unique per creature/move.
 side=-1 if i%2==0 else 1;stagger=(creature.index%5)*.014
 return [(a,.85+(creature.index%4)*.09,(.10,.58+stagger),side),(secondary,.40+i*.04,(.43-stagger,.88),-side)]

def animate(creature):
 rig=creature.rig;scene=bpy.context.scene;scene.render.fps=30;records=[]
 actions=COMMON+[x.replace(' ','_') for x in MOVESETS[creature.index].split('|')]
 if any(n.startswith('wing') for n in creature.bones):actions+=['Flight_Takeoff','Flight_Hover','Flight_Glide','Flight_Landing']
 if creature.kind in ('fish','serpent'):actions+=['Swim_Cruise','Swim_Burst','Swim_Turn','Swim_Surface']
 for ai,name in enumerate(actions):
  spec=12<=ai<20;duration=2.0 if ai<12 else 2.15+(ai-12)*.12+(creature.index%4)*.08
  if ai==10:duration=3.0
  end=round(duration*30)+1;act=bpy.data.actions.new(name);act.use_fake_user=True;rig.animation_data.action=act
  recipe=choose_recipe(name,ai-12,creature) if spec else None
  frames=list(range(1,end+1,2))
  if frames[-1]!=end:frames.append(end)
  for f in frames:
   t=(f-1)/(end-1);wave=math.sin(t*math.tau)
   for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
   if spec:
    for kind,amp,phase,side in recipe:apply_primitive(rig,kind,amp,t,phase,side)
    # movement is encoded in the root bone, with anticipation and return.
    root=rig.pose.bones['root'];disp=Vector((0,0,0));low=name.lower()
    if any(k in low for k in ('lunge','charge','pounce','rush','leap','dash')):disp.y=-.6*pulse(t,.1,.9)
    if any(k in low for k in ('dive','leap','pounce','vault','breach','ascend')):disp.z=.55*pulse(t,.04,.87)
    if any(k in low for k in ('sidestep','sideways','feint')):disp.x=.45*(-1 if ai%2 else 1)*pulse(t,.15,.85)
    if any(k in low for k in ('kneel','buried','burrowing','curl')):disp.z=-.35*pulse(t,.1,.9)
    root.location=root.bone.matrix_local.to_3x3().inverted()@disp
   else:
    for pb in rig.pose.bones:
     n=pb.name;sgn=-1 if 'L' in n else 1
     if ai==0:
      if n=='chest':rot(pb,0,.022*wave)
      if n in ('neck1','head'):rot(pb,0,.018*wave)
     elif ai in (1,2):
      freq=1 if ai==1 else 2;amp=.30 if ai==1 else .55
      if n.startswith(('hind','front','leg')):
       phase=math.pi if ('L' in n or (n.startswith('leg') and int(n[3:].split('_')[0])%2)) else 0
       if n.startswith('front'):phase+=math.pi
       rot(pb,0,amp*sin(t*math.tau*freq+phase)*(-.7 if 'shin' in n else 1))
      if n.startswith('arm'):rot(pb,0,-sgn*amp*.6*wave)
      if n.startswith('tail'):rot(pb,2,.08*sin(t*math.tau*freq+int(n[4:])*.6))
     elif ai in (3,4):
      if n=='root':rot(pb,1,(1 if ai==3 else -1)*t*math.pi/2)
      if n=='head':rot(pb,1,(1 if ai==3 else -1)*.25*pulse(t,0,1))
     elif ai in (5,6):
      if n=='root':pb.location=pb.bone.matrix_local.to_3x3().inverted()@Vector(((1 if ai==5 else -1)*.8*pulse(t,0,1),0,.2*pulse(t,0,1)))
      if n=='chest':rot(pb,1,(1 if ai==5 else -1)*.18*pulse(t,0,1))
     elif ai in (7,8):
      if n in ('chest','neck1','head'):rot(pb,0,(1 if ai==7 else -1)*.25*math.sin(t*math.pi*3)*(1-t))
     elif ai==9:
      if n=='chest':rot(pb,0,.3*pulse(t,0,1))
      if n=='root':pb.location=pb.bone.matrix_local.to_3x3().inverted()@Vector((0,0,-.2*pulse(t,0,1)))
     elif ai==10:
      if n=='root':rot(pb,2,1.40*min(1,t*1.6));pb.location=pb.bone.matrix_local.to_3x3().inverted()@Vector((0,0,-.35*min(1,t*1.6)))
      if n=='jaw':rot(pb,0,.35*t)
     elif ai==11:
      if n=='jaw':rot(pb,0,.7*pulse(t,.12,.87))
      if n in ('neck1','neck2'):rot(pb,0,-.18*pulse(t,.05,.9))
     elif name.startswith('Flight'):
      if n.startswith('wing'):rot(pb,1,sgn*.48*math.sin(t*math.tau*2))
      if n.startswith('hind'):rot(pb,0,.6*pulse(t,0,1))
      if n=='root':
       h=1.5*t if name.endswith('Takeoff') else 1.5*(1-t) if name.endswith('Landing') else 1.5+.06*wave
       pb.location=pb.bone.matrix_local.to_3x3().inverted()@Vector((0,0,h))
      if name.endswith('Glide') and n.startswith('wing'):pb.rotation_euler=(0,sgn*.10,0)
     elif name.startswith('Swim'):
      if n.startswith('tail') or n in ('chest','head'):rot(pb,1,.20*sin(t*math.tau*(2 if name.endswith('Burst') else 1)+(int(n[4:]) if n.startswith('tail') else 0)*.5))
   for pb in rig.pose.bones:
    pb.keyframe_insert('rotation_euler',frame=f);pb.keyframe_insert('location',frame=f)
  for fc in act.fcurves:
   for kp in fc.keyframe_points:kp.interpolation='LINEAR'
  records.append({'name':name,'frames':end,'fps':30,'duration':duration,'category':'creature_specific_sequence' if spec else 'locomotion_or_reaction','loop':name in ('Idle_Breathe','Locomotion_Walk','Locomotion_Run','Flight_Hover','Flight_Glide','Swim_Cruise'),'root_motion':name.startswith(('Flight','Dodge','Turn')) or spec,'motion_recipe':recipe,'events':[{'time':round(duration*.22,3),'event':'anticipation'},{'time':round(duration*.43,3),'event':'attack_cue'},{'time':round(duration*.82,3),'event':'recovery'}] if spec else []})
 rig.animation_data.action=None
 for pb in rig.pose.bones:pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
 return records
