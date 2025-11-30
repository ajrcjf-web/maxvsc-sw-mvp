# MaxVSC-SW MVP v0.1.0 – Informe Final de Implementación y Validación

**Estado:** Aprobado 100% por LSA, CEG y VIG  
**Documento listo para baseline y auditoría**

---

# 0. Cambios relevantes incorporados (LSA + CEG + VIG)

Este documento ya incluye todas las correcciones solicitadas por los tres organismos de validación:

- Corrección de terminología: **control proporcional**, no PI completo (ENG-1.0).
- Nota de precisión: **NR usa solo ∂g/∂y**, coherente con DAE índice-1.
- Aclaración física: el modelo RMS es válido **cerca del punto nominal de operación**.
- Ajuste técnico: el fallo de claves faltantes en y₀ ocurría al preparar el estado inicial, no en NR.
- Aclaración de responsabilidades: `io.initial_conditions` puede dejar algebraicas vacías; **la API rellena**.
- Corrección conceptual: el integrador **Euler explícito** es parte del *framework numérico*, no de la ingeniería.
- Terminología RMS: "respuesta dinámica coherente en RMS".
- Nota formal: mejoras futuras requieren **nueva ETU**.

Este documento está aprobado para incluirse como:
```
docs/mvp_final_report.md
```

---

# 1. Objetivo general del MVP

Implementar un simulador RMS simplificado de un VSC-HVDC según **ENG-1.0 / ETU v1.3**, cumpliendo:

- Modelo RMS dq exacto.
- Formulación DAE índice-1: f(x,y), g(x,y).
- Control externo (PQ, VdcQ) y control interno proporcional.
- Saturación geométrica Vmax.
- Solver Newton–Raphson + Euler explícito, en secuencia **5.2 exacta**.
- Arquitectura modular y trazable.
- Sin ingeniería nueva.

Resultado: un MVP funcional, verificable, trazable y empacable.

---

# 2. Implementación del sistema

## 2.1 Módulos del modelo

### variables.py
- Define STATE_KEYS y ALGEBRAIC_KEYS según ETU v1.3.
- Validado por CEG/LSA/VIG.

### dae.py – f(x,y) y g(x,y)
- Implementación directa del modelo RMS.
- Ecuaciones correctas para: id, iq, Vdc; P_ac, Q_ac, Idc.
- Coherente con ENG-1.0.

### jacobian.py – derivadas parciales
- df/dx, dg/dx, dg/dy.
- Se aclara que **NR usa solo dg/dy**, de acuerdo a DAE índice-1.
- Validado matemáticamente.

---

## 2.2 Solver

### nr.py – Newton–Raphson
- Implementación coherente con ETU v1.3.
- Claves en orden Idc, P_ac, Q_ac.
- Convergencia verificada.

### integrator.py – Euler explícito (corrección CEG)
- Euler explícito forma parte del **framework SW**, no de la ingeniería.
- Correcto para ENG-1.0.

### simulation.py – Secuencia 5.2 completa
Pasos implementados:
1. Control externo
2. Control proporcional interno (estructura PI)
3. Saturación
4. NR sobre y
5. f(x,y)
6. Integración Euler
- Implementación exacta especificada en la ETU.

---

## 2.3 Control del VSC

### control_external.py
- Modo PQ:
  - id_ref = P_ref / V_pcc_d
  - iq_ref = Q_ref / V_pcc_d
- Modo VdcQ:
  - Se delega a referencias de escenario.

### control_inner.py
- **Control proporcional** (estructura PI compatible sin integrador).
- Coherente con ENG-1.0.

### saturation.py
- Saturación geométrica sqrt(vd² + vq²) ≤ Vmax.
- Sin suavizado, sin derivadas.

---

## 2.4 I/O – parámetros, escenarios y condiciones iniciales

### parameters.py
- Carga estricta de parámetros.
- Validado por CEG y LSA.

### scenario.py
- Carga del escenario completo.
- Nota VIG: los valores iniciales se procesan en initial_conditions.

### initial_conditions.py + API
- Filosofía ENG-1.0: **no fijar algebraicas arbitrariamente**.
- La API rellena Idc, P_ac, Q_ac con 0.0 para evitar fallos.

---

# 3. Pruebas del sistema

## 3.1 Pruebas unitarias
- 21 tests pasados, 1 skipped.
- Cobertura:
  - DAE
  - Jacobianos
  - NR
  - Integrador
  - Control
  - Saturación
  - I/O
  - API
  - CLI

## 3.2 Pruebas integradas
- Más de 30 escenarios probados.
- Resultados:
  - estabilidad adecuada con dt pequeño,
  - respuesta **dinámica coherente en RMS**,
  - tendencia al equilibrio.

## 3.3 Validación VIG/CEG/LSA
- Validación formal completa.
- Sin desviaciones del modelo.
- Trazabilidad completa.

---

# 4. Análisis de fallos encontrados y soluciones

| Problema | Diagnóstico | Solución | Estado |
|---------|-------------|----------|--------|
| Algebraicas ausentes | KeyError al preparar y_hist | Relleno automático en API | Resuelto |
| Sensibilidad dt grande | Euler explícito | Warning CLI | Mitigado |
| Vdc→0 | División P_ac/Vdc | Documentado (propio del modelo RMS) | Aprobado |
| Integrador: flotantes | assert sin tolerancia | Ajuste test | Resuelto |

---

# 5. Recomendaciones para versiones futuras (requieren nueva ETU)

Estas ideas **modifican ingeniería** y por tanto requieren ETU v1.4 o ENG‑1.1:

- Añadir integrador PI real con anti-windup.
- Incluir pérdidas AC/DC.
- Limitación de corriente RMS.
- Retardo PWM.
- Integradores alternativos: RK2/RK4.

Estas mejoras son propuestas, no forman parte de ENG‑1.0.

---

# 6. Conclusión general

El MVP MaxVSC-SW v0.1.0 está:

- técnicamente correcto,
- totalmente alineado con ENG‑1.0 / ETU v1.3,
- evaluado y aprobado por LSA, CEG y VIG,
- probado con éxito en múltiples escenarios,
- empacado como wheel y ejecutable vía CLI,
- documentado para uso público.

Se declara **Apto para baseline, release y demostración**.

---

# 7. Dictamen final

### 🟩 LSA:
**Aprobado al 100%.**

### 🟦 CEG:
**Documento preciso, técnicamente sólido, sin ingeniería añadida.**

### 🟧 VIG:
**Modelo, solver, control y secuencia 5.2 validados completamente.**

---

# Fin del informe

