"""
vscsim.utils.logger

Logging estructurado y minimalista para el framework numérico.
No depende de la ingeniería ni del modelo RMS. Es puramente utilitario.

Características:
- Niveles: ERROR, WARNING, INFO, DEBUG
- Salida: texto normal o JSON-line (opcional)
- Logger global simple, sin dependencias externas
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Mapping, Optional


# ---------------------------------------------------------
# Niveles de log
# ---------------------------------------------------------

LOG_LEVELS = {
    "error": 40,
    "warning": 30,
    "info": 20,
    "debug": 10,
}


@dataclass
class Logger:
    """
    Logger minimalista independiente de la ingeniería.

    Parámetros
    ----------
    level : str
        Nivel de detalle: "error", "warning", "info", "debug".
    use_json : bool
        Si True, los mensajes se escriben como JSON-lines.
    """

    level: str = "info"
    use_json: bool = False

    def __post_init__(self) -> None:
        level_lc = self.level.lower()
        if level_lc not in LOG_LEVELS:
            raise ValueError(f"Unknown log level: {self.level}")
        self.level_value = LOG_LEVELS[level_lc]

    # -----------------------------------------------------
    # Funciones internas
    # -----------------------------------------------------
    def _should_log(self, msg_level: str) -> bool:
        return LOG_LEVELS[msg_level] >= self.level_value

    def _emit(self, record: Mapping[str, Any]) -> None:
        """
        Emite un registro al stdout, formateado como texto o JSON.
        """
        if self.use_json:
            sys.stdout.write(json.dumps(record) + "\n")
        else:
            level = record.get("level", "").upper()
            msg = record.get("message", "")
            sys.stdout.write(f"[{level}] {msg}\n")

    # -----------------------------------------------------
    # API pública
    # -----------------------------------------------------
    def log(self, level: str, message: str, **extra: Any) -> None:
        """
        Emite un mensaje si el nivel está permitido.
        """
        level_lc = level.lower()
        if level_lc not in LOG_LEVELS:
            raise ValueError(f"Unknown log level: {level}")

        if not self._should_log(level_lc):
            return

        record: dict[str, Any] = {"level": level_lc, "message": message}
        if extra:
            record.update(extra)

        self._emit(record)

    def error(self, msg: str, **extra: Any) -> None:
        self.log("error", msg, **extra)

    def warning(self, msg: str, **extra: Any) -> None:
        self.log("warning", msg, **extra)

    def info(self, msg: str, **extra: Any) -> None:
        self.log("info", msg, **extra)

    def debug(self, msg: str, **extra: Any) -> None:
        self.log("debug", msg, **extra)


# ---------------------------------------------------------
# Logger global opcional
# ---------------------------------------------------------

_global_logger: Optional[Logger] = None


def get_logger(level: str = "info", json_format: bool = False) -> Logger:
    """
    Crea un logger independiente (no global).
    """
    return Logger(level=level, use_json=json_format)


def set_global_logger(logger: Logger) -> None:
    """
    Registra un logger global para uso de toda la simulación.
    """
    global _global_logger
    _global_logger = logger


def global_log(level: str, msg: str, **extra: Any) -> None:
    """
    Escribe un mensaje usando el logger global si está configurado.
    Si no hay logger global, no hace nada.
    """
    if _global_logger is not None:
        _global_logger.log(level, msg, **extra)


# ---------------------------------------------------------
# Configuración global desde parámetros / config
# ---------------------------------------------------------

def configure_global_logger_from_config(config: Mapping[str, Any] | None) -> None:
    """
    Configura el logger global a partir de un diccionario de configuración.

    Claves reconocidas (todas opcionales):
    - "log_level": "error" | "warning" | "info" | "debug"
    - "log_json": bool

    Si config es None o está vacío, no se configura nada.
    """
    if not config:
        return

    level = str(config.get("log_level", "info")).lower()
    use_json = bool(config.get("log_json", False))

    logger = Logger(level=level, use_json=use_json)
    set_global_logger(logger)
