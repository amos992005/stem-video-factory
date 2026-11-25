"""Run from the repository root: manim -ql src/test_pipeline.py TestScene."""
from manim import Create, MathTex, SVGMobject, Write, UP, DOWN
from manim_voiceover import VoiceoverScene

from circuit_assets import create_circuit, energy_latex
from edge_tts_service import EdgeTTSService


class TestScene(VoiceoverScene):
    def construct(self):
        circuit = SVGMobject(str(create_circuit())).scale_to_fit_height(3).shift(UP * 1.1)
        equation = MathTex(energy_latex()).shift(DOWN * 2)
        self.set_speech_service(EdgeTTSService())
        narration = (
            "Welcome to our automated electrical engineering channel. "
            "Here is a simple RC circuit and its energy equation."
        )
        with self.voiceover(text=narration) as tracker:
            self.play(Create(circuit), run_time=tracker.duration * 0.55)
            self.play(Write(equation), run_time=tracker.duration * 0.45)
