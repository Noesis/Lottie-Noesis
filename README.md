# Lottie-Noesis

Lottie-Noesis renders [Adobe AfterEffects](https://www.adobe.com/products/aftereffects.html) animations using [NoesisGUI](https://www.noesisengine.com/). Noesis now offers a **Python** script to import JSON animations derived from [Bodymovin](https://github.com/airbnb/lottie-web) plugin for After Effects. It can be used on any platform compatible with NoesisGUI like desktop, mobile, consoles and web.

Click on [Sample0](https://www.noesisengine.com/xamltoy/e4c6986363164dabcb6e0ea8d8d96265) or [Sample1](https://www.noesisengine.com/xamltoy/637ecb0c5f601da643bdaf9e855b46f8) for realtime preview in [XamlToy](https://xamltoy.noesisengine.com) (Sample animations courtesy of [lottiefiles.com](https://lottiefiles.com/))

[![GIF](https://github.com/Noesis/Noesis.github.io/blob/master/NoesisGUI/Lottie/GIF.gif)](https://www.noesisengine.com/xamltoy/e4c6986363164dabcb6e0ea8d8d96265)
[![GIF](https://github.com/Noesis/Noesis.github.io/blob/master/NoesisGUI/Lottie/GIF3.gif)](https://www.noesisengine.com/xamltoy/637ecb0c5f601da643bdaf9e855b46f8)

## Requirements
* NoesisGUI 3.0+ is needed
* Compatible with C++ SDK, C# SDK, Unity and Unreal Engine
* Python 3
* JSON files exported with Bodymovin 5.6.1+

## Getting Started

Use the Python script to convert from .json to .xaml:

```
usage: json2xaml.py [-h] [--version] [--debug] [--viewbox] [--template <key>] [--repeat <behavior>] json_file xaml_file

Converts from After Effects Bodymovin format to Noesis XAML

positional arguments:
  json_file            the JSON file to be converted from
  xaml_file            the XAML file to created

optional arguments:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
  --debug              dump layers information
  --viewbox            use Viewbox as root element
  --template <key>     import lottie as a control template resource
  --repeat <behavior>  describe how the animation repeats
```

## Usage

By default the script generates a XAML with a root *Canvas*. This is not very convenient if you need to use it from another XAML. For these cases, the argument '*--template*' can be used to generate a control template that can be used this way:

```
json2xaml.py --template lottie lottie.json lottie.xaml
```

```
<Grid
  xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <Grid.Resources>
    <ResourceDictionary Source="lottie.xaml"/>
  </Grid.Resources>
  <Control Template="{StaticResource lottie}"/>
</Grid>
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
| **Fills** | Supported |
| Color |                         👍
| Opacity |                       👍
| Fill Rule |                     👍
| Radial Gradient |               👍
| Linear Gradient |               👍
| **Strokes** | Supported |
| Color |                         👍
| Opacity |                       👍
| Width |                         👍
| Line Cap |                      👍
| Line Join |                     👍
| Miter Limit |                   👍
| Dashes |                        👍
| Gradient |                      👍
| **Transforms** | Supported |
| Position |                      👍
| Position (separated X/Y) |      👍
| Scale |                         👍
| Rotation |                      👍
| Anchor Point |                  👍
| Opacity |                       👍
| Parenting |                     👍
| Auto Orient |                   ⛔️
| Skew |                          ⛔️
| **Interpolation** | Supported |
| Linear Interpolation |          👍
| Bezier Interpolation |          👍
| Hold Interpolation |            👍
| Spatial Bezier Interpolation |  ⛔️
| Rove Across Time |              ⛔️
| **Masks** | Supported |
| Mask Path |                     👍
| Mask Opacity |                  ⛔️
| Add |                           👍
| Subtract |                      ⛔️
| Intersect |                     ⛔️
| Lighten |                       ⛔️
| Darken |                        ⛔️
| Difference |                    ⛔️
| Expansion |                     ⛔️
| Feather |                       ⛔️
| **Mattes** | Supported |
| Alpha Matte |                   ⛔️
| Alpha Inverted Matte |          ⛔️
| Luma Matte |                    ⛔️
| Luma Inverted Matte |           ⛔️
| **Merge Paths** | Supported |
| Merge |                         ⛔️
| Add |                           ⛔️
| Subtract |                      ⛔️
| Intersect |                     ⛔️
| Exclude Intersection |          ⛔️
| **Layer Effects** | Supported |
| Fill |                          ⛔️
| Stroke |                        ⛔️
| Tint |                          ⛔️
| Tritone |                       ⛔️
| Levels Individual Controls |    ⛔️
| **Text**  | Supported |
| Glyphs |                        👍
| Fonts |                         👍
| Transform |                     👍
| Fill |                          👍
| Stroke |                        👍
| Tracking |                      👍
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
| **Other** | Supported |
| Expressions |                   ⛔️
| Images |                        👍
| Precomps |                      👍
| Time Stretch |                  ⛔️
| Time remap |                    ⛔️
| Markers |                       ⛔️

## Feedback

Please use our [forums](https://forums.noesisengine.com/) for bug reports and feature requests.
