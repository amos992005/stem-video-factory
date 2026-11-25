"""Generate the visual assets used in the pipeline smoke test."""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm
import sympy as sp

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def create_circuit(path=PROJECT_ROOT / "assets/svg/rc_circuit.svg"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with schemdraw.Drawing(show=False, color="white", bgcolor="none") as drawing:
        drawing += elm.SourceV().up().label("V")
        drawing += elm.Resistor().right().label("R")
        drawing += elm.Capacitor().down().label("C")
        drawing += elm.Line().left()
        drawing.save(str(path))
    return path


def energy_latex():
    energy, capacitance, voltage = sp.symbols("E C V")
    return sp.latex(sp.Eq(energy, sp.Rational(1, 2) * capacitance * voltage**2, evaluate=False))
