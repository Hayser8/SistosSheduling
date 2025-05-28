# backend/parsers.py

import os
from typing import List
from backend.models import Process, Resource, Action

class ParseError(Exception):
    """Error al leer/parsing de una línea."""
    pass

def load_processes(path: str) -> List[Process]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"'{path}' no existe")
    processes: List[Process] = []
    seen_pids = set()

    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 4:
                raise ParseError(f"{path}:{lineno} → se esperaban 4 campos, encontré {len(parts)}")

            pid, bt_s, at_s, prio_s = parts

            # Detección de PID duplicado
            if pid in seen_pids:
                raise ParseError(f"{path}:{lineno} → PID duplicado: '{pid}'")
            seen_pids.add(pid)

            # Conversión a enteros
            try:
                bt   = int(bt_s)
                at   = int(at_s)
                prio = int(prio_s)
            except ValueError as e:
                raise ParseError(f"{path}:{lineno} → valor no entero: {e}")

            # Validaciones de rango
            if bt < 0:
                raise ParseError(f"{path}:{lineno} → Burst Time debe ser ≥ 0, encontrado {bt}")
            if at < 0:
                raise ParseError(f"{path}:{lineno} → Arrival Time debe ser ≥ 0, encontrado {at}")
            if not (0 <= prio <= 10):
                raise ParseError(f"{path}:{lineno} → Priority fuera de rango 0–10: {prio}")

            processes.append(Process(pid=pid, bt=bt, at=at, priority=prio))

    return processes


def load_resources(path: str) -> List[Resource]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"'{path}' no existe")
    resources: List[Resource] = []
    seen_names = set()

    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 2:
                raise ParseError(f"{path}:{lineno} → se esperaban 2 campos, encontré {len(parts)}")

            name, counter_s = parts

            # Detección de recursos duplicados
            if name in seen_names:
                raise ParseError(f"{path}:{lineno} → recurso duplicado: '{name}'")
            seen_names.add(name)

            # Conversión y validación de contador
            try:
                counter = int(counter_s)
            except ValueError as e:
                raise ParseError(f"{path}:{lineno} → valor no entero: {e}")
            if counter < 1:
                raise ParseError(f"{path}:{lineno} → contador debe ser ≥1, encontrado {counter}")

            resources.append(Resource(name=name, counter=counter))

    return resources


def load_actions(path: str) -> List[Action]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"'{path}' no existe")
    actions: List[Action] = []

    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 4:
                raise ParseError(f"{path}:{lineno} → se esperaban 4 campos, encontré {len(parts)}")

            pid, action_s, resource, cycle_s = parts

            # Normalizar y validar tipo de acción
            action = action_s.upper()
            if action not in {"READ", "WRITE"}:
                raise ParseError(f"{path}:{lineno} → acción desconocida: '{action_s}' (debe ser READ o WRITE)")

            # Conversión y validación de ciclo
            try:
                cycle = int(cycle_s)
            except ValueError as e:
                raise ParseError(f"{path}:{lineno} → ciclo no entero: {e}")
            if cycle < 0:
                raise ParseError(f"{path}:{lineno} → ciclo debe ser ≥0, encontrado {cycle}")

            actions.append(Action(pid=pid, action=action, resource=resource, cycle=cycle))

    return actions
