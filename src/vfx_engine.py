"""Reusable, deterministic Cairo-compatible neon and motion primitives.

The transformer geometry is genuinely three-dimensional and rotated in object
space before the standard camera projects it. Current streams are diagrams, not
simulations of individual electrons. Effects are kept modest to preserve text
legibility and avoid violent full-screen flashes.
"""
from pathlib import Path
import numpy as np
from manim import *

BACKGROUND = '#050814'
MUTED = '#A6BBD0'
CYAN = '#47E5F5'
LIME = '#6CFFB0'
CORAL = '#FF5275'
GOLD = '#FFD166'
FONT = 'DejaVu Sans'
SOUND_DIR = Path(__file__).resolve().parents[1] / 'assets' / 'audio' / 'ep01'


def add_neon_glow(mobject, color, layers=4, max_stroke=18):
    """Return halo copies behind the original, without mutating the input."""
    if layers < 1 or max_stroke <= 0:
        raise ValueError('layers and max_stroke must be positive')
    halos=[]
    # Wide faint layer behind narrower brighter layers.
    for i in range(layers, 0, -1):
        halo=mobject.copy().set_fill(opacity=0)
        halo.set_stroke(color=color, width=max_stroke*i/layers, opacity=.05 + .35*(layers-i)/max(1,layers-1), family=True)
        halos.append(halo)
    return VGroup(*halos, mobject)


def create_explosion(point, num_particles=40, colors=None, seed=42):
    """A deterministic, finite ballistic spark burst, driven by elapsed dt."""
    if num_particles < 1:
        raise ValueError('num_particles must be positive')
    colors = colors or [RED_C, ORANGE, YELLOW_C, WHITE]
    rng=np.random.default_rng(seed)
    origin=np.array(point,dtype=float)
    sparks=VGroup()
    for i in range(num_particles):
        angle=rng.uniform(0,2*PI); speed=rng.uniform(1.0,5.0)
        shard=Line(ORIGIN, RIGHT*rng.uniform(.04,.14), color=colors[i%len(colors)],stroke_width=rng.uniform(2,5))
        shard.move_to(origin)
        shard.velocity=np.array([np.cos(angle)*speed,np.sin(angle)*speed,0])
        sparks.add(shard)
    sparks.elapsed=0.0
    def update(group,dt):
        group.elapsed += dt
        for shard in group:
            shard.shift(shard.velocity*dt)
            shard.velocity[1]-=3.5*dt
            shard.velocity*=np.exp(-.6*dt)
            shard.set_opacity(max(0,1-group.elapsed/1.5))
    sparks.add_updater(update)
    return sparks


class ContinuousFlowStream(VGroup):
    """Glowing markers moving continuously along a path, with optional AC reversal."""
    def __init__(self, path, color=CYAN, count=18, speed=.18, ac=False, **kwargs):
        if count < 1:
            raise ValueError('count must be positive')
        self.path=path
        self.elapsed=0.0
        self.speed=speed
        self.ac=ac
        markers=[]
        for i in range(count):
            core=Dot(radius=.035,color=color)
            halo=Dot(radius=.09,color=color,fill_opacity=.15,stroke_width=0)
            markers.append(VGroup(halo,core))
        super().__init__(*markers,**kwargs)
        def update(group,dt):
            group.elapsed += dt
            # A path may briefly have no points during a ReplacementTransform.
            if group.path.get_num_points() == 0:
                return
            for i,marker in enumerate(group):
                offset=i/count
                # AC displacement reverses (deliberately slowed to avoid aliasing).
                p=(offset + (.06*np.sin(group.elapsed*4) if ac else group.elapsed*speed))%1
                marker.move_to(group.path.point_from_proportion(p))
        self.add_updater(update)
        update(self,0)


def create_3d_coil(turns=20, radius=.55, length=3, color=ORANGE):
    """A helix around a tilted 3D axis; standard Cairo camera projects x/y."""
    if turns < 1:
        raise ValueError('turns must be positive')
    def helix(t):
        z=length*(t/(2*PI*turns)-.5)
        raw=np.array([radius*np.cos(t),radius*np.sin(t),z])
        # z becomes horizontal; tilted y/z creates a visible 3D projection.
        return np.array([raw[2]+.25*raw[0],raw[1]+.18*raw[0],raw[0]])
    return ParametricFunction(helix,t_range=[0,2*PI*turns, 2*PI/22],color=color,stroke_width=3,use_smoothing=False)


def create_3d_magnetic_rings(center=ORIGIN, count=4, radius=.7, color=CYAN):
    """Projected tilted circular flux loops that pulse and move across a gap."""
    rings=VGroup()
    for i in range(count):
        ring=ParametricFunction(lambda t: np.array([.25*np.cos(t),np.sin(t),.55*np.cos(t)]),
                                t_range=[0,TAU,.08], color=color, stroke_width=3)
        ring.scale(radius).move_to(center+RIGHT*(i-count/2)*.55)
        rings.add(ring)
    rings.elapsed=0.
    def update(group,dt):
        group.elapsed+=dt
        for i,ring in enumerate(group):
            ring.set_opacity(.2+.55*(.5+.5*np.sin(group.elapsed*3-i*.8)))
            ring.shift(RIGHT*(.12*np.cos(group.elapsed*2-i*.7)*dt))
    rings.add_updater(update)
    return rings


def kinetic_wave(width=5.2,height=1.5,kind='ac',color=CORAL):
    """Traveling waveform with an animated scan line and clear axes."""
    x=np.linspace(-width/2,width/2,180)
    axes=VGroup(Line(LEFT*width/2,RIGHT*width/2,stroke_color='#567085',stroke_width=2),
                Line(DOWN*height*.7,UP*height*.7,stroke_color='#567085',stroke_width=2).shift(LEFT*width/2))
    curve=VMobject(color=color,stroke_width=4)
    curve.clock=0.
    def update(m,dt):
        m.clock+=dt
        wave=np.sin((x+width/2)*TAU*2/width - m.clock*2.2)
        if kind=='half': wave=np.maximum(0,wave)
        if kind=='rect': wave=np.abs(wave)
        if kind=='ripple': wave=.78+.11*np.sin((x+width/2)*TAU*2/width-m.clock*2.2)
        if kind=='flat': wave=np.ones_like(x)*.8
        points=np.column_stack((x,wave*height*.42,np.zeros_like(x)))
        # Relative to axes so move_to on the parent remains stable.
        m.set_points_as_corners(points+axes[0].get_center())
    curve.add_updater(update); update(curve,0)
    halo=curve.copy().clear_updaters().set_stroke(color, width=12,opacity=.12)
    halo.add_updater(lambda h: h.become(curve.copy().clear_updaters().set_stroke(color,width=12,opacity=.12)))
    return VGroup(axes,halo,curve)


def heading(text, size=38, color=WHITE):
    return Text(text,font=FONT,font_size=size,weight=BOLD,color=color)


def tag(text, color=CYAN, size=20):
    return Text(text,font=FONT,font_size=size,weight=BOLD,color=color)


def circuit_panel(width=6,height=4):
    return RoundedRectangle(width=width,height=height,corner_radius=.18,stroke_width=1.5,
                            stroke_color='#345570',fill_color='#0D1C32',fill_opacity=.55)


def live_grid(width,height):
    """Subtle drifting grid plus rotating contour, not a strobe."""
    grid=NumberPlane(x_range=[-width,width,1],y_range=[-height,height,1],x_length=2*width,y_length=2*height,
                     background_line_style={'stroke_color':'#305275','stroke_opacity':.18,'stroke_width':1.0},
                     axis_config={'stroke_opacity':0,'include_ticks':False})
    def update(g,dt):
        g.shift(RIGHT*dt*.10 + UP*dt*.025)
        if g.get_center()[0]>.9: g.shift(LEFT*1)
        if g.get_center()[1]>.9: g.shift(DOWN*1)
    grid.add_updater(update)
    contour=VGroup(*[Ellipse(width=width*.9+i*.45,height=height*.65+i*.28,color='#163B57',stroke_opacity=.38,stroke_width=2) for i in range(3)])
    contour.add_updater(lambda m,dt: m.rotate(.035*dt))
    return VGroup(grid,contour)

