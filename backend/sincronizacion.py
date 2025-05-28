# backend/sincronizacion.py

from typing import List
from collections import defaultdict
from dataclasses import dataclass
from backend.models import Resource, Action
from backend.scheduling import Event

@dataclass
class ActionEvent(Event):
    resource: str
    status: str  # 'ACCESED' o 'WAITING'

def simulate_synchronization(
    resources: List[Resource],
    actions: List[Action],
    mode: str = "mutex"  # o "semaphore"
) -> List[ActionEvent]:
    """
    Para cada ciclo agrupa las acciones y, según el modo:
      - mutex: cap = 1
      - semaphore: cap = cuenta inicial del recurso
    Decide cuáles ACCESED y el resto WAITING. Cada acción dura 1 ciclo.
    """
    # counter inicial por recurso
    counters = {r.name: r.counter for r in resources}  # :contentReference[oaicite:0]{index=0}
    # agrupa acciones por ciclo
    acts_by_cycle = defaultdict(list)
    for act in actions:
        acts_by_cycle[act.cycle].append(act)           # :contentReference[oaicite:1]{index=1}

    events: List[ActionEvent] = []
    for cycle in sorted(acts_by_cycle):
        # agrupa por recurso
        por_recurso = defaultdict(list)
        for act in acts_by_cycle[cycle]:
            por_recurso[act.resource].append(act)

        for res_name, acts in por_recurso.items():
            # capacidad según modo
            if mode == "mutex":
                cap = 1
            else:  # semaphore
                cap = counters.get(res_name, 1)

            # genera ACCESED o WAITING
            for idx, act in enumerate(acts):
                status = "ACCESED" if idx < cap else "WAITING"
                events.append(
                    ActionEvent(
                        pid      = act.pid,
                        start    = cycle,
                        end      = cycle + 1,
                        resource = res_name,
                        status   = status
                    )
                )
    return events

class SincronizacionSimulator:
    def __init__(self):
        self.processes: List = []
        self.resources: List[Resource] = []
        self.actions:   List[Action]   = []
        self.events:    List[ActionEvent] = []
        self.max_cycle: int = 0

    def load_processes(self, path: str):
        from backend.parsers import load_processes
        self.processes = load_processes(path)

    def load_resources(self, path: str):
        from backend.parsers import load_resources
        self.resources = load_resources(path)

    def load_actions(self, path: str):
        from backend.parsers import load_actions
        self.actions = load_actions(path)

    def configure(self, mode: str = "mutex"):
        self.events = simulate_synchronization(self.resources, self.actions, mode)
        self.max_cycle = max(e.end for e in self.events) if self.events else 0

    def get_events(self) -> List[ActionEvent]:
        return self.events

    def get_max_cycle(self) -> int:
        return self.max_cycle

    def reset(self):
        self.events = []
        self.max_cycle = 0
