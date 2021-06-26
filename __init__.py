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


# This is the main function that is executed by the operator.
def add_wobble(camera: Camera, wobble_id):
    # TODO
    print("Add Wobble: ", camera, wobble_id)


    # TODO
def remove_wobble(camera: Camera, wobble_id):
    print("Remove Wobble: ", camera, wobble_id)


#========================================================


class CameraWobblePanel(bpy.types.Panel):
    """Add wobble to your Cameras."""
    bl_label = "Camera Wobble"
    bl_idname = "DATA_PT_camera_wobble"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        row = layout.row()
        row.operator("object.add_camera_wobble")
        row.operator("object.remove_camera_wobble")


class AddCameraWobble(bpy.types.Operator):
    """Add the selected camera-wobble to the selected camera"""
    bl_idname = "object.add_camera_wobble"
    bl_label = "Add Wobble"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'CAMERA'

    def execute(self, context):
        add_wobble(context.active_object, None)
        return {'FINISHED'}


class RemoveCameraWobble(bpy.types.Operator):
    """Remove the selected camera-wobble from the selected camera"""
    bl_idname = "object.remove_camera_wobble"
    bl_label = "Remove Wobble"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'CAMERA'

    def execute(self, context):
        remove_wobble(context.active_object, None)
        return {'FINISHED'}


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
    bpy.utils.register_class(AddCameraWobble)
    bpy.utils.register_class(RemoveCameraWobble)
    bpy.utils.register_class(ActionToPythonData)
    bpy.types.VIEW3D_MT_object.append(
        lambda self, context : self.layout.operator(ActionToPythonData.bl_idname)
    )

    # bpy.types.Scene.clean_blend_use_max_vert_check = bpy.props.BoolProperty(
    #     name="Use Max Vert Check",
    #     default=False,
    #     description="Use a random subset of vertices for mesh-duplicate checks.  This can make blend file cleaning faster, at the slight risk of de-duplicating meshes that aren't actually duplicates",
    # )


def unregister():
    bpy.utils.unregister_class(CameraWobblePanel)
    bpy.utils.unregister_class(AddCameraWobble)
    bpy.utils.unregister_class(RemoveCameraWobble)
    bpy.utils.unregister_class(ActionToPythonData)


if __name__ == "__main__":
    register()
