from jmetal.algorithm.singleobjective.evolutionaryalgorithm import ElitistEvolutionStrategy
from jmetal.core.solution import BinarySolution
from jmetal.operator.mutation import BitFlip
from jmetal.problem.singleobjective.unconstrained import OneMax


def main() -> None:
    bits = 512
    problem = OneMax(bits)

    algorithm = ElitistEvolutionStrategy[BinarySolution, BinarySolution](
        problem=problem,
        mu=1,
        lambd_a=10,
        max_evaluations=25000,
        mutation=BitFlip(probability=1.0/bits)
    )

    algorithm.run()
    result = algorithm.get_result()

    print("Algorithm: " + algorithm.get_name())
    print("Problem: " + problem.get_name())
    print("Solution: " + str(result.variables[0]))
    print("Fitness:  " + str(result.objectives[0]))
    print("Computing time: " + str(algorithm.total_computing_time))

if __name__ == '__main__':
    main()
