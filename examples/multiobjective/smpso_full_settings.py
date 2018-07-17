from jmetal.algorithm import SMPSO
from jmetal.problem import DTLZ1
from jmetal.operator import Polynomial
from jmetal.component import VisualizerObserver, ProgressBarObserver, CrowdingDistanceArchive
from jmetal.util import ScatterPlot, SolutionList


if __name__ == '__main__':
    problem = DTLZ1(rf_path='../../resources/reference_front/DTLZ1.pf')

    algorithm = SMPSO(
        problem=problem,
        swarm_size=100,
        max_evaluations=25000,
        mutation=Polynomial(probability=1.0/problem.number_of_variables, distribution_index=20),
        leaders=CrowdingDistanceArchive(100)
    )

    observer = VisualizerObserver()
    algorithm.observable.register(observer=observer)

    progress_bar = ProgressBarObserver(step=100, maximum=25000)
    algorithm.observable.register(observer=progress_bar)

    algorithm.run()
    front = algorithm.get_result()

    # Plot frontier to file
    pareto_front = ScatterPlot(plot_title='SMPSO-DTLZ1', axis_labels=problem.obj_labels)
    pareto_front.plot(front, reference_front=problem.reference_front)

    # Save variables to file
    SolutionList.print_function_values_to_file(front, 'FUN.SMPSO.' + problem.get_name())
    SolutionList.print_variables_to_file(front, 'VAR.SMPSO.' + problem.get_name())

    print('Algorithm (continuous problem): ' + algorithm.get_name())
    print('Problem: ' + problem.get_name())
    print('Computing time: ' + str(algorithm.total_computing_time))
