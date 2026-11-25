"""Symbolic idealized models used in Episode 01."""
import sympy as s

t, omega, R, C = s.symbols('t omega R C', positive=True)
Vp = s.Symbol('V_p', positive=True)
Vin = s.Function('V_{in}')(t)
Vhalf = s.Function('V_{half}')(t)
Vrect = s.Function('V_{rect}')(t)
Vcap = s.Function('V_{cap}')(t)
V1, V2, N1, N2 = s.symbols('V_1 V_2 N_1 N_2', positive=True)
EXPR = {
    'ac': s.Eq(Vin, Vp * s.sin(omega*t)),
    'transformer': s.Eq(V2/V1, N2/N1),
    'half': s.Eq(Vhalf, s.Max(0, Vp*s.sin(omega*t))),
    'rect': s.Eq(Vrect, s.Abs(Vp*s.sin(omega*t))),
    'cap': s.Eq(Vcap, Vp*s.exp(-t/(R*C))),
}
LATEX = {name: s.latex(value) for name, value in EXPR.items()}


def verify():
    assert s.simplify(EXPR['ac'].rhs.subs(t, 0)) == 0
    assert EXPR['half'].rhs.subs(omega*t, -s.pi/2) == 0
    assert EXPR['rect'].rhs.subs(omega*t, -s.pi/2) == Vp
    assert s.simplify(s.diff(EXPR['cap'].rhs, t) + EXPR['cap'].rhs/(R*C)) == 0
    assert s.simplify(EXPR['transformer'].lhs / EXPR['transformer'].rhs - V2*N1/(V1*N2)) == 0
    return True
