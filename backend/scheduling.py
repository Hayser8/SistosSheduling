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
    procs = sorted(processes, key=lambda p: p.at)
    ready: List[Process] = []
    timeline: List[Event] = []
    remaining = {p.pid: p.bt for p in procs}
    current = 0
    i = 0
    last_pid = None
    slice_start = 0

    while i < len(procs) or ready:
        while i < len(procs) and procs[i].at <= current:
            ready.append(procs[i])
            i += 1
        if not ready:
            current = procs[i].at
            continue
        # Escogemos el con menor tiempo restante
        ready.sort(key=lambda p: remaining[p.pid])
        p = ready[0]
        # Si cambiamos de proceso, cerramos el slice anterior
        if last_pid != p.pid:
            if last_pid is not None:
                timeline.append(Event(last_pid, slice_start, current))
            slice_start = current
            last_pid = p.pid
        # Ejecutamos un ciclo
        remaining[p.pid] -= 1
        current += 1
        # Si terminó, cerramos slice y sacamos de ready
        if remaining[p.pid] == 0:
            timeline.append(Event(p.pid, slice_start, current))
            ready.pop(0)
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