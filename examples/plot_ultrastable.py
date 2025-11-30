"""
Plots de los escenarios ULTRAestables:

1) Paso muy pequeño de potencia en modo PQ.
2) Paso muy pequeño de id_ref en modo VdcQ.

Usa los mismos parámetros y escenarios que step_ultrastable.py:

- params_ultrastable.json
- scenario_pq_ultrastable.json
- scenario_vdcq_ultrastable.json

No modifica el núcleo del simulador; solo ejecuta run_step en un bucle
y grafica resultados con matplotlib.

Uso desde la raíz del repo:

    $env:PYTHONPATH='src'; python examples/plot_ultrastable.py
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt

from vscsim.io.parameters import load_parameters
from vscsim.io.initial_conditions import load_initial_conditions
from vscsim.solver.simulation import run_step


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def simulate_pq_ultrastable(repo_root: Path):
    params_path = repo_root / "examples" / "params_ultrastable.json"
    scenario_path = repo_root / "examples" / "scenario_pq_ultrastable.json"

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
    Vdc_hist = [x["Vdc"]]
    P_ref_hist = [P_initial]

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
        Vdc_hist.append(x["Vdc"])
        P_ref_hist.append(P_ref)

    return times, Vdc_hist, P_ref_hist


def simulate_vdcq_ultrastable(repo_root: Path):
    params_path = repo_root / "examples" / "params_ultrastable.json"
    scenario_path = repo_root / "examples" / "scenario_vdcq_ultrastable.json"

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
    Vdc_hist = [x["Vdc"]]
    id_ref_hist = [id_initial]

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
        Vdc_hist.append(x["Vdc"])
        id_ref_hist.append(id_ref)

    return times, Vdc_hist, id_ref_hist


def main():
    repo_root = Path(__file__).resolve().parents[1]

    # Simulación PQ
    t_pq, Vdc_pq, P_ref_pq = simulate_pq_ultrastable(repo_root)

    # Simulación VdcQ
    t_vdcq, Vdc_vdcq, id_ref_vdcq = simulate_vdcq_ultrastable(repo_root)

    # --- Plot PQ ---
    fig1, ax1 = plt.subplots()
    ax1.plot(t_pq, Vdc_pq)
    ax1.set_xlabel("t [s]")
    ax1.set_ylabel("Vdc [pu]")
    ax1.set_title("Escenario ULTRAestable PQ: Vdc(t)")

    ax1b = ax1.twinx()
    ax1b.plot(t_pq, P_ref_pq, linestyle="--")
    ax1b.set_ylabel("P_ref [pu]")

    fig1.tight_layout()

    # --- Plot VdcQ ---
    fig2, ax2 = plt.subplots()
    ax2.plot(t_vdcq, Vdc_vdcq)
    ax2.set_xlabel("t [s]")
    ax2.set_ylabel("Vdc [pu]")
    ax2.set_title("Escenario ULTRAestable VdcQ: Vdc(t)")

    ax2b = ax2.twinx()
    ax2b.plot(t_vdcq, id_ref_vdcq, linestyle="--")
    ax2b.set_ylabel("id_ref [pu]")

    fig2.tight_layout()

    plt.show()


if __name__ == "__main__":
    main()
