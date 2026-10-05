from pathlib import Path
import struct,json,os
P=Path(__file__).resolve().parents[1];report=[]
for f in [x for cat in ['dragons','bosses','enemies'] for x in (P/cat).glob('*/*.glb')]:
 raw=f.read_bytes();off=12;chunks=[]
 while off<len(raw):
  n,t=struct.unpack_from('<II',raw,off);chunks.append((t,raw[off+8:off+8+n]));off+=8+n
 d=json.loads(next(b for t,b in chunks if t==0x4e4f534a));animated={c['target'].get('node') for a in d.get('animations',[]) for c in a.get('channels',[])};joints={j for s in d.get('skins',[]) for j in s['joints']};helpers={i for i,n in enumerate(d.get('nodes',[])) if n.get('name','').startswith('Icosphere') and 'mesh' in n and 'skin' not in n and not n.get('children') and i not in animated and i not in joints}
 if not helpers:continue
 for sc in d.get('scenes',[]):sc['nodes']=[n for n in sc.get('nodes',[]) if n not in helpers]
 for n in d['nodes']:
  if 'children' in n:n['children']=[c for c in n['children'] if c not in helpers]
 js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);outchunks=[(t,js if t==0x4e4f534a else b) for t,b in chunks];out=struct.pack('<III',0x46546c67,2,12+sum(8+len(b) for t,b in outchunks))+b''.join(struct.pack('<II',len(b),t)+b for t,b in outchunks)
 with f.open('wb') as h:h.write(out);h.flush();os.fsync(h.fileno())
 report.append({'file':str(f.relative_to(P)),'helpers_excluded_from_runtime_scene':[d['nodes'][i]['name'] for i in helpers],'geometry_joint_animation_indices_preserved':True})
(P/'audit/Runtime_Display_Helper_Removal.json').write_text(json.dumps(report,indent=2));print('REMOVED_RUNTIME_DISPLAY_HELPERS',len(report),flush=True)
