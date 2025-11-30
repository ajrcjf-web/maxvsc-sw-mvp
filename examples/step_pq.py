"""
Ejemplo de escenario con paso de potencia en modo PQ.

Antes de t_step: P_ref = P_ref_initial
Después de t_step: P_ref = valor del evento

No modifica el core del simulador; solo actúa como “driver” externa
que actualiza el escenario antes de cada llamada a run_step.
"""

import json
from pathlib import Path

from vscsim.io.parameters import load_parameters
from vscsim.io.initial_conditions import load_initial_conditions
from vscsim.solver.simulation import run_step


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    repo_root = Path(__file__).resolve().parents[1]
    params_path = repo_root / "examples" / "params_fast.json"
    scenario_path = repo_root / "examples" / "scenario_pq_step.json"

    params_config = load_json(params_path)
    scenario_cfg = load_json(scenario_path)

    # Parámetros del sistema
    params = load_parameters(params_config)

    # Tiempo
    t_end = 0.5
    dt = 0.001  # Recomendación: usar paso pequeño para estabilidad
    n_steps = int(t_end / dt)

    # Interpretar el escenario extendido
    control_mode = scenario_cfg["control_mode"]
    assert control_mode == "PQ"

    v_pcc_d = scenario_cfg["v_pcc_d"]
    v_pcc_q = scenario_cfg["v_pcc_q"]

    P_initial = scenario_cfg["P_ref_initial"]
    Q_initial = scenario_cfg["Q_ref_initial"]

    events = scenario_cfg.get("events", [])
    # Asumimos un solo evento de paso para el ejemplo
    if events:
        step_time = events[0]["time"]
        P_step = events[0]["P_ref"]
        Q_step = events[0]["Q_ref"]
    else:
        step_time = t_end + 1.0  # nunca se activa
        P_step = P_initial
        Q_step = Q_initial

    # Condiciones iniciales
    ic = load_initial_conditions(scenario_cfg.get("initial_conditions", {}))
    x = dict(ic["x0"])
    y = dict(ic["y0"])

    # Históricos mínimos
    times = [0.0]
    P_hist = []
    Vdc_hist = [x["Vdc"]]

    # Bucle temporal con paso de potencia
    t = 0.0
    for k in range(n_steps):
        t = (k + 1) * dt

        # Decidir P_ref, Q_ref según el tiempo
        if t < step_time:
            P_ref = P_initial
            Q_ref = Q_initial
        else:
            P_ref = P_step
            Q_ref = Q_step

        # Construir escenario “instantáneo” que consume run_step
        scenario = {
            "control_mode": "PQ",
            "P_ref": P_ref,
            "Q_ref": Q_ref,
            "v_pcc_d": v_pcc_d,
            "v_pcc_q": v_pcc_q,
        }

        # Paso de simulación (sec. 5.2)
        x, y = run_step(
            t=t,
            dt=dt,
            x=x,
            y=y,
            scenario=scenario,
            params=params,
        )

        times.append(t)
        P_hist.append(P_ref)
        Vdc_hist.append(x["Vdc"])

    # Resumen textual simple
    print("Simulación paso de potencia PQ:")
    print(f"  t_end       = {t_end}")
    print(f"  t_step      = {step_time}")
    print(f"  P_before    = {P_initial}")
    print(f"  P_after     = {P_step}")
    print(f"  Vdc(final)  = {Vdc_hist[-1]}")
    print(f"  pasos       = {len(times) - 1}")


if __name__ == "__main__":
    main()
