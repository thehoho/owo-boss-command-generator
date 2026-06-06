# Changelog

## v0.6.0-beta

### Added

- Added Image Mode for scanning OwO boss screenshots.
- Added Text Mode for pasted `wboss` output.
- Added weapon and passive icon detection using local asset images.
- Added editable detected fields for level, animal, weapon, passives, HP, and QE.
- Added image paste support from clipboard.
- Added local image browse support.
- Added portable build support with bundled assets and OCR files.
- Added icon-assisted weapon/passive selection fields.

### Improved

- Improved dark UI styling.
- Improved boss command generation workflow.
- Improved handling for duplicate passives, such as Orb passives.
- Improved asset loading for both local Python runs and PyInstaller builds.

### Known Issues

- Image Mode is still beta.
- OCR can occasionally misread small numbers, especially similar digits.
- Users should review detected level and HP values before using the generated command.

### Notes

- Text Mode is the most stable mode. (if used correctly)
- Image Mode is experimental and included for community testing.
