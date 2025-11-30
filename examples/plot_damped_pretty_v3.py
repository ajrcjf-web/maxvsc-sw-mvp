"""
Plots del escenario damped_pretty_v3:

- Paso de potencia en PQ.
- Paso de id_ref en VdcQ.

Este script NO usa load_scenario; en lugar de eso arma scenario_inst
exactamente igual que step_damped_pretty_v3.py, que ya funciona.

Uso:
    $env:PYTHONPATH='src'; python examples/plot_damped_pretty_v3.py
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt

from vscsim.io.parameters import load_parameters
from vscsim.io.initial_conditions import load_initial_conditions
from vscsim.solver.simulation import run_step


def load_json(path: Path) -> dict:
    """Carga un archivo JSON."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
#  Simulación PQ
# ============================================================

def simulate_pq(repo_root: Path):

    params_cfg = load_json(repo_root / "examples" / "params_damped_pretty_v3.json")
    scen_cfg = load_json(repo_root / "examples" / "scenario_pq_damped_pretty_v3.json")

    params = load_parameters(params_cfg)

    # Tiempos
    t_end = 0.5
    dt = 0.0005
    n_steps = int(t_end / dt)

    # Valores iniciales del escenario
    P_ini = scen_cfg["P_ref_initial"]
    Q_ini = scen_cfg["Q_ref_initial"]

    v_pcc_d = scen_cfg["v_pcc_d"]
    v_pcc_q = scen_cfg["v_pcc_q"]

    events = scen_cfg.get("events", [])
    if events:
        step_time = events[0]["time"]
        P_step = events[0]["P_ref"]
        Q_step = events[0]["Q_ref"]
    else:
        step_time = t_end + 10
        P_step = P_ini
        Q_step = Q_ini

    # Condiciones iniciales
    ic = load_initial_conditions(scen_cfg["initial_conditions"])
    x = dict(ic["x0"])
    y = dict(ic["y0"])

    t_hist = [0.0]
    Vdc_hist = [x["Vdc"]]
    Pref_hist = [P_ini]

    t = 0.0
    for k in range(n_steps):
        t = (k + 1) * dt

        if t < step_time:
            P_ref = P_ini
            Q_ref = Q_ini
        else:
            P_ref = P_step
            Q_ref = Q_step

        # Escenario instantáneo
        scenario_inst = {
            "control_mode": "PQ",
            "v_pcc_d": v_pcc_d,
            "v_pcc_q": v_pcc_q,
            "P_ref": P_ref,
            "Q_ref": Q_ref
        }

        x, y = run_step(t, dt, x, y, scenario_inst, params)

        t_hist.append(t)
        Vdc_hist.append(x["Vdc"])
        Pref_hist.append(P_ref)

    return t_hist, Vdc_hist, Pref_hist


# ============================================================
#  Simulación VdcQ
# ============================================================

def simulate_vdcq(repo_root: Path):

    params_cfg = load_json(repo_root / "examples" / "params_damped_pretty_v3.json")
    scen_cfg = load_json(repo_root / "examples" / "scenario_vdcq_damped_pretty_v3.json")

    params = load_parameters(params_cfg)

    t_end = 0.5
    dt = 0.0005
    n_steps = int(t_end / dt)

    id_ini = scen_cfg["id_ref_initial"]
    iq_ini = scen_cfg["iq_ref_initial"]

    v_pcc_d = scen_cfg["v_pcc_d"]
    v_pcc_q = scen_cfg["v_pcc_q"]

    events = scen_cfg.get("events", [])
    if events:
        step_time = events[0]["time"]
        id_step = events[0]["id_ref"]
        iq_step = events[0]["iq_ref"]
    else:
        step_time = t_end + 10
        id_step = id_ini
        iq_step = iq_ini

    ic = load_initial_conditions(scen_cfg["initial_conditions"])
    x = dict(ic["x0"])
    y = dict(ic["y0"])

    t_hist = [0.0]
    Vdc_hist = [x["Vdc"]]
    idref_hist = [id_ini]

    t = 0.0
    for k in range(n_steps):
        t = (k + 1) * dt

        if t < step_time:
            id_ref = id_ini
            iq_ref = iq_ini
        else:
            id_ref = id_step
            iq_ref = iq_step

        scenario_inst = {
            "control_mode": "VdcQ",
            "v_pcc_d": v_pcc_d,
            "v_pcc_q": v_pcc_q,
            "id_ref": id_ref,
            "iq_ref": iq_ref
        }

        x, y = run_step(t, dt, x, y, scenario_inst, params)

        t_hist.append(t)
        Vdc_hist.append(x["Vdc"])
        idref_hist.append(id_ref)

    return t_hist, Vdc_hist, idref_hist


# ============================================================
#  MAIN + PLOTS
# ============================================================

def main():

    repo_root = Path(__file__).resolve().parents[1]

    # Lanzar dos simulaciones
    t_pq, Vdc_pq, Pref = simulate_pq(repo_root)
    t_vdcq, Vdc_vdcq, idref = simulate_vdcq(repo_root)

    # --- Plot PQ ---
    fig1, ax1 = plt.subplots()
    ax1.plot(t_pq, Vdc_pq, label="Vdc(t)")
    ax1.set_title("damped_pretty_v3 — PQ")
    ax1.set_xlabel("t [s]")
    ax1.set_ylabel("Vdc [pu]")
    ax1.grid(True)

    ax1b = ax1.twinx()
    ax1b.plot(t_pq, Pref, "r--", label="P_ref(t)")
    ax1b.set_ylabel("P_ref [pu]")

    fig1.tight_layout()

    # --- Plot VdcQ ---
    fig2, ax2 = plt.subplots()
    ax2.plot(t_vdcq, Vdc_vdcq, label="Vdc(t)")
    ax2.set_title("damped_pretty_v3 — VdcQ")
    ax2.set_xlabel("t [s]")
    ax2.set_ylabel("Vdc [pu]")
    ax2.grid(True)

    ax2b = ax2.twinx()
    ax2b.plot(t_vdcq, idref, "r--", label="id_ref(t)")
    ax2b.set_ylabel("id_ref [pu]")

    fig2.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
