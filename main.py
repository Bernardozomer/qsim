import heapq
from dataclasses import dataclass
from functools import total_ordering

# RNG parameters.
A = 1_140_671_485
C = 12_820_163
M = 2 ** 24
SEED = 7
# Simulator parameters.
RANDOM_LIMIT = 100_000
MAX_QUEUE_SIZE = 10
SERVERS = 1
ARRIVAL_RANGE = range(5, 6)
DEPARTURE_RANGE = range(1, 3)


class Random:
    def __init__(self, a: int = A, c: int = C, m: int = M, seed: float = SEED):
        self.a = a
        self.c = c
        self.m = m
        self.previous = seed

    def next(self) -> float:
        self.previous = ((self.a * self.previous) + self.c) % self.m
        return self.previous / self.m


@ dataclass
@total_ordering
class Event:
    time: float
    is_arrival: bool

    def __eq__(self, o: 'Event') -> bool:
        return self.__dict__ == o.__dict__

    def __gt__(self, o: 'Event') -> bool:
        return self.time > o.time


class Simulator:
    def __init__(
            self, servers: int, max_queue_size: int,
            arrival_range: float, departure_range: float,
            random: Random = Random()
    ):
        self.servers = servers
        self.max_queue_size = max_queue_size
        self.arrival_range = arrival_range
        self.departure_range = departure_range
        self.random = random
        self.schedule = []
        self.in_queue = 0
        self.time = 0
        self.times_per_size = [0 for _ in range(0, self.max_queue_size)]
        self.random_generated = 0

    def start(self):
        self._schedule_arrival()

    def step(self):
        event = self._pop_next_event()

        if event.is_arrival:
            self._arrive(event)
        else:
            self._depart(event)

    def is_full(self) -> bool:
        return self.in_queue < self.max_queue_size

    def _pop_next_event(self) -> Event:
        return heapq.heappop(self.schedule)

    def _arrive(self, e: Event):
        self._increment_time(e.time)

        if not self.is_full():
            self._enqueue()

            if self.in_queue <= self.servers:
                self._schedule_departure()

        self._schedule_arrival()

    def _depart(self, e: Event):
        self._increment_time(e.time)
        self._dequeue()

        if self.in_queue >= self.servers:
            self._schedule_departure()

    def _schedule_arrival(self):
        heapq.heappush(
            self.schedule,
            Event(self.time + self._get_arrival_time(), is_arrival=True)
        )

    def _schedule_departure(self):
        heapq.heappush(
            self.schedule,
            Event(self.time + self._get_departure_time(), is_arrival=False)
        )

    def _enqueue(self):
        self.in_queue += 1

    def _dequeue(self):
        self.in_queue -= 1

    def _get_arrival_time(self) -> float:
        self.random_generated += 1

        return self.random.next() * (
            self.arrival_range.start - self.arrival_range.stop
        ) + self.arrival_range.start

    def _get_departure_time(self) -> float:
        self.random_generated += 1

        return self.random.next() * (
            self.departure_range.start - self.departure_range.stop
        ) + self.departure_range.start

    def _increment_time(self, delta: float):
        self.time += delta
        self.times_per_size[self.in_queue] += delta


def main():
    simulator = Simulator(
        SERVERS, MAX_QUEUE_SIZE, ARRIVAL_RANGE, DEPARTURE_RANGE
    )

    simulator.start()
    random_remaining = RANDOM_LIMIT - 1

    while (random_remaining > 0):
        simulator.step()
        random_remaining -= simulator.random_generated

    print(f'Final time: {simulator.time}\n')
    print('Times per queue size:')

    for i, time in enumerate(simulator.times_per_size):
        print(f'{i}: {time}   ')


if __name__ == '__main__':
    main()
