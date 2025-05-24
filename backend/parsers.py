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
    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 4:
                raise ParseError(f"{path}:{lineno} → se esperaban 4 campos, encontré {len(parts)}")
            pid, bt, at, prio = parts
            try:
                processes.append(Process(pid, int(bt), int(at), int(prio)))
            except ValueError as e:
                raise ParseError(f"{path}:{lineno} → valor no entero: {e}")
    return processes

def load_resources(path: str) -> List[Resource]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"'{path}' no existe")
    resources: List[Resource] = []
    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) != 2:
                raise ParseError(f"{path}:{lineno} → se esperaban 2 campos, encontré {len(parts)}")
            name, counter = parts
            try:
                resources.append(Resource(name, int(counter)))
            except ValueError as e:
                raise ParseError(f"{path}:{lineno} → valor no entero: {e}")
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
            pid, action, resource, cycle = parts
            try:
                actions.append(Action(pid, action.upper(), resource, int(cycle)))
            except ValueError as e:
                raise ParseError(f"{path}:{lineno} → valor no entero: {e}")
    return actions