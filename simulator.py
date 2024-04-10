import heapq
from dataclasses import dataclass
from enum import Enum, auto
from functools import total_ordering
from random import random


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


class EventKind(Enum):
    ARRIVAL = auto()
    PASSAGE = auto()
    DEPARTURE = auto()


@dataclass
@total_ordering
class Event:
    time: float
    kind: EventKind
    queue: str

    def __eq__(self, o: 'Event') -> bool:
        return self.__dict__ == o.__dict__

    def __gt__(self, o: 'Event') -> bool:
        return self.time > o.time


class Queue:
    def __init__(
        self, name: str, servers: int, max_queue_size: int,
        departure_range: float, out: dict[str, float]
    ):
        self.name = name
        self.servers = servers
        self.max_queue_size = max_queue_size
        self.departure_range = departure_range
        self.out = out
        self.is_end = len(self.out) == 0
        self.in_queue = 0
        self.times_per_size = [0 for _ in range(0, self.max_queue_size + 1)]
        self.events_lost = 0

    def is_full(self) -> bool:
        return self.in_queue >= self.max_queue_size


class Simulator:
    def __init__(
            self, queues: list[Queue], start_queue: str, arrival_range: range,
            random: Random | RandomFromList
    ):
        self.queues = {q.name: q for q in queues}
        self.start_queue = self.queues[start_queue]
        self.arrival_range = arrival_range
        self.random = random
        self.schedule = []
        self.time = 0
        self.random_generated = 0

    def start(self, time: float = None):
        self._schedule_arrival(time)

    def step(self):
        event = self._pop_next_event()

        if event.kind == EventKind.ARRIVAL:
            self._arrive(event)
        elif event.kind == EventKind.PASSAGE:
            self._pass(event)
        else:
            self._depart(event)

    def _pop_next_event(self) -> Event:
        return heapq.heappop(self.schedule)

    def _arrive(self, e: Event):
        self._set_time(e.time)

        if not self.start_queue.is_full():
            self.start_queue.in_queue += 1

            if self.start_queue.in_queue <= self.start_queue.servers:
                if self.start_queue.is_end:
                    self._schedule_departure(self.start_queue)
                else:
                    self._schedule_passage(self.start_queue)
        else:
            self.start_queue.events_lost += 1

        self._schedule_arrival()

    def _pass(self, e: Event):
        self._set_time(e.time)
        queue = e.queue
        queue.in_queue -= 1

        if queue.in_queue >= queue.servers:
            self._schedule_passage(queue)

        destination = self._get_destination(queue)

        if not destination.is_full():
            destination.in_queue += 1

            if destination.in_queue <= destination.servers:
                if destination.is_end:
                    self._schedule_departure(destination)
                else:
                    self._schedule_passage(destination)
        else:
            destination.events_lost += 1

    def _depart(self, e: Event):
        self._set_time(e.time)
        queue = e.queue
        queue.in_queue -= 1

        if queue.in_queue >= queue.servers:
            self._schedule_departure(queue)

    def _schedule_arrival(self, time: float = None):
        if time is None:
            time = self._get_arrival_time()

        heapq.heappush(
            self.schedule,
            Event(self.time + time, EventKind.ARRIVAL, self.start_queue)
        )

    def _schedule_passage(self, queue: Queue):
        heapq.heappush(
            self.schedule,
            Event(
                self.time + self._get_departure_time(queue),
                EventKind.PASSAGE, queue
            )
        )

    def _schedule_departure(self, queue: Queue):
        heapq.heappush(
            self.schedule,
            Event(
                self.time + self._get_departure_time(queue),
                EventKind.DEPARTURE, queue
            )
        )

    def _get_arrival_time(self) -> float:
        self.random_generated += 1

        return self.random.next() * (
            self.arrival_range.stop - self.arrival_range.start
        ) + self.arrival_range.start

    def _get_departure_time(self, queue: Queue) -> float:
        self.random_generated += 1

        return self.random.next() * (
            queue.departure_range.stop - queue.departure_range.start
        ) + queue.departure_range.start

    def _get_destination(self, queue: Queue) -> Queue:
        x = random()
        choice = None

        for q, p in queue.out.items():
            x -= p

            if x <= 0:
                choice = q

        return self.queues[choice]

    def _set_time(self, time: float):
        delta = time - self.time

        for q in self.queues.values():
            q.times_per_size[q.in_queue] += delta

        self.time = time
