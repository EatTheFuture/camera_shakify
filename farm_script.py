# Code for managing a blend-file-local script that registers the minimal types
# and properties needed for Camera Shakify shakes to animate even without Camera
# Shakify installed. Useful mainly for submitting files to render farms.

import bpy

FARM_SCRIPT_NAME = "camera_shakify_init.py"

FARM_SCRIPT_CONTENTS = """\
import bpy

class CameraShakeInstance(bpy.types.PropertyGroup):
    # Don't include the shake type in this stand-in version of the class, as it's not necessary
    # for the shakes to animate (only for managing the shakes), and it would require including
    # a bunch more cruft in this script.
    #
    # shake_type: bpy.props.EnumProperty(
    #     name = "Shake Type",
    #     items = [(id, SHAKE_LIST[id][0], "") for id in SHAKE_LIST.keys()],
    #     options = set(), # Not animatable.
    #     override = set(), # Not library overridable.
    #     update = on_shake_type_update,
    # )

    influence: bpy.props.FloatProperty(
        name="Influence",
        description="How much the camera shake affects the camera",
        default=1.0,
        min=0.0, max={influence_max},
        soft_min=0.0, soft_max=1.0,
    )
    scale: bpy.props.FloatProperty(
        name="Scale",
        description="The scale of the shake's location component",
        default=1.0,
        min=0.0, max={scale_max},
        soft_min=0.0, soft_max=2.0,
    )
    use_manual_timing: bpy.props.BoolProperty(
        name="Manual Timing",
        description="Manually animate the progression of time through the camera shake animation",
        default=False,
    )
    time: bpy.props.FloatProperty(
        name="Time",
        description="Current time (in frame number) of the shake animation",
        default=0.0,
        precision=1,
        step=100.0,
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
        precision=1,
        step=100.0,
    )

if __name__ == "__main__":
    # Only register the property if it doesn't already exist.  This is to guard against replacing
    # the property with the stand-in class when the real one from the addon already exists.
    if not hasattr(bpy.types.Object, "camera_shakes"):
        bpy.utils.register_class(CameraShakeInstance)
        bpy.types.Object.camera_shakes = bpy.props.CollectionProperty(type=CameraShakeInstance)
"""


def ensure_farm_script(influence_max, scale_max):
    # Get existing script if it exists, or create it otherwise.
    if FARM_SCRIPT_NAME in bpy.data.texts:
        script = bpy.data.texts[FARM_SCRIPT_NAME]
    else:
        script = bpy.data.texts.new(FARM_SCRIPT_NAME)

    script.clear()
    script.write(FARM_SCRIPT_CONTENTS.format(influence_max = influence_max, scale_max = scale_max))

    # Make sure it doesn't get garbage collected.
    script.use_fake_user = True

    # Mark for auto-execute on file load.
    script.use_module = True
