from dataclasses import dataclass
from typing import List
from backend.models import Process

@dataclass
class Event:
    pid: str
    start: int
    end: int

def fifo(processes: List[Process]) -> List[Event]:
    procs = sorted(processes, key=lambda p: p.at)
    timeline: List[Event] = []
    current = 0
    for p in procs:
        if current < p.at:
            current = p.at
        start = current
        end = current + p.bt
        timeline.append(Event(p.pid, start, end))
        current = end
    return timeline

def sjf(processes: List[Process]) -> List[Event]:
    procs = sorted(processes, key=lambda p: p.at)
    ready: List[Process] = []
    timeline: List[Event] = []
    current = 0
    i = 0
    while i < len(procs) or ready:
        # Añadimos a ready todos los que han llegado
        while i < len(procs) and procs[i].at <= current:
            ready.append(procs[i])
            i += 1
        if not ready:
            current = procs[i].at
            continue
        # Elegimos el de menor BT
        ready.sort(key=lambda p: p.bt)
        p = ready.pop(0)
        start = current
        end = current + p.bt
        timeline.append(Event(p.pid, start, end))
        current = end
    return timeline

def srt(processes: List[Process]) -> List[Event]:
    # 1) Orden inicial por llegada
    procs = sorted(processes, key=lambda p: p.at)
    remaining = {p.pid: p.bt for p in procs}
    
    timeline: List[Event] = []
    ready: List[Process] = []
    current = 0
    i = 0
    
    last_pid = None
    slice_start = 0

    while i < len(procs) or ready:
        # 2) Añadir al ready todos los que han llegado
        while i < len(procs) and procs[i].at <= current:
            ready.append(procs[i])
            i += 1

        # 3) Si no hay nada listo, avanzar al siguiente at
        if not ready:
            current = procs[i].at
            continue

        # 4) Selección del siguiente proceso:
        #    menor remaining, y en empate el que llegó más tarde (–p.at)
        p = min(ready, key=lambda p: (remaining[p.pid], -p.at))

        # 5) Si cambiamos de PID, cerramos slice previo
        if p.pid != last_pid:
            if last_pid is not None:
                timeline.append(Event(last_pid, slice_start, current))
            slice_start = current
            last_pid = p.pid

        # 6) Ejecutar un “tick”
        remaining[p.pid] -= 1
        current += 1

        # 7) Si remanentes, se queda en ready; si no, lo sacamos y cerramos slice
        if remaining[p.pid] == 0:
            timeline.append(Event(p.pid, slice_start, current))
            ready.remove(p)
            last_pid = None

    return timeline

def rr(processes: List[Process], quantum: int) -> List[Event]:
    procs = sorted(processes, key=lambda p: p.at)
    queue: List[(Process,int)] = []
    timeline: List[Event] = []
    current = 0
    i = 0

    while i < len(procs) or queue:
        while i < len(procs) and procs[i].at <= current:
            queue.append((procs[i], procs[i].bt))
            i += 1
        if not queue:
            current = procs[i].at
            continue
        p, rem = queue.pop(0)
        start = current
        run = min(quantum, rem)
        current += run
        rem -= run
        timeline.append(Event(p.pid, start, current))
        # Añadimos nuevas llegadas durante esta ejecución
        while i < len(procs) and procs[i].at <= current:
            queue.append((procs[i], procs[i].bt))
            i += 1
        if rem > 0:
            queue.append((p, rem))

    return timeline

def priority_np(processes: List[Process]) -> List[Event]:
    # Priority non-preemptive; prioridad menor = más alta
    procs = sorted(processes, key=lambda p: p.at)
    ready: List[Process] = []
    timeline: List[Event] = []
    current = 0
    i = 0

    while i < len(procs) or ready:
        while i < len(procs) and procs[i].at <= current:
            ready.append(procs[i])
            i += 1
        if not ready:
            current = procs[i].at
            continue
        ready.sort(key=lambda p: p.priority)
        p = ready.pop(0)
        start = current
        end = current + p.bt
        timeline.append(Event(p.pid, start, end))
        current = end

    return timeline