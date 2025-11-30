"""
Ejemplo de escenario con cambio de referencia de “Vdc” emulado como
paso en id_ref en modo VdcQ.

No modifica el núcleo; solo cambia id_ref/iq_ref según el tiempo y
llama a run_step.
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
    params_path = repo_root / "examples" / "params_base.json"
    scenario_path = repo_root / "examples" / "scenario_vdcq_step.json"

    params_config = load_json(params_path)
    scenario_cfg = load_json(scenario_path)

    params = load_parameters(params_config)

    t_end = 0.5
    dt = 0.01
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
    id_ref_hist = []
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

        scenario = {
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
            scenario=scenario,
            params=params,
        )

        times.append(t)
        id_ref_hist.append(id_ref)
        Vdc_hist.append(x["Vdc"])

    print("Simulación cambio de referencia Vdc (emulado via id_ref):")
    print(f"  t_end       = {t_end}")
    print(f"  t_step      = {step_time}")
    print(f"  id_before   = {id_initial}")
    print(f"  id_after    = {id_step}")
    print(f"  Vdc(final)  = {Vdc_hist[-1]}")
    print(f"  pasos       = {len(times) - 1}")


if __name__ == "__main__":
    main()
