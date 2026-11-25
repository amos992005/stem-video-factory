"""Create unlabeled, white-on-transparent circuit illustrations for Episode 01."""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm

ROOT = Path(__file__).resolve().parents[1]
SVG_DIR = ROOT / 'assets' / 'svg' / 'ep01'


def drawing():
    return schemdraw.Drawing(show=False, color='white', lw=3, bgcolor='none')


def bridge(d):
    # Conventional-current diodes: left/right -> positive; negative -> left/right.
    left, top, right, bottom = (-2, 0), (0, 2), (2, 0), (0, -2)
    for start, end in ((left, top), (right, top), (bottom, left), (bottom, right)):
        d += elm.Diode().at(start).to(end)
    for point in (left, top, right, bottom):
        d += elm.Dot().at(point)


def generate(output_dir=SVG_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with drawing() as d:
        d += elm.Transformer(t1=6, t2=3, core=True)
        d.save(str(output_dir / 'transformer.svg'))
    with drawing() as d:
        d += elm.SourceSin().at((0, 0)).up().length(3)
        d += elm.Diode().right().length(3)
        d += elm.Resistor().down().length(3)
        d += elm.Line().left().length(3)
        d.save(str(output_dir / 'single_diode.svg'))
    with drawing() as d:
        bridge(d)
        d += elm.Line().at((-2, 0)).left().length(1)
        d += elm.Line().at((2, 0)).right().length(1)
        d += elm.Line().at((0, 2)).up().length(1)
        d += elm.Line().at((0, -2)).down().length(1)
        d.save(str(output_dir / 'bridge_rectifier.svg'))
    with drawing() as d:
        bridge(d)
        d += elm.Line().at((-2, 0)).left().length(1)
        d += elm.Line().at((2, 0)).right().length(1)
        # Separate, parallel branches connected to + and - output nodes.
        d += elm.Line().at((0, 2)).to((5, 2))
        d += elm.Line().at((0, -2)).to((5, -2))
        d += elm.Capacitor().at((3, 2)).to((3, -2))
        d += elm.Resistor().at((5, 2)).to((5, -2))
        for p in ((3, 2), (3, -2)):
            d += elm.Dot().at(p)
        d.save(str(output_dir / 'smoothed_charger.svg'))
    return output_dir


if __name__ == '__main__':
    print('Generated circuit SVGs in', generate())
