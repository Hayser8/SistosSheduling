#!/usr/bin/env python3
import os
import sys
import time
import argparse
from typing import List

# 1) Aseguramos que la raíz del proyecto esté en sys.path:
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.parsers    import load_processes, load_resources, load_actions, ParseError
from backend.scheduling import fifo, sjf, srt, rr, priority_np, Event
from backend.sincronizacion import SincronizacionSimulator
from backend.calendarizacion import CalendarizacionSimulator
from backend.engine     import SimulationEngine
from backend.metrics    import compute_metrics

def load_all():
    datos = os.path.join(project_root, 'datos')
    procs = load_processes( os.path.join(datos, 'procesos.txt') )
    res   = load_resources( os.path.join(datos, 'recursos.txt') )
    acts  = load_actions( os.path.join(datos, 'acciones.txt') )
    return procs, res, acts

def simulate_with_engine(events: List[Event], delay: float = 0.2):
    max_cycle = max(e.end for e in events)
    def on_cycle(cycle: int, evs: List[Event]):
        if evs:
            print(f"[ Ciclo {cycle:3d} ] ──", 
                  ", ".join(f"{e.pid} ({e.start}→{e.end})" for e in evs))
        else:
            print(f"[ Ciclo {cycle:3d} ] (no inicia ningún proceso)")
    engine = SimulationEngine(events, on_cycle, max_cycle)
    print(f"\n▶▶▶ Iniciando simulación hasta ciclo {max_cycle} (delay={delay}s)\n")
    while engine.current <= engine.max_cycle:
        engine.step()
        time.sleep(delay)
    print("\n✅ Simulación finalizada.")

def main():
    parser = argparse.ArgumentParser(description="Prueba de distintos algoritmos de scheduling y sincronización")
    parser.add_argument('-m','--mode', choices=['sched','sync'], default='sched',
                        help="Modo: 'sched' para calendarización, 'sync' para sincronización")
    parser.add_argument('-a','--alg', choices=['fifo','sjf','srt','rr','priority'], default='sjf',
                        help="Algoritmo de calendarización (solo en modo sched)")
    parser.add_argument('-q','--quantum', type=int, default=2,
                        help="Quantum para Round Robin (solo en mode sched)")
    parser.add_argument('-d','--delay', type=float, default=0.2,
                        help="Delay en segundos entre ciclos de simulación")
    args = parser.parse_args()

    try:
        procs, res, acts = load_all()
        print("\n=== Objetos Cargados ===")
        print("Procesos:", procs)
        print("Recursos:", res)
        print("Acciones:", acts)

        if args.mode == 'sched':
            # Calendarización
            if args.alg == 'fifo':
                events = fifo(procs)
            elif args.alg == 'sjf':
                events = sjf(procs)
            elif args.alg == 'srt':
                events = srt(procs)
            elif args.alg == 'rr':
                events = rr(procs, quantum=args.quantum)
            elif args.alg == 'priority':
                events = priority_np(procs)
            else:
                sys.exit("Algoritmo desconocido")

            metrics = compute_metrics(events, procs)
            print(f"\nMétricas de {args.alg.upper()}:")
            print(f"  Avg Waiting Time    = {metrics['avg_waiting_time']:.2f}")
            print(f"  Avg Turnaround Time = {metrics['avg_turnaround_time']:.2f}")
            for pid, m in metrics["per_process"].items():
                print(f"    {pid}: WT={m['waiting_time']}, TA={m['turnaround_time']}")

        else:
            # Sincronización
            sim = SincronizacionSimulator()
            sim.processes = procs
            sim.resources = res
            sim.actions   = acts
            # elija 'mutex' o 'semaphore' según convenga
            sim.configure('mutex')
            events = sim.get_events()
            # contamos accesos vs esperas
            acc  = sum(1 for ev in events if getattr(ev, 'status','')=='ACCESED')
            wait = sum(1 for ev in events if getattr(ev, 'status','')!='ACCESED')
            print("\nMétricas de Sincronización:")
            print(f"  Accesos totales: {acc}")
            print(f"  Esperas totales: {wait}")

        # Ejecutar la simulación en consola
        simulate_with_engine(events, delay=args.delay)

    except FileNotFoundError as fnf:
        print('❌ Archivo no encontrado:', fnf)
    except ParseError as pe:
        print('❌ Error de parseo:', pe)
    except Exception as e:
        print('❌ Error inesperado:', e)

if __name__ == '__main__':
    main()
