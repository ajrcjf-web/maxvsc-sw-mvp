"""
Escenarios 'damped_pretty_v3' con oscilaciones amortiguadas más suaves:

1) Paso de potencia en modo PQ.
2) Paso de id_ref en modo VdcQ.

No modifica el núcleo del simulador; solo construye escenarios
instantáneos a partir de JSON y llama a run_step en un bucle.

Uso desde la raíz del repo:

    $env:PYTHONPATH='src'; python examples/step_damped_pretty_v3.py
"""

import json
from pathlib import Path

from vscsim.io.parameters import load_parameters
from vscsim.io.initial_conditions import load_initial_conditions
from vscsim.solver.simulation import run_step


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_pq_damped_pretty_v3(repo_root: Path) -> None:
    params_path = repo_root / "examples" / "params_damped_pretty_v3.json"
    scenario_path = repo_root / "examples" / "scenario_pq_damped_pretty_v3.json"

    params_config = load_json(params_path)
    scenario_cfg = load_json(scenario_path)

    params = load_parameters(params_config)

    t_end = 0.5
    dt = 0.0005
    n_steps = int(t_end / dt)

    control_mode = scenario_cfg["control_mode"]
    assert control_mode == "PQ"

    v_pcc_d = scenario_cfg["v_pcc_d"]
    v_pcc_q = scenario_cfg["v_pcc_q"]

    P_initial = scenario_cfg["P_ref_initial"]
    Q_initial = scenario_cfg["Q_ref_initial"]

    events = scenario_cfg.get("events", [])
    if events:
        step_time = events[0]["time"]
        P_step = events[0]["P_ref"]
        Q_step = events[0]["Q_ref"]
    else:
        step_time = t_end + 1.0
        P_step = P_initial
        Q_step = Q_initial

    ic = load_initial_conditions(scenario_cfg.get("initial_conditions", {}))
    x = dict(ic["x0"])
    y = dict(ic["y0"])

    times = [0.0]
    P_hist = [P_initial]
    Vdc_hist = [x["Vdc"]]

    t = 0.0
    for k in range(n_steps):
        t = (k + 1) * dt

        if t < step_time:
            P_ref = P_initial
            Q_ref = Q_initial
        else:
            P_ref = P_step
            Q_ref = Q_step

        scenario_inst = {
            "control_mode": "PQ",
            "P_ref": P_ref,
            "Q_ref": Q_ref,
            "v_pcc_d": v_pcc_d,
            "v_pcc_q": v_pcc_q,
        }

        x, y = run_step(
            t=t,
            dt=dt,
            x=x,
            y=y,
            scenario=scenario_inst,
            params=params,
        )

        times.append(t)
        P_hist.append(P_ref)
        Vdc_hist.append(x["Vdc"])

    print("=== Escenario damped_pretty_v3: paso de potencia PQ ===")
    print(f"  t_end       = {t_end}")
    print(f"  t_step      = {step_time}")
    print(f"  P_before    = {P_initial}")
    print(f"  P_after     = {P_step}")
    print(f"  Vdc(initial)= {Vdc_hist[0]}")
    print(f"  Vdc(final)  = {Vdc_hist[-1]}")
    print(f"  pasos       = {len(times) - 1}")
    print()


def run_vdcq_damped_pretty_v3(repo_root: Path) -> None:
    params_path = repo_root / "examples" / "params_damped_pretty_v3.json"
    scenario_path = repo_root / "examples" / "scenario_vdcq_damped_pretty_v3.json"

    params_config = load_json(params_path)
    scenario_cfg = load_json(scenario_path)

    params = load_parameters(params_config)

    t_end = 0.5
    dt = 0.0005
    n_steps = int(t_end / dt)

    control_mode = scenario_cfg["control_mode"]
    assert control_mode == "VdcQ"

    v_pcc_d = scenario_cfg["v_pcc_d"]
    v_pcc_q = scenario_cfg["v_pcc_q"]

    id_initial = scenario_cfg["id_ref_initial"]
    iq_initial = scenario_cfg["iq_ref_initial"]

    events = scenario_cfg.get("events", [])
    if events:
        step_time = events[0]["time"]
        id_step = events[0]["id_ref"]
        iq_step = events[0]["iq_ref"]
    else:
        step_time = t_end + 1.0
        id_step = id_initial
        iq_step = iq_initial

    ic = load_initial_conditions(scenario_cfg.get("initial_conditions", {}))
    x = dict(ic["x0"])
    y = dict(ic["y0"])

    times = [0.0]
    id_ref_hist = [id_initial]
    Vdc_hist = [x["Vdc"]]

    t = 0.0
    for k in range(n_steps):
        t = (k + 1) * dt

        if t < step_time:
            id_ref = id_initial
            iq_ref = iq_initial
        else:
            id_ref = id_step
            iq_ref = iq_step

        scenario_inst = {
            "control_mode": "VdcQ",
            "id_ref": id_ref,
            "iq_ref": iq_ref,
            "v_pcc_d": v_pcc_d,
            "v_pcc_q": v_pcc_q,
        }

        x, y = run_step(
            t=t,
            dt=dt,
            x=x,
            y=y,
            scenario=scenario_inst,
            params=params,
        )

        times.append(t)
        id_ref_hist.append(id_ref)
        Vdc_hist.append(x["Vdc"])

    print("=== Escenario damped_pretty_v3: paso de id_ref (VdcQ) ===")
    print(f"  t_end       = {t_end}")
    print(f"  t_step      = {step_time}")
    print(f"  id_before   = {id_initial}")
    print(f"  id_after    = {id_step}")
    print(f"  Vdc(initial)= {Vdc_hist[0]}")
    print(f"  Vdc(final)  = {Vdc_hist[-1]}")
    print(f"  pasos       = {len(times) - 1}")
    print()


def main():
    repo_root = Path(__file__).resolve().parents[1]
    run_pq_damped_pretty_v3(repo_root)
    run_vdcq_damped_pretty_v3(repo_root)


if __name__ == "__main__":
    main()
