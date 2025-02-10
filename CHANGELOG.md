# Changelog


## [Unreleased]


## [0.5.0] - 2025-02-10

- Update code to work properly with the new slotted/layered Action APIs in Blender 4.4.  Otherwise functionally identical to v0.4.0.


## [0.4.0] - 2025-02-10

- Added button to prep blend files for submission to render farms.  A common issue that people ran into when working with Camera Shakify is that they would have to bake their camera animation for submission to a Render Farm, since Camera Shakify shakes don't function without the addon installed.  This button addresses this by instead creating a small auto-execute Python script in the blend file that registers the minimal types and properties needed for the shakes to function.


## [0.3.0] - 2024-10-14

### Additions

- Turned into a [Blender Extension](https://extensions.blender.org/add-ons/camera-shakify/).  No functional changes.


## [0.2.0]

To be filled out.


## [0.1.0]

To be filled out.


[Unreleased]: https://github.com/cessen/colorbox/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/cessen/colorbox/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/cessen/colorbox/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/cessen/colorbox/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/cessen/colorbox/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/cessen/colorbox/releases/tag/v0.1.0
