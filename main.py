import heapq
import json
import sys
from dataclasses import dataclass
from functools import total_ordering


class Parameters:
    def __init__(self, params):
        self.pregen = params['pregen']
        self.max_queue_size = params['max_queue_size']
        self.servers = params['servers']

        self.arrival_range = range(
            params['arrival_range'][0], params['arrival_range'][1]
        )

        self.departure_range = range(
            params['departure_range'][0], params['departure_range'][1]
        )

        self.start_time = params['start_time']
        self.random_limit = params['random_limit']
        self.pregen = params['pregen']

        if self.pregen:
            self.randoms = params['randoms']
        else:
            self.a = params['a']
            self.c = params['c']
            self.m = params['m']
            self.seed = params['seed']


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
            random: Random | RandomFromList
    ):
        self.servers = servers
        self.max_queue_size = max_queue_size
        self.arrival_range = arrival_range
        self.departure_range = departure_range
        self.random = random
        self.schedule = []
        self.in_queue = 0
        self.time = 0
        self.times_per_size = [0 for _ in range(0, self.max_queue_size + 1)]
        self.random_generated = 0
        self.events_lost = 0

    def start(self, time: float = None):
        self._schedule_arrival(time)

    def step(self):
        event = self._pop_next_event()

        if event.is_arrival:
            self._arrive(event)
        else:
            self._depart(event)

    def is_full(self) -> bool:
        return self.in_queue >= self.max_queue_size

    def _pop_next_event(self) -> Event:
        return heapq.heappop(self.schedule)

    def _arrive(self, e: Event):
        self._set_time(e.time)

        if not self.is_full():
            self.in_queue += 1

            if self.in_queue <= self.servers:
                self._schedule_departure()
        else:
            self.events_lost += 1

        self._schedule_arrival()

    def _depart(self, e: Event):
        self._set_time(e.time)
        self.in_queue -= 1

        if self.in_queue >= self.servers:
            self._schedule_departure()

    def _schedule_arrival(self, time: float = None):
        if time is None:
            time = self._get_arrival_time()

        heapq.heappush(
            self.schedule,
            Event(self.time + time, is_arrival=True)
        )

    def _schedule_departure(self):
        heapq.heappush(
            self.schedule,
            Event(self.time + self._get_departure_time(), is_arrival=False)
        )

    def _get_arrival_time(self) -> float:
        self.random_generated += 1

        return self.random.next() * (
            self.arrival_range.stop - self.arrival_range.start
        ) + self.arrival_range.start

    def _get_departure_time(self) -> float:
        self.random_generated += 1

        return self.random.next() * (
            self.departure_range.stop - self.departure_range.start
        ) + self.departure_range.start

    def _set_time(self, delta: float):
        self.times_per_size[self.in_queue] += delta - self.time
        self.time = delta


def main():
    args = sys.argv
    params = parse_params_file(args[1])

    if params.pregen:
        random_ = RandomFromList(params.randoms)
    else:
        random_ = Random(params.a, params.c, params.m, params.seed)

    simulator = Simulator(
        params.servers, params.max_queue_size,
        params.arrival_range, params.departure_range,
        random_
    )

    simulator.start(params.start_time)
    last_random_generated = 0
    random_remaining = params.random_limit

    while (random_remaining > 0):
        simulator.step()
        random_remaining -= simulator.random_generated - last_random_generated
        last_random_generated = simulator.random_generated

    print(f'Final time: {simulator.time}\n')
    print('Times per queue size:')

    for i, time in enumerate(simulator.times_per_size):
        print(f'{i}: {time}   ')

    print(f'\nEvents lost: {simulator.events_lost}')


def parse_params_file(filename) -> Parameters:
    with open(filename) as fp:
        params = json.load(fp)
        return Parameters(params)


if __name__ == '__main__':
    main()
