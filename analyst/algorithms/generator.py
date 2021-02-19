#!/usr/bin/env python

operators = {
    'addition': '+',
    'multiplication': '*',
    'root': 'Wurzel',
    'minimum': 'Min',
}

def num_operands(operator_label):
    if operator_label in ['addition', 'multiplication', 'minimum']:
        return 2
    elif operator_label in ['root']:
        return 1
    else:
        raise ValueError(f'Given \'operator_label\' must be a key in \'operators\' (found label: {operator_label})')


def generate(scenario_basename, operator_label, num_operations=1):
    if operator_label not in operators:
        raise ValueError(f'Given \'operator_label\' must be a key in \'operators\' (found label: {operator_label})')

    if not isinstance(num_operations, int):
        raise TypeError(f'Given \'num_operations\' must be of type \'int\' (found type: {type(num_operations)})')

    if num_operations == 1:
        filename = f'{scenario_basename}-{operator_label}'
    else:
        filename = f'{scenario_basename}-{operator_label}-{num_operations}'

    with open(filename + '.alg', 'w') as fd_alg:
        with open(filename + '.kpi', 'w') as fd_kpi:
            operator = operators[operator_label]
            operands = num_operands(operator_label)

            inputs = []
            for i in range(operands):
                inputs.append(f'aa{i:04d}')

            last_eid = inputs[0]
            for i in range(num_operations):
                new_eid = f'bb{i:04d}'
                operand1 = last_eid
                if operands > 1:
                    operand2 = ' ' + inputs[-1]
                else:
                    operand2 = ''

                fd_alg.write(f'{new_eid} {operator} {operand1}{operand2}\n')
                last_eid = new_eid

            fd_kpi.write(f'{last_eid}\n')


def main():
    # generate benchmarks
    for operator_label in operators:
        generate('benchmark', operator_label)

    # generated nested
    for operator_label in operators:
        for num_operators in range(10, 101, 10):
            generate('nested', operator_label, num_operators)


if __name__ == '__main__':
    main()
