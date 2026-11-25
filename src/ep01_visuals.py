"""Reusable Manim building blocks; all current arrows show conventional current."""
import numpy as np
from manim import *
from manim_voiceover import VoiceoverScene
from edge_tts_service import EdgeTTSService
from ep01_math import LATEX
from generate_ep01_svgs import SVG_DIR, generate

INK = '#000000'
MUTED = '#A9B8C9'
FONT = 'DejaVu Sans'


def words(text, size=26, color=WHITE, **kw):
    return Text(text, font=FONT, font_size=size, color=color, **kw)


def label(text, color=TEAL_C, size=21):
    return words(text, size, color, weight=BOLD)


def svg(name, width=4.5):
    generate()
    return SVGMobject(str(SVG_DIR / f'{name}.svg')).scale_to_fit_width(width)


def formula(key, size=35):
    return MathTex(LATEX[key], font_size=size, color=WHITE)


def graph(kind='ac', width=5.5, height=2.2):
    axes = Axes(x_range=[0, 4*PI, PI], y_range=[-1.25, 1.25, 1],
                x_length=width, y_length=height, tips=False,
                axis_config={'stroke_width': 2, 'color': MUTED, 'include_ticks': False})
    def f(x):
        s = np.sin(x)
        if kind == 'half': return max(0, s)
        if kind == 'rect': return abs(s)
        if kind == 'flat': return 0.82
        if kind == 'ripple':
            peak = PI/2
            if x < peak: return abs(s)
            elapsed = (x-peak) % PI
            return max(abs(s), np.exp(-elapsed/6))
        return s
    curve = axes.plot(f, x_range=[0, 4*PI, .025], color={'ac': RED_C, 'half': YELLOW_C, 'rect': BLUE_C, 'ripple': GREEN_C, 'flat': GREEN_C}[kind], stroke_width=5, use_smoothing=False)
    return VGroup(axes, curve)


def battery(height=1.7):
    body = RoundedRectangle(width=0.9, height=1.8, corner_radius=.12, color=WHITE, stroke_width=3)
    nub = Rectangle(width=.32, height=.12, color=WHITE).next_to(body, UP, buff=0)
    level = Rectangle(width=.7, height=1.2, fill_color=GREEN_C, fill_opacity=0.85, stroke_width=0).move_to(body).shift(DOWN*.2)
    return VGroup(body, nub, level).scale_to_fit_height(height)


def bridge_diagram(scale=1.0):
    """Four diodes and a load; paths use the exact circuit's vertices."""
    L, T, R, B = np.array([-1.45,0,0]), np.array([0,1.45,0]), np.array([1.45,0,0]), np.array([0,-1.45,0])
    def diode(a,b):
        u=(b-a)/np.linalg.norm(b-a); v=np.array([-u[1],u[0],0]); mid=(a+b)/2
        base=mid-u*.22; tip=mid+u*.20
        return VGroup(Line(a,base,stroke_width=3), Polygon(base+v*.17,base-v*.17,tip,stroke_width=3,fill_opacity=0),
                      Line(tip+v*.18,tip-v*.18,stroke_width=3), Line(tip,b,stroke_width=3))
    ds = VGroup(diode(L,T), diode(R,T), diode(B,L), diode(B,R))
    # A load on the right, with bridges to the +/- vertices.
    p1, p2, p3, p4 = T+UP*.45, T+UP*.45+RIGHT*2.4, B+DOWN*.45+RIGHT*2.4, B+DOWN*.45
    wires = VGroup(Line(L,L+LEFT*.6), Line(R,R+RIGHT*.6), Line(T,p1), Line(p1,p2), Line(p2,p3), Line(p3,p4), Line(p4,B))
    load = Rectangle(width=.30,height=.55,fill_color=INK,fill_opacity=1,stroke_color=WHITE,stroke_width=3).move_to((p2+p3)/2)
    plus=label('+',GREEN_C,24).next_to(T,UP,buff=.05)
    minus=label('−',MUTED,24).next_to(B,DOWN,buff=.05)
    # Curves go through the load in the same direction for either polarity.
    def path(points): return VMobject().set_points_as_corners(points).set_opacity(0)
    positive=path([L,T,p1,p2,p3,p4,B,R]); negative=path([R,T,p1,p2,p3,p4,B,L])
    group=VGroup(ds,wires,load,plus,minus,positive,negative).scale(scale)
    return group, ds, positive, negative


class EpisodeScene(VoiceoverScene):
    def setup(self):
        super().setup()
        self.camera.background_color = INK
        self.set_speech_service(EdgeTTSService())

    def beat(self, narration, *animations):
        with self.voiceover(text=narration) as tracker:
            if animations:
                self.play(*animations, run_time=max(0.1, tracker.duration * 0.96))

    def clear_scene(self):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in list(self.mobjects)], run_time=.5)

    def header(self, number, title):
        title_obj = words(title, 36, WHITE, weight=BOLD).to_edge(UP, buff=.38)
        tag = label(f'EP 01  /  {number}', TEAL_C, 18).to_corner(UL, buff=.28)
        rule = Line(LEFT*6.6, RIGHT*6.6, color='#334155', stroke_width=1).next_to(title_obj, DOWN, buff=.18)
        return VGroup(title_obj, tag, rule)
