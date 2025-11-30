# 📘 MaxVSC-SW – Simulador RMS VSC-HVDC (MVP)

Este paquete implementa el simulador RMS del convertidor VSC-HVDC bajo el baseline de ingeniería:

- **ENG-1.0**
- **Especificación Técnica Unificada v1.3**

Cumple estrictamente:

- Modelo RMS en dq  
- DAE f(x,y), g(x,y)  
- Solver Newton–Raphson  
- Integrador Euler explícito  
- Secuencia numérica aprobada (Sección 5.2)  
- Sin dinámicas nuevas, sin modificaciones del modelo aprobado  


---

# 🔧 Instalación

## ✔ Instalar desde wheel local

El proyecto se empaqueta mediante `pyproject.toml` y `build`.

```bash
python -m pip install build
python -m build
```

Esto genera:

```
dist/
  maxvsc_sw-0.1.0-py3-none-any.whl
  maxvsc_sw-0.1.0.tar.gz
```

Para instalarlo:

```bash
pip install dist/maxvsc_sw-0.1.0-py3-none-any.whl
```

## ✔ Usar la CLI instalada

```bash
python -m vscsim.cli.main --help
```


---

# ⚠ Advertencia sobre dt (Euler explícito)

El integrador en ENG-1.0 es **Euler explícito**.  
Si el paso temporal `dt` es demasiado grande, la simulación puede volverse numéricamente inestable.

La CLI emite automáticamente un warning si:

```
dt > 2 × 5e-4
```

Este aviso:

- No altera el solver  
- No modifica el modelo  
- Solo informa al usuario para evitar divergencias numéricas  


---

# 📊 Recomendaciones de dt según escenario

| Tipo de escenario | Descripción | dt recomendado | Comentario |
|------------------|-------------|----------------|------------|
| **ultrastable** | Cambios suaves | **5e-4** | Validado en ENG-1.0 |
| **pretty_v3** | Respuesta oscilatoria suave | **5e-4** | Estable |
| **agresivo** | Escalones grandes | **1e-4 – 5e-4** | dt grande puede divergir |
| **CLI demo** | Uso típico desde CLI | **5e-4** | Configurado |
| **estudios numéricos** | Convergencia exacta | **1e-4 → 1e-5** | Opcional |


---

# ▶ Ejemplo CLI

```bash
python -m vscsim.cli.main \
    --params examples/params_base.json \
    --scenario examples/scenario_pq_step.json \
    --t-end 0.5 \
    --dt 0.0005
```


---

# 📁 Estructura del paquete

```
vscsim/
  model/
  solver/
  vsc/
  io/
  api/
  cli/
```


---

# 📄 Baseline de ingeniería

- Respeta **ENG-1.0**
- Cumple **ETU v1.3**
- Sin nuevas dinámicas
- Sin estados adicionales
- Sin modificación de saturación
- Secuencia 5.2 intacta


---

# 🧪 Estado del proyecto

- **21 tests pasando**, 1 saltado (por diseño)
- Build wheel correcto
- CLI funcional  
- Ejemplos validados y graficados


---

# 📝 Licencia / Créditos

*(añadir si aplica)*

