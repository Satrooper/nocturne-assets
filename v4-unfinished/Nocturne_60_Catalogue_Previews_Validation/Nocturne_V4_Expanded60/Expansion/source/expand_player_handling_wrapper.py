"""New actual body-and-prop handling clips using the saved grip/IK workflow."""
from pathlib import Path
import json
W=Path(__file__).resolve().parents[1];E=W/'Nocturne_Expansion_60';P=W/'Nocturne_V4_Visual_Revision'
code=(P/'source/player_handling.py').read_text()
start="P=Path(__file__).resolve().parents[1];folder=P/'player_handling';folder.mkdir(exist_ok=True)"
assert start in code
code=code.replace(start,"P=Path(__file__).resolve().parents[2];folder=Path(__file__).resolve().parents[1]/'player_handling';folder.mkdir(exist_ok=True)")
a=code.index('spec=[]');b=code.index('records=[]',a)
code=code[:a]+'''spec=[]
for key in ['Pistol','Rifle']:
 for suffix,kind,dur in [('Aim_High','Aim_Idle',2),('Aim_Low','Aim_Idle',2),('Peek_Left','Aim_Raise',1),('Peek_Right','Aim_Raise',1),('Fire_Hip' if key=='Pistol' else 'Fire_Burst3','Fire_Aimed',.8),('Crouch_Fire','Fire_Aimed',.7),('Reload_Crouched','Reload_Tactical',2.8),('Draw_LowReady','Draw',1.35),('Holster_Crouched','Holster',1.35)]:spec.append((key+'_'+suffix,key,kind,dur))
'''+code[b:]
old="t=(frame-1)/30;reset();B('Hips').location=bodyrest[B('Hips').name].to_3x3().inverted()@(wi.to_3x3()@Vector((0,0,-.065)));bpy.context.view_layer.update()"
new="t=(frame-1)/30;reset();crouch=any(v in name for v in ['Crouch','Crouched']);B('Hips').location=bodyrest[B('Hips').name].to_3x3().inverted()@(wi.to_3x3()@Vector((0,0,-.32 if crouch else -.065)));bpy.context.view_layer.update()"
assert old in code;code=code.replace(old,new)
marker="actual=solve('Right','arm',wrist,q@QR);"
addition='''if name.endswith('Aim_High'):wrist+=Vector((0,.015,.16));q=Quaternion((1,0,0),-.25)
  if name.endswith('Aim_Low'):wrist+=Vector((0,.015,-.18));q=Quaternion((1,0,0),.28)
  if name.endswith('Peek_Left'):wrist+=Vector((.12,0,.03))*math.sin(math.pi*t/dur);B('Spine2').rotation_quaternion=Quaternion((0,1,0),-.16*math.sin(math.pi*t/dur))
  if name.endswith('Peek_Right'):wrist+=Vector((-.12,0,.03))*math.sin(math.pi*t/dur);B('Spine2').rotation_quaternion=Quaternion((0,1,0),.16*math.sin(math.pi*t/dur))
  if crouch:wrist.z-=.22
  if name.endswith('Fire_Hip'):wrist+=Vector((-.10,.12,-.4));q=Quaternion((1,0,0),.05)
  if name.endswith('Fire_Burst3'):
   pulse=sum(max(0,1-abs(t-tt)/.08) for tt in [.07,.27,.47]);wrist+=Vector((0,.025*pulse,.014*pulse));q=Quaternion((1,0,0),-.12*pulse);B('Spine2').rotation_quaternion=Quaternion((1,0,0),-.024*pulse)
  if name.endswith('Draw_LowReady'):wrist+=Vector((0,.05,-.20))*ease(t,.5,dur)
  '''+marker
assert marker in code;code=code.replace(marker,addition)
marker="records=[]"
code=code.replace(marker,"records=[]",1)
code=code.replace("if kind=='Fire_Aimed':events=[{'time_s':2/30,'event':'projectile_and_muzzle_cue','bone':weapons[key]['prefix']+'muzzle','validated_damage_window':False}]","if kind=='Fire_Aimed':events=[{'time_s':tt,'event':'projectile_and_muzzle_cue','bone':weapons[key]['prefix']+'muzzle','validated_damage_window':False} for tt in ([.07,.27,.47] if name.endswith('Fire_Burst3') else [2/30])]")
dest=E/'source/player_handling_expanded.py';dest.write_text(code)
exec(compile(code,str(dest),'exec'),{'__file__':str(dest),'__name__':'__main__'})
