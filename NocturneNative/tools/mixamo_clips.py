# Copies the curated Mixamo clips from the nocturne-assets repo into the game
# and writes Godot import settings that retarget them onto the humanoid skeleton.
import shutil, os, sys
REPO=sys.argv[1] if len(sys.argv)>1 else '/home/claude/assets-repo'
A=REPO+'/animations/'
CLIPS={
 'idle':'Pro Rifle Pack/idle aiming','walk_f':'Pro Rifle Pack/walk forward','walk_b':'Pro Rifle Pack/walk backward',
 'walk_l':'Pro Rifle Pack/walk left','walk_r':'Pro Rifle Pack/walk right','run_f':'Pro Rifle Pack/run forward',
 'run_b':'Pro Rifle Pack/run backward','run_l':'Pro Rifle Pack/run left','run_r':'Pro Rifle Pack/run right',
 'sprint':'Pro Rifle Pack/sprint forward','jump_up':'Pro Rifle Pack/jump up','jump_loop':'Pro Rifle Pack/jump loop',
 'jump_down':'Pro Rifle Pack/jump down','death_front':'Pro Rifle Pack/death from the front','death_back':'Pro Rifle Pack/death from the back',
 'reload':'Extras/Reload','hit':'Great Sword Pack/great sword impact (4)','roll':'Action Adventure Pack/falling to roll',
 'kneel':'Extras/Kneeling','fly':'Extras/Flying',
 'gs_idle':'Great Sword Pack/great sword idle','gs_run':'Great Sword Pack/great sword run','gs_walk':'Great Sword Pack/great sword walk',
 'gs_slash_1':'Great Sword Pack/great sword slash (5)','gs_slash_2':'Great Sword Pack/great sword slash (3)',
 'gs_slam':'Great Sword Pack/great sword jump attack','gs_spin':'Great Sword Pack/great sword high spin attack',
}
SKEL='''"PATH:Skeleton3D": {
"retarget/bone_map": Resource("res://assets/anim/mixamo_bonemap.tres"),
"retarget/bone_renamer/rename_bones": true,
"retarget/bone_renamer/unique_node/make_unique": true,
"retarget/bone_renamer/unique_node/skeleton_name": "GeneralSkeleton",
"retarget/rest_fixer/apply_node_transforms": true,
"retarget/rest_fixer/normalize_position_tracks": true,
"retarget/rest_fixer/overwrite_axis": true,
"retarget/rest_fixer/reset_all_bone_poses_after_import": true,
"retarget/remove_tracks/except_bone_transform": false,
"retarget/remove_tracks/unimportant_positions": true,
"retarget/remove_tracks/unmapped_bones": true
}'''
IMP='''[remap]

importer="animation_library"
importer_version=1
type="AnimationLibrary"

[params]

nodes/root_type=""
nodes/root_name=""
nodes/apply_root_scale=true
nodes/root_scale=1.0
nodes/import_as_skeleton_bones=false
nodes/use_name_suffixes=true
nodes/use_node_type_suffixes=true
meshes/ensure_tangents=false
meshes/generate_lods=false
meshes/create_shadow_meshes=false
meshes/light_baking=0
meshes/force_disable_compression=false
skins/use_named_skins=true
animation/import=true
animation/fps=60
animation/trimming=true
animation/remove_immutable_tracks=true
animation/import_rest_as_RESET=false
import_script/path=""
materials/extract=0
_subresources={
"nodes": {
%s
}
}
fbx/importer=0
fbx/allow_geometry_helper_nodes=false
fbx/embedded_image_handling=0
fbx/naming_version=2
''' % SKEL
out='assets/anim/clips'; os.makedirs(out,exist_ok=True)
credits=[]
for k,src in CLIPS.items():
    shutil.copy(A+src+'.fbx',f'{out}/{k}.fbx')
    open(f'{out}/{k}.fbx.import','w').write(IMP)
    credits.append(f'{k}: Mixamo (Adobe) "{os.path.basename(src)}"')
open(out+'/CLIPS.txt','w').write('\n'.join(credits)+'\n')
print(len(CLIPS),'clips')
