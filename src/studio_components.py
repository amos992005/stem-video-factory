"""Animated educational objects shared by the horizontal and vertical cuts."""
import numpy as np
from manim import *
from vfx_engine import *
from ep01_visuals import bridge_diagram, formula


def battery_icon(scale=1.0):
    shell=RoundedRectangle(width=1.35,height=2.1,corner_radius=.18,color=LIME,stroke_width=4)
    nub=RoundedRectangle(width=.4,height=.18,corner_radius=.04,color=LIME,stroke_width=3).next_to(shell,UP,buff=0)
    fill=RoundedRectangle(width=1.05,height=1.35,corner_radius=.1,fill_color=LIME,fill_opacity=.65,stroke_width=0).move_to(shell).shift(DOWN*.2)
    bolt=Polygon(ORIGIN+UP*.55+LEFT*.05,ORIGIN+LEFT*.28,ORIGIN+RIGHT*.02,ORIGIN+DOWN*.55+RIGHT*.05,ORIGIN+RIGHT*.28,ORIGIN+LEFT*.02,fill_color=WHITE,fill_opacity=1,stroke_width=0).move_to(shell)
    return VGroup(add_neon_glow(shell,LIME,2,12),nub,fill,bolt).scale(scale)


def outlet_icon(scale=1):
    plate=RoundedRectangle(width=1.6,height=2,corner_radius=.2,color=CYAN,stroke_width=4,fill_color='#11293D',fill_opacity=.75)
    holes=VGroup(*[RoundedRectangle(width=.11,height=.5,corner_radius=.05,color=WHITE,fill_color=WHITE,fill_opacity=.8).shift(RIGHT*x+UP*.15) for x in (-.33,.33)],Circle(radius=.12,color=WHITE,fill_opacity=.6).shift(DOWN*.47))
    return VGroup(add_neon_glow(plate,CYAN,2,12),holes).scale(scale)


def wireframe_brick():
    front=RoundedRectangle(width=2.7,height=1.5,corner_radius=.18,color=CYAN,stroke_width=4)
    back=front.copy().shift(RIGHT*.35+UP*.28).set_stroke(CYAN,2,.55)
    connectors=VGroup(*[Line(a,b,color=CYAN,stroke_width=2) for a,b in zip([front.get_corner(UL),front.get_corner(UR),front.get_corner(DL),front.get_corner(DR)],[back.get_corner(UL),back.get_corner(UR),back.get_corner(DL),back.get_corner(DR)])])
    return VGroup(back,connectors,add_neon_glow(front,CYAN,2,13))


def wave_card(kind,color,width=5.4,height=2):
    panel=circuit_panel(width+.35,height+1)
    graph=kinetic_wave(width,height*.8,kind,color)
    return VGroup(panel,graph)


def transformer_unit(width=6):
    left=create_3d_coil(20,.45,2.2,CORAL).move_to(LEFT*1.85)
    right=create_3d_coil(5,.45,1.1,LIME).move_to(RIGHT*1.85)
    l=add_neon_glow(left,CORAL,2,12); r=add_neon_glow(right,LIME,2,12)
    # A slow oscillating 3D rotation, not a flattened 2D spiral.
    for coil in (l,r):
        coil.clock=0.
        def turn(m,dt):
            m.clock+=dt
            m.rotate(.17*np.cos(m.clock*.7)*dt,axis=UP,about_point=m.get_center())
        coil.add_updater(turn)
    rings=create_3d_magnetic_rings(ORIGIN,4,.8)
    boundary=VGroup(Line(UP*1.15,DOWN*1.15,color='#6E95A3',stroke_width=2),Line(UP*1.15+RIGHT*.16,DOWN*1.15+RIGHT*.16,color='#6E95A3',stroke_width=2))
    assembly=VGroup(l,r,boundary,rings)
    if assembly.width>width: assembly.scale_to_fit_width(width)
    return assembly


def diode_gate():
    wire=Line(LEFT*2,RIGHT*2,color=CYAN,stroke_width=5)
    left=add_neon_glow(Line(LEFT*2,LEFT*.5,color=CYAN,stroke_width=4),CYAN,2,12)
    right=add_neon_glow(Line(RIGHT*.5,RIGHT*2,color=CYAN,stroke_width=4),CYAN,2,12)
    triangle=Polygon(LEFT*.5+UP*.45,LEFT*.5+DOWN*.45,RIGHT*.45,color=GOLD,fill_color=GOLD,fill_opacity=.15,stroke_width=4)
    gate=Line(RIGHT*.5+UP*.55,RIGHT*.5+DOWN*.55,color=GOLD,stroke_width=6)
    base=VGroup(left,right,add_neon_glow(triangle,GOLD,2,12),add_neon_glow(gate,GOLD,2,12))
    path=Line(LEFT*2,RIGHT*2).set_opacity(0)
    return VGroup(base,path),path


def bridge_unit(scale=.7):
    diagram,diodes,positive,negative=bridge_diagram(scale)
    # Glows are copied after the source diagram is laid out, so the wiring stays exact.
    glow=diagram.copy().clear_updaters().set_fill(opacity=0).set_stroke(color=CYAN,width=12,opacity=.16,family=True)
    return VGroup(glow,diagram),diodes,positive,negative


def energy_tank():
    shell=RoundedRectangle(width=.9,height=2.4,corner_radius=.2,color=CYAN,stroke_width=4)
    level=RoundedRectangle(width=.65,height=1.65,corner_radius=.12,fill_color=CYAN,fill_opacity=.65,stroke_width=0).move_to(shell).shift(DOWN*.2)
    level.clock=0.
    def surge(m,dt):
        m.clock+=dt
        height=.45+1.48*(.5+.5*np.sin(m.clock*2.6))
        replacement=RoundedRectangle(width=.65,height=height,corner_radius=.10,fill_color=CYAN,fill_opacity=.68,stroke_width=0)
        replacement.move_to(shell.get_bottom()+UP*(height/2+.12))
        m.become(replacement)
    level.add_updater(surge)
    return VGroup(add_neon_glow(shell,CYAN,2,12),level)


def burst_arc(start,end,color=GOLD):
    rng=np.random.default_rng(29)
    points=[]
    for i in range(13):
        alpha=i/12
        p=(1-alpha)*np.array(start)+alpha*np.array(end)
        if i not in (0,12): p=p+UP*rng.uniform(-.3,.3)
        points.append(p)
    arc=VMobject(color=color,stroke_width=5).set_points_as_corners(points)
    return add_neon_glow(arc,color,3,20)
