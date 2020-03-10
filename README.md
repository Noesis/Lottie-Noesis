# Lottie-Noesis

Lottie-Noesis renders [Adobe AfterEffects](https://www.adobe.com/products/aftereffects.html) animations using [NoesisGUI](https://www.noesisengine.com/). Noesis now offers a **Python** script to import JSON animations derived from [Bodymovin](https://github.com/airbnb/lottie-web) plugin for After Effects. It can be used on any platform compatible with NoesisGUI like desktop, mobile, consoles and web.

![GIF](https://github.com/Noesis/Noesis.github.io/blob/master/NoesisGUI/Lottie/GIF.gif)
![GIF](https://github.com/Noesis/Noesis.github.io/blob/master/NoesisGUI/Lottie/GIF3.gif)

## Requirements
* NoesisGUI 3.0+ is needed
* Compatible with C++ SDK, C# SDK, Unity and Unreal Engine
* Python 2.7
* JSON files exported with Bodymovin 5.6.1+

## Getting Started

Use the Python script to convert from .json to .xaml:

```
usage: json2xaml.py [-h] [--version] [--debug] json_file xaml_file
```

## Features supported

| **Shapes** | Supported |
|:--|:-:|
| Shape |                         👍
| Ellipse |                       👍
| Rectangle |                     👍
| Rounded Rectangle |             👍
| Polystar |                      ⛔️
| Group |                         👍
| Repeater |                      ⛔️
| Trim Path (individually) |      👍
| Trim Path (simultaneously) |    ⛔️
| **Fills**
| Color |                         👍
| Opacity |                       👍
| Fill Rule |                     👍
| Radial Gradient |               👍
| Linear Gradient |               👍
| **Strokes**
| Color |                         👍
| Opacity |                       👍
| Width |                         👍
| Line Cap |                      👍
| Line Join |                     👍
| Miter Limit |                   👍
| Dashes |                        👍
| Gradient |                      👍
| **Transforms**
| Position |                      👍
| Position (separated X/Y) |      👍
| Scale |                         👍
| Rotation |                      👍
| Anchor Point |                  👍
| Opacity |                       👍
| Parenting |                     👍
| Auto Orient |                   ⛔️
| Skew |                          ⛔️
| **Interpolation**
| Linear Interpolation |          👍
| Bezier Interpolation |          ⛔️
| Hold Interpolation |            👍
| Spatial Bezier Interpolation |  👍
| Rove Across Time |              ⛔️
| **Masks**
| Mask Path |                     ⛔️
| Mask Opacity |                  ⛔️
| Add |                           ⛔️
| Subtract |                      ⛔️
| Intersect |                     ⛔️
| Lighten |                       ⛔️
| Darken |                        ⛔️
| Difference |                    ⛔️
| Expansion |                     ⛔️
| Feather |                       ⛔️
| **Mattes**
| Alpha Matte |                   ⛔️
| Alpha Inverted Matte |          ⛔️
| Luma Matte |                    ⛔️
| Luma Inverted Matte |           ⛔️
| **Merge Paths**
| Merge |                         ⛔️
| Add |                           ⛔️
| Subtract |                      ⛔️
| Intersect |                     ⛔️
| Exclude Intersection |          ⛔️
| **Layer Effects**
| Fill |                          ⛔️
| Stroke |                        ⛔️
| Tint |                          ⛔️
| Tritone |                       ⛔️
| Levels Individual Controls |    ⛔️
| **Text** |
| Glyphs |                        ⛔️
| Fonts |                         ⛔️
| Transform |                     ⛔️
| Fill |                          ⛔️
| Stroke |                        ⛔️
| Tracking |                      ⛔️
| Anchor point grouping |         ⛔️
| Text Path |                     ⛔️
| Per-character 3D |              ⛔️
| Range selector (Units) |        ⛔️
| Range selector (Based on) |     ⛔️
| Range selector (Amount) |       ⛔️
| Range selector (Shape) |        ⛔️
| Range selector (Ease High) |    ⛔️
| Range selector (Ease Low)  |    ⛔️
| Range selector (Randomize order) | ⛔️
| expression selector |           ⛔️
| **Other**
| Expressions |                   ⛔️
| Images |                        ⛔️
| Precomps |                      👍
| Time Stretch |                  ⛔️
| Time remap |                    ⛔️
| Markers |                       ⛔️

## Feedback

Please use our [forums](https://forums.noesisengine.com/) for bug reports and feature requests.
