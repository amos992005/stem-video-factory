"""Large, self-contained visuals for the cinematic acts (no fixed HUD)."""
import numpy as np
from manim import *
from vfx_engine import *
from studio_components import battery_icon,outlet_icon,wireframe_brick,transformer_unit,diode_gate,bridge_unit,energy_tank,burst_arc
from ep01_visuals import formula


def tube_pair(width=11):
    objects=VGroup()
    for y,color,ac in [(1.25,CORAL,True),(-.8,LIME,False)]:
        path=Line(LEFT*width/2+UP*y,RIGHT*width/2+UP*y,color=color,stroke_width=5)
        tube=RoundedRectangle(width=width,height=1.4,corner_radius=.55,color=color,stroke_width=4,fill_color='#172738',fill_opacity=.85).move_to(path)
        glow=add_neon_glow(tube,color,2,16)
        stream=ContinuousFlowStream(path,GOLD if ac else LIME,count=16,speed=.12,ac=ac)
        # Large drifting carriers, with short vectors indicating direction.
        for marker in stream:
            marker.scale(2.6)
        objects.add(glow,path,stream)
    return objects


def charger_blueprint():
    shell=RoundedRectangle(width=10,height=3.4,corner_radius=.4,color=CYAN,stroke_width=5,fill_color='#10243C',fill_opacity=.55)
    boxes=VGroup()
    for i,c in enumerate((CORAL,GOLD,CYAN,LIME)):
        rect=RoundedRectangle(width=1.9,height=2,corner_radius=.2,color=c,stroke_width=4,fill_color=c,fill_opacity=.12).shift(LEFT*3.2+RIGHT*i*2.15)
        rect.clock=float(i)
        def pulse(m,dt,i=i):
            m.clock+=dt;m.set_fill(opacity=.08+.2*(.5+.5*np.sin(m.clock*2-i)))
        rect.add_updater(pulse);boxes.add(rect)
    path=Line(LEFT*4.4,RIGHT*4.4).set_opacity(0)
    flow=ContinuousFlowStream(path,CYAN,count=24,speed=.12)
    return VGroup(add_neon_glow(shell,CYAN,3,18),boxes,path,flow)


def transformer_full(width=10):
    t=transformer_unit(width)
    t.scale_to_fit_width(width)
    return t


def mechanical_valve():
    pipe=RoundedRectangle(width=11,height=3.2,corner_radius=.7,color=CYAN,stroke_width=6,fill_color='#10263B',fill_opacity=.55)
    hinge=Dot(UP*1.15,radius=.12,color=GOLD)
    gate=Line(UP*1.15,DOWN*1.15,color=GOLD,stroke_width=14)
    path=Line(LEFT*5.3,RIGHT*5.3).set_opacity(0)
    flow=ContinuousFlowStream(path,LIME,24,.2)
    return VGroup(add_neon_glow(pipe,CYAN,2,16),hinge,add_neon_glow(gate,GOLD,3,20),path,flow),gate,path,flow


def giant_wave(kind='ac',color=CORAL,width=11,height=3.5):
    return kinetic_wave(width,height,kind,color).shift(UP*.35)


def rectified_bridge_trace(width=10,height=3):
    x=np.linspace(0,4*PI,350); xcoord=np.linspace(-width/2,width/2,len(x))
    s=np.abs(np.sin(x)); peak=np.pi/2
    y=np.where(x<peak,s,np.maximum(s,np.exp(-np.mod(x-peak,np.pi)/6.0)))
    pts=np.column_stack((xcoord,(y-.5)*height+.25,np.zeros_like(x)))
    curve=VMobject(color=LIME,stroke_width=6).set_points_as_corners(pts)
    shade=Polygon(*[np.array([xcoord[0],-height*.5+.25,0]),*pts,np.array([xcoord[-1],-height*.5+.25,0])],fill_color=LIME,fill_opacity=.12,stroke_width=0)
    return curve,shade


def battery_final():
    battery=battery_icon(1.5).shift(RIGHT*3.6+UP*.3)
    gate=RoundedRectangle(width=2.8,height=1.8,corner_radius=.25,color=CYAN,stroke_width=5,fill_color='#0B2C3E',fill_opacity=.8).shift(LEFT*2.8+UP*.3)
    laser=Line(gate.get_right(),battery.get_left(),color=LIME,stroke_width=7)
    return battery,add_neon_glow(gate,CYAN,2,16),add_neon_glow(laser,LIME,3,20)
