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


import bpy
from bpy.types import Action, Context


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

# rot_factor and loc_factor are scaling factors for rotation and
# location values, respectively.
def python_data_to_loop_action(data, action_name, rot_factor=1.0, loc_factor=1.0) -> Action:
    act = bpy.data.actions.new(action_name)
    for k in data:
        curve = act.fcurves.new(k[0], index=k[1])
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
    act.use_fake_user = False
    act.user_clear()
    return act


def action_frame_range(act: Action):
    r = [9999999999, -9999999999]
    for curve in act.fcurves:
        cr = curve.range()
        r[0] = min(r[0], cr[0])
        r[1] = max(r[1], cr[1])
    return r
