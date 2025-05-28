import pytest
from backend.calendarizacion import fifo, sjf, srt, rr, priority_np, Event
from backend.models import Process

@pytest.fixture
def simple_processes():
    # pid, arrival time, burst time, priority
    return [
        Process(pid='P1', at=0, bt=3, priority=2),
        Process(pid='P2', at=2, bt=6, priority=1),
        Process(pid='P3', at=4, bt=4, priority=3),
    ]

def test_fifo_basic(simple_processes):
    tl = fifo(simple_processes)
    expected = [
        Event('P1', 0, 3),
        Event('P2', 3, 9),
        Event('P3', 9, 13),
    ]
    assert tl == expected

def test_fifo_with_idle():
    procs = [Process(pid='X', at=5, bt=2, priority=0)]
    tl = fifo(procs)
    # Arranca en t=5 tras el idle
    assert tl == [Event('X', 5, 7)]

def test_sjf_non_preemptive():
    procs = [
        Process(pid='P1', at=0, bt=7, priority=2),
        Process(pid='P2', at=2, bt=4, priority=1),
        Process(pid='P3', at=4, bt=1, priority=3),
    ]
    tl = sjf(procs)
    # P1 corre primero (único disponible), luego P3 (bt=1), luego P2
    expected = [
        Event('P1', 0, 7),
        Event('P3', 7, 8),
        Event('P2', 8, 12),
    ]
    assert tl == expected

def test_sjf_with_idle():
    procs = [
        Process(pid='A', at=3, bt=2, priority=5),
        Process(pid='B', at=5, bt=1, priority=1),
    ]
    tl = sjf(procs)
    # Idle hasta t=3, A:3-5, luego B:5-6
    assert tl == [Event('A', 3, 5), Event('B', 5, 6)]

def test_srt_preemptive_simple():
    procs = [
        Process(pid='P1', at=0, bt=2, priority=1),
        Process(pid='P2', at=1, bt=1, priority=2),
    ]
    tl = srt(procs)
    # P1 corre 0-1, luego llega P2 (rem=1<P1 rem=1) → P2:1-2 → rem P1: 2-3
    expected = [
        Event('P1', 0, 1),
        Event('P2', 1, 2),
        Event('P1', 2, 3),
    ]
    assert tl == expected

def test_srt_no_preemption():
    procs = [Process(pid='Z', at=0, bt=3, priority=1)]
    tl = srt(procs)
    assert tl == [Event('Z', 0, 3)]

def test_rr_round_robin():
    procs = [
        Process(pid='P1', at=0, bt=3, priority=1),
        Process(pid='P2', at=2, bt=1, priority=2),
    ]
    tl = rr(procs, quantum=1)
    # Timeline por quantum=1:
    # P1:0-1, P1:1-2, luego llega P2, P2:2-3, P1 rem=1 → 3-4
    expected = [
        Event('P1', 0, 1),
        Event('P1', 1, 2),
        Event('P2', 2, 3),
        Event('P1', 3, 4),
    ]
    assert tl == expected

def test_rr_with_idle_and_long_quantum():
    procs = [
        Process(pid='X', at=5, bt=4, priority=0),
    ]
    tl = rr(procs, quantum=10)
    # Quantum mayor que burst → se completa en un solo slice
    assert tl == [Event('X', 5, 9)]

def test_priority_non_preemptive():
    procs = [
        Process(pid='P1', at=0, bt=4, priority=3),
        Process(pid='P2', at=1, bt=3, priority=1),
        Process(pid='P3', at=2, bt=2, priority=2),
    ]
    tl = priority_np(procs)
    # P1 corre t=0-4 (único), luego llegan P2 & P3;
    # prioridad menor = más alta → P2 (1):4-7, luego P3:7-9
    expected = [
        Event('P1', 0, 4),
        Event('P2', 4, 7),
        Event('P3', 7, 9),
    ]
    assert tl == expected
