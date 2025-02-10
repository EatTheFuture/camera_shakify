#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

import math

import bpy
from bpy.types import Action, ActionSlot, Context


# TODO: update this function to work with slotted actions.  This is only used
# when exporting actions as new shakes, and is never run for end users, so I've
# left it as-is for now.  We can update it when we actually need to use it.
def action_to_python_data_text(act: Action, text_block_name):
    channels = {}
    act_range = action_frame_range(act)
    for curve in act.fcurves:
        baked_keys = []
        for frame in range(int(act_range[0]), int(act_range[1]) + 1):
            baked_keys += [(frame, curve.evaluate(frame))]
        channels[(curve.data_path, curve.array_index)] = baked_keys

    text = "{\n"
    for k in channels:
        text += "  {}: [".format(k)
        for point in channels[k]:
            text += "({}, {:.6f}), ".format(point[0], point[1])
        text += "],\n"
    text += "}\n"
    
    return bpy.data.texts.new(text_block_name).from_string(text)

# Ensure that an Action with the given name exists, and that it has a layer and
# a keyframe strip.
def ensure_action(action_name) -> Action:
    # Ensure the action exists.
    #
    # The song-and-dance here is to make sure we get a *local* action, not a
    # library-linked action.
    action = None
    for act in bpy.data.actions:
        if act.name == action_name and act.library == None:
            action = act
            break
    if action == None:
        action = bpy.data.actions.new(action_name)
        action.use_fake_user = False

    # Ensure there's at least one layer.
    if len(action.layers) > 0:
        layer = action.layers[0]
    else:
        layer = action.layers.new("Layer")

    # Ensure there's a keyframe strip.
    if len(layer.strips) > 0:
        assert(layer.strips[0].type == 'KEYFRAME')
    else:
        layer.strips.new(type='KEYFRAME')

    return action


# Ensures that a shake with the given name exists as a slot in the given action.
#
# If it doesn't exist, it will be created from the passed `data`.
#
# rot_factor and loc_factor are scaling factors for rotation and location
# values, respectively.
#
# Returns the slot in the action corresponding to the shake.
def ensure_shake_in_action(shake_name, action: Action, data, rot_factor=1.0, loc_factor=1.0) -> ActionSlot:
    slot_identifier = "OB" + shake_name

    # Ensure a slot for the shake exists.
    if slot_identifier in action.slots:
        slot = action.slots[slot_identifier]
    else:
        slot = action.slots.new('OBJECT', shake_name)
    assert(slot.identifier == slot_identifier)

    # If there's already a channelbag for the slot, we assume it's filled with
    # the correct shake animation.
    if action.layers[0].strips[0].channelbag(slot) != None:
        return slot

    # Create channelbag and fill it in with the shake data.
    channelbag = action.layers[0].strips[0].channelbags.new(slot)
    for k in data:
        curve = channelbag.fcurves.new(k[0], index=k[1])
        curve.keyframe_points.add(len(data[k]))
        for i in range(len(data[k])):
            co = [data[k][i][0], data[k][i][1]]
            if k[0].startswith("rotation"):
                co[1] *= rot_factor
            if k[0].startswith("location"):
                co[1] *= loc_factor

            curve.keyframe_points[i].co = co
            curve.keyframe_points[i].handle_left_type = 'AUTO'
            curve.keyframe_points[i].handle_right_type = 'AUTO'
        curve.keyframe_points[-1].co[1] = curve.keyframe_points[0].co[1] # Ensure looping.
        curve.modifiers.new('CYCLES')
        curve.update()

    return slot


def action_slot_frame_range(action: Action, slot: ActionSlot):
    channelbag = action.layers[0].strips[0].channelbag(slot)

    r = [9999999999, -9999999999]
    for curve in channelbag.fcurves:
        cr = curve.range()
        r[0] = min(r[0], cr[0])
        r[1] = max(r[1], cr[1])

    # Ensure integer values.
    r[0] = math.floor(r[0])
    r[1] = math.ceil(r[1])

    return r
