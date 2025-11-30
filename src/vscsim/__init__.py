"""
vscsim — Núcleo del simulador RMS VSC-HVDC.

Implementación conforme al baseline de ingeniería ENG-1.0,
basado en la Especificación Técnica Unificada v1.3.

Este paquete contiene:
- model: ecuaciones RMS, DAE y Jacobianos
- vsc: control externo, PI interno y saturación
- solver: Newton–Raphson e integración
- io: parámetros, escenarios y condiciones iniciales
- api: interfaz mínima del simulador
- cli: interfaz de línea de comandos
"""
