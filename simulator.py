import heapq
from dataclasses import dataclass
from functools import total_ordering
from typing import List
from enum import Enum


class Random:
    def __init__(self, a: int, c: int, m: int, seed: float):
        self.a = a
        self.c = c
        self.m = m
        self.previous = seed

    def next(self) -> float:
        self.previous = ((self.a * self.previous) + self.c) % self.m
        return self.previous / self.m


class RandomFromList:
    def __init__(self, randoms: list[float]):
        self.randoms = randoms
        self.next_idx = 0

    def next(self) -> float:
        next_idx = self.next_idx

        if self.next_idx + 1 == len(self.randoms):
            self.next_idx = 0
        else:
            self.next_idx += 1

        return self.randoms[next_idx]


class EventType(Enum):
    ARRIVE = "arrive"
    PASS = "pass"
    DEPART = "depart"

@dataclass
@total_ordering
class Event:
    time: float
    event_type: EventType

    def __eq__(self, o: 'Event') -> bool:
        return self.__dict__ == o.__dict__

    def __gt__(self, o: 'Event') -> bool:
        return self.time > o.time

class Queue:
    def __init__(
            self, servers: int, max_queue_size: int,
            arrival_range: float, departure_range: float
    ):
        self.servers = servers
        self.max_queue_size = max_queue_size
        self.arrival_range = arrival_range
        self.departure_range = departure_range

class Simulator:
    def __init__(
            self, random: Random | RandomFromList, queues: List[Queue]
    ):
        self.queues = queues
        self.random = random
        self.schedule = []
        self.in_queue = [0, 0]
        self.time = 0
        self.times_per_size = [0 for _ in range(0, self.queues[0].max_queue_size + 1)]
        self.random_generated = 0
        self.events_lost = 0

    def start(self, time: float = None):
        self._schedule_arrival(time)

    def step(self):
        event = self._pop_next_event()

        if event.event_type == EventType.ARRIVE:
            self._arrive(event)
        elif event.event_type == EventType.DEPART:
            self._depart(event)
        else:
            self._pass(event)

    def first_is_full(self) -> bool:
        return (self.in_queue[0] >= self.queues[0].max_queue_size)

    def second_is_full(self) -> bool:
        return (self.in_queue[1] >= self.queues[1].max_queue_size)


    def _pop_next_event(self) -> Event:
        return heapq.heappop(self.schedule)

    def _arrive(self, e: Event):
        self._set_time(e.time, 0)

        if not self.first_is_full():
            self.in_queue[0] += 1

            if self.in_queue[0] <= self.queues[0].servers:
                self._schedule_departure()
        else:
            self.events_lost += 1

        self._schedule_arrival()

    def _pass(self, e: Event):
        self._set_time(e.time, 0)
        self.in_queue[0] -= 1
        
        if self.in_queue[1] < self.queues[1].max_queue_size:
            self._set_time(e.time, 1)
            self.in_queue[1] += 1
            self._schedule_pass()
            
    def _depart(self, e: Event):
        self._set_time(e.time, 1)
        self.in_queue[1] -= 1

        if self.in_queue[1] >= self.queues[1].servers:
            self._schedule_departure()

    def _schedule_arrival(self, time: float = None):
        if time is None:
            time = self._get_arrival_time()

        heapq.heappush(
            self.schedule,
            Event(self.time + time, event_type=EventType.ARRIVE)
        )

    def _schedule_pass(self, time: float = None):
        if time is None:
            time = self.time

        heapq.heappush(
            self.schedule,
            Event(self.time + time, event_type=EventType.PASS)
        )
    
    def _schedule_departure(self):
        heapq.heappush(
            self.schedule,
            Event(self.time + self._get_departure_time(), event_type = EventType.DEPART)
        )

    def _get_arrival_time(self) -> float:
        self.random_generated += 1

        return self.random.next() * (
            self.queues[0].arrival_range.stop - self.queues[0].arrival_range.start
        ) + self.queues[0].arrival_range.start

    def _get_departure_time(self) -> float:
        self.random_generated += 1

        return self.random.next() * (
            self.queues[1].departure_range.stop - self.queues[1].departure_range.start
        ) + self.queues[1].departure_range.start

    def _set_time(self, delta: float, queueNumber: int):
        self.times_per_size[self.in_queue[queueNumber]] += delta - self.time
        self.time = delta
