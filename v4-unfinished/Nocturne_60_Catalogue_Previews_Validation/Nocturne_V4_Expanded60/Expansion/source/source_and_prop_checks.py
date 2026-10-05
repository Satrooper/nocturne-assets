import bpy,json,math,struct,zlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P.parent;receipts=[]
for f in sorted(P.rglob('*.blend')):
    bpy.ops.wm.open_mainfile(filepath=str(f));images=[]
    for im in bpy.data.images:
        if im.packed_file:
            data=bytes(im.packed_file.data)
            if data.startswith(b'\x89PNG'):
                off=8;raw=b''
                while off+12<=len(data):
                    n=struct.unpack_from('>I',data,off)[0];typ=data[off+4:off+8];chunk=data[off+8:off+8+n];assert off+n+12<=len(data);assert zlib.crc32(typ+chunk)==struct.unpack_from('>I',data,off+8+n)[0]
                    if typ==b'IDAT':raw+=chunk
                    off+=12+n
                assert off==len(data);zlib.decompress(raw)
            images.append({'name':im.name,'packed':True,'bytes':len(data)})
        elif im.source=='FILE':images.append({'name':im.name,'packed':False,'path':im.filepath,'exists':Path(bpy.path.abspath(im.filepath)).exists()})
    assert all(i.get('packed') or i.get('exists') for i in images)
    receipts.append({'file':str(f.relative_to(P)),'source_open_passed':True,'texture_checks':images,'bones':sum(len(o.data.bones) for o in bpy.context.scene.objects if o.type=='ARMATURE'),'actions':len(bpy.data.actions)});(P/'audit/Editable_Source_Validation.json').write_text(json.dumps(receipts,indent=2));print('SOURCE_CHECK',f.parent.name,flush=True)
helper=(P/'source/validate_render_expansion.py').read_text().split('for row in rows:')[0];exec(compile(helper,'studio_helpers','exec'))
other=[]
for f in sorted(list((P/'weapons').glob('*/*.glb'))+list((P/'player_handling').glob('*.glb'))+list((P/'player_animation').glob('*.glb'))):
    r,meshes,lo,hi=load(f);record={'file':str(f.relative_to(P)),'glb_reimport_passed':True,'glb_clips':len(bpy.data.actions),'glb_bones':len(r.data.bones)}
    if 'weapons' in f.parts:
        folder=P/'previews/weapons'/f.parent.name;folder.mkdir(parents=True,exist_ok=True);sc,cam,center,extent=studio(lo,hi);pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
        aim(cam,center,extent,(1,-1,.35),pts);sc.render.filepath=str(folder/'Threequarter.jpg');bpy.ops.render.render(write_still=True)
    fbx=f.with_suffix('.fbx');r,m,lo,hi=load(fbx);record['fbx_reimport_passed']=True;record['fbx_clips']=len(bpy.data.actions);record['fbx_bones']=len(r.data.bones);other.append(record)
(P/'audit/Player_Weapon_FBX_GLB_Checks.json').write_text(json.dumps(other,indent=2));print('SOURCES_AND_PROPS_COMPLETE',len(receipts),len(other),flush=True)
