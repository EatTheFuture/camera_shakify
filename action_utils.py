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


def action_to_python_data(act: Action, text_block_name):
    channels = {}
    act_range = action_frame_range(act)
    for curve in act.fcurves:
        baked_keys = []
        for frame in range(int(act_range[0]), int(act_range[1]) + 1):
            baked_keys += [(frame, curve.evaluate(frame))]
        channels[curve.data_path] = baked_keys

    text = "{\n"
    for k in channels:
        text += "  \"{}\": {},\n".format(k, channels[k])
    text += "}\n"
    
    bpy.data.texts.new(text_block_name).from_string(text)


def python_data_to_action(data):
    # TODO
    pass


def action_frame_range(act: Action):
    r = [9999999999, -9999999999]
    for curve in act.fcurves:
        cr = curve.range()
        r[0] = min(r[0], cr[0])
        r[1] = max(r[1], cr[1])
    return r
