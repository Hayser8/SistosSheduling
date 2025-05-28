# Simulador de Scheduling y Sincronización

**Autor:** Julio García Salas
**Carné:** 22076

---

## Descripción

Este proyecto ofrece una aplicación gráfica y un backend en Python para simular dinámicamente:

1. **Algoritmos de Calendarización (Scheduling)**:

   * FIFO (First In, First Out)
   * SJF (Shortest Job First)
   * SRT (Shortest Remaining Time)
   * Round Robin (con quantum configurable)
   * Priority (no-preemptivo)

2. **Mecanismos de Sincronización**:

   * Mutex (locks por recurso)
   * Semáforos (capacidad configurable por recurso)

La simulación se muestra con diagramas de Gantt dinámicos, métricas de rendimiento (Waiting Time y Turnaround Time) y visualización de accesos/esperas a recursos.

## Requisitos

* Python 3.8 o superior
* Dependencias (instalables vía `pip`):

  ```bash
  pip install customtkinter
  ```
* Sistema operativo: Windows, macOS o Linux

## Estructura del proyecto

```
project_root/
├── backend/
│   ├── calendarizacion.py
│   ├── sincronizacion.py
│   ├── scheduling.py
│   ├── engine.py
│   ├── metrics.py
│   ├── models.py
│   ├── parsers.py
│   └── main.py
├── datos/
│   ├── procesos.txt
│   ├── recursos.txt
│   └── acciones.txt
├── app_ui.py (SimulationApp)
└── README.md
```

* **`backend/`**: lógica de simulación y algoritmos.
* **`datos/`**: ejemplos de archivos de entrada.
* **`main.py`**: cliente de consola para pruebas y debugging.
* **`app_ui.py`**: interfaz gráfica (CustomTkinter).

## Formato de archivos de entrada

### Procesos (`procesos.txt`)

Cada línea: `<PID>, <BurstTime>, <ArrivalTime>, <Priority>`

```txt
P1, 8, 0, 1
P2, 4, 1, 2
```

### Recursos (`recursos.txt`)

Cada línea: `<NombreRecurso>, <Contador>`

```txt
R1, 1
R2, 2
```

### Acciones (`acciones.txt`)

Cada línea: `<PID>, <ACCION>, <Recurso>, <Ciclo>`

```txt
P1, READ, R1, 0
P2, WRITE, R2, 1
```

## Uso

### Interfaz gráfica

1. Ejecuta:

   ```bash
   python app_ui.py
   ```
2. Selecciona la pestaña **Calendarización** o **Sincronización**.
3. Carga tus archivos `.txt` (procesos, recursos, acciones).
4. Configura algoritmos o modo (mutex/semaphore) y quantum si aplica.
5. Haz clic en **Ejecutar** para ver la simulación dinámica y métricas.
6. Usa **Pausar**, **Reset** y consulta PID para ver métricas individuales.

### Cliente de consola

1. Ejecuta:

   ```bash
   python main.py --mode sync
   ```

   o bien:

   ```bash
   python main.py --mode sched --alg sjf --quantum 2
   ```
2. Observa en consola los diagramas de eventos y métricas.

## Métricas Calculadas

* **Waiting Time (WT)**: tiempo total en cola de listos.
* **Turnaround Time (TA)**: tiempo desde llegada hasta finalización.
* Promedios globales por algoritmo.

## Licencia

Este proyecto es parte de la asignatura Sistemas Operativos en la Universidad del Valle de Guatemala. Todos los derechos reservados.
