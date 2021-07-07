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
    "name": "Camera Wobble",
    "version": (0, 1, 0),
    "author": "Nathan Vegdahl, Ian Hubert",
    "blender": (2, 93, 0),
    "description": "Add captured camera shake/wobble to your cameras",
    "location": "Camera properties",
    # "doc_url": "",
    "category": "Animation",
}

import bpy
from bpy.types import Camera, Context
from .action_utils import action_to_python_data_text, python_data_to_loop_action, action_frame_range
from .wobble_data import WOBBLE_LIST

BASE_NAME = "CameraWobble.v2"
COLLECTION_NAME = BASE_NAME
FRAME_EMPTY_NAME = BASE_NAME + "_frame_empty"

# Maximum values of our per-camera scaling/influence properties.
INFLUENCE_MAX = 4.0
SCALE_MAX = 100.0

# The maximum supported world unit scale.
UNIT_SCALE_MAX = 1000.0


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
        row.template_list(
            listtype_name="OBJECT_UL_camera_shake_items",
            list_id="Floog",
            dataptr=camera,
            propname="camera_shakes",
            active_dataptr=camera,
            active_propname="camera_shakes_active_index",
        )
        col = row.column()
        col.operator("object.camera_shake_add", text="", icon='ADD')
        col.operator("object.camera_shake_remove", text="", icon='REMOVE')
        col.operator("object.camera_shake_move", text="", icon='TRIA_UP').type = 'UP'
        col.operator("object.camera_shake_move", text="", icon='TRIA_DOWN').type = 'DOWN'

        if camera.camera_shakes_active_index < len(camera.camera_shakes):
            shake = camera.camera_shakes[camera.camera_shakes_active_index]
            row = layout.row()
            col = row.column(align=True)
            col.alignment = 'RIGHT'
            col.use_property_split = True
            col.prop(shake, "shake_type", text="Shake")
            col.separator()
            col.prop(shake, "influence", slider=True)
            col.separator()
            col.prop(shake, "scale")
            col.separator()
            col.prop(shake, "speed")
            col.prop(shake, "offset")


class OBJECT_UL_camera_shake_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            col = layout.column()
            col.label(
                text=str(item.shake_type).replace("_", " ").title(),
                icon='FCURVE_SNAPSHOT',
            )

            col = layout.column()
            col.alignment = 'RIGHT'
            col.prop(item, "influence", text="", expand=False, slider=True, emboss=False)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


#========================================================

# Creates a camera shake setup for the given camera and
# shake item index, using the given collection to store
# shake empties.
def build_single_shake(camera, shake_item_index, collection, context):
    shake = camera.camera_shakes[shake_item_index]
    shake_data = WOBBLE_LIST[shake.shake_type]

    action_name = BASE_NAME + "_" + shake.shake_type.lower()
    shake_object_name = BASE_NAME + "_" + camera.name + "_" + str(shake_item_index)

    # Ensure the needed action exists, and fetch it.
    action = None
    if action_name in bpy.data.actions:
        action = bpy.data.actions[action_name]
    else:
        action = python_data_to_loop_action(
            shake_data[2],
            action_name,
            INFLUENCE_MAX,
            INFLUENCE_MAX * SCALE_MAX * UNIT_SCALE_MAX
        )

    # Ensure the needed shake object exists, fetch it.
    shake_object = None
    if shake_object_name in bpy.data.objects:
        shake_object = bpy.data.objects[shake_object_name]
    else:
        shake_object = bpy.data.objects.new(shake_object_name, None)

    # Make sure the shake object is linked into our collection.
    if shake_object.name not in collection.objects:
        collection.objects.link(shake_object)

    #----------------
    # Set up the constraints and drivers on the shake object.
    #----------------

    # Clear out all constraints and drivers, and fetch animation data block.
    shake_object.constraints.clear()
    shake_object.animation_data_clear()
    anim_data = shake_object.animation_data_create()

    # Some weird gymnastics needed because of a Blender bug.
    # Without first assigning an action to the animation data,
    # then on a fresh scene we won't be able to assign an action
    # to the action constraint (below).
    anim_data.action = action
    anim_data.action = None
    shake_object.location = (0,0,0)
    shake_object.rotation_euler = (0,0,0)
    shake_object.rotation_quaternion = (0,0,0,0)
    shake_object.rotation_axis_angle = (0,0,0,0)
    shake_object.scale = (1,1,1)

    # Get action info for calculations below.
    action_fps = shake_data[1]
    action_range = action_frame_range(action)
    action_length = action_range[1] - action_range[0]

    # Create the action constraint.
    constraint = shake_object.constraints.new('ACTION')
    constraint.use_eval_time = True
    constraint.mix_mode = 'BEFORE'
    constraint.action = action
    constraint.frame_start = action_range[0]
    constraint.frame_end = action_range[1]

    # Create the driver for the constraint's eval time.
    driver = constraint.driver_add("eval_time").driver
    driver.type = 'SCRIPTED'
    fps_factor = 1.0 / ((context.scene.render.fps / context.scene.render.fps_base) / action_fps)
    driver.expression = \
        "((((frame + subframe) * speed) + frame_offset) * {}) % 1.0" \
        .format(fps_factor / action_length)

    frame_var = driver.variables.new()
    frame_var.name = "frame"
    frame_var.type = 'SINGLE_PROP'
    frame_var.targets[0].id_type = 'SCENE'
    frame_var.targets[0].id = context.scene
    frame_var.targets[0].data_path = "frame_current"

    subframe_var = driver.variables.new()
    subframe_var.name = "subframe"
    subframe_var.type = 'SINGLE_PROP'
    subframe_var.targets[0].id_type = 'SCENE'
    subframe_var.targets[0].id = context.scene
    subframe_var.targets[0].data_path = "frame_subframe"

    offset_var = driver.variables.new()
    offset_var.name = "frame_offset"
    offset_var.type = 'SINGLE_PROP'
    offset_var.targets[0].id_type = 'OBJECT'
    offset_var.targets[0].id = camera
    offset_var.targets[0].data_path = 'camera_shakes[{}].offset'.format(shake_item_index)

    speed_var = driver.variables.new()
    speed_var.name = "speed"
    speed_var.type = 'SINGLE_PROP'
    speed_var.targets[0].id_type = 'OBJECT'
    speed_var.targets[0].id = camera
    speed_var.targets[0].data_path = 'camera_shakes[{}].speed'.format(shake_item_index)

    #----------------
    # Set up the constraints and drivers on the camera object.
    #----------------

    loc_constraint_name = BASE_NAME + "_loc_" + str(shake_item_index)
    rot_constraint_name = BASE_NAME + "_rot_" + str(shake_item_index)

    # Create the new constraints.
    loc_constraint = camera.constraints.new(type='COPY_LOCATION')
    rot_constraint = camera.constraints.new(type='COPY_ROTATION')
    loc_constraint.name = loc_constraint_name
    rot_constraint.name = rot_constraint_name
    loc_constraint.show_expanded = False
    rot_constraint.show_expanded = False

    # Set up location constraint.
    loc_constraint.target = shake_object
    loc_constraint.target_space = 'WORLD'
    loc_constraint.owner_space = 'LOCAL'
    loc_constraint.use_offset = True

    # Set up rotation constraint.
    rot_constraint.target = shake_object
    rot_constraint.target_space = 'WORLD'
    rot_constraint.owner_space = 'LOCAL'
    rot_constraint.mix_mode = 'AFTER'

    # Set up the location constraint driver.
    driver = loc_constraint.driver_add("influence").driver
    driver.type = 'SCRIPTED'
    driver.expression = "{} * influence * location_scale / unit_scale".format(1.0 / (UNIT_SCALE_MAX * INFLUENCE_MAX * SCALE_MAX))
    if "influence" not in driver.variables:
        var = driver.variables.new()
        var.name = "influence"
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = camera
        var.targets[0].data_path = 'camera_shakes[{}].influence'.format(shake_item_index)
    if "location_scale" not in driver.variables:
        var = driver.variables.new()
        var.name = "location_scale"
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = camera
        var.targets[0].data_path = 'camera_shakes[{}].scale'.format(shake_item_index)
    if "unit_scale" not in driver.variables:
        var = driver.variables.new()
        var.name = "unit_scale"
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = context.scene
        var.targets[0].data_path ='unit_settings.scale_length'

    # Set up the rotation constraint driver.
    driver = rot_constraint.driver_add("influence").driver
    driver.type = 'SCRIPTED'
    driver.expression = "influence * {}".format(1.0 / INFLUENCE_MAX)
    if "influence" not in driver.variables:
        var = driver.variables.new()
        var.name = "influence"
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = camera
        var.targets[0].data_path = 'camera_shakes[{}].influence'.format(shake_item_index)


# The main function that actually does the real work of this addon.
# It's called whenever anything relevant in the shake list on a
# camera is changed, and just tears down and completely rebuilds
# the camera-shake setup for it.
def rebuild_camera_shakes(camera, context):
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

    #----------------
    # First, completely tear down the current setup, if any.
    #----------------

    # Remove shake constraints from the camera.
    remove_list = []
    for constraint in camera.constraints:
        if constraint.name.startswith(BASE_NAME):
            constraint.driver_remove("influence")
            remove_list += [constraint]
    for constraint in remove_list:
        camera.constraints.remove(constraint)

    # Remove shake empties for this camera.
    for obj in collection.objects:
        if obj.name.startswith(BASE_NAME + "_" + camera.name):
            obj.constraints[0].driver_remove("eval_time")
            obj.animation_data_clear()
            bpy.data.objects.remove(obj)

    #----------------
    # Then build the new setup.
    #----------------

    for shake_item_index in range(0, len(camera.camera_shakes)):
        build_single_shake(camera, shake_item_index, collection, context)

    #----------------
    # Finally, clean up any data that's no longer needed, up to and
    # including removing the collection itself if there no shakes left.
    #----------------

    # If there's nothing left in the collection, delete it.
    if len(collection.objects) == 0:
        context.scene.collection.children.unlink(collection)
        if collection.users == 0:
            bpy.data.collections.remove(collection)

    # Delete unused actions.
    to_remove = []
    for action in bpy.data.actions:
        if action.name.startswith(BASE_NAME):
            if action.users == 0:
                to_remove += [action]
    for action in to_remove:
        bpy.data.actions.remove(action)


def on_shake_type_update(shake_instance, context):
    rebuild_camera_shakes(shake_instance.id_data, context)


#class ActionToPythonData(bpy.types.Operator):
#    """Writes the action on the currently selected object to a text block as Python data"""
#    bl_idname = "object.action_to_python_data"
#    bl_label = "Action to Python Data"
#    bl_options = {'UNDO'}
#
#    @classmethod
#    def poll(cls, context):
#        return context.active_object is not None \
#               and context.active_object.animation_data is not None \
#               and context.active_object.animation_data.action is not None
#
#    def execute(self, context):
#        action_to_python_data_text(context.active_object.animation_data.action, "action_output.txt")
#        return {'FINISHED'}


class CameraShakeAdd(bpy.types.Operator):
    """Adds the selected camera shake to the list"""
    bl_idname = "object.camera_shake_add"
    bl_label = "Add Shake Item"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'CAMERA'

    def execute(self, context):
        camera = context.active_object
        shake = camera.camera_shakes.add()
        rebuild_camera_shakes(camera, context)
        return {'FINISHED'}


class CameraShakeRemove(bpy.types.Operator):
    """Removes the selected camera shake item from the list"""
    bl_idname = "object.camera_shake_remove"
    bl_label = "Remove Shake Item"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'CAMERA' and len(obj.camera_shakes) > 0

    def execute(self, context):
        camera = context.active_object
        if camera.camera_shakes_active_index < len(camera.camera_shakes):
            camera.camera_shakes.remove(camera.camera_shakes_active_index)
            rebuild_camera_shakes(camera, context)
            if camera.camera_shakes_active_index >= len(camera.camera_shakes) and camera.camera_shakes_active_index > 0:
                camera.camera_shakes_active_index -= 1
        return {'FINISHED'}


class CameraShakeMove(bpy.types.Operator):
    """Moves the selected camera shake up/down in the list"""
    bl_idname = "object.camera_shake_move"
    bl_label = "Move Shake Item"
    bl_options = {'UNDO'}

    type: bpy.props.EnumProperty(items = [
        ('UP', "", ""),
        ('DOWN', "", ""),
    ])

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == 'CAMERA' and len(obj.camera_shakes) > 1

    def execute(self, context):
        camera = context.active_object
        index = int(camera.camera_shakes_active_index)
        if self.type == 'UP' and index > 0:
            camera.camera_shakes.move(index, index - 1)
            camera.camera_shakes_active_index -= 1
        elif self.type == 'DOWN' and (index + 1) < len(camera.camera_shakes):
            camera.camera_shakes.move(index, index + 1)
            camera.camera_shakes_active_index += 1
        rebuild_camera_shakes(camera, context)
        return {'FINISHED'}


# An actual instance of Camera shake added to a camera.
class CameraShakeInstance(bpy.types.PropertyGroup):
    shake_type: bpy.props.EnumProperty(
        name = "Shake Type",
        items = [(id, WOBBLE_LIST[id][0], "") for id in WOBBLE_LIST.keys()],
        options = set(), # Not animatable.
        override = set(), # Not library overridable.
        update = on_shake_type_update,
    )
    influence: bpy.props.FloatProperty(
        name="Influence",
        description="How much the camera shake affects the camera",
        default=1.0,
        min=0.0, max=INFLUENCE_MAX,
        soft_min=0.0, soft_max=1.0,
    )
    scale: bpy.props.FloatProperty(
        name="Scale",
        description="The scale of the shake's location component",
        default=1.0,
        min=0.0, max=SCALE_MAX,
        soft_min=0.0, soft_max=2.0,
    )
    speed: bpy.props.FloatProperty(
        name="Speed",
        description="Multiplier for how fast the shake animation plays",
        default=1.0,
        soft_min=0.0, soft_max=4.0,
        options = set(), # Not animatable.
    )
    offset: bpy.props.FloatProperty(
        name="Frame Offset",
        description="How many frames to offset the shake animation",
        default=0.0,
    )


#========================================================


def register():
    bpy.utils.register_class(CameraWobblePanel)
    bpy.utils.register_class(OBJECT_UL_camera_shake_items)
    bpy.utils.register_class(CameraShakeInstance)
    bpy.utils.register_class(CameraShakeAdd)
    bpy.utils.register_class(CameraShakeRemove)
    bpy.utils.register_class(CameraShakeMove)
    #bpy.utils.register_class(ActionToPythonData)
    #bpy.types.VIEW3D_MT_object.append(
    #    lambda self, context : self.layout.operator(ActionToPythonData.bl_idname)
    #)

    # The list of camera shakes active on an camera, along with each shake's parameters.
    bpy.types.Object.camera_shakes = bpy.props.CollectionProperty(type=CameraShakeInstance)
    bpy.types.Object.camera_shakes_active_index = bpy.props.IntProperty(name="Camera Shake List Active Item Index")


def unregister():
    bpy.utils.unregister_class(CameraWobblePanel)
    bpy.utils.unregister_class(OBJECT_UL_camera_shake_items)
    bpy.utils.unregister_class(CameraShakeInstance)
    bpy.utils.unregister_class(CameraShakeAdd)
    bpy.utils.unregister_class(CameraShakeRemove)
    bpy.utils.unregister_class(CameraShakeMove)
    #bpy.utils.unregister_class(ActionToPythonData)


if __name__ == "__main__":
    register()
