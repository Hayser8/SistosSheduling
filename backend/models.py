from dataclasses import dataclass

@dataclass
class Process:
    pid: str
    bt: int       # Burst Time
    at: int       # Arrival Time
    priority: int

@dataclass
class Resource:
    name: str
    counter: int

@dataclass
class Action:
    pid: str
    action: str  
    resource: str
    cycle: int
