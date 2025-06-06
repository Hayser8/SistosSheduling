from typing import List, Optional
from backend.models    import Process
from backend.scheduling import Event, fifo, sjf, srt, rr, priority_np
from backend.metrics    import compute_metrics

class CalendarizacionSimulator:
    def __init__(self):
        self.processes: List[Process] = []
        self.events:    List[Event]   = []
        self.max_cycle: int           = 0

    def load_processes(self, path: str):
        from backend.parsers import load_processes
        self.processes = load_processes(path)

    def configure(self, algorithm: str, quantum: Optional[int] = None):
        """
        Configura y ejecuta el algoritmo de calendarización indicado.
        Para Round Robin, quantum debe ser un entero positivo.
        """
        alg = algorithm.lower()
        if alg == "fifo":
            self.events = fifo(self.processes)

        elif alg == "sjf":
            self.events = sjf(self.processes)

        elif alg == "srt":
            self.events = srt(self.processes)

        elif alg == "round robin":
            # Validación de quantum
            if quantum is None:
                raise ValueError("Quantum requerido para Round Robin")
            if not isinstance(quantum, int) or quantum < 1:
                raise ValueError(f"Quantum inválido ({quantum}); debe ser un entero ≥ 1")
            self.events = rr(self.processes, quantum)

        elif alg == "priority":
            self.events = priority_np(self.processes)

        else:
            raise ValueError(f"Algoritmo desconocido: '{algorithm}'")

        # Calcular hasta qué ciclo llega la simulación
        self.max_cycle = max((e.end for e in self.events), default=0)

    def get_events(self) -> List[Event]:
        return self.events

    def get_max_cycle(self) -> int:
        return self.max_cycle

    def get_metrics(self) -> dict:
        return compute_metrics(self.events, self.processes)

    def reset(self):
        self.events = []
        self.max_cycle = 0
