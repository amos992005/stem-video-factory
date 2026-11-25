"""Three independently staged portrait cuts, without persistent HUD labels."""
from manim import *
from cinematic_scene import FilmScene
from cinematic_acts import *

config.pixel_width=1080
config.pixel_height=1920
config.frame_width=9
config.frame_height=16


class PortraitFilm(FilmScene):
    portrait=True
    speech_rate='+15%'


class Short01_ACvsDC(PortraitFilm):
    def construct(self):
        self.card('AC  vs  DC')
        wall=outlet_icon(1.15).move_to(LEFT*2.5+UP*1.6);battery=battery_icon(1.15).move_to(RIGHT*2.5+UP*1.6)
        self.add(wall,battery);arc=burst_arc(wall.get_right(),battery.get_left())
        self.say('Why is connecting a phone battery directly to a wall outlet so dangerous?',FadeIn(arc),sfx='zap')
        sparks=self.burst(battery.get_center())
        self.say('It can cause electric shock, fire, and battery failure. Never try it.',shake=True)
        self.clear_act()
        tubes=tube_pair(7).scale(.85).shift(UP*.5);self.add(tubes)
        self.say('The wall supplies alternating voltage, so its polarity keeps reversing.')
        self.say('The charge motion is slowed down here; direct current flows in one direction.')
        self.say('A USB charger commonly starts at five volts, and the phone controls its battery.')
        self.clear_act()
        wave=giant_wave('ac',CORAL,7,2.8).shift(UP*.5);self.add(wave)
        half=giant_wave('half',GOLD,7,2.8).shift(UP*.5)
        self.say('A single diode blocks one half of the wave, leaving gaps.',ReplacementTransform(wave,half))
        self.say('A four-diode bridge can use both halves of the cycle.')
        self.say('Watch the full video to see how the whole charger works.')
        self.clear_act()


class Short02_WirelessTransformer(PortraitFilm):
    def construct(self):
        self.card('THE MAGNETIC JUMP')
        coils=transformer_full(7).shift(UP*1.3);self.add(coils);self.frame_act(.8,UP*1.2)
        self.say('Did you know an isolated charger has no direct wire connection from the wall to your phone cord?',sfx='whoosh')
        self.say('Proper insulation helps protect you from the mains.')
        self.clear_act()
        coils=transformer_full(7).shift(UP*1.2);rings=create_3d_magnetic_rings(UP*1.2,6,1.6);self.add(coils,rings)
        self.say('Changing current creates a magnetic field in the first winding.')
        self.say('That changing field induces voltage in the separate second winding.')
        self.clear_act()
        wave=giant_wave('ac',CORAL,7,3).shift(UP*.4);eq=formula('transformer',52).move_to(UP*3.1)
        self.add(wave)
        self.say('In an ideal transformer, the voltage ratio follows the turns ratio.',Write(eq))
        small=giant_wave('ac',LIME,7,1.2).shift(UP*.4)
        self.say('Fewer secondary turns mean a lower winding voltage.',ReplacementTransform(wave,small))
        self.say('Real phone chargers rectify the mains and switch at high frequency.')
        self.say('Watch the full video for the complete story.')
        self.clear_act()


class Short03_DiamondBridge(PortraitFilm):
    def construct(self):
        self.card('THE DIODE DIAMOND')
        bridge,diodes,pos,neg=bridge_unit(1.35);bridge.shift(UP*1.3);self.add(bridge)
        self.say('This classic diamond circuit performs a famous math function in real life.')
        self.say('Four diodes form a bridge rectifier that routes current through the load.')
        self.clear_act()
        bridge,diodes,pos,neg=bridge_unit(1.35);bridge.shift(UP*1.3);self.add(bridge);self.frame_act(.78,UP*1.2)
        dot=Dot(pos.get_start(),radius=.12,color=CORAL);self.add(dot)
        with self.voiceover(text='On one half-cycle, current follows the red path.') as tracker:
            self.play(MoveAlongPath(dot,pos),self.camera.frame.animate.move_to(UP*1.3+RIGHT*.3),run_time=tracker.duration*.94,rate_func=linear)
        self.remove(dot);dot=Dot(neg.get_start(),radius=.12,color=BLUE_C);self.add(dot)
        with self.voiceover(text='When the input reverses, the blue path keeps the load current moving the same way.') as tracker:
            self.play(MoveAlongPath(dot,neg),self.camera.frame.animate.move_to(UP*1.3+LEFT*.3),run_time=tracker.duration*.94,rate_func=linear)
        self.say('These dots represent conventional current, not individual electrons.')
        self.clear_act()
        wave=giant_wave('ac',BLUE_C,7,3).shift(UP*.3);self.add(wave)
        rect=giant_wave('rect',CYAN,7,3).shift(UP*.3)
        self.say('Ideally the negative valleys flip upward: that is the absolute value function.',ReplacementTransform(wave,rect))
        self.say('A capacitor can then smooth the resulting ripples.')
        self.say('Watch the full video for the real charger story.')
        self.clear_act()
