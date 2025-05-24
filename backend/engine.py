from typing import List, Callable
from backend.scheduling import Event

class SimulationEngine:
    def __init__(
        self,
        events: List[Event],
        on_cycle: Callable[[int, List[Event]], None],
        max_cycle: int
    ):
        """
        events: lista de Event(pid, start, end)
        on_cycle: callback que recibe (ciclo_actual, lista_de_events_que_empiezan_este_ciclo)
        max_cycle: hasta dónde simular
        """
        self.events_by_cycle = {}
        for e in events:
            self.events_by_cycle.setdefault(e.start, []).append(e)
        self.on_cycle = on_cycle
        self.current = 0
        self.max_cycle = max_cycle
        self._running = False

    def step(self):
        """Un ciclo: dispara el callback con los eventos que arrancan ahora."""
        evs = self.events_by_cycle.get(self.current, [])
        self.on_cycle(self.current, evs)
        self.current += 1

    def run(self, delay: float):
        """Loop automático con pausa de ‘delay’ segundos entre ciclos."""
        import time
        self._running = True
        while self._running and self.current <= self.max_cycle:
            self.step()
            time.sleep(delay)

    def pause(self):
        self._running = False

    def reset(self):
        self.current = 0
        self._running = False