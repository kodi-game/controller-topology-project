# Kodi Game Controller Add-ons

The data in this repo is stored in the form of Kodi add-ons. This documentation describes the schema used for these add-ons.

The add-ons consist of several files:

1. **addon.xml** - the add-on fluff

2. **layout.png** - the picture shown in the configuration GUI

3. **mask.png** - optional, the button mask of layout.png

3. **icon.png** - the thumbnail used in the GUI

4. **layout.xml** - the button layout and topology

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

Possible use of this is to [generate a costmap for automatic line placement](scripts).

## icon.png

Opaque image of the controller. This should be the transparent image against [background.png](https://github.com/kodi-game/kodi-game-controllers/blob/master/textures/background.png) in the `textures` folder. Recommended size 512x512 as per Kodi add-on rules.

## layout.xml

This file describes the button layout and topology (how controllers connect to each other). The root `<layout>` tag contains the following attributes:

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

#### Buttons

Buttons must provide a `type` attribute to specify analog or digital input.

#### Keys

Keys must provide a `symbol` attribute to facilitate keyboard mapping. Symbols are hardware-independent virtual key representations. The following symbols are used:

##### ASCII keys

Symbol | Character | ASCII value
--- | --- | ---
backspace | | 8
tab | | 9
clear | | 12
return | | 13
pause | | 19
escape | | 27
space | | 32
exclaim | ! | 33
doublequote | " | 34
hash | # | 35
dollar | $ | 36
ampersand | & | 38
quote | ' | 39
leftparen | ( | 40
rightparen | ) | 41
asterisk | * | 42
plus | + | 43
comma | , | 44
minus | - | 45
period | . | 46
slash | / | 47
0 | 0 | 48
1 | 1 | 49
2 | 2 | 50
3 | 3 | 51
4 | 4 | 52
5 | 5 | 53
6 | 6 | 54
7 | 7 | 55
8 | 8 | 56
9 | 9 | 57
colon | : | 58
semicolon | ; | 59
less | < | 60
equals | = | 61
greater | > | 62
question | ? | 63
at | @ | 64
leftbracket | [ | 91
backslash | \ | 92
rightbracket | ] | 93
caret | ^ | 94
underscore | _ | 95
grave | ` | 96
a | a | 97
b | b | 98
c | c | 99
d | d | 100
e | e | 101
f | f | 102
g | g | 103
h | h | 104
i | i | 105
j | j | 106
k | k | 107
l | l | 108
m | m | 109
n | n | 110
o | o | 111
p | p | 112
q | q | 113
r | r | 114
s | s | 115
t | t | 116
u | u | 117
v | v | 118
w | w | 119
x | x | 120
y | y | 121
z | z | 122
leftbrace | [ | 123
bar | \| | 124
rightbrace | ] | 125
tilde | ~ | 126
delete | | 127

##### Symbols without ASCII characters
Symbol | Comment
--- | ---
kp0 | Numpad 0
kp1 | Numpad 1
kp2 | Numpad 2
kp3 | Numpad 3
kp4 | Numpad 4
kp5 | Numpad 5
kp6 | Numpad 6
kp7 | Numpad 7
kp8 | Numpad 8
kp9 | Numpad 9
kpperiod | Numpad .
kpdivide | Numpad /
kpmultiply | Numpad *
kpminus | Numpad -
kpplus | Numpad +
kpenter | Numpad Enter
kpequals | Numpad =
up |
down |
right |
left |
insert |
home |
end |
pageup |
pagedown |
f1 |
f2 |
f3 |
f4 |
f5 |
f6 |
f7 |
f8 |
f9 |
f10 |
f11 |
f12 |
f13 |
f14 |
f15 |
numlock |
capslock |
scrollock |
leftshift |
rightshift |
leftctrl |
rightctrl |
leftalt |
rightalt |
leftmeta |
rightmeta |
leftsuper | Left "Windows" key
rightsuper | Right "Windows" key
mode | "Alt Gr" key
compose | Multi-key compose key
help |
printscreen |
sysreq |
break |
menu |
power | Power Macintosh power key
euro | Some European keyboards
undo | Atari keyboard has Undo
oem102 | Present in some European layouts

### Topology

The topology is given by the `<physicaltopology>` tag. This allows for hubs and daisy-chaining. It describes the physical connections possible for this controller.

Controller topologies have the following properties:

1. Whether the controller provides input - true for controllers, false for hubs
2. List of ports on the device

A port contains:

1. Port ID (used in Kodi's Game API)
2. List of controllers that the port accepts

## strings.po

This file contains the internationalized versions of the translatable strings above. Its format is described by Kodi's translation system.
