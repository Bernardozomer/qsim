import json
import sys

import simulator


class Parameters:
    def __init__(self, params):
        self.random_limit = params['random_limit']
        self.pregen = params['pregen']

        if self.pregen:
            self.randoms = params['randoms']
        else:
            self.a = params['a']
            self.c = params['c']
            self.m = params['m']
            self.seed = params['seed']

        self.start_queue = params['start_queue']
        self.start_time = params['start_time']

        self.arrival_range = range(
            params['arrival_range'][0], params['arrival_range'][1]
        )

        self.queues = []

        for q_name, q_params in params['queues'].items():
            departure_range = range(
                q_params['departure_range'][0], q_params['departure_range'][1]
            )

            self.queues.append(simulator.Queue(
                q_name, q_params['servers'], q_params['max_queue_size'],
                departure_range, q_params['out']
            ))


def main():
    args = sys.argv
    params = parse_params_file(args[1])

    if params.pregen:
        rand = simulator.RandomFromList(params.randoms)
    else:
        rand = simulator.Random(params.a, params.c, params.m, params.seed)

    simul = simulator.Simulator(
        params.queues, params.start_queue, params.arrival_range, rand
    )

    simul.start(params.start_time)
    last_random_generated = 0
    random_remaining = params.random_limit

    while (random_remaining > 0):
        simul.step()
        random_remaining -= simul.random_generated - last_random_generated
        last_random_generated = simul.random_generated

    print(f'Final time: {simul.time}')

    for q in simul.queues.values():
        print(f'\n{q.name}\n')
        print('Times per queue size:')

        for i, time in enumerate(q.times_per_size):
            print(f'{i}: {time}   ')

        print(f'\nEvents lost: {q.events_lost}')


def parse_params_file(filename) -> Parameters:
    with open(filename) as fp:
        params = json.load(fp)
        return Parameters(params)


if __name__ == '__main__':
    main()
