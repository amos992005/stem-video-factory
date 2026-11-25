"""Standalone portrait shorts; bottom region is reserved for burnt-in captions."""
from manim import *
import numpy as np
from ep01_visuals import *

config.pixel_width = 1080
config.pixel_height = 1920
config.frame_width = 9
config.frame_height = 16


def heading(top, title):
    return VGroup(label(top, TEAL_C, 22), words(title, 39, WHITE, weight=BOLD, line_spacing=.9)).arrange(DOWN,buff=.2).move_to(UP*5.45)


class Short01_ACvsDC(EpisodeScene):
    def construct(self):
        h=heading('PHONE CHARGER  /  01','AC vs DC')
        warning=words('NEVER CONNECT\nA BATTERY TO MAINS', 29, RED_C, weight=BOLD, line_spacing=.9).move_to(UP*2.8)
        wave=graph('ac',6.4,2.2).move_to(UP*.3)
        top=label('WALL  •  ALTERNATING VOLTAGE', RED_C, 19).next_to(wave,UP,buff=.15)
        self.beat('Why is connecting a phone battery directly to a wall outlet so dangerous? It can cause electric shock, fire, and battery failure. Never try it. The outlet supplies alternating voltage, while your phone needs carefully controlled direct current.',FadeIn(h),FadeIn(warning),Create(wave),FadeIn(top))
        timer=ValueTracker(0)
        acdot=always_redraw(lambda: Dot(point=np.array([2*np.sin(timer.get_value()*2),-2.05,0]),color=YELLOW_C,radius=.12))
        dcdot=always_redraw(lambda: Dot(point=np.array([-2.7+(timer.get_value()%1)*5.4,-3.15,0]),color=GREEN_C,radius=.12))
        wire=VGroup(Line(LEFT*3,RIGHT*3,color=RED_C),Line(LEFT*3,RIGHT*3,color=GREEN_C)).arrange(DOWN,buff=1.1).move_to(DOWN*2.6)
        self.add(acdot,dcdot)
        self.beat('With AC, charges oscillate back and forth. With DC, the current has one direction. A USB charger usually begins with a regulated five volt output, and the phone controls its own battery charging.',FadeOut(warning),FadeIn(wire),timer.animate.set_value(8))
        half=graph('half',6.4,2.2).move_to(wave)
        tip=words('ONE DIODE: HALF-WAVE',25,YELLOW_C,weight=BOLD).move_to(DOWN*2.8)
        self.beat('One diode blocks the reverse half of the wave. With an ideal resistive load, that leaves half the original waveform power. A four-diode bridge makes use of both halves. Watch the full video to see how the whole charger works.',Transform(wave,half),FadeOut(wire),FadeOut(acdot),FadeOut(dcdot),FadeIn(tip),FadeOut(top))
        self.clear_scene()


class Short02_WirelessTransformer(EpisodeScene):
    def construct(self):
        h=heading('PHONE CHARGER  /  02','The magnetic jump')
        trans=svg('transformer',5.5).move_to(UP*1.5)
        gap=label('SEPARATE WINDINGS',TEAL_C,24).next_to(trans,DOWN,buff=.3)
        self.beat('Did you know the wall side of an isolated phone charger does not have a direct electrical connection to your phone cord? Energy crosses a transformer through a changing magnetic field. The insulating barrier is there to help protect you from the mains.',FadeIn(h),Create(trans),FadeIn(gap))
        rings=VGroup(*[Circle(radius=r,color=TEAL_C,stroke_width=4,stroke_opacity=.7).move_to(trans) for r in (.45,.8,1.15)])
        eq=formula('transformer',48).move_to(DOWN*1.75)
        self.beat('A changing current in the primary winding creates a changing magnetic field in the core. That field induces voltage in the separate secondary. In an ideal transformer, the voltage ratio follows the turns ratio: fewer secondary turns mean lower voltage.',LaggedStart(*[Create(c) for c in rings],lag_ratio=.15),Write(eq))
        note=words('REAL CHARGERS SWITCH\nAT HIGH FREQUENCY',24,YELLOW_C,weight=BOLD).move_to(DOWN*3.65)
        self.beat('Modern chargers first rectify the mains, then switch at high frequency through a compact transformer. That is why the brick can be so small. Watch the full video for the complete story.',FadeOut(rings),FadeIn(note))
        self.clear_scene()


class Short03_DiamondBridge(EpisodeScene):
    def construct(self):
        h=heading('PHONE CHARGER  /  03','The diode diamond')
        circuit,ds,redpath,bluepath=bridge_diagram(.9)
        circuit.move_to(UP*1.5)
        note=label('CONVENTIONAL CURRENT',MUTED,18).next_to(circuit,DOWN,buff=.1)
        self.beat('This classic diamond circuit performs a famous math function in real life. Four diodes form a bridge rectifier. Their one-way action routes both halves of an alternating input through the load in the same direction.',FadeIn(h),Create(circuit),FadeIn(note))
        dot=Dot(redpath.get_start(),radius=.1,color=RED_C)
        self.add(dot)
        self.beat('On one half-cycle, current follows the red path. Two diodes conduct, and current flows down through the load.',MoveAlongPath(dot,redpath),ds[0].animate.set_color(RED_C),ds[3].animate.set_color(RED_C))
        dot.move_to(bluepath.get_start()).set_color(BLUE_C)
        self.beat('When the input reverses, the blue pair takes over. The load still sees current in the same direction. These dots show conventional current, not individual electrons.',MoveAlongPath(dot,bluepath),ds[0].animate.set_color(WHITE),ds[3].animate.set_color(WHITE),ds[1].animate.set_color(BLUE_C),ds[2].animate.set_color(BLUE_C))
        wave=graph('ac',5.8,1.7).move_to(DOWN*2.2)
        self.add(wave)
        rect=graph('rect',5.8,1.7).move_to(wave)
        eq=formula('rect',28).move_to(DOWN*3.9)
        self.beat('Ideally, that flips the negative valleys upward: the absolute value of a sine wave. A capacitor can smooth the resulting ripples. Watch the full video for the real charger story.',Transform(wave,rect),Write(eq),FadeOut(dot))
        self.clear_scene()
