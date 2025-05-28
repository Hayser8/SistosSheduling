import pytest
from backend.sincronizacion import (
    simulate_synchronization,
    SincronizacionSimulator,
    ActionEvent,
)
from backend.models import Resource, Action

@pytest.fixture
def simple_resources():
    # Un recurso R1 con counter=1 (mutex), otro R2 con counter=2 (semaphore)
    return [
        Resource(name="R1", counter=1),
        Resource(name="R2", counter=2),
    ]

@pytest.fixture
def simple_actions():
    # Dos procesos acceden a R1 en ciclo 0, tres procesos acceden a R2 en ciclo 1
    return [
        Action(pid="P1", resource="R1", cycle=0, action="acquire"),
        Action(pid="P2", resource="R1", cycle=0, action="acquire"),
        Action(pid="P3", resource="R2", cycle=1, action="acquire"),
        Action(pid="P4", resource="R2", cycle=1, action="acquire"),
        Action(pid="P5", resource="R2", cycle=1, action="acquire"),
    ]

def test_mutex_mode_limits_to_one(simple_resources, simple_actions):
    events = simulate_synchronization(simple_resources, simple_actions, mode="mutex")
    # En ciclo 0, R1 tiene counter=1 => solo P1 ACCESED, P2 WAITING
    ev0 = [e for e in events if e.start == 0 and e.resource == "R1"]
    assert ev0 == [
        ActionEvent(pid="P1", start=0, end=1, resource="R1", status="ACCESED"),
        ActionEvent(pid="P2", start=0, end=1, resource="R1", status="WAITING"),
    ]

    # En ciclo 1, R2 counter=2 => P3,P4 ACCESED, P5 WAITING
    ev1 = [e for e in events if e.start == 1 and e.resource == "R2"]
    assert ev1 == [
        ActionEvent(pid="P3", start=1, end=2, resource="R2", status="ACCESED"),
        ActionEvent(pid="P4", start=1, end=2, resource="R2", status="ACCESED"),
        ActionEvent(pid="P5", start=1, end=2, resource="R2", status="WAITING"),
    ]

def test_semaphore_mode_same_as_mutex(simple_resources, simple_actions):
    # Dado que cap se lee de Resource.counter y mode no altera lógica actual,
    # el resultado debe ser idéntico
    mtx = simulate_synchronization(simple_resources, simple_actions, mode="mutex")
    sem = simulate_synchronization(simple_resources, simple_actions, mode="semaphore")
    assert sem == mtx

def test_default_counter_when_resource_missing():
    # Acción sobre recurso X que no está en la lista => cap=1 por defecto
    evt = simulate_synchronization(
        resources=[],
        actions=[Action(pid="Z1", resource="X", cycle=5, action="acquire")]
    )
    assert evt == [
        ActionEvent(pid="Z1", start=5, end=6, resource="X", status="ACCESED")
    ]

def test_multiple_cycles_and_ordering():
    resources = [Resource(name="A", counter=1)]
    actions = [
        Action(pid="A1", resource="A", cycle=2, action="acquire"),
        Action(pid="A2", resource="A", cycle=1, action="acquire"),
        Action(pid="A3", resource="A", cycle=2, action="acquire"),
    ]
    ev = simulate_synchronization(resources, actions)
    # Ciclo 1: solo A2
    assert ev[0] == ActionEvent(pid="A2", start=1, end=2, resource="A", status="ACCESED")
    # Ciclo 2: A1 llega antes en la lista => ACCESED, A3 WAITING
    assert ev[1:] == [
        ActionEvent(pid="A1", start=2, end=3, resource="A", status="ACCESED"),
        ActionEvent(pid="A3", start=2, end=3, resource="A", status="WAITING"),
    ]

def test_sincronizacion_simulator_integration(simple_resources, simple_actions):
    sim = SincronizacionSimulator()
    sim.resources = simple_resources
    sim.actions = simple_actions
    sim.configure(mode="mutex")

    # get_events
    events = sim.get_events()
    expected = simulate_synchronization(simple_resources, simple_actions, mode="mutex")
    assert events == expected

    # get_max_cycle
    assert sim.get_max_cycle() == max(e.end for e in expected)

    # reset
    sim.reset()
    assert sim.get_events() == []
    assert sim.get_max_cycle() == 0
