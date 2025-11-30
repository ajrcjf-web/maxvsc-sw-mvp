"""
Definición nominal de conjuntos de variables del modelo RMS en dq.

Estados dinámicos:
    x = {id, iq, Vdc}

Variables algebraicas:
    y = {Idc, P_ac, Q_ac}

No contiene lógica numérica. Solo sirve como referencia estructural,
alineada con la ETU v1.3 (ENG-1.0).
"""

STATE_KEYS = ("id", "iq", "Vdc")
ALGEBRAIC_KEYS = ("Idc", "P_ac", "Q_ac")