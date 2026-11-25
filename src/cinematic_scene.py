"""Full-screen act choreography with explicit foreground ownership and cleanup."""
from pathlib import Path
import numpy as np
from manim import *
from manim_voiceover import VoiceoverScene
from edge_tts_service import EdgeTTSService
from vfx_engine import BACKGROUND, SOUND_DIR, live_grid, heading, create_explosion


class FilmScene(VoiceoverScene, MovingCameraScene):
    portrait=False
    speech_rate='+25%'

    def setup(self):
        super().setup()
        self.camera.background_color=BACKGROUND
        self.set_speech_service(EdgeTTSService(rate=self.speech_rate),create_subcaption=False)
        self.backdrop=live_grid(config.frame_width,config.frame_height)
        self.add(self.backdrop)
        self.beat_index=0
        self.base_width=config.frame_width
        self.focus=ORIGIN.copy()
        self.view_width=self.base_width

    def card(self,title):
        """A temporary 1.5-second full-screen chapter card, never a header."""
        text=heading(title,46 if not self.portrait else 42)
        if text.width>config.frame_width*.82: text.scale_to_fit_width(config.frame_width*.82)
        self.add(text)
        self.play(self.camera.frame.animate.scale(.84),run_time=.95,rate_func=smooth)
        self.play(FadeOut(text),self.camera.frame.animate.set(width=self.base_width).move_to(ORIGIN),run_time=.55)
        self.remove(text)

    def clear_act(self):
        # Never accumulate a previous act's labels or diagrams.
        foreground=[m for m in list(self.mobjects) if m is not self.backdrop and m is not self.camera.frame]
        if foreground:
            self.play(*[FadeOut(m) for m in foreground],run_time=.32)
            self.remove(*foreground)
        self.camera.frame.set(width=self.base_width).move_to(ORIGIN)
        self.view_width=self.base_width
        self.focus=ORIGIN.copy()

    def frame_act(self,width=1.,focus=ORIGIN):
        self.view_width=self.base_width*width
        self.focus=np.array(focus,dtype=float)
        self.camera.frame.set(width=self.view_width).move_to(self.focus)

    def say(self,text,*animations,sfx=None,shake=False,camera=True):
        """Play an intro animation then continue a slow pan throughout each clip."""
        self.beat_index+=1
        with self.voiceover(text=text) as tracker:
            if sfx:
                sound=SOUND_DIR/f'{sfx}.wav'
                if not sound.is_file(): raise FileNotFoundError(sound)
                self.add_sound(str(sound),gain=-15)
            if animations:
                self.play(*animations,run_time=min(1.15,max(.1,tracker.duration*.35)))
            if shake:
                origin=self.camera.frame.get_center().copy()
                def shake_frame(m,alpha):
                    m.move_to(origin+RIGHT*(.12*np.sin(alpha*12*PI)*(1-alpha))+UP*(.07*np.sin(alpha*14*PI)*(1-alpha)))
                self.play(UpdateFromAlphaFunc(self.camera.frame,shake_frame),run_time=min(.38,max(.1,tracker.get_remaining_duration()*.25)))
            remaining=tracker.get_remaining_duration()
            if camera and remaining>1/config.frame_rate:
                direction=1 if self.beat_index%2 else -1
                target=self.focus+RIGHT*.28*direction+UP*.12
                width=self.view_width*(.93 if direction>0 else 1.04)
                self.play(self.camera.frame.animate.move_to(target).set(width=width),run_time=remaining,rate_func=linear)
            # If an explicit path/camera animation was used, wait_for_voiceover
            # fills any remaining duration and updater-driven effects continue.

    def burst(self,point):
        sparks=create_explosion(point,50)
        self.add(sparks)
        return sparks
