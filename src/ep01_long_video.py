"""Five chapters of the educational episode, in standard 16:9 Manim framing."""
from manim import *
import numpy as np
from ep01_visuals import *


class Ch1_TheHookAndACvsDC(EpisodeScene):
    def construct(self):
        head = self.header('01', 'The wall and the battery')
        danger = words('NEVER CONNECT A BATTERY TO MAINS', 31, RED_C, weight=BOLD).move_to(UP*.25)
        sub = words('Risk of shock, fire and battery failure', 23, color=MUTED).next_to(danger,DOWN)
        self.beat('Every day you plug your phone into the wall without thinking twice. But that little brick is doing some serious electrical work. Never connect a phone or a battery directly to a wall outlet: the result could be electric shock, fire, or a damaged battery. The charger is a vital safety barrier.', FadeIn(head), FadeIn(danger), FadeIn(sub))
        wall=VGroup(label('WALL  /  AC',RED_C), graph('ac',5,2)).arrange(DOWN,buff=.3).move_to(LEFT*3.35+UP*.15)
        phone=VGroup(label('USB OUTPUT  /  DC',GREEN_C), graph('flat',5,2)).arrange(DOWN,buff=.3).move_to(RIGHT*3.35+UP*.15)
        ac_eq=formula('ac',30).next_to(wall,DOWN,buff=.2)
        dc=label('typically 5 V DC',GREEN_C,24).next_to(phone,DOWN,buff=.2)
        time=ValueTracker(0)
        ac_dot=always_redraw(lambda: Dot(LEFT*3.35 + DOWN*2.25 + RIGHT*np.sin(time.get_value()*2), color=YELLOW_C, radius=.09))
        dc_dot=always_redraw(lambda: Dot(RIGHT*3.35 + DOWN*2.25 + RIGHT*((time.get_value()%1)*2-1), color=GREEN_C, radius=.09))
        wires=VGroup(Line(LEFT*4.7+DOWN*2.25, LEFT*2+DOWN*2.25,color=RED_C),Line(RIGHT*2+DOWN*2.25, RIGHT*4.7+DOWN*2.25,color=GREEN_C))
        self.beat('The wall supplies alternating voltage: its polarity reverses, typically fifty or sixty times a second. In North America, a common outlet is one hundred twenty volts RMS; in many other places it is about two hundred thirty. A USB output often starts at five volts DC. The phone then manages the battery voltage and charging current itself.', FadeOut(danger), FadeOut(sub), FadeIn(wall), FadeIn(phone), Write(ac_eq), FadeIn(dc), FadeIn(wires), FadeIn(ac_dot), FadeIn(dc_dot), time.animate.set_value(8))
        stage = VGroup(*[VGroup(RoundedRectangle(width=2.6,height=.7,corner_radius=.12,color=c),label(s,c,18)) for s,c in [('RECTIFY',RED_C),('SWITCH',YELLOW_C),('ISOLATE',TEAL_C),('REGULATE',GREEN_C)]]).arrange(RIGHT,buff=.22).move_to(DOWN*2.55)
        self.beat('Inside a modern charger, rectification, rapid switching, magnetic isolation and regulation work together. To understand the ideas, we will first explore a simpler teaching model, then see how real switching chargers differ. Let us open the box.', FadeOut(wires), FadeOut(ac_dot), FadeOut(dc_dot), FadeIn(stage))
        self.clear_scene()


class Ch2_TheWirelessJumpTransformer(EpisodeScene):
    def construct(self):
        head=self.header('02','The magnetic jump')
        circuit=svg('transformer',4.4).move_to(LEFT*3.3+UP*.35)
        gap=label('SEPARATE WINDINGS',TEAL_C,20).next_to(circuit,DOWN,buff=.4)
        eq=formula('transformer',45).move_to(RIGHT*3.3+UP*1.3)
        note=words('Ideal turns ratio',22,color=MUTED).next_to(eq,DOWN,buff=.25)
        self.beat('A transformer moves energy between separate windings without a direct electrical connection between them. A changing current in the primary produces a changing magnetic field in the core. That field links the secondary winding and induces a voltage there. The insulation and construction are crucial for safety; do not assume every transformer is safely isolated.', FadeIn(head), Create(circuit), FadeIn(gap))
        rings=VGroup(*[Circle(radius=r,color=TEAL_C,stroke_width=3,stroke_opacity=.7).move_to(circuit) for r in (.45,.75,1.05)])
        self.beat('In an ideal transformer, the voltage ratio follows the turns ratio. Fewer secondary turns mean a lower secondary voltage. The relationship describes the winding voltages, not a promise that a bare winding is ready to charge a battery.', LaggedStart(*[Create(c) for c in rings],lag_ratio=.12), Write(eq), FadeIn(note))
        wave=graph('ac',4.5,1.6).move_to(RIGHT*3.25+DOWN*1.25)
        smaller=graph('ac',4.5,1.6).move_to(wave)
        smaller[1].stretch(.35,1,about_point=smaller[0].c2p(0,0)).set_color(TEAL_C)
        self.add(wave)
        self.beat('A changing magnetic field is the key. Modern phone adapters first rectify the mains, then switch the resulting high voltage at high frequency through a small transformer. This is different from putting a large mains-frequency transformer directly at the wall, but the magnetic principle is the same.', Transform(wave,smaller), FadeOut(rings))
        self.clear_scene()


class Ch3_OneWayValveDiode(EpisodeScene):
    def construct(self):
        head=self.header('03','A one-way valve')
        circuit=svg('single_diode',4.3).move_to(LEFT*3.45+UP*.25)
        text=label('ONE DIODE',YELLOW_C,20).next_to(circuit,DOWN)
        gr=graph('ac',5.1,2.3).move_to(RIGHT*3.4+UP*.25)
        self.beat('A diode is an electronic one-way valve. In the simplest model it allows conventional current in one direction and blocks it in the other. Put one in series with a load and only one half of a sinusoidal cycle can pass. This is called half-wave rectification.',FadeIn(head),Create(circuit),FadeIn(text),Create(gr))
        arrow=Arrow(LEFT*5+DOWN*1.45,LEFT*2+DOWN*1.45,buff=0,color=GREEN_C,stroke_width=7)
        stop=label('REVERSE BLOCKED',RED_C,20).next_to(arrow,DOWN,buff=.12)
        half=graph('half',5.1,2.3).move_to(gr)
        eq=formula('half',27).next_to(gr,DOWN,buff=.25)
        self.beat('Imagine a turnstile: current can pass forward, but the reverse half-cycle is blocked. On the graph the negative troughs disappear, leaving gaps between the positive humps. The ideal mathematical model is the maximum of zero and the input sine wave.',GrowArrow(arrow),FadeIn(stop),Transform(gr,half),Write(eq))
        warn=words('Half the ideal waveform power reaches the load',21,color=YELLOW_C).to_edge(DOWN,buff=.48)
        self.beat('With an ideal diode and a resistive load, the average load power is half that of the original sine wave. That is not a universal statement about how much energy every real charger wastes. It is a useful clue that a better rectifier can use both halves of the cycle.',FadeIn(warn))
        self.clear_scene()


class Ch4_TheMagicDiamondBridge(EpisodeScene):
    def construct(self):
        head=self.header('04','The four-diode diamond')
        circuit,ds,redpath,bluepath=bridge_diagram(.9)
        circuit.move_to(LEFT*3.35+UP*.1)
        gr=graph('ac',5.1,2.3).move_to(RIGHT*3.35+UP*.3)
        caption=label('CONVENTIONAL CURRENT',MUTED,18).next_to(circuit,DOWN,buff=.35)
        self.beat('A bridge rectifier uses four diodes to route both halves of the input through a load in the same direction. Here the moving dots represent conventional current, not the motion of individual electrons. Each conducting route uses two diodes.',FadeIn(head),Create(circuit),FadeIn(caption),Create(gr))
        dot=Dot(redpath.get_start(),radius=.1,color=RED_C)
        self.add(dot)
        self.beat('During one half-cycle, the red route carries current from one input, through the top output and the load, then back to the other input. The other pair of diodes blocks the reverse routes.', MoveAlongPath(dot,redpath), ds[0].animate.set_color(RED_C), ds[3].animate.set_color(RED_C))
        dot.move_to(bluepath.get_start()).set_color(BLUE_C)
        self.beat('When the input reverses, the blue pair conducts instead. Notice that through the load, the current still goes from the same top output toward the bottom. The input has reversed, but the load polarity has not.',MoveAlongPath(dot,bluepath), ds[0].animate.set_color(WHITE),ds[3].animate.set_color(WHITE),ds[1].animate.set_color(BLUE_C),ds[2].animate.set_color(BLUE_C))
        rect=graph('rect',5.1,2.3).move_to(gr)
        eq=formula('rect',32).next_to(gr,DOWN,buff=.3)
        self.beat('Ignoring diode voltage drops, the bridge performs an absolute value operation: it flips the negative valleys into positive peaks. Real diodes have losses, so the output is a little lower than this ideal curve.', Transform(gr,rect),Write(eq),FadeOut(dot))
        self.clear_scene()


class Ch5_TheCapacitorIron(EpisodeScene):
    def construct(self):
        head=self.header('05','From ripples to a steady output')
        circuit=svg('smoothed_charger',5.5).move_to(LEFT*3.3+UP*.2)
        cap=label('C',TEAL_C,26).next_to(circuit,DOWN,buff=.15)
        wave=graph('rect',5.2,2.3).move_to(RIGHT*3.35+UP*.1)
        self.beat('The rectified voltage is positive, but it still falls between peaks. A capacitor connected across a load stores energy as it charges. As the source voltage falls, the capacitor can supply the load, helping fill the valleys. Think of a small reservoir that tops up at each peak.',FadeIn(head),Create(circuit),FadeIn(cap),Create(wave))
        ripple=graph('ripple',5.2,2.3).move_to(wave)
        eq=formula('cap',32).next_to(wave,DOWN,buff=.2)
        tank=Rectangle(width=.35,height=1.4,stroke_color=TEAL_C).next_to(circuit,LEFT,buff=.25)
        fill=Rectangle(width=.25,height=1,fill_color=TEAL_C,fill_opacity=.8,stroke_width=0).align_to(tank,DOWN).shift(UP*.05).align_to(tank,LEFT).shift(RIGHT*.05)
        self.beat('Between charging peaks, an ideal capacitor discharging through a fixed resistor follows an exponential curve. The time constant is R times C. More capacitance or a lighter load generally reduces the ripple, though real circuits include losses and changing current.',Transform(wave,ripple),Write(eq),Create(tank),FadeIn(fill))
        flat=graph('flat',5.2,2.3).move_to(wave)
        batt=battery(1.4).move_to(LEFT*5.8+DOWN*1.5)
        dc=label('REGULATED USB OUTPUT',GREEN_C,20).next_to(wave,UP,buff=.1)
        self.beat('Regulation and feedback control the output, typically starting at five volts for USB. Inside the phone another charging circuit protects and manages the battery. Real switch-mode chargers use a more complex sequence than this simplified transformer, diode and capacitor demonstration. Respect the mains: never open or modify a plugged-in charger. Subscribe for more hidden engineering.',Transform(wave,flat),FadeIn(batt),FadeIn(dc))
        self.clear_scene()
