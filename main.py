import json
import sys

import simulator
from typing import List


class Parameters:
    def __init__(self, params):
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
        
        self.queues = []
        
        for queue in params['queues']:
            max_queue_size = queue['max_queue_size']
            servers = queue['servers']

            if 'arrival_range' in queue:
                arrival_range = range(
                    queue['arrival_range'][0], queue['arrival_range'][1]
                )

            departure_range = range(
                queue['departure_range'][0], queue['departure_range'][1]
            )

            self.queues.append(simulator.Queue(
                servers, max_queue_size, arrival_range, departure_range
            ))


def main():
    args = sys.argv
    params = parse_params_file(args[1])

    if params.pregen:
        rand = simulator.RandomFromList(params.randoms)
    else:
        rand = simulator.Random(params.a, params.c, params.m, params.seed)

    simul = simulator.Simulator(
        params.queues,
        rand
    )

    simul.start(params.start_time)
    last_random_generated = 0
    random_remaining = params.random_limit

    while (random_remaining > 0):
        simul.step()
        random_remaining -= simul.random_generated - last_random_generated
        last_random_generated = simul.random_generated

    print(f'Final time: {simul.time}\n')
    print('Times per queue size:')

    for i, time in enumerate(simul.times_per_size):
        print(f'{i}: {time} -> {(time / simul.time)*100:.2f}%   ')

    print(f'\nEvents lost: {simul.events_lost}')


def parse_params_file(filename) -> Parameters:
    with open(filename) as fp:
        params = json.load(fp)
        return Parameters(params)


if __name__ == '__main__':
    main()
