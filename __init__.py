#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

bl_info = {
    "name": "CameraWobble",
    "version": (0, 1, 0),
    "author": "Nathan Vegdahl",
    "blender": (2, 93, 0),
    "description": "Adds controllable camera shake/wobble to a camera",
    "location": "",
    "doc_url": "",
    "category": "Camera",
}

import bpy
from bpy.types import Camera, Context
from .action_utils import action_to_python_data_text, python_data_to_loop_action
from .wobble_data import WOBBLE_LIST

# Constants used in various parts of the code.
INFLUENCE_PROP = "shake_influence"  # The name of the shake influence property.
INFLUENCE_PROP_MAX = 4.0  # The maximum value the shake influence property can take.


#========================================================


class CameraWobblePanel(bpy.types.Panel):
    """Add wobble to your Cameras."""
    bl_label = "Camera Wobble"
    bl_idname = "DATA_PT_camera_wobble"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.active_object.type == 'CAMERA'

    def draw(self, context):
        layout = self.layout

        camera = context.active_object

        row = layout.row()
        row.separator_spacer()
        row.prop(camera, "camera_shake")

        if INFLUENCE_PROP in camera:
            row = layout.row()
            row.separator_spacer()
            row.prop(camera, '["{}"]'.format(INFLUENCE_PROP), text="Influence".format(camera.name), slider=True)


#========================================================

# The main function that actually does the real work of this addon.
# It's called whenever the shake type is changed on a camera.
def on_set_camera_wobble(camera_object, context):
    BASE_NAME = "CameraWobble.v1"
    wobble_name = str(camera_object.camera_shake)
    loc_constraint_name = BASE_NAME + "_location"
    rot_constraint_name = BASE_NAME + "_rotation"

    # Handle the "None" case.
    if wobble_name == 'NONE':
        if loc_constraint_name in camera_object.constraints:
            camera_object.constraints.remove(camera_object.constraints[loc_constraint_name])
        if rot_constraint_name in camera_object.constraints:
            camera_object.constraints.remove(camera_object.constraints[rot_constraint_name])
        return

    # Ensure that our camera wobble collection exists and fetch it.
    collection = None
    if BASE_NAME in context.scene.collection.children:
        collection = context.scene.collection.children[BASE_NAME]
    else:
        if BASE_NAME not in bpy.data.collections:
            collection = bpy.data.collections.new(BASE_NAME)
            collection.hide_viewport = True
            collection.hide_render = True
            collection.hide_select = True
        else:
            collection = bpy.data.collections[BASE_NAME]
        context.scene.collection.children.link(bpy.data.collections[BASE_NAME])
        for layer in context.scene.view_layers:
            if collection.name in layer.layer_collection.children:
                layer.layer_collection.children[collection.name].exclude = True

    # Ensure the needed action exists, and fetch it.
    action = None
    action_name = BASE_NAME + "_" + wobble_name.lower()
    if action_name in bpy.data.actions:
        action = bpy.data.actions[action_name]
    else:
        action = python_data_to_loop_action(WOBBLE_LIST[wobble_name], action_name, INFLUENCE_PROP_MAX)
        action.use_fake_user = False  # Just to make sure stale ones don't stick around on accident.

    # Ensure the needed empty object exists, fetch it.
    shake_object = None
    shake_object_name = BASE_NAME + "_" + wobble_name.lower()
    if shake_object_name in bpy.data.objects:
        shake_object = bpy.data.objects[shake_object_name]
    else:
        shake_object = bpy.data.objects.new(shake_object_name, None)

    # Make sure the empty object has the right action on it.
    if shake_object.animation_data == None:
        shake_object.animation_data_create()
    shake_object.animation_data.action = action

    # Make sure the empty object is linked into our collection.
    if shake_object.name not in collection.objects:
        collection.objects.link(shake_object)

    # Ensure the camera has the needed custom properties.
    if INFLUENCE_PROP not in camera_object:
        if "_RNA_UI" not in camera_object:
            camera_object["_RNA_UI"] = {}
        camera_object[INFLUENCE_PROP] = 1.0
        camera_object["_RNA_UI"][INFLUENCE_PROP] = {
            "default": 1.0,
            "min": 0.0,
            "max": INFLUENCE_PROP_MAX,
            "soft_min": 0.0,
            "soft_max": 1.0,
            "description": "How much the camera shake should affect the camera",
        }

    # Clear old constraints from camera if needed.
    # Add/remove constraints to/from the camera.
    if loc_constraint_name in camera_object.constraints:
        camera_object.constraints.remove(camera_object.constraints[loc_constraint_name])
    if rot_constraint_name in camera_object.constraints:
        camera_object.constraints.remove(camera_object.constraints[rot_constraint_name])

    # Create the new constraints.
    loc_constraint = camera_object.constraints.new(type='COPY_LOCATION')    
    rot_constraint = camera_object.constraints.new(type='COPY_ROTATION')    
    loc_constraint.name = loc_constraint_name
    rot_constraint.name = rot_constraint_name

    # Set up location constraint.
    loc_constraint.target = shake_object
    loc_constraint.target_space = 'WORLD'
    loc_constraint.owner_space = 'LOCAL'
    loc_constraint.use_offset = True
    loc_constraint.influence = 1.0 / INFLUENCE_PROP_MAX

    # Set up rotation constraint.
    rot_constraint.target = shake_object
    rot_constraint.target_space = 'WORLD'
    rot_constraint.owner_space = 'LOCAL'
    rot_constraint.mix_mode = 'AFTER'
    rot_constraint.influence = 1.0 / INFLUENCE_PROP_MAX

    # Set up the location constraint driver.
    driver = loc_constraint.driver_add("influence").driver
    driver.type = 'SCRIPTED'
    driver.expression = "influence * {}".format(1.0 / INFLUENCE_PROP_MAX)
    var = driver.variables.new()
    var.name = "influence"
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'OBJECT'
    var.targets[0].id = camera_object
    var.targets[0].data_path ='["{}"]'.format(INFLUENCE_PROP)

    # Set up the rotation constraint driver.
    driver = rot_constraint.driver_add("influence").driver
    driver.type = 'SCRIPTED'
    driver.expression = "influence * {}".format(1.0 / INFLUENCE_PROP_MAX)
    var = driver.variables.new()
    var.name = "influence"
    var.type = 'SINGLE_PROP'
    var.targets[0].id_type = 'OBJECT'
    var.targets[0].id = camera_object
    var.targets[0].data_path ='["{}"]'.format(INFLUENCE_PROP)


class ActionToPythonData(bpy.types.Operator):
    """Writes the action on the currentl selected object to a text block as Python data"""
    bl_idname = "object.action_to_python_data"
    bl_label = "Action to Python Data"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None \
               and context.active_object.animation_data is not None \
               and context.active_object.animation_data.action is not None

    def execute(self, context):
        action_to_python_data_text(context.active_object.animation_data.action, "action_output.txt")
        return {'FINISHED'}


#========================================================


def register():
    bpy.utils.register_class(CameraWobblePanel)
    bpy.utils.register_class(ActionToPythonData)
    bpy.types.VIEW3D_MT_object.append(
        lambda self, context : self.layout.operator(ActionToPythonData.bl_idname)
    )

    # Add list of Camera shakes to object properties.
    bpy.types.Object.camera_shake = bpy.props.EnumProperty(
        name = "Camera Shake",
        items = [('NONE', 'None', "")] \
            + [(id, id.replace("_", " ").title(), "") for id in WOBBLE_LIST.keys()],
        default = 'NONE',
        update = on_set_camera_wobble,
    )

    # bpy.types.Scene.clean_blend_use_max_vert_check = bpy.props.BoolProperty(
    #     name="Use Max Vert Check",
    #     default=False,
    #     description="Use a random subset of vertices for mesh-duplicate checks.  This can make blend file cleaning faster, at the slight risk of de-duplicating meshes that aren't actually duplicates",
    # )


def unregister():
    bpy.utils.unregister_class(CameraWobblePanel)
    bpy.utils.unregister_class(ActionToPythonData)


if __name__ == "__main__":
    register()
