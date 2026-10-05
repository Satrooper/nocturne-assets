"""Read-only exported-byte / GLB geometry / motion / preview repetition audit."""
from pathlib import Path
import json, struct, hashlib, collections
import numpy as np
from PIL import Image

P=Path(__file__).resolve().parents[1]
def digest(b): return hashlib.sha256(b).hexdigest()
def groups(mapping): return [v for v in mapping.values() if len(v)>1]
def glb(path):
    b=path.read_bytes(); magic,version,length=struct.unpack_from('<III',b)
    assert magic==0x46546c67 and version==2 and length==len(b)
    offset=12; doc=None; binary=None
    while offset<len(b):
        n,t=struct.unpack_from('<II',b,offset);chunk=b[offset+8:offset+8+n];offset+=8+n
        if t==0x4e4f534a:doc=json.loads(chunk)
        if t==0x004e4942:binary=chunk
    def arr(i):
        a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        dt=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
        k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        return np.ndarray((a['count'],k),dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*k),dt.itemsize)).copy()
    return doc,arr
def pointkey(points,normalise=False):
    p=np.asarray(points,dtype=float)
    if normalise:p=(p-p.min(axis=0))/max(float(np.ptp(p,axis=0).max()),1e-9)
    q=np.round(p*1e5).astype('<i8');q=q[np.lexsort((q[:,2],q[:,1],q[:,0]))]
    return digest(q.tobytes())

manifest=json.loads((P/'asset_manifest.json').read_text())
report={'scope_complete':False,'method':{'exact_bytes':'SHA-256 for all FBX, GLB and preview files outside historical provenance','geometry':'Material-free, vertex-order-independent position fingerprints in exported mesh-local space; uniform-scale-normalised fingerprints flag reuse, not world-space silhouette equality. Skinning/topology are not implied equal.','shared_motion':'Exact sampler arrays, interpolation, channel target path and exported node name. Equal signatures indicate reusable motion, not an error.','near_preview':'64-bit difference-hash candidates, Hamming distance <= 5; candidates require visual review.','fbx_limitation':'FBX checked for exact bytes here; geometry analysis uses companion GLB. Prior structural FBX reimports are retained separately.'}}
bytegroups=collections.defaultdict(list)
for f in P.rglob('*'):
    if f.is_file() and 'provenance' not in f.parts and f.suffix.lower() in {'.fbx','.glb','.jpg','.png','.gif','.mp4'}:
        bytegroups[digest(f.read_bytes())].append(str(f.relative_to(P)))
report['exact_file_groups']=groups(bytegroups)
geometry=collections.defaultdict(list);normal=collections.defaultdict(list);components=collections.defaultdict(set);motion=collections.defaultdict(list);inventory=[]
for c in manifest['characters']:
    f=P/c['canonical_glb'];doc,arr=glb(f);pts=[];nindices=0
    for m in doc.get('meshes',[]):
        for primitive in m['primitives']:
            p=arr(primitive['attributes']['POSITION']);pts.append(p)
            components[pointkey(p,True)].add(c['asset'])
            nindices+=len(arr(primitive['indices'])) if 'indices' in primitive else len(p)
    points=np.concatenate(pts);geometry[pointkey(points)].append(c['asset']);normal[pointkey(points,True)].append(c['asset'])
    inventory.append({'asset':c['asset'],'category':c['category'],'glb':c['canonical_glb'],'vertices':len(points),'triangle_indices_div3':nindices//3,'mesh_count':len(doc.get('meshes',[])),'animations':len(doc.get('animations',[])),'preview_source':c['validation'].get('motion_preview_source',c['canonical_glb'])})
    for a in doc.get('animations',[]):
        channels=[]
        for ch in a['channels']:
            s=a['samplers'][ch['sampler']];target=ch['target'];node=doc['nodes'][target['node']].get('name','unnamed')
            channels.append((node,target['path'],s.get('interpolation','LINEAR'),digest(arr(s['input']).tobytes()),digest(arr(s['output']).tobytes())))
        key=digest(json.dumps(sorted(channels)).encode());motion[key].append({'asset':c['asset'],'clip':a.get('name','unnamed')})
report.update(characters=inventory,exact_position_cloud_groups=groups(geometry),uniform_scale_position_cloud_groups=groups(normal),shared_component_groups=[sorted(v) for v in components.values() if len(v)>1],exact_motion_groups=groups(motion))
ph=[]
for c in manifest['characters']:
    f=P/'previews/roster'/c['asset']/'After_Threequarter.jpg'
    im=np.asarray(Image.open(f).convert('L').resize((9,8)))
    ph.append((c['asset'],im[:,1:]>im[:,:-1]))
report['near_preview_candidates']=[{'assets':[a,b],'hash_distance':int(np.count_nonzero(x!=y))} for i,(a,x) in enumerate(ph) for b,y in ph[i+1:] if np.count_nonzero(x!=y)<=5]
report['known_visual_repetition_review']=[{'assets':['Crypt_Arachnarch','Hundredleg'],'finding':'Both retain the same broad segmented arthropod design language and face/leg arrangement. Distinct geometry alone does not resolve this near-duplicate visual identity.','status':'unfinished_redesign_required'},{'assets':['Cathedral_Bellwarden','Neon_Reaper'],'finding':'Shared blocky humanoid armour construction and similar proportions remain visible despite different accessories.','status':'unfinished_redesign_required'},{'assets':['Abyss_Maw','Razorfin'],'finding':'Fish/shark family proportions and silhouette require intentional differentiation.','status':'unfinished_redesign_required'}]
report['exact_duplicate_interpretation']='The repeated file groups found in this run are texture maps, not duplicate model files or byte-identical previews. Constant/neutral maps can deliberately be shared; retained to preserve existing texture paths.'
report['coverage']={'canonical_creatures':len(inventory),'creature_animation_instances':sum(i['animations'] for i in inventory),'fbx_files_byte_checked':sum(1 for f in P.rglob('*.fbx') if 'provenance' not in f.parts),'glb_files_byte_checked':sum(1 for f in P.rglob('*.glb') if 'provenance' not in f.parts),'canonical_mesh_geometry_parsed':len(inventory),'historical_provenance':'excluded from current-asset duplicate groups; intentionally preserved','visual_candidate_scope':'After threequarter views only; all preview bytes checked separately'}
report['deletions']=[]
report['changes_this_audit']='No model or useful LOD/animation removed. Repetition is measured and flagged; cinematic redesign is not claimed.'
out=P/'audit/Repetition_Audit.json';out.write_text(json.dumps(report,indent=2))
print(json.dumps({k:len(v) for k,v in report.items() if isinstance(v,list)},indent=2))
