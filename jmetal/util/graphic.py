import logging
from abc import ABCMeta
from typing import TypeVar, List

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from plotly import graph_objs as go
from plotly.offline import plot
from pandas import DataFrame

jMetalPyLogger = logging.getLogger('jMetalPy')
S = TypeVar('S')

"""
.. module:: Visualization
   :platform: Unix, Windows
   :synopsis: Classes for plotting fronts.

.. moduleauthor:: Antonio Benítez-Hidalgo <antonio.b@uma.es>
"""


class Plot:
    __metaclass__ = ABCMeta

    def __init__(self, plot_title: str, axis_labels: list):
        self.plot_title = plot_title
        self.axis_labels = axis_labels

        self.number_of_objectives: int = None

    @staticmethod
    def get_objectives(front: List[S]) -> DataFrame:
        if front is None:
            raise Exception('Front is none!')

        return DataFrame(list(solution.objectives for solution in front))


class ScatterStreaming(Plot):

    def __init__(self, plot_title: str, axis_labels: list = None):
        """ Creates a new :class:`ScatterStreaming` instance. Suitable for problems with 2 or 3 objectives in streaming.

        :param plot_title: Title of the diagram.
        :param axis_labels: List of axis labels. """
        super(ScatterStreaming, self).__init__(plot_title, axis_labels)

        import warnings
        warnings.filterwarnings("ignore", ".*GUI is implemented.*")

        self.fig = plt.figure()
        self.sc = None
        self.axis = None

    def plot(self, front: List[S], reference_front: List[S], filename: str = '', show: bool = True) -> None:
        """ Plot a front of solutions (2D or 3D).

        :param front: List of solutions.
        :param reference_front: Reference solution list (if any).
        :param filename: If specified, save the plot into a file.
        :param show: If True, show the final diagram (default to True). """
        objectives = self.get_objectives(front)

        # Initialize plot
        self.number_of_objectives = objectives.shape[1]
        self.__initialize()

        if reference_front:
            jMetalPyLogger.info('Reference front found')
            ref_objectives = self.get_objectives(reference_front)

            if self.number_of_objectives == 2:
                self.__plot(ref_objectives[0], ref_objectives[1], None,
                            color='#323232', marker='*', markersize=3)
            else:
                self.__plot(ref_objectives[0], ref_objectives[1], ref_objectives[2],
                            color='#323232', marker='*', markersize=3)

        if self.number_of_objectives == 2:
            self.__plot(objectives[0], objectives[1], None, color='#98FB98', marker='o', markersize=3)
        else:
            self.__plot(objectives[0], objectives[1], objectives[2], color='#98FB98', marker='o', markersize=3)

        if filename:
            self.fig.savefig(filename, format='png', dpi=200)
        if show:
            self.fig.canvas.mpl_connect('pick_event', lambda event: self.__pick_handler(front, event))
            plt.show()

    def update(self, front: List[S], reference_front: List[S], rename_title: str = '',
               persistence: bool = True) -> None:
        """ Update an already created plot.

        :param front: List of solutions.
        :param reference_front: Reference solution list (if any).
        :param rename_title: New title of the plot.
        :param persistence: If True, keep old points; else, replace them with new values.
        """
        if self.sc is None:
            jMetalPyLogger.warning('Plot must be initialized first.')
            self.plot(front, reference_front, show=False)
            return

        objectives = self.get_objectives(front)

        if persistence:
            # Replace with new points
            self.sc.set_data(objectives[0], objectives[1])

            if self.number_of_objectives == 3:
                self.sc.set_3d_properties(objectives[2])
        else:
            # Add new points
            if self.number_of_objectives == 2:
                self.__plot(objectives[0], objectives[1], None, color='#98FB98', marker='o', markersize=3)
            else:
                self.__plot(objectives[0], objectives[1], objectives[2], color='#98FB98', marker='o', markersize=3)

        # Also, add event handler
        event_handler = \
            self.fig.canvas.mpl_connect('pick_event', lambda event: self.__pick_handler(front, event))

        # Update title with new times and evaluations
        self.fig.suptitle(rename_title, fontsize=13)

        # Re-align the axis
        self.axis.relim()
        self.axis.autoscale_view(True, True, True)

        try:
            # Draw
            self.fig.canvas.draw()
        except KeyboardInterrupt:
            pass

        plt.pause(0.01)

        # Disconnect the pick event for the next update
        self.fig.canvas.mpl_disconnect(event_handler)

    def __initialize(self) -> None:
        """ Initialize the scatter plot for the first time. """
        jMetalPyLogger.info('Generating plot')

        # Initialize a plot
        self.fig.canvas.set_window_title('jMetalPy')

        if self.number_of_objectives == 2:
            self.axis = self.fig.add_subplot(111)

            # Stylize axis
            self.axis.spines['top'].set_visible(False)
            self.axis.spines['right'].set_visible(False)
            self.axis.get_xaxis().tick_bottom()
            self.axis.get_yaxis().tick_left()
        elif self.number_of_objectives == 3:
            self.axis = Axes3D(self.fig)
            self.axis.autoscale(enable=True, axis='both')
        else:
            raise Exception('Number of objectives must be either 2 or 3')

        self.axis.set_autoscale_on(True)
        self.axis.autoscale_view(True, True, True)

        # Style options
        self.axis.grid(color='#f0f0f5', linestyle='-', linewidth=1, alpha=0.5)
        self.fig.suptitle(self.plot_title, fontsize=13)

        jMetalPyLogger.info('Plot initialized')

    def __plot(self, x_values, y_values, z_values, **kwargs) -> None:
        if self.number_of_objectives == 2:
            self.sc, = self.axis.plot(x_values, y_values, ls='None', picker=10, **kwargs)
        else:
            self.sc, = self.axis.plot(x_values, y_values, z_values, ls='None', picker=10, **kwargs)

    def __pick_handler(self, front: List[S], event):
        """ Handler for picking points from the plot. """
        line, ind = event.artist, event.ind[0]
        x, y = line.get_xdata(), line.get_ydata()

        jMetalPyLogger.debug('Selected front point ({0}): ({1}, {2})'.format(ind, x[ind], y[ind]))

        sol = next((solution for solution in front
                    if solution.objectives[0] == x[ind] and solution.objectives[1] == y[ind]), None)

        if sol is not None:
            with open('{0}-{1}'.format(x[ind], y[ind]), 'w') as of:
                of.write(sol.__str__())
        else:
            jMetalPyLogger.warning('Solution is none')
            return True


class ScatterPlot(Plot):

    def __init__(self, plot_title: str, axis_labels: list = None):
        """ Creates a new :class:`ScatterPlot` instance. Suitable for problems with 2 or more objectives.

        :param plot_title: Title of the diagram.
        :param axis_labels: List of axis labels. """
        super(ScatterPlot, self).__init__(plot_title, axis_labels)

        self.figure: go.Figure = None
        self.layout = None
        self.data = None

    def plot(self, front: List[S], reference_front: List[S] = None, show: bool = True) -> None:
        """ Plot a front of solutions (2D, 3D or parallel coordinates).

        :param front: List of solutions.
        :param reference_front: Reference solution list (if any).
        :param show: If True, show and save (file `front.html`) the final diagram (default to True). """
        self.__initialize()

        objectives = self.get_objectives(front)
        self.data = [self.__generate_trace(objectives, legend='front')]

        if reference_front:
            objectives = self.get_objectives(reference_front)
            self.data.append(
                self.__generate_trace(
                    objectives, legend='reference',
                    symbol='diamond-open', size=3, opacity=0.4, color='rgb(2, 130, 242)'))

        self.figure = go.Figure(data=self.data, layout=self.layout)

        if show:
            plot(self.figure, filename='front.html')

    def add_data(self, data: List[S], **kwargs) -> None:
        """ Update an already created plot with new data.

        :param data: List of solutions to be included.
        :param kwargs: Optional values for `styling markers <https://plot.ly/python/marker-style/>`_. """
        if self.figure is None:
            jMetalPyLogger.warning('Plot must be initialized first.')
            self.plot(data, None, show=False)
            return

        objectives = self.get_objectives(data)
        new_data = self.__generate_trace(objectives=objectives, size=5, color='rgb(255, 170, 0)', **kwargs)

        self.data.append(new_data)
        self.figure = go.Figure(data=self.data, layout=self.layout)

    def show(self) -> None:
        plot(self.figure, filename='front')

    def __initialize(self):
        """ Initialize the plot for the first time. """
        jMetalPyLogger.info('Generating plot')

        self.layout = go.Layout(
            margin=dict(l=100, r=100, b=100, t=100),
            title=self.plot_title,
            scene=dict(
                xaxis=dict(title=self.axis_labels[0:1][0] if self.axis_labels[0:1] else None),
                yaxis=dict(title=self.axis_labels[1:2][0] if self.axis_labels[1:2] else None),
                zaxis=dict(title=self.axis_labels[2:3][0] if self.axis_labels[2:3] else None)
            ),
            images=[dict(
                source='https://raw.githubusercontent.com/jMetal/jMetalPy/master/docs/source/jmetalpy.png',
                xref='paper', yref='paper',
                x=0, y=1.05,
                sizex=0.1, sizey=0.1,
                xanchor="left", yanchor="bottom"
            )]
        )

    @staticmethod
    def __generate_trace(objectives: DataFrame, legend: str = '', **kwargs):
        number_of_objectives = objectives.shape[1]

        marker = dict(
            color='rgb(127, 127, 127)',
            size=3,
            symbol='circle',
            line=dict(
                color='rgb(204, 204, 204)',
                width=1
            ),
            opacity=1.0
        )
        marker.update(**kwargs)

        if number_of_objectives == 2:
            trace = go.Scattergl(
                x=objectives[0],
                y=objectives[1],
                mode='markers',
                marker=marker,
                name=legend
            )
        elif number_of_objectives == 3:
            trace = go.Scatter3d(
                x=objectives[0],
                y=objectives[1],
                z=objectives[2],
                mode='markers',
                marker=marker,
                name=legend
            )
        else:
            dimensions = list()
            for column in objectives:
                dimensions.append(
                    dict(range=[0, 1],
                         label='O',
                         values=objectives[column])
                )

            trace = go.Parcoords(
                line=dict(color='blue'),
                dimensions=dimensions,
                name=legend
            )

        return trace
