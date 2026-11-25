"""Episode 01: fifteen explicitly separated full-screen cinematic acts."""
from manim import *
from cinematic_scene import FilmScene
from cinematic_acts import *


class Ch1_TheHookAndACvsDC(FilmScene):
    def construct(self):
        self.card('THE WALL AND THE BATTERY')
        # 1A: a direct-connection hazard, not a claim of inevitable explosion.
        wall=outlet_icon(1.65).move_to(LEFT*4+UP*.5);battery=battery_icon(1.55).move_to(RIGHT*4+UP*.5)
        arc=burst_arc(wall.get_right(),battery.get_left());self.add(wall,battery)
        self.say('Every day you plug your phone into the wall without a second thought.',FadeIn(arc),sfx='zap')
        sparks=self.burst(battery.get_center())
        self.say('But a direct connection to mains can cause electric shock, fire, and battery failure.',shake=True)
        self.say('Never try this: the charger is an essential safety barrier.',FadeOut(arc),FadeOut(sparks))
        self.clear_act()
        # 1B: an inside-the-wire visualization, deliberately slowed to avoid aliasing.
        tubes=tube_pair(11).shift(UP*.35);self.add(tubes)
        ac=heading('AC',40,CORAL).move_to(LEFT*5.8+UP*2.4);dc=heading('DC',40,LIME).move_to(LEFT*5.8+DOWN*.1)
        self.frame_act(.80,UP*.25)
        self.say('The wall supplies alternating voltage, whose polarity repeatedly reverses.',FadeIn(ac),FadeIn(dc))
        self.say('In North America, a common outlet is one hundred twenty volts RMS at sixty hertz.')
        self.say('Many other countries use about two hundred thirty volts at fifty hertz.')
        self.say('The moving charges are deliberately slowed here; direct current flows in one direction.')
        self.clear_act()
        # 1C: x-ray, animated energy flowing through four chambers.
        brick=charger_blueprint().shift(UP*.35);self.add(brick)
        self.say('A USB charger often starts at five volts, while the phone manages its own battery.',sfx='whoosh')
        self.say('Modern adapters rectify, switch, isolate, and regulate the electrical energy.')
        self.say('We will first use a simplified model and then connect it to the real charger.')
        self.clear_act()


class Ch2_TheWirelessJumpTransformer(FilmScene):
    def construct(self):
        self.card('THE MAGNETIC JUMP')
        # 2A: tight shot of the insulated gap.
        coils=transformer_full(10).shift(UP*.35);scanner=Line(UP*2.3,DOWN*1.5,color=GOLD,stroke_width=6)
        scanner.add_updater(lambda m,dt:m.shift(RIGHT*.18*np.cos(self.renderer.time*2)*dt))
        self.add(coils,scanner);self.frame_act(.65,UP*.3)
        self.say('A transformer transfers energy between separate windings without a direct wire connection.',sfx='whoosh')
        self.say('The physical insulation and construction are crucial to safe isolation.')
        self.say('A changing current in the primary winding creates a changing magnetic field.')
        self.clear_act()
        # 2B: moving flux rings surround both windings.
        coils=transformer_full(10).shift(UP*.3)
        rings=create_3d_magnetic_rings(UP*.3,7,1.8,CYAN);self.add(coils,rings)
        self.frame_act(1.04,UP*.15)
        self.say('That field links the secondary winding and induces a voltage there.')
        self.say('A changing field is essential; a steady direct current cannot drive this transformer action.')
        self.say('The separate windings are a simplified view of the isolation barrier inside a charger.')
        self.clear_act()
        # 2C: waveform compression with the correct ideal turns relationship.
        wave=giant_wave('ac',CORAL,10,3.2);self.add(wave)
        eq=formula('transformer',55).move_to(UP*2.5)
        self.say('In an ideal transformer the voltage ratio equals the turns ratio.',Write(eq))
        self.say('Fewer secondary turns produce a lower secondary voltage.')
        compressed=giant_wave('ac',LIME,10,1.2)
        self.say('The reduced voltage still alternates; it is not yet a regulated USB supply.',ReplacementTransform(wave,compressed))
        self.say('Real phone chargers first rectify the mains and then switch at high frequency.')
        self.say('That high-frequency switching lets a compact transformer transfer the energy.')
        self.clear_act()


class Ch3_OneWayValveDiode(FilmScene):
    def construct(self):
        self.card('THE ONE-WAY VALVE')
        # 3A: animated check valve and opposing flows.
        valve,gate,path,flow=mechanical_valve();valve.shift(UP*.35);self.add(valve)
        self.say('A diode acts like a one-way valve for conventional current.')
        self.say('In an ideal model current can pass forward.',valve[2].animate.rotate(-PI/3,about_point=valve[1].get_center()))
        reverse=ContinuousFlowStream(path,CORAL,24,speed=-.24)
        self.say('When the input reverses, the valve blocks the flow.',FadeOut(flow),FadeIn(reverse),valve[2].animate.rotate(PI/3,about_point=valve[1].get_center()))
        sparks=self.burst(valve.get_center())
        self.say('The moving particles are a visual analogy, not a microscopic simulation.',FadeOut(reverse),sfx='zap',shake=True)
        self.clear_act()
        # 3B: turnstile becomes diode symbol.
        valve,_,_,flow=mechanical_valve();valve.shift(UP*.3);self.add(valve)
        symbol=VGroup(Polygon(LEFT*1.4+UP*1.4,LEFT*1.4+DOWN*1.4,RIGHT*1.3,color=GOLD,stroke_width=8),Line(RIGHT*1.3+UP*1.55,RIGHT*1.3+DOWN*1.55,color=GOLD,stroke_width=9))
        symbol=add_neon_glow(symbol,GOLD,3,22).shift(UP*.3)
        flow.clear_updaters()  # Its path is consumed by the morph.
        self.say('In a circuit diagram, that one-way behavior is represented by the diode symbol.',ReplacementTransform(valve,symbol))
        self.say('Place a single diode in series with a load and only one half-cycle passes.')
        self.say('This simple arrangement is called a half-wave rectifier.')
        self.clear_act()
        # 3C: full-screen laser slice and ideal power gauge.
        wave=giant_wave('ac',CORAL,10,3.2);self.add(wave)
        laser=add_neon_glow(Line(LEFT*5,RIGHT*5,color=CORAL,stroke_width=6),CORAL,3,22).shift(UP*.35)
        self.say('The negative half of the wave is cut off, leaving gaps between positive humps.',Create(laser))
        half=giant_wave('half',GOLD,10,3.2)
        self.say('The mathematical output is the maximum of zero and the input wave.',ReplacementTransform(wave,half))
        gauge_value=ValueTracker(100)
        gauge=always_redraw(lambda: Integer(round(gauge_value.get_value()),color=WHITE,font_size=60).move_to(UP*2.4))
        percent=Text('%',font_size=48,color=WHITE).move_to(RIGHT*.95+UP*2.4)
        self.say('For an ideal diode and a resistive load, the output receives half the original sine-wave power.',FadeIn(gauge),FadeIn(percent))
        self.say('That result is not a universal measure of losses in a real phone charger.',gauge_value.animate.set_value(50))
        self.clear_act()


class Ch4_TheMagicDiamondBridge(FilmScene):
    def construct(self):
        self.card('THE DIODE DIAMOND')
        # 4A: four diodes fly into position before the complete circuit appears.
        bridge,diodes,pos,neg=bridge_unit(1.35);bridge.shift(UP*.25)
        copies=VGroup(*[d.copy().move_to(p) for d,p in zip(diodes,[UL*3,UR*3,DL*3,DR*3])]);self.add(copies)
        self.say('Four diodes can form a diamond called a full-wave bridge rectifier.',*[Transform(c,d.copy()) for c,d in zip(copies,diodes)])
        self.remove(copies);self.add(bridge)
        self.say('The bridge steers both input polarities through the load in the same direction.')
        self.say('Each conducting route uses two of the four diodes.')
        self.clear_act()
        # 4B: camera chase along the real path geometry.
        bridge,diodes,pos,neg=bridge_unit(1.35);bridge.shift(UP*.25);self.add(bridge)
        self.frame_act(.78,UP*.25)
        red=Dot(pos.get_start(),radius=.12,color=CORAL);self.add(red)
        with self.voiceover(text='During one half-cycle, the red route carries conventional current through the load.') as tracker:
            self.play(MoveAlongPath(red,pos),self.camera.frame.animate.move_to(RIGHT*.5+UP*.25),run_time=tracker.duration*.94,rate_func=linear)
        self.remove(red);blue=Dot(neg.get_start(),radius=.12,color=BLUE_C);self.add(blue)
        with self.voiceover(text='When the input reverses, the blue pair takes over and current still crosses the load the same way.') as tracker:
            self.play(MoveAlongPath(blue,neg),self.camera.frame.animate.move_to(LEFT*.35+UP*.25),run_time=tracker.duration*.94,rate_func=linear)
        self.say('The dots represent conventional current, not individual electron trajectories.')
        self.clear_act()
        # 4C: show a waveform transform across the axis.
        wave=giant_wave('ac',BLUE_C,10,3.4);self.add(wave)
        self.say('In the ideal model, negative valleys can be flipped up into positive peaks.')
        rect=giant_wave('rect',CYAN,10,3.4)
        self.say('The output is the absolute value of the original sine wave.',ReplacementTransform(wave,rect))
        eq=formula('rect',48).move_to(UP*2.5)
        self.say('Real diodes have voltage drops, so the actual output is lower than this ideal curve.',Write(eq))
        self.clear_act()


class Ch5_TheCapacitorIron(FilmScene):
    def construct(self):
        self.card('THE ENERGY RESERVOIR')
        # 5A: full-screen tank and capacitor plates.
        tank=energy_tank().scale(1.65).move_to(RIGHT*2.5+UP*.4)
        plates=VGroup(Line(LEFT*1.4,RIGHT*1.4,color=CYAN,stroke_width=9).shift(UP*.35),Line(LEFT*1.4,RIGHT*1.4,color=CYAN,stroke_width=9).shift(DOWN*.35),Line(UP*.35,UP*1.5,color=CYAN,stroke_width=5),Line(DOWN*.35,DOWN*1.5,color=CYAN,stroke_width=5)).move_to(LEFT*2.5+UP*.3)
        self.add(tank,add_neon_glow(plates,CYAN,3,20))
        self.say('Rectified voltage flows in one direction, but it still drops between the peaks.')
        self.say('A capacitor connected across the load stores energy as it charges.')
        self.say('When the source falls, that stored energy helps supply the load.')
        self.say('Think of it as a small reservoir that refills at every peak.')
        self.clear_act()
        # 5B: trace the idealized exponential envelope over rectified peaks.
        wave=giant_wave('rect',BLUE_C,10,3.1);self.add(wave)
        curve,shade=rectified_bridge_trace(10,3)
        self.say('The capacitor bridges the valleys and leaves a smaller voltage ripple.',Create(curve),FadeIn(shade))
        eq=formula('cap',44).move_to(UP*2.55)
        self.say('An ideal capacitor discharging through a fixed resistor follows an exponential curve.',Write(eq))
        self.say('The time constant is resistance multiplied by capacitance.')
        self.say('More capacitance or a lighter load generally reduces ripple in this model.')
        self.clear_act()
        # 5C: regulator beam and charging indicator.
        battery,regulator,beam=battery_final();self.add(regulator,battery)
        self.say('Feedback and regulation control the output, typically starting at five volts for USB.',Create(beam),sfx='chime')
        count=Integer(85,font_size=54,color=WHITE).move_to(battery.get_center());pct=Text('%',font_size=38,color=WHITE).next_to(count,RIGHT,buff=.08)
        self.say('Inside the phone, another charging circuit manages and protects the battery.',FadeIn(count),FadeIn(pct))
        self.say('The illustration represents the battery charging toward one hundred percent.',count.animate.set_value(100))
        # A genuine recomposition: the charger safety shield replaces the battery
        # and regulator, rather than relying on tiny background motion.
        shield=Polygon(UP*2.4+LEFT*2.1,UP*2.4+RIGHT*2.1,RIGHT*1.8+DOWN*.65,DOWN*2.0,LEFT*1.8+DOWN*.65,
                       color=CYAN,stroke_width=7,fill_color='#10334A',fill_opacity=.75).shift(UP*.4)
        lock=VGroup(RoundedRectangle(width=2.2,height=1.5,corner_radius=.18,color=GOLD,stroke_width=7),
                    Arc(radius=.7,start_angle=0,angle=PI,color=GOLD,stroke_width=7).shift(UP*.75)).shift(UP*.35)
        safety=VGroup(add_neon_glow(shield,CYAN,3,20),add_neon_glow(lock,GOLD,2,14))
        self.say('Real switching chargers use more stages than this classroom model.',FadeOut(regulator),FadeOut(beam),FadeOut(battery),FadeOut(count),FadeOut(pct),FadeIn(safety))
        self.say('Never open or modify a plugged-in charger: mains voltage is dangerous.')
        self.say('Subscribe for more hidden engineering all around you.')
        self.clear_act()
