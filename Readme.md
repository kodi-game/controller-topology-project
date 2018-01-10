# Kodi Game Controller Add-ons

Kodi has controller profiles for each systems it supports. Add-ons consist of several files:

1. **addon.xml** - the add-on fluff

2. **layout.png** - the picture shown in the configuration GUI

3. **mask.png** - optional, the button mask of layout.png

3. **icon.png** - the thumbnail used in the GUI

4. **layout.xml** - the button layout

6. **strings.po** - The names of the buttons

## addon.xml

This schema is described by Kodi's add-on system. It includes:

1. Controller ID (identical to add-on ID)
2. Metadata version
3. Controller name
4. Internationalized controller name
5. Internationalized 2-3 sentence description including release year
6. Path to icon.png
7. Path to layout.xml
8. Image credit

Metadata version uses semantic versioning (MAJOR.MINOR.PATCH). Increment the:

1. MAJOR version when you make incompatible schema changes
2. MINOR version when you make schema changes in a backwards-compatible manner, and
3. PATCH version when you make data changes.

## layout.png

Transparent image of the controller. Recommended size 1024x1024.

## mask.png

Unused currently. Same dimensions as layout.png.

Possible use of this is to [generate a costmap for automatic line placement](https://forum.kodi.tv/showthread.php?tid=211138&pid=1932869#pid1932869).

## icon.png

Opaque image of the controller. This should be the transparent image against [background.png](https://github.com/kodi-game/kodi-game-controllers/blob/master/textures/background.png) in the `textures` folder. Recommended size 512x512 as per Kodi add-on rules.

## layout.xml

This file describes the button layout. The root `<layout>` tag contains the following attributes:

1. Path to layout.png
2. Path to mask.png

### Button layout

The button layout is given by `<category>` tags. Categories are groups for buttons shown in the controller mapping window. Categories have the following attributes defined in [categories.po](https://github.com/kodi-game/kodi-game-controllers/blob/master/categories.po):

1. Category name
2. Internationalized name
3. Category description
4. Kodi string ID

Categories contain a list of features. Each feature has the following attributes:

1. Feature name
2. Internationalized name
3. Feature type
4. Input type (analog or digital, defaults to analog)

The following feature types are available:

* `button`
* `analogstick`
* `accelerometer`
* `motor`
* `relpointer`
* `abspointer`
* `wheel`
* `throttle`
* `key`

Buttons must provide a `type` attribute to specify analog or digital input.

Keys must provide a `keycode` attribute to facilitate keyboard mapping.

## strings.po

This file contains the internationalized versions of the translatable strings above. Its format is described by Kodi's translation system.
