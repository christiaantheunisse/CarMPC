import numpy as np
import itertools

from lib.mpc import MPCStateFB
from lib.simulator import CarSimulator, CarTrailerDimension
from lib.visualize_state import plot_live, plot_history, plot_graphs
from lib.environments import *
# Contains the all CAPS variables
from lib.configuration import *

# Set up the environment
environment = RoadMultipleCarsEnv()

# Set up the MPC controller
controller = MPCStateFB(dt=DT_CONTROL, N=N, lin_state=LINEARIZE_STATE, lin_input=LINEARIZE_INPUT,
                        terminal_constraint=True, input_constraint=True, state_constraint=True, env=environment)
controller.set_goal(environment.goal)
print(controller.P)
# Set up the simulation environment (uses the same non-linearized model with a smaller timestep
simulation = CarSimulator(dt=DT_SIMULATION)
start_position = [5, -1.5, 0.1, 0]
simulation.reset(np.array(start_position))

control_input = [0, 0]
max_gamma = 0
max_pred_gamma = 0
car_states, inputs, costs = [], [], []

for i in itertools.count():
    log = simulation.step(control_input)
    car_states.append(log['car'])
    inputs.append(log['inputs'])

    if i % STEPS_UPDATE == 0:
        control_input = controller.step(simulation.state)
        plot_live(log, dt=0.01, time=simulation.time, state_horizon=controller.x_horizon,
                  env=environment)

    if np.all(np.abs(simulation.state - controller.goal) <= 1e-1).astype(bool) or i > 30 / DT_SIMULATION:
        break
        # simulation.reset(np.array(start_position))

log_history = {'car': np.array(car_states), 'inputs': np.array(inputs)}
plot_history(log_history, dt=DT_SIMULATION, goal=controller.goal, env=environment)
plot_graphs(log_history, dt=DT_SIMULATION)
