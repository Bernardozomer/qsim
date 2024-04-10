import heapq
from dataclasses import dataclass
from enum import Enum, auto
from functools import total_ordering
from random import random


class Random:
    """Random number generator."""

    def __init__(self, a: int, c: int, m: int, seed: float):
        self.a = a
        self.c = c
        self.m = m
        self.previous = seed

    def next(self) -> float:
        """Generate a random number between 0 and 1."""
        self.previous = ((self.a * self.previous) + self.c) % self.m
        return self.previous / self.m


class RandomFromList:
    """Random number "generator"
    which cycles through a list of pregenerated random numbers.
    """

    def __init__(self, randoms: list[float]):
        self.randoms = randoms
        self.next_idx = 0

    def next(self) -> float:
        """Return the next random number in the list,
        looping back to the beginning if needed.
        """

        next_idx = self.next_idx

        # Loop back if needed.
        if self.next_idx + 1 == len(self.randoms):
            self.next_idx = 0
        else:
            self.next_idx += 1

        return self.randoms[next_idx]


class EventKind(Enum):
    ARRIVAL = auto()
    """Arrival events come from outside into the system."""
    PASSAGE = auto()
    """Passage events go from one queue in the system to another."""
    DEPARTURE = auto()
    """Departure events go from the system to outside."""


@dataclass
@total_ordering
class Event:
    """Event class with custom ordering per time."""

    time: float
    """The time at which this event should take effect."""
    kind: EventKind
    """The event kind."""
    queue: str
    """From which queue this event was issued.
    Ignored for arrival events.
    """

    def __eq__(self, o: 'Event') -> bool:
        return self.__dict__ == o.__dict__

    def __gt__(self, o: 'Event') -> bool:
        return self.time > o.time


class Queue:
    """Query parameters and current state."""

    def __init__(
        self, name: str, servers: int, max_queue_size: int,
        departure_range: float, out: dict[str, float]
    ):
        self.name = name
        """The query name."""
        self.servers = servers
        """The amount of servers in this queue."""
        self.max_queue_size = max_queue_size
        """The capacity of this queue."""
        self.departure_range = departure_range
        """Time range for how long clients stay in this queue."""
        self.out = out
        """Queue-name-to-probability mapping for determining next queue
        in a passage event. Empty for end queues.
        """
        self.is_end = len(self.out) == 0
        """End queues are those which issue departure events."""
        self.in_queue = 0
        """How many client are currently in the queue."""
        self.times_per_size = [0 for _ in range(0, self.max_queue_size + 1)]
        """How much time the queue spent with each amount of client present
        during the simulation.
        """
        self.events_lost = 0
        """How many events had to be discarded by the queue
        and were thus lost.
        """

    def is_full(self) -> bool:
        """Return if the queue is full and cannot take any more clients."""
        return self.in_queue >= self.max_queue_size


class Simulator:
    """Manage queues, process events and route clients."""

    def __init__(
            self, queues: list[Queue], start_queue: str, arrival_range: range,
            random: Random | RandomFromList
    ):
        self.queues = {q.name: q for q in queues}
        """Queue-name-to-queue-object mapping for O(1) access."""
        self.start_queue = self.queues[start_queue]
        """Queue in the system which receives all arrival events."""
        self.arrival_range = arrival_range
        """Time range for how long it takes for an arrival to occur."""
        self.random = random
        """The random number generator"""
        self.schedule = []
        """Heap of events to be processed, sorted by earliest deadline first.
        Should not be manipulated without the heapq package functions.
        """
        self.time = 0
        """Global simulation time."""
        self.random_generated = 0
        """Amount of random numbers generated."""

    def start(self, time: float = None):
        """Schedule the first arrival."""
        self._schedule_arrival(time)

    def step(self):
        """Step through the simulation."""
        event = self._pop_next_event()

        if event.kind == EventKind.ARRIVAL:
            self._arrive(event)
        elif event.kind == EventKind.PASSAGE:
            self._pass(event)
        else:
            self._depart(event)

    def _pop_next_event(self) -> Event:
        """Return the event with the earliest deadline
        and remove it from the schedule."""

        return heapq.heappop(self.schedule)

    def _arrive(self, e: Event):
        """Process an arrival event and schedule a new one.
        If possible, adds a new client to the start queue and schedules their
        passage or departure.
        """

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
        """Process a passage event and schedule a new one if needed.
        Choose the next queue at random from the passer's output probabilities.
        If the client could enter the next queue,
        also schedule their passage or departure.
        """

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
        """Process a departure event and schedule a new one if needed."""
        self._set_time(e.time)
        queue = e.queue
        queue.in_queue -= 1

        if queue.in_queue >= queue.servers:
            self._schedule_departure(queue)

    def _schedule_arrival(self, time: float = None):
        """Add a new arrival event to the schedule."""
        if time is None:
            time = self._get_arrival_time()

        heapq.heappush(
            self.schedule,
            Event(self.time + time, EventKind.ARRIVAL, self.start_queue)
        )

    def _schedule_passage(self, queue: Queue):
        """Add a new passage event to the schedule."""
        heapq.heappush(
            self.schedule,
            Event(
                self.time + self._get_departure_time(queue),
                EventKind.PASSAGE, queue
            )
        )

    def _schedule_departure(self, queue: Queue):
        """Add a new departure event to the schedule."""
        heapq.heappush(
            self.schedule,
            Event(
                self.time + self._get_departure_time(queue),
                EventKind.DEPARTURE, queue
            )
        )

    def _get_arrival_time(self) -> float:
        """Randomly generate the time for an arrival event."""
        self.random_generated += 1

        return self.random.next() * (
            self.arrival_range.stop - self.arrival_range.start
        ) + self.arrival_range.start

    def _get_departure_time(self, queue: Queue) -> float:
        """Randomly generate the time for a passage or departure event."""
        self.random_generated += 1

        return self.random.next() * (
            queue.departure_range.stop - queue.departure_range.start
        ) + queue.departure_range.start

    def _get_destination(self, queue: Queue) -> Queue:
        """Choose the next queue for a passage event at random
        from the passer's output probabilities.
        """

        # Generate a random number between 0 and 1.
        x = random()
        choice = None

        # Continuously subtract the random number from the passer's output
        # probabilities and elect the queue whose probability brings it at
        # or below zero as the receiver.
        for q, p in queue.out.items():
            x -= p

            if x <= 0:
                choice = q

        return self.queues[choice]

    def _set_time(self, time: float):
        """Set the global simulation time
        and update the times per size of each queue.
        """

        delta = time - self.time

        for q in self.queues.values():
            q.times_per_size[q.in_queue] += delta

        self.time = time
