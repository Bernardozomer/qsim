import json
import sys

import simulator


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


def main():
    args = sys.argv
    params = parse_params_file(args[1])

    if params.pregen:
        rand = simulator.RandomFromList(params.randoms)
    else:
        rand = simulator.Random(params.a, params.c, params.m, params.seed)

    simul = simulator.Simulator(
        params.servers, params.max_queue_size,
        params.arrival_range, params.departure_range,
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
