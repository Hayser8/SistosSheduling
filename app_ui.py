import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from backend.parsers import load_processes, load_resources, load_actions
from backend.scheduling import fifo, sjf, srt, rr, priority_np
from backend.sincronizacion import SincronizacionSimulator
from backend.calendarizacion import CalendarizacionSimulator
from backend.engine import SimulationEngine
from backend.metrics import compute_metrics
import threading
import time

# Parámetros de dibujo
X_SCALE = 30
ROW_HEIGHT = 30

class SimulationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Ventana
        self.title("Simulador de Scheduling y Sincronización")
        self.geometry("1200x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Estado
        self.processes = []
        self.resources = []
        self.actions = []
        self.delay = 0.5

        self.color_map = {}
        self.last_metrics = {}
        self.sim_events = {}
        self._pause_event = threading.Event()
        self._running = False

        # Layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(0, weight=1)

        # Panel de controles
        ctrl = ctk.CTkFrame(self, width=300, corner_radius=0)
        ctrl.grid(row=0, column=0, sticky="nsew")

        # Ciclo actual
        self.cycle_label = ctk.CTkLabel(ctrl, text="Ciclo: 0")
        self.cycle_label.grid(row=12, column=0, padx=10, pady=(5,0), sticky="w")

        # Pestañas de simulación
        tabs = ctk.CTkTabview(ctrl, width=280)
        tabs.add("Calendarización"); tabs.add("Sincronización")
        tabs.grid(row=0, column=0, padx=10, pady=10, sticky="nwe")
        self.tabview = tabs

        # --- Calendarización: previsualización y algoritmos ---
        cal = tabs.tab("Calendarización")
        ctk.CTkButton(cal, text="Cargar procesos", command=self.load_processes_cal)\
            .pack(padx=10, pady=(10,5), anchor="w")
        self.scroll_proc = ctk.CTkScrollableFrame(cal, height=100)
        self.scroll_proc.pack(fill="both", padx=10, pady=(0,10))

        ctk.CTkLabel(cal, text="Algoritmos:").pack(padx=10, pady=(5,0), anchor="w")
        self.alg_vars = {}
        algo_frame = ctk.CTkFrame(cal)
        algo_frame.pack(padx=10, pady=5, anchor="w")
        names = ["FIFO","SJF","SRT","Round Robin","Priority"]
        for i,name in enumerate(names):
            var = tk.BooleanVar(value=(name=="FIFO"))
            var.trace_add('write', self.update_quantum_state)
            chk = ctk.CTkCheckBox(algo_frame, text=name, variable=var)
            chk.grid(row=i//2, column=i%2, sticky="w", padx=5, pady=2)
            self.alg_vars[name] = var

        ctk.CTkLabel(cal, text="Quantum (RR):").pack(padx=10, pady=(5,2), anchor="w")
        self.quantum_entry = ctk.CTkEntry(cal, placeholder_text="Enter quantum", state="disabled")
        self.quantum_entry.insert(0, "2")
        self.quantum_entry.pack(padx=10, pady=2, anchor="w")

        # --- Sincronización ---
        sync = tabs.tab("Sincronización")
        ctk.CTkButton(sync, text="Cargar procesos", command=self.load_processes_sync)\
            .pack(padx=10, pady=(10,5), anchor="w")
        ctk.CTkButton(sync, text="Cargar recursos", command=self.load_resources_sync)\
            .pack(padx=10, pady=5, anchor="w")
        ctk.CTkButton(sync, text="Cargar acciones", command=self.load_actions_sync)\
            .pack(padx=10, pady=5, anchor="w")
        self.scroll_sync = ctk.CTkScrollableFrame(sync, height=150)
        self.scroll_sync.pack(fill="both", padx=10, pady=(0,10))
        ctk.CTkLabel(sync, text="Modo de sincronización:")\
            .pack(padx=10, pady=(5,2), anchor="w")
        self.mode_menu = ctk.CTkOptionMenu(sync, values=["mutex","semaphore"])
        self.mode_menu.set("mutex"); self.mode_menu.pack(padx=10, pady=2, anchor="w")

        # --- Controles de ejecución ---
        execf = ctk.CTkFrame(ctrl)
        execf.grid(row=1, column=0, padx=10, pady=10, sticky="we")
        for i,(txt,cmd) in enumerate([
            ("Ejecutar", self.execute_simulation),
            ("Pausar",  self.pause_simulation),
            ("Reset",   self.reset_simulation)
        ]):
            ctk.CTkButton(execf, text=txt, command=cmd)\
               .grid(row=0,column=i,padx=5,pady=5)
        ctk.CTkLabel(execf, text="Delay (s):").grid(row=1,column=0,padx=5,pady=5,sticky="w")
        self.delay_slider = ctk.CTkSlider(execf, from_=0.1, to=2.0,
                                          number_of_steps=19,
                                          command=self.on_delay_change)
        self.delay_slider.set(self.delay)
        self.delay_slider.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="we")

        # --- Panel de consulta ---
        consulta = ctk.CTkFrame(ctrl)
        consulta.grid(row=2, column=0, padx=10, pady=10, sticky="we")
        ctk.CTkLabel(consulta, text="Consulta PID:").grid(row=0, column=0, sticky="w")
        self.pid_menu = ctk.CTkOptionMenu(consulta, values=[], command=self.on_pid_select)
        self.pid_menu.grid(row=0, column=1, padx=5)
        self.detail_label = ctk.CTkLabel(consulta,
                                         text="Seleccione un PID para ver métricas",
                                         justify="left")
        self.detail_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5,0))

        # --- Área de Gantt múltiple con scroll ---
        disp = ctk.CTkFrame(self, corner_radius=0)
        disp.grid(row=0, column=1, sticky="nsew")
        self.multi_gantt = ctk.CTkScrollableFrame(disp)
        self.multi_gantt.pack(fill="both", expand=True, padx=10, pady=10)

    def update_quantum_state(self, *args):
        """
        Habilita el entry de quantum solo si está seleccionado Round Robin.
        """
        if self.alg_vars["Round Robin"].get():
            self.quantum_entry.configure(state="normal")
        else:
            self.quantum_entry.delete(0, tk.END)
            self.quantum_entry.configure(state="disabled")

    def on_delay_change(self, v):
        self.delay = v

    def load_processes_cal(self):
        path = filedialog.askopenfilename(filetypes=[("Txt","*.txt")])
        if not path: return
        self.processes = load_processes(path)
        self.clear_frame(self.scroll_proc)
        for p in self.processes:
            ctk.CTkLabel(self.scroll_proc,
                         text=f"{p.pid}, BT={p.bt}, AT={p.at}, Prio={p.priority}")\
               .pack(anchor="w", padx=5, pady=2)

    def load_processes_sync(self):
        path = filedialog.askopenfilename(filetypes=[("Txt","*.txt")])
        if not path: return
        self.processes = load_processes(path)
        self.refresh_sync_display()

    def load_resources_sync(self):
        path = filedialog.askopenfilename(filetypes=[("Txt","*.txt")])
        if not path: return
        self.resources = load_resources(path)
        self.refresh_sync_display()

    def load_actions_sync(self):
        path = filedialog.askopenfilename(filetypes=[("Txt","*.txt")])
        if not path: return
        self.actions = load_actions(path)
        self.refresh_sync_display()

    def refresh_sync_display(self):
        """
        Limpia y muestra procesos, recursos y acciones en bloques bien diferenciados.
        """
        self.clear_frame(self.scroll_sync)

        # Procesos
        ctk.CTkLabel(self.scroll_sync, text="Procesos:", anchor="w").pack(anchor="w", padx=5, pady=(5,2))
        for p in self.processes:
            ctk.CTkLabel(self.scroll_sync, text=f"  {p.pid}, BT={p.bt}, AT={p.at}, Prio={p.priority}").pack(anchor="w", padx=15)

        # Recursos
        ctk.CTkLabel(self.scroll_sync, text="Recursos:", anchor="w").pack(anchor="w", padx=5, pady=(10,2))
        for r in self.resources:
            ctk.CTkLabel(self.scroll_sync, text=f"  {r.name} (count={r.counter})").pack(anchor="w", padx=15)

        # Acciones
        ctk.CTkLabel(self.scroll_sync, text="Acciones:", anchor="w").pack(anchor="w", padx=5, pady=(10,2))
        for a in self.actions:
            ctk.CTkLabel(self.scroll_sync,
                        text=f"  {a.pid}@{a.cycle}: {a.action} → {a.resource}")\
            .pack(anchor="w", padx=15)

    def clear_frame(self, frame):
        for w in frame.winfo_children():
            w.destroy()

    def execute_simulation(self):
        if self._running:
            return
        self._pause_event.clear()
        is_calendar = (self.tabview.get() == "Calendarización")
        selected = [alg for alg,var in self.alg_vars.items() if var.get()]
        if is_calendar:
            if not selected:
                messagebox.showwarning("Atención", "Selecciona al menos un algoritmo")
                return
            self.sim_events.clear()
            self.last_metrics.clear()
            max_cycle = 0
            quantum = int(self.quantum_entry.get() or 0)
            for alg in selected:
                sim = CalendarizacionSimulator()
                sim.processes = self.processes
                sim.configure(alg, quantum if alg=="Round Robin" else None)
                evs = sim.get_events()
                self.sim_events[alg] = evs
                m = compute_metrics(evs, self.processes)
                self.last_metrics[alg] = m
                max_cycle = max(max_cycle, max(e.end for e in evs))
            texto = "\n".join(
                f"{alg}: WT={self.last_metrics[alg]['avg_waiting_time']:.1f}, "
                f"TA={self.last_metrics[alg]['avg_turnaround_time']:.1f}"
                for alg in selected
            )
            messagebox.showinfo("Métricas por algoritmo", texto)
            self.build_gantt_canvases(selected)
            self.populate_pid_menu([p.pid for p in self.processes])
            self._running = True
            threading.Thread(target=lambda: self.run_multi(selected, max_cycle),
                             daemon=True).start()
        else:
            # 1) Limpiar cualquier Gantt previo
            for w in self.multi_gantt.winfo_children():
                w.destroy()

            # 2) Configurar simulador de sincronización
            sim = SincronizacionSimulator()
            sim.processes, sim.resources, sim.actions = (
                self.processes, self.resources, self.actions
            )
            sim.configure(self.mode_menu.get())
            evs      = sim.get_events()
            max_c    = sim.get_max_cycle()
            acc      = sum(1 for e in evs if e.status=="ACCESED")
            waits    = sum(1 for e in evs if e.status!="ACCESED")
            messagebox.showinfo("Métricas de Sincronización",
                                f"Accesos: {acc}\nEsperas: {waits}")

            # 3) Crear canvas exclusivo para sincronización
            container = tk.Frame(self.multi_gantt)
            container.pack(fill="both", expand=True)
            self.sync_canvas = tk.Canvas(container, bg="white", height=ROW_HEIGHT* len(self.processes))
            v_scroll = tk.Scrollbar(container, orient="vertical", command=self.sync_canvas.yview)
            h_scroll = tk.Scrollbar(self.multi_gantt, orient="horizontal", command=self.sync_canvas.xview)
            self.sync_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

            self.sync_canvas.pack(side="left", fill="both", expand=True)
            v_scroll.pack(side="right", fill="y")
            h_scroll.pack(side="bottom", fill="x")

            # 4) Lanzar animación de sincronización
            self._running = True
            self._pause_event.clear()
            threading.Thread(target=lambda: self.run_sync(evs, max_c), daemon=True).start()
    
    def run_sync(self, events, max_cycle):
        """
        Dibuja cada evento de sincronización en self.sync_canvas,
        iterando ciclos por ev.start en lugar de ev.cycle.
        """
        # Prepara índice de recursos
        recurso_index = {r.name: i for i, r in enumerate(self.resources)}

        for cycle in range(max_cycle + 1):
            # pausa/resume
            while self._pause_event.is_set():
                time.sleep(0.1)
            if not self._running:
                break

            # actualiza etiqueta de ciclo
            self.cycle_label.configure(text=f"Ciclo: {cycle}")

            # dibuja los eventos que comienzan en este ciclo
            for ev in events:
                if ev.start == cycle:
                    # coordenadas
                    x1 = cycle * X_SCALE
                    x2 = ev.end * X_SCALE
                    row = recurso_index[ev.resource]
                    y1 = row * ROW_HEIGHT
                    y2 = y1 + ROW_HEIGHT - 5

                    # color según estado
                    color = "#4CAF50" if ev.status == "ACCESED" else ""
                    rect = self.sync_canvas.create_rectangle(
                        x1, y1, x2, y2,
                        fill=color, outline="black"
                    )
                    self.sync_canvas.create_text(
                        (x1 + x2) / 2, (y1 + y2) / 2,
                        text=ev.pid, fill="black"
                    )
                    # bind para detalle
                    self.sync_canvas.tag_bind(
                        rect, "<Button-1>",
                        lambda e, ev=ev: self.show_event_details(ev)
                    )

            # actualiza scrollregion
            self.sync_canvas.configure(
                scrollregion=self.sync_canvas.bbox("all")
            )

            time.sleep(self.delay)

        self._running = False
        self.cycle_label.configure(text="¡Listo!")

    def pause_simulation(self):
        if not self._running:
            return
        if self._pause_event.is_set():
            self._pause_event.clear()
        else:
            self._pause_event.set()

    def reset_simulation(self):
        self._running = False
        self._pause_event.clear()
        for canvas in getattr(self, 'gantt_canvases', {}).values():
            canvas.delete("all")
        self.color_map.clear()
        self.cycle_label.configure(text="Ciclo: 0")
        self.pid_menu.configure(values=[])
        self.detail_label.configure(text="Seleccione un PID para ver métricas")

    def build_gantt_canvases(self, algos):
        """
        Crea un block por algoritmo con:
        - un Canvas que ocupa todo el ancho
        - scrollbar vertical a la derecha del Canvas
        - scrollbar horizontal al fondo, sobre todo el ancho
        Usamos PACK exclusivamente para no mezclar gestores.
        """
        # 1) limpia previos
        for w in self.multi_gantt.winfo_children():
            w.destroy()

        self.gantt_canvases = {}
        for alg in algos:
            # contenedor principal
            frm = ctk.CTkFrame(self.multi_gantt)
            frm.pack(fill="x", pady=5)

            # etiqueta del algoritmo
            ctk.CTkLabel(frm, text=alg, anchor="w").pack(fill="x", padx=5, pady=(0,2))

            # sub-contenedor para Canvas + scroll vertical
            container = tk.Frame(frm)
            container.pack(fill="both", expand=True)

            # 2) crea el Canvas y el scroll vertical
            canvas = tk.Canvas(container, bg="white", height=150)
            v_scroll = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=v_scroll.set)

            canvas.pack(side="left", fill="both", expand=True)
            v_scroll.pack(side="right", fill="y")

            # 3) crea el scroll horizontal **en el frame principal**, ocupando todo el ancho
            h_scroll = tk.Scrollbar(frm, orient="horizontal", command=canvas.xview)
            canvas.configure(xscrollcommand=h_scroll.set)

            h_scroll.pack(side="bottom", fill="x")

            # 4) guarda referencias para el run_multi
            self.gantt_canvases[alg] = canvas
            self.color_map[alg] = {}


    def run_multi(self, algos, max_cycle):
        for cycle in range(max_cycle+1):
            while self._pause_event.is_set():
                time.sleep(0.1)
            if not self._running:
                break
            self.cycle_label.configure(text=f"Ciclo: {cycle}")
            for alg in algos:
                canvas = self.gantt_canvases[alg]
                for ev in self.sim_events[alg]:
                    if ev.start == cycle:
                        pid = ev.pid
                        cmap = self.color_map[alg]
                        if pid not in cmap:
                            import random
                            r,g,b = [random.randint(100,255) for _ in range(3)]
                            cmap[pid] = f"#{r:02X}{g:02X}{b:02X}"
                        color = cmap[pid]
                        x1, x2 = ev.start*X_SCALE, ev.end*X_SCALE
                        idx = list(cmap).index(pid)
                        y1, y2 = idx*ROW_HEIGHT, idx*ROW_HEIGHT+ROW_HEIGHT-5
                        rect = canvas.create_rectangle(x1,y1,x2,y2,
                                                       fill=color, outline=color)
                        canvas.create_text((x1+x2)/2,(y1+y2)/2, text=pid, fill="white")
                        canvas.tag_bind(rect, "<Button-1>",
                                        lambda e, ev=ev: self.show_event_details(ev))
                        canvas.configure(scrollregion=canvas.bbox("all"))
            time.sleep(self.delay)
        self._running = False
        self.cycle_label.configure(text="¡Listo!")

    def populate_pid_menu(self, pid_list):
        self.pid_menu.configure(values=pid_list)
        if pid_list:
            self.pid_menu.set(pid_list[0])
            self.on_pid_select(pid_list[0])

    def on_pid_select(self, pid):
        if not self.last_metrics:
            return
        text = f"PID: {pid}\n"
        for alg, m in self.last_metrics.items():
            pm = m["per_process"].get(pid, {})
            wt = pm.get("waiting_time", 0)
            ta = pm.get("turnaround_time", 0)
            text += f"{alg}: WT={wt:.1f}, TA={ta:.1f}\n"
        self.detail_label.configure(text=text.strip())

    def show_event_details(self, ev):
        text = (
            f"PID: {ev.pid}\n"
            f"Inicia en: {ev.start}\n"
            f"Termina en: {ev.end}\n"
            f"Estado: {getattr(ev, 'status','ACCESED')}"
        )
        messagebox.showinfo("Detalle de Evento", text)

if __name__ == "__main__":
    app = SimulationApp()
    app.mainloop()
