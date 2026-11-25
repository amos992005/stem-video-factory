"""Portrait versions use the same motion engine and leave room for captions."""
from manim import *
from vfx_engine import *
from studio_components import *

config.pixel_width=1080
config.pixel_height=1920
config.frame_width=9
config.frame_height=16


class PortraitStudio(StudioScene):
    portrait=True
    speech_rate='+15%'


class Short01_ACvsDC(PortraitStudio):
    def construct(self):
        self.title('SHORT 01','AC vs DC')
        wall=outlet_icon(.8).move_to(LEFT*2.3+UP*2.2)
        battery=battery_icon(.8).move_to(RIGHT*2.3+UP*2.2)
        arc=burst_arc(wall.get_right(),battery.get_left())
        self.add(wall,battery)
        self.sentence('Why is connecting a phone battery directly to a wall outlet so dangerous?','NEVER CONNECT TO MAINS',FadeIn(arc),sfx='zap')
        sparks=create_explosion(battery.get_center(),40); self.add(sparks)
        self.sentence('It can cause electric shock, fire, and battery failure.','SHOCK  /  FIRE  /  DAMAGE',shake=True)
        self.sentence('Never try it: the charger is a critical safety barrier.','THIS IS A WARNING',FadeOut(arc),FadeOut(sparks))
        wave=wave_card('ac',CORAL,5.7,1.6).move_to(UP*.15)
        self.sentence('The outlet supplies alternating voltage, so the polarity reverses again and again.','WALL  /  ALTERNATING',FadeOut(wall),FadeOut(battery),FadeIn(wave))
        path=Line(LEFT*3+DOWN*2,RIGHT*3+DOWN*2,color=CYAN,stroke_width=4)
        flow=ContinuousFlowStream(path,GOLD,18,ac=True)
        self.sentence('Charges in alternating current oscillate; this visualization is deliberately slowed down.','60 HZ  /  MOTION SLOWED',Create(path),FadeIn(flow))
        dc=ContinuousFlowStream(path,LIME,18,speed=.25)
        self.sentence('Direct current flows in one direction, and a USB output often starts at five volts.','USB  /  DIRECT CURRENT',FadeOut(flow),FadeIn(dc))
        half=wave_card('half',GOLD,5.7,1.6).move_to(wave)
        self.sentence('One diode blocks half the waveform, leaving gaps in the ideal output.','ONE DIODE  /  HALF WAVE',ReplacementTransform(wave,half))
        self.sentence('A four-diode bridge can use both halves of the cycle.','THE DIAMOND SOLUTION')
        self.sentence('Watch the full video to see how the whole charger works.','WATCH THE FULL EPISODE')
        self.clear_foreground()


class Short02_WirelessTransformer(PortraitStudio):
    def construct(self):
        self.title('SHORT 02','THE MAGNETIC JUMP')
        transformer=transformer_unit(6).move_to(UP*1.75)
        self.add(transformer)
        self.sentence('Did you know an isolated charger has no direct wire connection from the wall to your phone cord?','SEPARATE WINDINGS',sfx='whoosh')
        self.sentence('Energy crosses a transformer through a changing magnetic field.','ENERGY CROSSES THE GAP')
        self.sentence('Insulation and careful construction help protect you from mains voltage.','ISOLATION IS ENGINEERED')
        self.sentence('Changing current in the first coil makes the field pulse.','PRIMARY  /  CHANGING CURRENT')
        self.sentence('That field induces a voltage in the separate secondary coil.','SECONDARY  /  INDUCED VOLTAGE')
        eq=formula('transformer',50).move_to(DOWN*.9)
        self.sentence('In an ideal transformer, the voltage ratio follows the turns ratio.','THE TURNS RATIO',Write(eq))
        self.sentence('Fewer secondary turns mean a lower winding voltage.','20 TURNS  →  5 TURNS')
        self.sentence('Real phone chargers rectify the mains and then switch at high frequency.','SMALL CORE  /  FAST SWITCHING')
        self.sentence('Watch the full video for the rest of the story.','WATCH THE FULL EPISODE')
        self.clear_foreground()


class Short03_DiamondBridge(PortraitStudio):
    def construct(self):
        self.title('SHORT 03','THE DIODE DIAMOND')
        bridge,diodes,positive,negative=bridge_unit(.8);bridge.move_to(UP*1.5)
        self.add(bridge)
        self.sentence('This classic diamond circuit performs a famous math function in real life.','FOUR DIODES  /  ONE TRICK')
        self.sentence('A bridge rectifier routes both input halves through a load in one direction.','THE BRIDGE RECTIFIER')
        red=ContinuousFlowStream(positive,CORAL,18,.28)
        self.sentence('On one half-cycle, two diodes conduct along the red path.','POSITIVE HALF  /  RED PATH',FadeIn(red),diodes[0].animate.set_color(CORAL),diodes[3].animate.set_color(CORAL))
        blue=ContinuousFlowStream(negative,BLUE_C,18,.28)
        self.sentence('When the input reverses, the blue pair takes over.','NEGATIVE HALF  /  BLUE PATH',FadeOut(red),FadeIn(blue),diodes[0].animate.set_color(WHITE),diodes[3].animate.set_color(WHITE),diodes[1].animate.set_color(BLUE_C),diodes[2].animate.set_color(BLUE_C))
        self.sentence('The load current still goes in the same direction.','SAME OUTPUT POLARITY')
        wave=wave_card('ac',CORAL,5.8,1.2).move_to(DOWN*2)
        self.sentence('The paths represent conventional current, rather than individual electrons.','CONVENTIONAL CURRENT',FadeIn(wave))
        rect=wave_card('rect',CYAN,5.8,1.2).move_to(wave)
        self.sentence('Ideally, negative valleys flip upward: that is the absolute value function.','FLIP THE VALLEYS',ReplacementTransform(wave,rect))
        self.sentence('A capacitor can then smooth the resulting ripples.','SMOOTH THE RIPPLES')
        self.sentence('Watch the full video for the real charger story.','WATCH THE FULL EPISODE')
        self.clear_foreground()
