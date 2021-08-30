import json
import sys
import codecs
import colorama
import copy
import math
from collections import namedtuple
from argparse import ArgumentParser

__version__ = "0.51"

# Bodymovin JSON to XAML converter
# See: https://github.com/airbnb/lottie-web/tree/master/docs/json for the (usually out-of-date) schema
# See: https://helpx.adobe.com/pdf/after_effects_reference.pdf for the After Effects semantic

Keyframe = namedtuple('Keyframe', 'time value easing to ti')
Animation = namedtuple('Animation', 'first keyframes')
Transform = namedtuple('Transform', 'anchor position scale rotation opacity')
Asset = namedtuple('Asset', 'id source layers')
Font = namedtuple('Font', 'name path family style')

Gradient = namedtuple('Gradient', 'start end length angle stops')
Stroke = namedtuple('Stroke', 'opacity color gradient width line_cap line_join miter_limit dash_offset dash_array')
Fill = namedtuple('Fill', 'opacity color gradient fill_rule')
Paint = namedtuple('Paint', 'fill stroke')

LAYER_TYPE_PRECOMP = 0
LAYER_TYPE_SOLID = 1
LAYER_TYPE_IMAGE = 2
LAYER_TYPE_NULL = 3
LAYER_TYPE_SHAPE = 4
LAYER_TYPE_TEXT = 5

FILL_RULE_NON_ZERO = 1
FILL_RULE_EVEN_ODD = 2

EASING_DISCRETE = 0
EASING_LINEAR = 1

GRADIENT_LINEAR = 1
GRADIENT_RADIAL = 2

LINE_CAP_FLAT = 1
LINE_CAP_ROUND = 2
LINE_CAP_SQUARE = 3

LINE_JOIN_MITER = 1
LINE_JOIN_ROUND = 2
LINE_JOIN_BEVEL = 3

TRIM_PATH_INDIVIDUALLY = 0
TRIM_PATH_SIMULTANEOUSLY = 1

def error(msg):
    print(colorama.Fore.RED + msg)
    exit(1)

def warning(msg):
    print(colorama.Fore.GREEN + msg)

def as_list(x):
    return x if type(x) is list else [x]

def remove_list(x):
    return x[0] if type(x) is list else x

def format_float(x):
    return ('%.2f' % x).rstrip('0').rstrip('.')

def format_rgb(obj):
    r = max(min((int)(obj[0] * 255), 255), 0)
    g = max(min((int)(obj[1] * 255), 255), 0)
    b = max(min((int)(obj[2] * 255), 255), 0)
    return '%02X%02X%02X' % (r, g, b)

def format_rgba(obj):
    r = max(min((int)(obj[0] * 255), 255), 0)
    g = max(min((int)(obj[1] * 255), 255), 0)
    b = max(min((int)(obj[2] * 255), 255), 0)
    a = max(min((int)(obj[3] * 255), 255), 0)
    return '%02X%02X%02X%02X' % (a, r, g, b)

def vec2_len(a, b):
    # Returns the length betwwen two 2D vectors
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return math.sqrt(dx * dx + dy * dy)

def vec2_add(a, b):
    # Adds two 2D vectors
    return (a[0] + b[0], a[1] + b[1])

def vec2_sub(a, b):
    # Substracts two 2D vectors
    return (a[0] - b[0], a[1] - b[1])

def vec2_scale(v, scale):
    # Multiply 2D vector by number
    return (v[0] * scale, v[1] * scale)

def vec2_rot(v, center, angle):
    # Rotate a 2D vector given degrees around given center
    x = v[0] - center[0]
    y = v[1] - center[1]
    rad = math.radians(angle)
    sin = math.sin(rad)
    cos = math.cos(rad)
    return (center[0] + cos * x - sin * y, center[1] + sin * x + cos * y)

class JsonParser:
    def __init__(self, debug, template, repeat):
        self.animations = ''
        self.body = ''
        self.context = []
        self.num_paths = 0
        self.num_groups = 0
        self.num_texts = 0
        self.assets = []
        self.fonts = []
        self.noesis_namespace = False
        self.start = 0
        self.end = 0
        self.fps = 0
        self.width = 0
        self.height = 0
        self.debug = debug
        self.template = template
        self.tab = '    ' if template else ''
        self.ani_tab = '  ' if template else ''
        self.repeat = repeat

    def parse(self, input, output):
        colorama.init(autoreset = True)

        with open(input, 'r') as f:
            obj = json.load(f)

        self.read_composition(obj)

        with open(output, 'w') as f:

            repeat_behavior = ' RepeatBehavior="%s"' % self.repeat if self.repeat else ""

            if self.template:
                f.write('<ResourceDictionary\n')
                f.write('  xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"\n')
                if self.noesis_namespace:
                    f.write('  xmlns:noesis="clr-namespace:NoesisGUIExtensions;assembly=Noesis.GUI.Extensions"\n')
                f.write('  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">\n\n')

                print(output)
                f.write('  <ControlTemplate x:Key="%s" TargetType="Control">\n' % self.template)

                if self.animations:
                    f.write('    <ControlTemplate.Resources>\n')
                    f.write('      <Storyboard x:Key="Anims" Duration="%s"%s>\n' % (self.as_time(self.end - self.start), repeat_behavior))
                    f.write(self.animations)
                    f.write('      </Storyboard>\n')
                    f.write('    </ControlTemplate.Resources>\n\n')

                    f.write('    <ControlTemplate.Triggers>\n')
                    f.write('      <EventTrigger RoutedEvent="FrameworkElement.Loaded">\n')
                    f.write('        <BeginStoryboard Storyboard="{StaticResource Anims}"/>\n')
                    f.write('      </EventTrigger>\n')
                    f.write('    </ControlTemplate.Triggers>\n\n')

                f.write('    <Canvas Width="%d" Height="%d">\n' % (self.width, self.height))
                f.write(self.body)
                f.write('    </Canvas>\n')
                f.write('  </ControlTemplate>\n')
                f.write('\n</ResourceDictionary>')
            else:
                f.write('<Canvas\n')
                f.write('  xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"\n')
                if self.noesis_namespace:
                    f.write('  xmlns:noesis="clr-namespace:NoesisGUIExtensions;assembly=Noesis.GUI.Extensions"\n')
                f.write('  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"\n')
                f.write('  Width="%d" Height="%d">\n\n' % (self.width, self.height))

                if self.animations:
                    f.write('  <Canvas.Resources>\n')
                    f.write('    <Storyboard x:Key="Anims" Duration="%s">\n' % self.as_time(self.end - self.start))
                    f.write(self.animations)
                    f.write('    </Storyboard>\n')
                    f.write('  </Canvas.Resources>\n\n')
                    f.write('  <Canvas.Triggers>\n')
                    f.write('    <EventTrigger RoutedEvent="FrameworkElement.Loaded">\n')
                    f.write('      <BeginStoryboard Storyboard="{StaticResource Anims}"/>\n')
                    f.write('    </EventTrigger>\n')
                    f.write('  </Canvas.Triggers>\n\n')

                f.write(self.body)
                f.write('\n</Canvas>')

    def clear_body(self):
        body = self.body
        self.body = ""
        return body

    def push_tab(self):
        self.tab += '  '

    def pop_tab(self):
        self.tab = self.tab[:-2]

    def next_path_name(self):
        name = 'Path%d' % self.num_paths
        self.num_paths += 1
        return name

    def next_group_name(self):
        name = 'Group%d' % self.num_groups
        self.num_groups += 1
        return name

    def next_text_name(self):
        name = 'Text%d' % self.num_texts
        self.num_texts += 1
        return name

    def as_time(self, frame):
        m, s = divmod(frame / float(self.fps), 60)
        h, m = divmod(m, 60)
        return "%s:%s:%s" % (format_float(h), format_float(m), format_float(s))

    def begin_reading(self, name, obj):
        self.context.append((name, obj))

    def read_field(self, field, default = 'default'):
        name = self.context[-1][0]
        obj = self.context[-1][1]

        if default != 'default':
            return obj.pop(field, default)
        else:
            value = obj.pop(field, None)
            if value is None:
                error("Field not found '%s.%s'" % (name, field))
            return value

    def end_reading(self):
        name = self.context[-1][0]
        obj = self.context[-1][1]

        for k in obj.keys():
            warning("Ignored field '%s.%s'" % (name, k))

        self.context.pop()

    def read_animation_path(self, obj):
        def split(obj):
            self.begin_reading('geometry', obj[0])
            closed = self.read_field('c')
            in_tangents = self.read_field('i')
            out_tangents = self.read_field('o')
            vertices = self.read_field('v')
            self.end_reading()

            # Convert path to XAML friendly format -> BezierSegment(Point1, Point2, Point3)
            start = [0, 0]
            segments = []
            num_segments = len(vertices) if closed else len(vertices) - 1
            if num_segments > 0:
                start = vertices[0]
                cp3 = vertices[0]
                for i in range(num_segments):
                    cp0 = cp3
                    cp1 = [cp0[0] + out_tangents[i][0], cp0[1] + out_tangents[i][1]]
                    cp3 = vertices[(i + 1) % len(vertices)]
                    cp2 = [cp3[0] + in_tangents[(i + 1) % len(in_tangents)][0], cp3[1] + in_tangents[(i + 1) % len(in_tangents)][1]]
                    segments.append((cp1, cp2, cp3))

            # Split into N-dimensional array
            return [start] + [point for segment in segments for point in segment]

        return self.read_animation_impl(obj, split)

    def read_animation_color(self, obj):
        def split(obj):
            return [ format_rgb(obj) ]
        return self.read_animation_impl(obj, split)

    def read_animation_gradient(self, obj):
        if obj is None: return None

        self.begin_reading("gradient", obj)
        num_stops = self.read_field('p')
        stops = self.read_field('k')
        self.end_reading()

        def interpolate(offset, stops):
            # Returns the interpolated value at the given offset

            # First, make sure we have values at offset 0 and 1
            if stops[0][0] != 0:
                stops.insert(0, (0.0, stops[0][1]))
            if stops[-1][0] != 1:
                stops.append((1.0, stops[-1][1]))

            # Second, find the segment and interpolate
            for i in range(0, len(stops) - 1):
                t0 = stops[i][0]
                t1 = stops[i + 1][0]
                if offset >= t0 and offset <= t1:
                    value0 = stops[i][1]
                    value1 = stops[i + 1][1]
                    t = (offset - t0) / (t1 - t0)

                    if isinstance(value0, list):
                        return [(1.0 - t) * value0[0] + t * value1[0], \
                                (1.0 - t) * value0[1] + t * value1[1], \
                                (1.0 - t) * value0[2] + t * value1[2]]
                    else:
                        return (1.0 - t) * value0 + t * value1

            assert(False)

        def split(obj):
            # Format given by Bodymovin (num_stops only refers to rgb stops)
            # [offset rgb offset rgb offset rgb offset alpha offset alpha]

            rgb_stops = []
            for i in range(0, num_stops * 4, 4):
                rgb_stops.append((obj[i], obj[i + 1: i + 4]))

            alpha_stops = []
            for i in range(num_stops * 4, len(obj), 2):
                alpha_stops.append((obj[i], obj[i + 1]))

            values = []

            for v in rgb_stops:
                alpha = interpolate(v[0], alpha_stops) if alpha_stops else 1.0
                values.append(v[0])
                values.append(format_rgba(v[1] + [alpha]))

            for v in alpha_stops:
                rgb = interpolate(v[0], rgb_stops)
                values.append(v[0])
                values.append(format_rgba(rgb + [v[1]]))

            return values

        return self.read_animation_impl(stops, split)

    def read_animation_float(self, obj):
        return self.read_animation_impl(obj, lambda x: x[:1])

    def read_animation_float2(self, obj):
        return self.read_animation_impl(obj, lambda x: x[:2])

    def read_animation_point(self, obj):
        return self.read_animation_impl(obj, lambda x: [(x[0], x[1])])

    def read_animation_impl(self, obj, split_func):
        if obj is None: return None

        self.begin_reading("animation", obj)
        unused_animated = self.read_field('a', None)
        unused_index = self.read_field('ix', None)
        unused_l = self.read_field('l', None)
        k = self.read_field('k', None)

        values = None

        if k is not None:
            first = None
            keyframes = []

            expression = self.read_field('x', None)
            if expression:
                warning("Property expressions not supported")

            # Keyframes are encoded in Bodymovin as sequences of start value and frame.
            # [
            #   { startValue_1, startFrame_1 },  # interpolates from startValue_1 to startValue_2 from startFrame_1 to startFrame_2
            #   { startValue_2, startFrame_2 },  # interpolates from startValue_2 to startValue_3 from startFrame_2 to startFrame_3
            #   { startValue_3, startFrame_3 },  # interpolates from startValue_3 to startValue_4 from startFrame_3 to startFrame_4
            #   { startValue_4, startFrame_4 }
            # ]
            #
            # Earlier versions of Bodymovin used an end value in each key frame. To be compatible
            # # with old formats, the presence of the end value is detected
            # [
            #   { startValue_1, endValue_1, startFrame_1 },  # interpolates from startValue_1 to endValue_1 from startFrame_1 to startFrame_2
            #   { startValue_2, endValue_2, startFrame_2 },  # interpolates from startValue_2 to endValue_2 from startFrame_2 to startFrame_3
            #   { startValue_3, endValue_3, startFrame_3 },  # interpolates from startValue_3 to endValue_3 from startFrame_3 to startFrame_4
            #   { startFrame_4 }
            # ]
            #
            # Bodymovin format is converted to XAML keyframes which are { endValue, endTime } pairs.

            if isinstance(k, list) and isinstance(k[0], dict):
                count = len(k)
                end_value = None
                to = None
                ti = None
                easing = EASING_DISCRETE

                for i in range(count):
                    self.begin_reading("keyframe", k[i])
                    unused_name = self.read_field('n', None)
                    start_frame = self.read_field('t')
                    s = self.read_field('s', None)
                    start_value = split_func(as_list(s)) if s is not None else None
                    hold = self.read_field('h', 0) == 1

                    if i == count - 1:
                        if start_value is None:
                            # Old format
                            keyframes.append((start_frame, end_value, easing, to, ti))
                        else:
                            keyframes.append((start_frame, start_value, easing, to, ti))
                    else:
                        keyframes.append((start_frame, start_value, easing, to, ti))

                        to = self.read_field('to', None)
                        ti = self.read_field('ti', None)

                        if hold:
                            easing = EASING_DISCRETE
                            end_value = start_value
                        else:
                            e = self.read_field('e', None)
                            end_value = None if e is None else split_func(as_list(e))
                            cp1 = self.read_field('o', None)
                            cp2 = self.read_field('i', None)
                            if cp1 is not None and cp2 is not None:
                                cp1x = remove_list(cp1['x'])
                                cp1y = remove_list(cp1['y'])
                                cp2x = remove_list(cp2['x'])
                                cp2y = remove_list(cp2['y'])
                                if cp1x != cp1y or cp2x != cp2y:
                                    easing = [(cp1x, cp1y), (cp2x, cp2y)]
                                else:
                                    easing = EASING_LINEAR
                            else:
                                easing = EASING_LINEAR

                    self.end_reading()

                first = keyframes[0][1]

            else:
                first = split_func(as_list(k))

            # TODO: tangents are not correct for Point2 animations
            values = [Animation(first[i], [Keyframe(key[0], key[1][i], key[2], \
                key[3][i] if key[3] is not None else None, \
                key[4][i] if key[4] is not None else None) \
                for key in keyframes]) for i in range(len(first))]

        else:
            # Separate dimensions for X and Y
            self.read_field('s')
            values = []
            values.extend(self.read_animation_float(self.read_field('x')))
            values.extend(self.read_animation_float(self.read_field('y')))

        # Remove empty channels
        for i in range(len(values)):
            if values[i].keyframes is not None:
                if all(k.value == values[i].keyframes[0].value for k in values[i].keyframes):
                    values[i] = Animation(values[i].first, None)

        self.end_reading()

        return values

    def write_float_animation(self, obj, property, name, scale = 1, offset = 0):
        if obj.keyframes:
            self.animations += self.ani_tab + '      <DoubleAnimationUsingKeyFrames Storyboard.TargetProperty="%s" Storyboard.TargetName="%s">\n' % (property, name)
            for k in obj.keyframes:
                if k.easing == EASING_DISCRETE: kind = 'DiscreteDoubleKeyFrame'
                elif k.easing == EASING_LINEAR: kind = 'LinearDoubleKeyFrame'
                else: kind = 'SplineDoubleKeyFrame KeySpline="%s,%s %s,%s"' % (k.easing[0][0], k.easing[0][1], k.easing[1][0],k.easing[1][1])
                self.animations += self.ani_tab + '        <%s KeyTime="%s" Value="%s"/>\n' % (kind, self.as_time(k.time), format_float(k.value * scale + offset))
            self.animations += self.ani_tab + '      </DoubleAnimationUsingKeyFrames>\n'

    def write_point_animation(self, obj, property, name):
        if obj.keyframes:
            self.animations += self.ani_tab + '      <PointAnimationUsingKeyFrames Storyboard.TargetProperty="%s" Storyboard.TargetName="%s">\n' % (property, name)
            for k in obj.keyframes:
                if k.easing == EASING_DISCRETE: kind = 'DiscretePointKeyFrame'
                elif k.easing == EASING_LINEAR: kind = 'LinearPointKeyFrame'
                else: kind = 'SplinePointKeyFrame KeySpline="%s,%s %s,%s"' % (k.easing[0][0], k.easing[0][1], k.easing[1][0],k.easing[1][1])
                self.animations += self.ani_tab + '        <%s KeyTime="%s" Value="%s,%s"/>\n' % (kind, self.as_time(k.time), format_float(k.value[0]), format_float(k.value[1]))
            self.animations += self.ani_tab + '      </PointAnimationUsingKeyFrames>\n'

    def write_color_animation(self, obj, property, name):
        if obj.keyframes:
            self.animations += self.ani_tab + '      <ColorAnimationUsingKeyFrames Storyboard.TargetProperty="%s" Storyboard.TargetName="%s">\n' % (property, name)
            for k in obj.keyframes:
                if k.easing == EASING_DISCRETE: kind = 'DiscreteColorKeyFrame'
                elif k.easing == EASING_LINEAR: kind = 'LinearColorKeyFrame'
                else: kind = 'SplineColorKeyFrame KeySpline="%s,%s %s,%s"' % (k.easing[0][0], k.easing[0][1], k.easing[1][0],k.easing[1][1])
                self.animations += self.ani_tab + '        <%s KeyTime="%s" Value="#%s"/>\n' % (kind, self.as_time(k.time), k.value)
            self.animations += self.ani_tab + '      </ColorAnimationUsingKeyFrames>\n'

    def read_transform(self, obj):
        self.begin_reading("transform", obj)
        unused_nm = self.read_field('nm', None)
        unused_ty = self.read_field('ty', None)
        anchor = self.read_animation_float2(self.read_field('a', None))
        position = self.read_animation_float2(self.read_field('p', None))
        scale = self.read_animation_float2(self.read_field('s', None))
        rotation = self.read_animation_float(self.read_field('r', None))
        opacity = self.read_animation_float(self.read_field('o', None))
        skew = self.read_animation_float(self.read_field('sk', None))
        if skew and (skew[0].first != 0 or self.is_animated(skew[0])):
            warning('Skew not supported')
        skew_axis = self.read_animation_float(self.read_field('sa', None))
        if skew_axis and (skew_axis[0].first != 0 or self.is_animated(skew_axis[0])):
            warning('Skew Axis not supported')
        self.end_reading()

        return Transform(anchor, position, scale, rotation, opacity)

    def is_animated(self, obj):
        return obj is not None and obj.keyframes is not None

    def is_transform_animated(self, obj):
        return self.is_animated(obj.anchor[0]) or self.is_animated(obj.anchor[1]) or \
               self.is_animated(obj.position[0]) or self.is_animated(obj.position[1]) or \
               self.is_animated(obj.scale[0]) or self.is_animated(obj.scale[1]) or \
               self.is_animated(obj.rotation[0])

    def has_transform_elements(self, obj):
        return self.is_transform_animated(obj) or \
               obj.position[0].first - obj.anchor[0].first != 0 or \
               obj.position[1].first - obj.anchor[1].first != 0 or \
               obj.scale[0].first != 100 or obj.scale[1].first != 100 or \
               obj.rotation[0].first != 0

    def write_transform_elements(self, root_class, obj, name):
        scaling = self.is_animated(obj.scale[0]) or self.is_animated(obj.scale[1]) or obj.scale[0].first != 100 or obj.scale[1].first != 100
        rotating = self.is_animated(obj.rotation[0]) or obj.rotation[0].first != 0
        moving = self.is_animated(obj.position[0]) or self.is_animated(obj.position[1]) or \
            (obj.position[0].first - obj.anchor[0].first) != 0 or (obj.position[1].first - obj.anchor[1].first) != 0
        num_transforms = scaling + rotating + moving
        use_group = num_transforms > 1
        align = '  ' if use_group else ''

        if self.is_animated(obj.anchor[0]) or self.is_animated(obj.anchor[1]):
            warning("Animated anchor points not supported")

        self.body += self.tab + '    <%s.RenderTransform>\n' % root_class
        if use_group: self.body += self.tab + '      <TransformGroup>\n'

        if scaling:
            self.body += align + self.tab + '      <ScaleTransform'
            if obj.scale[0].first != 100:
                self.body += ' ScaleX="%s"' % format_float(obj.scale[0].first / 100.0)
            if obj.scale[1].first != 100:
                self.body += ' ScaleY="%s"' % format_float(obj.scale[1].first / 100.0)
            if obj.anchor[0].first != 0:
                self.body += ' CenterX="%s"' % format_float(obj.anchor[0].first)
            if obj.anchor[1].first != 0:
                self.body += ' CenterY="%s"' % format_float(obj.anchor[1].first)
            self.body += '/>\n'

            if (num_transforms > 1):
                self.write_float_animation(obj.scale[0], 'RenderTransform.Children[0].ScaleX', name, 0.01, 0.0)
                self.write_float_animation(obj.scale[1], 'RenderTransform.Children[0].ScaleY', name, 0.01, 0.0)
            else:
                self.write_float_animation(obj.scale[0], 'RenderTransform.ScaleX', name, 0.01, 0.0)
                self.write_float_animation(obj.scale[1], 'RenderTransform.ScaleY', name, 0.01, 0.0)

        if rotating:
            self.body += align + self.tab + '      <RotateTransform'
            if obj.rotation[0].first != 0:
                self.body += ' Angle="%s"' % format_float(obj.rotation[0].first)
            if obj.anchor[0].first != 0:
                self.body += ' CenterX="%s"' % format_float(obj.anchor[0].first)
            if obj.anchor[1].first != 0:
                self.body += ' CenterY="%s"' % format_float(obj.anchor[1].first)
            self.body += '/>\n'

            if (num_transforms > 1):
                index = scaling
                self.write_float_animation(obj.rotation[0], 'RenderTransform.Children[%d].Angle' % index, name)
            else:
                self.write_float_animation(obj.rotation[0], 'RenderTransform.Angle', name)

        if moving:
            self.body += align + self.tab + '      <TranslateTransform'
            x = obj.position[0].first - obj.anchor[0].first
            y = obj.position[1].first - obj.anchor[1].first
            if x != 0: self.body += ' X="%s"' % format_float(x)
            if y != 0: self.body += ' Y="%s"' % format_float(y)
            self.body += '/>\n'

            if (num_transforms > 1):
                index = scaling + rotating
                self.write_float_animation(obj.position[0], 'RenderTransform.Children[%d].X' % index, name, 1.0, -obj.anchor[0].first)
                self.write_float_animation(obj.position[1], 'RenderTransform.Children[%d].Y' % index, name, 1.0, -obj.anchor[1].first)
            else:
                self.write_float_animation(obj.position[0], 'RenderTransform.X', name, 1.0, -obj.anchor[0].first)
                self.write_float_animation(obj.position[1], 'RenderTransform.Y', name, 1.0, -obj.anchor[1].first)

        if use_group: self.body += self.tab + '      </TransformGroup>\n'
        self.body += self.tab + '    </%s.RenderTransform>\n' % root_class

    def write_visibility_animations(self, name, start, end):
        write_start = start != 0
        write_end = end != self.end
        if write_start or write_end:
            self.animations += self.ani_tab + '      <ObjectAnimationUsingKeyFrames Storyboard.TargetProperty="Visibility" Storyboard.TargetName="%s">\n' % name
            if write_start:
                self.animations += self.ani_tab + '        <DiscreteObjectKeyFrame KeyTime="%s" Value="{x:Static Visibility.Visible}"/>\n' % self.as_time(start)
            if write_end:
                self.animations += self.ani_tab + '        <DiscreteObjectKeyFrame KeyTime="%s" Value="{x:Static Visibility.Hidden}"/>\n' % self.as_time(end)
            self.animations += self.ani_tab + '      </ObjectAnimationUsingKeyFrames>\n'

    def is_line(self, c0, c1, c2, c3):
        # This is an extreme simplification
        return c0 == c1 and c2 == c3

    def gen_segments(self, path):
        c0 = path[0].first
        for i in range(1, len(path), 3):
            c1 = path[i].first
            c2 = path[i + 1].first
            c3 = path[i + 2].first
            points_animated = self.is_animated(path[i]) or self.is_animated(path[i + 1]) or self.is_animated(path[i + 2])

            if self.is_line(c0, c1, c2, c3) and not points_animated:
                yield('L', c3)
            else:
                yield('C', c1, c2, c3)

            c0 = c3

    def read_paint(self, obj):
        self.begin_reading('paint', obj)
        unused_name = self.read_field('nm', None)
        unused_match_name = self.read_field('mn', None)
        unused_hidden = self.read_field('hd', None)
        unused_fill_enabled = self.read_field('fillEnabled', None)
        ty = self.read_field('ty')

        blend_mode = self.read_field('bm', None)
        if blend_mode is not None and blend_mode != 0:
            warning("Unsupported FillMode '%d'" % blend_mode)

        fill_rule = self.read_field('r', FILL_RULE_EVEN_ODD)
        if fill_rule != FILL_RULE_NON_ZERO and fill_rule != FILL_RULE_EVEN_ODD:
            warning("Unsupported FillRule '%d'" % fill_rule)
            fill_rule = FILL_RULE_EVEN_ODD

        opacity = self.read_animation_float(self.read_field('o'))
        color = self.read_animation_color(self.read_field('c', None))

        gradient_type = self.read_field('t', None)
        if gradient_type != None and gradient_type != GRADIENT_LINEAR and gradient_type != GRADIENT_RADIAL:
            warning("Unsupported Gradient Type '%d'" % gradient_type)

        stops = self.read_animation_gradient(self.read_field('g', None))
        start = self.read_animation_point(self.read_field('s', None))
        end = self.read_animation_point(self.read_field('e', None))
        length = self.read_animation_float(self.read_field('h', None))
        angle = self.read_animation_float(self.read_field('a', None))

        width = self.read_animation_float(self.read_field('w', None))
        line_cap = self.read_field('lc', None)
        line_join = self.read_field('lj', None)
        miter_limit_ = self.read_field('ml', None)
        miter_limit = self.read_animation_float(self.read_field('ml2', None))
        if miter_limit is None and miter_limit_ is not None:
            # 'ml' is not animated
            miter_limit = [ Animation(miter_limit_, None) ]

        # In XAML, dashes are expressed relative to the thickness of the stroke. Values in AE are
        # expressed in pixels, so a division is necessary. Because of this, animations are not supported
        dash_array = []
        dash_offset = 0
        dashes = self.read_field('d', None)
        if dashes:
            if width[0].keyframes:
                warning('Dash not supported with animated Width')
            else:
                for segment in dashes:
                    self.begin_reading('dash', segment)
                    unused_name = self.read_field('nm', None)
                    v = self.read_animation_float(self.read_field('v'))
                    n = self.read_field('n', None)
                    self.end_reading()

                    if v[0].keyframes:
                        warning('Animated Dashes not supported')
                        dash_array = []
                        break

                    if n == 'o':
                        dash_offset = float(v[0].first) / width[0].first
                    else:
                        dash_array.append(float(v[0].first) / width[0].first)

        self.end_reading()

        fill = None
        stroke = None

        # Solid Color fill
        if ty == 'fl':
            fill = Fill(opacity, color, None, fill_rule)
        # Gradient Fill
        elif ty == 'gf':
            gradient = Gradient(start, end, length, angle, stops)
            fill = Fill(opacity, None, gradient, fill_rule)
        # Solid Color Stroke
        elif ty == 'st':
            stroke = Stroke(opacity, color, None, width, line_cap, line_join, miter_limit, dash_offset, dash_array)
        # Gradient Stroke
        elif ty == 'gs':
            gradient = Gradient(start, end, length, angle, stops)
            stroke = Stroke(opacity, None, gradient, width, line_cap, line_join, miter_limit, dash_offset, dash_array)
        else:
            warning("Unsupported paint type '%d'" % ty)

        return Paint(fill, stroke)

    def write_brush_animations(self, obj, name, kind):
        self.write_float_animation(obj.opacity[0], "%s.Opacity" % kind, name, 0.01)
        if obj.color:
            self.write_color_animation(obj.color[0], "%s.Color" % kind, name)
        else:
            if not obj.gradient.length:
                # Linear Gradient Brush
                self.write_point_animation(obj.gradient.start[0], "%s.StartPoint" % kind, name)
                self.write_point_animation(obj.gradient.end[0], "%s.EndPoint" % kind, name)
            else:
                # Radial Gradient Brush
                if obj.gradient.start[0].keyframes:
                    warning('Radial animated Start Point not supported')

                if obj.gradient.end[0].keyframes:
                    warning('Radial animated End Point not supported')

                if obj.gradient.length[0].keyframes:
                    warning('Radial animated Hightlight Length not supported')

                if obj.gradient.angle[0].keyframes:
                    warning('Radial animated Hightlight Angle not supported')

            for i in range(0, len(obj.gradient.stops), 2):
                self.write_float_animation(obj.gradient.stops[i], "%s.GradientStops[%d].Offset" % (kind, i / 2), name)
                self.write_color_animation(obj.gradient.stops[i + 1], "%s.GradientStops[%d].Color" % (kind, i / 2), name)

    def write_paint_animations(self, obj, name):
        start_size = len(self.animations)
        if obj.fill:
            self.write_brush_animations(obj.fill, name, "Fill")
        elif obj.stroke:
            self.write_brush_animations(obj.stroke, name, "Stroke")
            self.write_float_animation(obj.stroke.width[0], "StrokeThickness", name)
            if obj.stroke.miter_limit:
                self.write_float_animation(obj.stroke.miter_limit[0], "StrokeMiterLimit", name)

        # Returns whether animations were found
        return start_size != len(self.animations)

    def write_paint_attributes(self, obj):
        if obj.fill:
            if obj.fill.color:
                # Fill attribute can be inlined if opacity is 1.0
                if obj.fill.opacity[0].first == 100:
                    self.body += ' Fill="#%s"' % obj.fill.color[0].first

        if obj.stroke:
            if obj.stroke.color:
                # Stroke attribute can be inlined if opacity is 1.0
                if obj.stroke.opacity[0].first == 100:
                    self.body += ' Stroke="#%s"' % obj.stroke.color[0].first

            # '1.0' is the default thickness
            if obj.stroke.width[0].first != 1:
                self.body += ' StrokeThickness="%s"' % format_float(obj.stroke.width[0].first)

            # 'Flat' is the default cap
            if obj.stroke.line_cap == LINE_CAP_ROUND:
                self.body += ' StrokeStartLineCap="Round" StrokeEndLineCap="Round"'
            elif obj.stroke.line_cap == LINE_CAP_SQUARE:
                self.body += ' StrokeStartLineCap="Square" StrokeEndLineCap="Square"'

            if obj.stroke.line_join == LINE_JOIN_MITER:
                # 'Miter' is the default join. '10' is the default limit
                if obj.stroke.miter_limit[0].first != 10:
                    self.body += ' StrokeMiterLimit="%s"' % format_float(obj.stroke.miter_limit[0].first)
            elif obj.stroke.line_join == LINE_JOIN_ROUND:
                self.body += ' StrokeLineJoin="Round"'
            elif obj.stroke.line_join == LINE_JOIN_BEVEL:
                self.body += ' StrokeLineJoin="Bevel"'

            if obj.stroke.dash_array:
                self.body += ' StrokeDashArray="%s"' % ','.join([format_float(s) for s in obj.stroke.dash_array])
                if obj.stroke.dash_offset != 0:
                    self.body += ' StrokeDashOffset="%s"' % format_float(obj.stroke.dash_offset)

                if obj.stroke.line_cap == LINE_CAP_ROUND:
                    self.body += ' StrokeDashCap="Round"'
                elif obj.stroke.line_cap == LINE_CAP_SQUARE:
                    self.body += ' StrokeDashCap="Square"'

    def write_paint_elements(self, obj):
        if obj.fill:
            kind = 'Fill'
            paint = obj.fill
        elif obj.stroke:
            kind = 'Stroke'
            paint = obj.stroke

        if paint.color:
            # Color already written as attribute if opacity = 1
            if paint.opacity[0].first != 100:
                self.body += self.tab + '      <Path.%s>\n' % kind
                self.body += self.tab + '        <SolidColorBrush Color="#%s" Opacity="%s"/>\n' % (paint.color[0].first, format_float(paint.opacity[0].first / 100.0))
                self.body += self.tab + '      </Path.%s>\n' % kind
        else:
            self.body += self.tab + '      <Path.%s>\n' % kind
            is_linear_gradient = paint.gradient.length == None
            start = paint.gradient.start[0].first
            end = paint.gradient.end[0].first

            if is_linear_gradient:
                self.body += self.tab + '        <LinearGradientBrush MappingMode="Absolute" StartPoint="%s,%s" EndPoint="%s,%s"' % \
                    (format_float(start[0]), format_float(start[1]), format_float(end[0]), format_float(end[1]))
            else:
                self.body += self.tab + '        <RadialGradientBrush MappingMode="Absolute"'

                # Convert from AE Hightlight Length and Angle to XAML RadiusX, RadiusY and GradientOrigin
                radius = vec2_len(start, end)
                length = paint.gradient.length[0].first
                angle = paint.gradient.angle[0].first
                origin = vec2_rot(vec2_add(start, vec2_scale(vec2_sub(end, start), length / 100.0)), start, angle)

                if start[0] != 0 or start[1] != 0:
                    self.body += ' Center="%s,%s"' % (format_float(start[0]), format_float(start[1]))
                if radius != 0:
                    self.body += ' RadiusX="%s" RadiusY="%s"' % (format_float(radius), format_float(radius))
                if origin[0] != 0 or origin[1] != 0:
                    self.body += ' GradientOrigin="%s,%s"' % (format_float(origin[0]), format_float(origin[1]))

            if paint.opacity[0].first != 100:
                self.body += ' Opacity="%s"' % format_float(paint.opacity[0].first / 100.0)
            self.body += '>\n'

            for i in range(0, len(paint.gradient.stops), 2):
                self.body += self.tab + '          <GradientStop Offset="%s" Color="#%s"/>\n' % (format_float(paint.gradient.stops[i].first), paint.gradient.stops[i + 1].first)

            if is_linear_gradient:
                self.body += self.tab + '        </LinearGradientBrush>\n'
            else:
                self.body += self.tab + '        </RadialGradientBrush>\n'

            self.body += self.tab + '      </Path.%s>\n' % kind

    def write_paths(self, obj, paint_, operators):
        paths = []
        path_animated = False

        # Copy the path because it can be read more than once
        for path in copy.deepcopy(obj):
            if path['ty'] == 'sh':
                self.begin_reading('shape', path)
                unused_ix = self.read_field('ix', None)
                unused_ind = self.read_field('ind', None)
                unused_name = self.read_field('nm', None)
                unused_match_name = self.read_field('mn', None)
                unused_hidden = self.read_field('hd', None)
                unused_ty = self.read_field('ty', None)
                geometry = self.read_animation_path(self.read_field('ks'))
                path_animated = path_animated or any(self.is_animated(v) for v in geometry)
                paths.append((geometry))
                self.end_reading()
            elif path['ty'] == 'rc':
                self.begin_reading('rectangle', path)
                unused_name = self.read_field('nm', None)
                unused_match_name = self.read_field('mn', None)
                unused_hidden = self.read_field('hd', None)
                unused_ty = self.read_field('ty', None)
                direction = self.read_field('d')
                size = self.read_animation_point(self.read_field('s'))
                position = self.read_animation_point(self.read_field('p'))
                roundness = self.read_animation_float(self.read_field('r'))
                self.end_reading()

                path_animated = False
                if self.is_animated(size[0]) or self.is_animated(position[0]) or self.is_animated(roundness[0]):
                    warning('Animated Rectangles not supported')

                w = size[0].first[0]
                h = size[0].first[1]
                x = position[0].first[0]
                y = position[0].first[1]
                r = min(roundness[0].first, w * 0.5, h * 0.5)

                geometry = ""

                if r == 0:
                    if direction == 2:
                        geometry += "M%s,%s" % (format_float(x + w * 0.5), format_float(y - h * 0.5))
                        geometry += "v%s" % format_float(h)
                        geometry += "h%s" % format_float(-w)
                        geometry += "v%s" % format_float(-h)
                    else:
                        geometry += "M%s,%s" % (format_float(x + w * 0.5), format_float(y - h * 0.5))
                        geometry += "h%s" % format_float(-w)
                        geometry += "v%s" % format_float(h)
                        geometry += "h%s" % format_float(w)
                else:
                    if direction == 2:
                        geometry += "M%s,%s" % (format_float(x + w * 0.5), format_float(y - h * 0.5 + r))
                        if h - 2 * r > 0:
                            geometry += "v%s" % format_float(h - 2 * r)
                        geometry += "a%s,%s,0,0,1,%s,%s" % (format_float(r), format_float(r), format_float(-r), format_float(r))
                        if w - 2 * r > 0:
                            geometry += "h%s" % format_float(2 * r - w)
                        geometry += "a%s,%s,0,0,1,%s,%s" % (format_float(r), format_float(r), format_float(-r), format_float(-r))
                        if h - 2 * r > 0:
                            geometry += "v%s" % format_float(2 * r - h)
                        geometry += "a%s,%s,0,0,1,%s,%s" % (format_float(r), format_float(r), format_float(r), format_float(-r))
                        if w - 2 * r > 0:
                            geometry += "h%s" % format_float(w - 2 * r)
                        geometry += "a%s,%s,0,0,1,%s,%s" % (format_float(r), format_float(r), format_float(r), format_float(r))
                    else:
                        geometry += "M%s,%s" % (format_float(x + w * 0.5), format_float(y - h * 0.5 + r))
                        geometry += "a%s,%s,0,0,0,%s,%s" % (format_float(r), format_float(r), format_float(-r), format_float(-r))
                        if w - 2 * r > 0:
                            geometry += "h%s" % format_float(2 * r - w)
                        geometry += "a%s,%s,0,0,0,%s,%s" % (format_float(r), format_float(r), format_float(-r), format_float(r))
                        if h - 2 * r > 0:
                            geometry += "v%s" % format_float(h - 2 * r)
                        geometry += "a%s,%s,0,0,0,%s,%s" % (format_float(r), format_float(r), format_float(r), format_float(r))
                        if w - 2 * r > 0:
                            geometry += "h%s" % format_float(w - 2 * r)
                        geometry += "a%s,%s,0,0,0,%s,%s" % (format_float(r), format_float(r), format_float(r), format_float(-r))
                        if h - 2 * r > 0:
                            geometry += "v%s" % format_float(2 * r - h)

                geometry += "Z"
                paths.append(geometry)

            elif path['ty'] == 'el':
                self.begin_reading('ellipse', path)
                unused_name = self.read_field('nm', None)
                unused_match_name = self.read_field('mn', None)
                unused_hidden = self.read_field('hd', None)
                unused_ty = self.read_field('ty', None)
                direction = self.read_field('d')
                size = self.read_animation_point(self.read_field('s'))
                position = self.read_animation_point(self.read_field('p'))
                self.end_reading()

                path_animated = False
                if self.is_animated(size[0]) or self.is_animated(position[0]):
                    warning('Animated Ellipses not supported')

                rx = size[0].first[0] * 0.5
                ry = size[0].first[1] * 0.5
                x = position[0].first[0]
                y = position[0].first[1]

                geometry = ""

                if direction == 2:
                    geometry += "M%s,%s" % (format_float(x), format_float(y - ry))
                    geometry += "a%s,%s,0,0,1,%s,%s" % (format_float(rx), format_float(ry), format_float(0.0), format_float(2 * ry))
                    geometry += "a%s,%s,0,0,1,%s,%s" % (format_float(rx), format_float(ry), format_float(0.0), format_float(-2 * ry))
                else:
                    geometry += "M%s,%s" % (format_float(x), format_float(y - ry))
                    geometry += "a%s,%s,0,0,0,%s,%s" % (format_float(rx), format_float(ry), format_float(0.0), format_float(2 * ry))
                    geometry += "a%s,%s,0,0,0,%s,%s" % (format_float(rx), format_float(ry), format_float(0.0), format_float(-2 * ry))

                geometry += "Z"
                paths.append(geometry)

        trim_start = None
        trim_end = None
        trim_offset = None
        trim_animated = False

        if operators:
            if len(operators) > 1:
                warning("More than one path operators not implemented")

            self.begin_reading('trim_path', copy.deepcopy(operators[0]))
            trim_start = self.read_animation_float(self.read_field('s'))
            trim_end = self.read_animation_float(self.read_field('e'))
            trim_offset = self.read_animation_float(self.read_field('o'))
            m = self.read_field('m')

            if m == TRIM_PATH_SIMULTANEOUSLY and len(paths) > 1:
                warning("Trim Path 'Simultaneously' mode not implemented")

            unused_ix = self.read_field('ix', None)
            unused_name = self.read_field('nm', None)
            unused_match_name = self.read_field('mn', None)
            unused_hidden = self.read_field('hd', None)
            unused_ty = self.read_field('ty', None)
            self.end_reading()

            trim_animated = self.is_animated(trim_start[0]) or self.is_animated(trim_end[0]) or self.is_animated(trim_offset[0])

        self.body += self.tab + '    <Path'
        path_name = self.next_path_name()
        paint = self.read_paint(paint_)
        paint_animated = self.write_paint_animations(paint, path_name)

        if path_animated or trim_animated or paint_animated:
            self.body += ' x:Name="%s"' % path_name

        fill_rule = paint.fill.fill_rule if paint.fill else None
        self.write_paint_attributes(paint)

        if trim_start:
            if trim_start[0].first != 0:
                self.noesis_namespace = True
                self.body += ' noesis:Path.TrimStart="%s"' % format_float(trim_start[0].first / 100.0)
            self.write_float_animation(trim_start[0], "(noesis:Path.TrimStart)", path_name, 1.0 / 100.0)

        if trim_end:
            if trim_end[0].first != 100:
                self.noesis_namespace = True
                self.body += ' noesis:Path.TrimEnd="%s"' % format_float(trim_end[0].first / 100.0)
            self.write_float_animation(trim_end[0], "(noesis:Path.TrimEnd)", path_name, 1.0 / 100.0)

        if trim_offset:
            if trim_offset[0].first != 0:
                self.noesis_namespace = True
                self.body += ' noesis:Path.TrimOffset="%s"' % format_float(trim_offset[0].first / 360.0)
            self.write_float_animation(trim_offset[0], "(noesis:Path.TrimOffset)", path_name, 1.0 / 360.0)

        if path_animated:
            self.body += '>\n'
            self.body += self.tab + '      <Path.Data>\n'
            self.body += self.tab +  '        <PathGeometry%s>\n' % (' FillRule="Nonzero"' if fill_rule == FILL_RULE_NON_ZERO else '')
            for path in paths:
                self.body += self.tab +  '          <PathFigure StartPoint="%s,%s">\n' % (format_float(path[0].first[0]), format_float(path[0].first[1]))
                for s in self.gen_segments(path):
                    if s[0] == 'L':
                        self.body += self.tab + '            <LineSegment Point="%s,%s"/>\n' % (format_float(s[1][0]), format_float(s[1][1]))
                    else:
                        self.body += self.tab + '            <BezierSegment Point1="%s,%s" Point2="%s,%s" Point3="%s,%s"/>\n' \
                            % (format_float(s[1][0]), format_float(s[1][1]), format_float(s[2][0]), format_float(s[2][1]), format_float(s[3][0]), format_float(s[3][1]))
                self.body += self.tab + '          </PathFigure>\n'
            self.body += self.tab + '        </PathGeometry>\n'
            self.body += self.tab + '      </Path.Data>\n'
            self.write_paint_elements(paint)
            self.body += self.tab + '    </Path>\n'

            for figure_idx in range(len(paths)):
                path = paths[figure_idx]
                self.write_point_animation(path[0], 'Data.Figures[%d].StartPoint' % figure_idx, path_name)

                for i in range(1, len(path), 3):
                    segment_idx = (i - 1) / 3
                    self.write_point_animation(path[i], 'Data.Figures[%d].Segments[%d].Point1' % (figure_idx, segment_idx), path_name)
                    self.write_point_animation(path[i + 1], 'Data.Figures[%d].Segments[%d].Point2' % (figure_idx, segment_idx), path_name)
                    self.write_point_animation(path[i + 2], 'Data.Figures[%d].Segments[%d].Point3' % (figure_idx, segment_idx), path_name)

        else:
            data = 'F1' if fill_rule == FILL_RULE_NON_ZERO else ''
            for path in paths:
                if isinstance(path, str):
                    data += path
                else:
                    data += 'M%s,%s' % (format_float(path[0].first[0]), format_float(path[0].first[1]))
                    last_segment = ''
                    for s in self.gen_segments(path):
                        if s[0] == 'L':
                            data += 'L' if last_segment != 'L' else ' '
                            data += '%s,%s' % (format_float(s[1][0]), format_float(s[1][1]))
                        else:
                            data += 'C' if last_segment != 'C' else ' '
                            data += '%s,%s %s,%s,%s,%s' % (format_float(s[1][0]), format_float(s[1][1]), \
                                format_float(s[2][0]), format_float(s[2][1]), \
                                format_float(s[3][0]), format_float(s[3][1]))
                        last_segment = s[0]
            self.body += ' Data="%s"' % data

            body = self.clear_body()
            self.write_paint_elements(paint)

            if self.body:
                self.body = body + '>\n' + self.body + '    </Path>\n'
            else:
                self.body = body + '/>\n'

    def is_paint_attr(self, obj):
        ty = obj['ty']
        return ty == 'fl' or ty == 'gf' or ty == 'st' or ty == 'gs'

    def is_path_attr(self, obj):
        ty = obj['ty']
        return ty == 'sh' or ty == 'el' or ty == 'rc'

    def is_group_attr(self, obj):
        return obj['ty'] == 'gr'

    def is_transform_attr(self, obj):
        return obj['ty'] == 'tr'

    def is_operator_attr(self, obj):
        return obj['ty'] == 'tm'

    def write_shapes(self, obj, operators = []):
        close_transform = False
        group_operators = list(operators)

        # Collect paths for each paint. Paints are rendered in reverse order
        for i in reversed(range(len(obj))):
            node = obj[i]

            if self.is_transform_attr(node):
                transform = self.read_transform(node)
                if self.has_transform_elements(transform) or transform.opacity[0].first != 100 or self.is_animated(transform.opacity[0]):
                    close_transform = True
                    self.push_tab()
                    name = self.next_group_name()
                    self.body += self.tab + '  <Canvas'

                    if self.is_transform_animated(transform) or self.is_animated(transform.opacity[0]):
                        self.body += ' x:Name="%s"' % name

                    if transform.opacity[0].first != 100:
                        self.body += ' Opacity="%s"' % format_float(transform.opacity[0].first / 100.0)
                    self.write_float_animation(transform.opacity[0], "Opacity", name, 0.01)

                    self.body += '>\n'
                    if self.has_transform_elements(transform):
                        self.write_transform_elements("Canvas", transform, name)

            elif self.is_paint_attr(node):
                paths = []
                paint_operators = []

                # Apply paint to paths found before this paint
                for j in reversed(range(i)):
                    if self.is_path_attr(obj[j]):
                        paths.append(obj[j])
                    elif self.is_operator_attr(obj[j]):
                        paint_operators.append(obj[j])

                if paths:
                    self.write_paths(paths, node, group_operators + paint_operators)

            elif self.is_operator_attr(node):
                group_operators.append(node)

            elif self.is_path_attr(node):
                pass

            elif self.is_group_attr(node):
                self.write_shapes(node['it'], group_operators)

            else:
                warning("Unsupported shape attribute '%s'" % node['ty'])

        if close_transform:
            self.body += self.tab + '  </Canvas>\n'
            self.pop_tab()

    def dump_shapes(self, obj, level = 0):
        for shape in obj:
            print('  %s- %s - %s' % (' ' * level, shape['ty'].upper(), shape['nm']))
            if shape['ty'] == 'gr':
                self.dump_shapes(shape['it'], level + 1)

    def write_text(self, obj):
        self.begin_reading('text_data', obj)
        unused_more_options = self.read_field('m', None)
        unused_path = self.read_field('p', None)
        animators = self.read_field('a', None)
        document = self.read_field('d', None)
        self.end_reading()

        self.begin_reading('text_document', document)
        keyframes = self.read_field('k', None)
        self.end_reading()

        color_animation = None
        opacity_animation = None
        stroke_color_animation = None
        stroke_opacity_animation = None

        for animator in animators:
            self.begin_reading('animator', animator)
            animation = self.read_field('a', None)
            unused_ranges = self.read_field('s', None)
            unused_name = self.read_field('nm', None)
            self.end_reading()

            # Animator ranges are not supported, we are just taking first animation and ignoring the range
            self.begin_reading('animation', animation)
            color_animation = color_animation or self.read_animation_color(self.read_field('fc', None))
            opacity_animation = opacity_animation or self.read_animation_float(self.read_field('fo', None))
            stroke_color_animation = stroke_color_animation or self.read_animation_color(self.read_field('sc', None))
            stroke_opacity_animation = stroke_opacity_animation or self.read_animation_float(self.read_field('so', None))
            self.end_reading()

        names = []
        times = []

        for k in keyframes:
            self.begin_reading('text_keyframe', k)
            time = self.read_field('t', None)
            properties = self.read_field('s', None)
            self.end_reading()

            self.begin_reading('text_properties', properties)
            unused_justify = self.read_field('j', None)
            unused_ca = self.read_field('ca', None)
            unused_of = self.read_field('of', None)
            font_name = self.read_field('f', None)
            text = self.read_field('t', "")
            size = self.read_field('s', 0)
            tracking = self.read_field('tr', 0)
            line_height = self.read_field('lh', 0)
            baseline_shift = self.read_field('ls', 0)
            fill_color = self.read_field('fc', None)
            stroke_color = self.read_field('sc', None)
            stroke = self.read_field('sw', 0)
            self.end_reading()

            font = self.find_font(font_name)

            weight = None
            style = None

            if "Thin" in font.style: weight = "Thin"
            if "ExtraLight" in font.style: weight = "ExtraLight"
            if "UltraLight" in font.style: weight = "UltraLight"
            if "Light" in font.style: weight = "Light"
            if "SemiLight" in font.style: weight = "SemiLight"
            if "Medium" in font.style: weight = "Medium"
            if "DemiBold" in font.style: weight = "DemiBold"
            if "SemiBold" in font.style: weight = "SemiBold"
            if "Bold" in font.style: weight = "Bold"
            if "ExtraBold" in font.style: weight = "ExtraBold"
            if "UltraBold" in font.style: weight = "UltraBold"
            if "Black" in font.style: weight = "Black"
            if "Heavy" in font.style: weight = "Heavy"
            if "ExtraBlack" in font.style: weight = "ExtraBlack"
            if "UltraBlack" in font.style: weight = "UltraBlack"
            if "Italic" in font.style: style = "Italic"

            text = text.replace('\r', '&#x0a;')

            self.body += self.tab + '  <TextBlock'

            name = None

            if len(keyframes) > 1:
                name = name or self.next_text_name()

            if color_animation and self.is_animated(color_animation[0]):
                name = name or self.next_text_name()
                self.write_color_animation(color_animation[0], "Foreground.Color", name)

            if opacity_animation and self.is_animated(opacity_animation[0]):
                name = name or self.next_text_name()
                self.write_float_animation(opacity_animation[0], "Foreground.Opacity", name, 0.01)

            if stroke_color_animation and self.is_animated(stroke_color_animation[0]):
                name = name or self.next_text_name()
                self.write_color_animation(stroke_color_animation[0], "(noesis:Text.Stroke).Color", name)
                self.noesis_namespace = True

            if stroke_opacity_animation and self.is_animated(stroke_opacity_animation[0]):
                name = name or self.next_text_name()
                self.write_float_animation(stroke_opacity_animation[0], "(noesis:Text.Stroke).Opacity", name, 0.01)
                self.noesis_namespace = True

            if name:
                self.body += ' x:Name="%s"' % name

            self.body += ' FontFamily="%s" FontSize="%d" Text="%s"' % (font.path + "#" + font.family if font.path else font.family, size, text)
            if weight:
                self.body += ' FontWeight="%s"' % weight
            if style:
                self.body += ' FontStyle="%s"' % style

            if color_animation or fill_color:
                self.body += ' Foreground="#%s"' % (color_animation[0].first if color_animation else format_rgb(fill_color))
            else:
                self.body += ' Foreground="Transparent"'

            if stroke > 0.01:
                self.noesis_namespace = True
                self.body += ' noesis:Text.StrokeThickness="%s"' % stroke
                self.body += ' noesis:Text.Stroke="#%s"' % (stroke_color_animation[0].first if stroke_color_animation else format_rgb(stroke_color))

            if tracking > 0:
                self.noesis_namespace = True
                self.body += ' noesis:Text.CharacterSpacing="%s"' % tracking

            if time > 0:
                self.body += ' Visibility="Hidden"'

            names.append(name)
            times.append(time)

            self.body += '>\n'

            self.body += self.tab + '    <TextBlock.RenderTransform>\n'
            self.body += self.tab + '      <TranslateTransform Y="%s"/>\n' % format_float(-size - baseline_shift)
            self.body += self.tab + '    </TextBlock.RenderTransform>\n'
            self.body += self.tab + '  </TextBlock>\n'

        times.append(self.end)

        if len(keyframes) > 1:
            for i in range(len(names)):
                self.write_visibility_animations(names[i], times[i], times[i + 1])

    def write_parent_layers(self, index, layers):
        if index != None:
            for layer in layers:
                if layer['ind'] == index:
                    self.write_parent_layers(layer.get('parent', None), layers)
            self.body += self.tab + '  <Canvas RenderTransform="{Binding RenderTransform, ElementName=Layer%d}">\n' % index
            self.push_tab()

    def find_asset(self, id):
        for asset in self.assets:
            if asset.id == id:
                return asset
        return None

    def find_font(self, name):
        for font in self.fonts:
            if font.name == name:
                return font
        return None

    def write_layer(self, obj, layers, prefix=""):
        self.begin_reading('layer', obj)
        unused_name = self.read_field('nm')
        unused_class = self.read_field('cl', None)
        unused_is_3d = self.read_field('ddd', None)
        unused_hidden = self.read_field('hd', None)
        unused_auto_orient = self.read_field('ao', None)
        unused_blend_mode = self.read_field('bm', None)
        unused_start_frame = self.read_field('st', None)
        # Common
        index = self.read_field('ind', None)
        parent = self.read_field('parent', None)
        transform = self.read_transform(self.read_field('ks'))
        start = max(self.start, self.read_field('ip'))
        end = min(self.end, self.read_field('op'))
        time_stretch = self.read_field('sr', None)
        refId = self.read_field('refId', None)
        ty = self.read_field('ty')
        # Solid 
        solid_width = self.read_field('sw', None)
        solid_height = self.read_field('sh', None)
        solid_color = self.read_field('sc', None)
        # Precomp
        unused_precomp_w = self.read_field('w', None)
        unused_precomp_h = self.read_field('h', None)
        # Shape
        shapes = self.read_field('shapes', None)
        # Text
        text_data = self.read_field('t', None)
        self.end_reading()

        if time_stretch != 1:
            warning('Time Stretch not supported')

        if ty > LAYER_TYPE_TEXT:
            warning("Unsupported layer type '%d'" % ty)

        if self.debug:
            print(' = #%d - %s - (%s - %s)' % \
                (index, ['Precomp', 'Solid', 'Image', 'Null', 'Shape', 'Text'][ty], \
                self.as_time(start), self.as_time(end)))

        start_tab = self.tab
        name = 'Layer%s%d' % (prefix, index)
        self.write_parent_layers(parent, layers)

        root_class = "Image" if ty == LAYER_TYPE_IMAGE else "Canvas"

        self.body += self.tab + '  <%s x:Name="%s"' % (root_class, name)

        if ty == LAYER_TYPE_SOLID:
            self.body += ' Width="%d" Height="%d"' % (solid_width, solid_height)
            self.body += ' Background="%s"' % solid_color.upper()

        if ty == LAYER_TYPE_IMAGE:
            image = self.find_asset(refId)
            self.body += ' Source="%s"' % image.source

        if ty != LAYER_TYPE_NULL:
            if transform.opacity[0].first != 100:
                self.body += ' Opacity="%s"' % format_float(transform.opacity[0].first / 100.0)
            self.write_float_animation(transform.opacity[0], "Opacity", name, 0.01)

        if start > 0:
            self.body += ' Visibility="Hidden"'
        self.write_visibility_animations(name, start, end)
        self.body += '>\n'

        num_lines = self.body.count('\n')

        if self.has_transform_elements(transform):
            self.write_transform_elements(root_class, transform, name)

        if ty == LAYER_TYPE_PRECOMP:
            self.push_tab()
            asset = self.find_asset(refId)
            for layer in asset.layers:
                self.write_layer(copy.deepcopy(layer), asset.layers, '%s%d_' % (prefix, index))
            self.pop_tab()

        if ty == LAYER_TYPE_SHAPE:
            if self.debug:
                self.dump_shapes(shapes)
            self.write_shapes(shapes)

        if ty == LAYER_TYPE_TEXT:
            self.push_tab()
            self.write_text(text_data)
            self.pop_tab()

        # Don't add extra line if no elements were written
        if num_lines == self.body.count('\n'):
            self.body = self.body[:-2]
            self.body += '/>\n'
        else:
            self.body += self.tab + '  </%s>\n' % root_class

        while self.tab != start_tab:
            self.pop_tab()
            self.body += self.tab + '  </%s>\n' % root_class

    def read_assets(self, obj):
        if obj:
            for asset in obj:
                self.begin_reading('asset', asset)
                id = self.read_field('id')
                unused_e = self.read_field('e', 0)
                unused_width = self.read_field('w', None)
                unused_height = self.read_field('h', None)
                path = self.read_field('u', "")
                filename = self.read_field('p', "")
                layers = self.read_field('layers', None)
                if layers: layers.sort(key = lambda layer: layer['ind'], reverse = True)
                self.assets.append(Asset(id, path + filename, layers))
                self.end_reading()

    def read_fonts(self, obj):
        if obj:
            self.begin_reading('fonts', obj)
            fonts = self.read_field('list')
            for font in fonts:
                self.begin_reading('font', font)
                origin = self.read_field('origin', None)
                fClass = self.read_field('fClass', None)
                fFamily = self.read_field('fFamily', None)
                fStyle = self.read_field('fStyle', None)
                fWeight = self.read_field('fWeight', None)
                ascent = self.read_field('ascent', None)
                fName = self.read_field('fName', None)
                fPath = self.read_field('fPath', None)
                self.fonts.append(Font(fName, fPath, fFamily, fStyle))
                self.end_reading()
            self.end_reading()

    def read_composition(self, obj):
        self.begin_reading('composition', obj)
        name = self.read_field('nm', "")
        version = self.read_field('v')
        self.width = self.read_field('w')
        self.height = self.read_field('h')
        self.start = self.read_field('ip')
        self.end = self.read_field('op')
        self.fps = self.read_field('fr')
        layers = self.read_field('layers')
        unused_is_3d = self.read_field('ddd')
        unused_markers = self.read_field('markers', None)
        self.read_assets(self.read_field('assets', None))
        self.read_fonts(self.read_field('fonts', None))
        unused_chars = self.read_field('chars', None)
        self.end_reading()

        if self.start != 0:
            warning('Composition start is not at zero')

        secs = format_float((self.end - self.start) / float(self.fps))
        print('= %s - %d x %d @%d - %s secs - BodyMovin v%s' % (name, self.width, self.height, self.fps, secs, version))

        # Sort layers by rendering order
        layers.sort(key = lambda layer: layer['ind'], reverse = True)

        for layer in layers:
            self.write_layer(copy.deepcopy(layer), layers)

def main():
    arg_parser = ArgumentParser(description="Converts from After Effects Bodymovin format to Noesis XAML")
    arg_parser.add_argument("--version", action="version", version="%(prog)s "  + __version__)
    arg_parser.add_argument("--debug", action='store_true', help="dump layers information")
    arg_parser.add_argument("--template", action='store', metavar='<key>', help="imports lottie as a control template resource")
    arg_parser.add_argument("--repeat", action='store', metavar='<behavior>', help="describes how the animation repeats")
    arg_parser.add_argument("json_file", help="the JSON file to be converted from")
    arg_parser.add_argument("xaml_file", help="the XAML file to created")

    args = arg_parser.parse_args()
    json_parser = JsonParser(args.debug, args.template, args.repeat)
    json_parser.parse(args.json_file, args.xaml_file)

if __name__ == "__main__":
    main()