from typing import List, Dict
from collections import defaultdict

from backend.models   import Process
from backend.scheduling import Event

def compute_metrics(events: List[Event], processes: List[Process]) -> Dict:
    """
    Dada la lista de eventos y la lista de procesos, calcula:
      - waiting_time por proceso  = turnaround_time - burst_time
      - turnaround_time por proceso = finish_time - arrival_time
      - avg_waiting_time global
      - avg_turnaround_time global

    Devuelve un dict con estructura:
    {
      "per_process": {
          pid: {"waiting_time": ..., "turnaround_time": ...},
          ...
      },
      "avg_waiting_time": float,
      "avg_turnaround_time": float
    }
    """
    # map pid → Process
    proc_map = {p.pid: p for p in processes}

    # agrupar todos los eventos por pid
    ev_by_pid = defaultdict(list)
    for e in events:
        ev_by_pid[e.pid].append(e)

    per_proc = {}
    total_wait = 0.0
    total_ta   = 0.0
    n = len(processes)

    for pid, proc in proc_map.items():
        evs = sorted(ev_by_pid.get(pid, []), key=lambda e: e.start)
        if not evs:
            # proceso nunca ejecutado
            turnaround = 0
            waiting    = 0
        else:
            finish_time = max(e.end for e in evs)
            turnaround  = finish_time - proc.at
            waiting     = turnaround - proc.bt

        per_proc[pid] = {
            "waiting_time": waiting,
            "turnaround_time": turnaround
        }
        total_wait += waiting
        total_ta   += turnaround

    return {
        "per_process": per_proc,
        "avg_waiting_time": total_wait / n if n else 0.0,
        "avg_turnaround_time": total_ta / n if n else 0.0
    }
