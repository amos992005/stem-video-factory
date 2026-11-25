"""Episode 01, five motion-driven landscape chapters; run with Manim -qh."""
from manim import *
from vfx_engine import *
from studio_components import *


class Ch1_TheHookAndACvsDC(StudioScene):
    def construct(self):
        self.title('01','THE WALL IS NOT YOUR BATTERY')
        wall=outlet_icon(1.05).move_to(LEFT*3.6+UP*.25)
        battery=battery_icon(1.05).move_to(RIGHT*3.6+UP*.25)
        arc=burst_arc(wall.get_right(),battery.get_left())
        self.add(wall,battery)
        self.sentence('Every day, you plug your phone into the wall without thinking twice.','INSIDE THE BRICK',FadeIn(arc),sfx='zap')
        sparks=create_explosion(battery.get_center(),40)
        self.add(sparks)
        self.sentence('But directly connecting a battery to mains can cause shock, fire, and battery failure.','NEVER CONNECT DIRECTLY',shake=True)
        self.sentence('This animation is a warning, not an instruction to try it.','DANGER  /  MAINS VOLTAGE',FadeOut(arc))
        left=wave_card('ac',CORAL,5.2,1.8).move_to(LEFT*3.35)
        right=wave_card('flat',LIME,5.2,1.8).move_to(RIGHT*3.35)
        ac=tag('WALL  /  AC',CORAL,23).next_to(left,UP,buff=.16)
        dc=tag('USB  /  DC',LIME,23).next_to(right,UP,buff=.16)
        self.sentence('The wall supplies alternating voltage: its polarity keeps reversing.','A WAVE THAT REVERSES',FadeOut(wall),FadeOut(battery),FadeOut(sparks),FadeIn(left),FadeIn(ac))
        path1=Line(LEFT*5.5+DOWN*1.7,LEFT*1.2+DOWN*1.7,color=CORAL,stroke_width=4)
        stream1=ContinuousFlowStream(path1,color=GOLD,count=18,ac=True)
        self.sentence('In North America that is usually one hundred twenty volts RMS at sixty hertz.','60 HZ  /  MOTION SLOWED',Create(path1),FadeIn(stream1))
        self.sentence('Many other countries use about two hundred thirty volts at fifty hertz.','VOLTAGE VARIES BY COUNTRY')
        path2=Line(RIGHT*1.2+DOWN*1.7,RIGHT*5.5+DOWN*1.7,color=LIME,stroke_width=4)
        stream2=ContinuousFlowStream(path2,color=LIME,count=18)
        self.sentence('Your phone expects carefully controlled direct current instead.','A ONE-WAY FLOW',FadeIn(right),FadeIn(dc),Create(path2),FadeIn(stream2))
        self.sentence('A USB charger often starts at five volts, while the phone controls its own battery.','USB OUTPUT ≠ BATTERY VOLTAGE')
        brick=wireframe_brick().move_to(ORIGIN)
        # Orbiting energy tracks keep the cutaway active while the stages are explained.
        orbit=VGroup(*[DashedVMobject(Ellipse(width=3.5+i*.6,height=2.0+i*.4,color=c,stroke_width=3),num_dashes=30) for i,c in enumerate((CYAN,LIME,GOLD))])
        for i,ring in enumerate(orbit):
            ring.add_updater(lambda m,dt,i=i: m.rotate((.48 if i%2==0 else -.35)*dt))
        route=RoundedRectangle(width=2.7,height=1.5,corner_radius=.18).set_opacity(0)
        energy=ContinuousFlowStream(route,CYAN,24,speed=.24)
        self.sentence('That tiny charger is a safety barrier and a power converter.','LET’S OPEN THE MODEL',FadeOut(left),FadeOut(right),FadeOut(ac),FadeOut(dc),FadeOut(path1),FadeOut(path2),FadeOut(stream1),FadeOut(stream2),FadeIn(brick),FadeIn(orbit),FadeIn(energy),sfx='whoosh')
        stages=VGroup(*[tag(s,c,20) for s,c in [('RECTIFY',CORAL),('SWITCH',GOLD),('ISOLATE',CYAN),('REGULATE',LIME)]]).arrange(RIGHT,buff=.5).move_to(DOWN*1.65)
        self.sentence('Its real stages rectify, switch, isolate, and regulate the electrical energy.','FOUR STAGES',FadeIn(stages,shift=UP*.2))
        self.sentence('We will explore a simpler model, and then connect it back to real chargers.','FOLLOW THE ENERGY')
        self.clear_foreground()


class Ch2_TheWirelessJumpTransformer(StudioScene):
    def construct(self):
        self.title('02','THE MAGNETIC JUMP')
        coil=transformer_unit().move_to(LEFT*3.05+UP*.3)
        wave=wave_card('ac',CORAL,4.5,1.5).move_to(RIGHT*3.65+UP*.35)
        self.add(coil,wave)
        self.sentence('A transformer can transfer energy without a direct electrical connection between its windings.','A REAL INSULATION BARRIER',sfx='whoosh')
        self.sentence('A changing current creates a changing magnetic field in the first coil.','PRIMARY  /  CHANGING CURRENT')
        self.sentence('The field crosses the core and induces a voltage in the separate secondary winding.','MAGNETIC ENERGY TRANSFER')
        self.sentence('The windings must be properly insulated and constructed for safe isolation.','ISOLATION IS ENGINEERED')
        eq=formula('transformer',45).move_to(RIGHT*3.5+DOWN*1.5)
        self.sentence('In an ideal transformer, the voltage ratio equals the turns ratio.','IDEAL TURNS RATIO',Write(eq))
        self.sentence('Fewer turns on the secondary produce a smaller secondary voltage.','20 TURNS  →  5 TURNS')
        smaller=wave_card('ac',LIME,4.5,.65).move_to(wave)
        self.sentence('The reduced waveform is still alternating; it is not yet battery-ready.','LOWER VOLTAGE  ≠  DC',ReplacementTransform(wave,smaller))
        self.sentence('A modern charger does not usually use this large mains-frequency arrangement.','THE REAL BRICK IS DIFFERENT')
        self.sentence('Instead, it first rectifies mains and switches high voltage at high frequency.','RECTIFY  →  SWITCH')
        self.sentence('That lets a compact transformer move energy through its isolation barrier.','SMALL CORE  /  FAST SWITCHING')
        self.sentence('The magnetic principle is the same, but the practical circuit is more sophisticated.','MODEL  VS  REALITY')
        self.clear_foreground()


class Ch3_OneWayValveDiode(StudioScene):
    def construct(self):
        self.title('03','THE ONE-WAY VALVE')
        gate,path=diode_gate(); gate.move_to(LEFT*3.2+UP*.25)
        wave=wave_card('ac',CORAL,5,1.7).move_to(RIGHT*3.45+UP*.25)
        stream=ContinuousFlowStream(path,LIME,18,speed=.28)
        self.add(gate,wave,stream)
        self.sentence('A diode is an electronic one-way valve for conventional current.','THE DIODE',sfx='whoosh')
        self.sentence('In an ideal model it lets current pass in one direction.','FORWARD  /  OPEN',gate[0][3].animate.rotate(-PI/4,about_point=gate[0][3].get_top()))
        reverse=ContinuousFlowStream(path,BLUE_C,18,speed=-.28)
        self.sentence('Try to reverse it, and the gate blocks the flow.','REVERSE  /  BLOCKED',FadeOut(stream),FadeIn(reverse),gate[0][3].animate.rotate(PI/4,about_point=gate[0][3].get_top()))
        impact=create_explosion(gate.get_center(),22,[CORAL,GOLD,WHITE],seed=17);self.add(impact)
        self.sentence('One diode in series with a load creates a half-wave rectifier.','ONE DIODE  /  HALF WAVE',FadeOut(reverse),sfx='zap')
        half=wave_card('half',GOLD,5,1.7).move_to(wave)
        self.sentence('The negative halves are cut away, leaving gaps between the positive humps.','NEGATIVE HALF REMOVED',ReplacementTransform(wave,half),FadeOut(impact))
        eq=formula('half',29).move_to(RIGHT*3.4+DOWN*1.7)
        self.sentence('Mathematically, the output is the maximum of zero and the input wave.','MAXIMUM OF ZERO AND INPUT',Write(eq))
        self.sentence('For an ideal diode and resistive load, half the original sine-wave power reaches the load.','HALF THE IDEAL LOAD POWER')
        self.sentence('That is not a universal measurement of energy wasted by a real phone charger.','IDEAL MODEL  /  NOT A CHARGER')
        self.sentence('To use both halves of the cycle, we need a more ingenious arrangement.','CAN WE FLIP THE VALLEYS?')
        self.clear_foreground()


class Ch4_TheMagicDiamondBridge(StudioScene):
    def construct(self):
        self.title('04','THE MAGIC DIAMOND')
        bridge,diodes,positive,negative=bridge_unit(.85);bridge.move_to(LEFT*3.35+UP*.15)
        wave=wave_card('ac',CORAL,5,1.7).move_to(RIGHT*3.4+UP*.25)
        self.add(bridge,wave)
        self.sentence('Four diodes form a diamond called a bridge rectifier.','FOUR ONE-WAY VALVES')
        red=ContinuousFlowStream(positive,CORAL,20,.24)
        self.sentence('During one half-cycle, the red path carries conventional current through the load.','POSITIVE HALF  /  RED PATH',FadeIn(red),diodes[0].animate.set_color(CORAL),diodes[3].animate.set_color(CORAL))
        self.sentence('Two diodes conduct, while the other pair blocks the reverse routes.','TWO DIODES CONDUCT')
        blue=ContinuousFlowStream(negative,BLUE_C,20,.24)
        self.sentence('When the input reverses, a different pair takes over.','NEGATIVE HALF  /  BLUE PATH',FadeOut(red),FadeIn(blue),diodes[0].animate.set_color(WHITE),diodes[3].animate.set_color(WHITE),diodes[1].animate.set_color(BLUE_C),diodes[2].animate.set_color(BLUE_C))
        self.sentence('The clever routing keeps current through the load in the very same direction.','SAME OUTPUT POLARITY')
        self.sentence('The dots show conventional current, not the paths of individual electrons.','CURRENT DIRECTION  /  DIAGRAM')
        rect=wave_card('rect',CYAN,5,1.7).move_to(wave)
        self.sentence('In the ideal model, every negative valley flips into a positive peak.','FLIP THE VALLEYS',ReplacementTransform(wave,rect))
        eq=formula('rect',34).move_to(RIGHT*3.4+DOWN*1.7)
        self.sentence('That is the mathematical absolute value of the input sine wave.','THE ABSOLUTE VALUE FUNCTION',Write(eq))
        self.sentence('Real diodes have voltage drops, so the real output is lower than the ideal curve.','REAL DIODES HAVE LOSSES')
        self.clear_foreground()


class Ch5_TheCapacitorIron(StudioScene):
    def construct(self):
        self.title('05','SMOOTHING THE STORM')
        tank=energy_tank().move_to(LEFT*3.8+UP*.25)
        plates=VGroup(Line(LEFT*.42,RIGHT*.42,color=CYAN,stroke_width=5).shift(UP*.12),
                      Line(LEFT*.42,RIGHT*.42,color=CYAN,stroke_width=5).shift(DOWN*.12),
                      Line(UP*.12,UP*.55,color=CYAN,stroke_width=3),
                      Line(DOWN*.12,DOWN*.55,color=CYAN,stroke_width=3))
        capacitor=add_neon_glow(plates,CYAN,2,12).move_to(LEFT*5.35+UP*.25)
        wave=wave_card('rect',CYAN,6,1.7).move_to(RIGHT*2.6+UP*.25)
        self.add(capacitor,tank,wave)
        self.sentence('Rectified voltage is positive, but it still falls between the peaks.','ONE DIRECTION  /  BIG RIPPLES')
        self.sentence('A capacitor connected across the load stores energy as it charges.','CAPACITOR  /  ENERGY RESERVOIR')
        self.sentence('When the source voltage rises, the reservoir fills.','CHARGE AT THE PEAK')
        self.sentence('As the source falls, stored energy supplies the load and helps fill the valleys.','DISCHARGE BETWEEN PEAKS')
        ripple=wave_card('ripple',LIME,6,1.7).move_to(wave)
        self.sentence('The result is a smoother voltage, with smaller remaining ripples.','BRIDGING THE VALLEYS',ReplacementTransform(wave,ripple))
        eq=formula('cap',34).move_to(RIGHT*2.6+DOWN*1.65)
        self.sentence('Across a fixed resistor, an ideal capacitor follows an exponential discharge curve.','EXPONENTIAL DISCHARGE',Write(eq))
        self.sentence('Its time constant is resistance multiplied by capacitance.','TIME CONSTANT  /  R × C')
        battery=battery_icon(.75).move_to(LEFT*5.5+DOWN*1.55)
        flat=wave_card('flat',LIME,6,1.7).move_to(ripple)
        self.sentence('Feedback and regulation control the final output, commonly five volts for USB.','REGULATED  /  5 V USB',ReplacementTransform(ripple,flat),FadeIn(battery),sfx='chime')
        charge=tag('100%',LIME,22).next_to(battery,DOWN,buff=.1)
        self.sentence('Inside the phone, another circuit safely manages charging the battery.','THE PHONE CONTROLS THE BATTERY',battery[2].animate.stretch(1.3,1,about_edge=DOWN),FadeIn(charge))
        self.sentence('Real switching chargers have more stages than this simplified classroom model.','THE REAL CIRCUIT IS MORE COMPLEX')
        self.sentence('Never open or modify a plugged-in charger: mains voltage is dangerous.','RESPECT THE MAINS')
        self.sentence('Subscribe for more hidden engineering all around you.','FOLLOW FOR MORE ENGINEERING')
        self.clear_foreground()
