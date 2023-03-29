import numpy as np
from typing import Union


class CarTrailerDimension:
    l1 = 3.5
    l2 = 4
    l12 = 1
    car_length = 5
    car_width = 2
    trailer_length = 5.5
    trailer_width = 2
    triangle_length = 2


class CarTrailerSim:
    def __init__(self, v: float = 4, use_CT: bool = True, dt: float = 0.01) -> None:
        """
        The class with the model in it, which can be updated for every timestep.

        :param v: The constant speed of the car; forward defined as positive [m/s]
        :param use_CT: Whether to use the continuous time dynamics or the discretized system
        :param dt: The timestep to use in the continuous time dynamics
        """
        self.l1 = CarTrailerDimension.l1
        self.l2 = CarTrailerDimension.l2
        self.l12 = CarTrailerDimension.l12
        self.v = v
        # state = [x, y, psi, gamma]
        self.state = np.zeros(4)
        self.use_CT = use_CT
        self.dt = dt if use_CT else None
        # Constraints
        self.x_lower, self.x_upper = -np.inf, np.inf
        self.y_lower, self.y_upper = -np.inf, np.inf
        self.psi_lower, self.psi_upper = -np.inf, np.inf
        self.gamma_lower, self.gamma_upper = -np.pi / 4, np.pi / 4
        self.delta_lower, self.delta_upper = -np.pi / 4, np.pi / 4

    def reset(self, state: np.ndarray = np.zeros(4)) -> None:
        self.state = state

    def dynamics_discrete(self, state: np.ndarray, delta_f: float) -> np.ndarray:
        """
        Contains the system dynamics -> can be a non-linear model
        should be a DISCRETE TIME model.
        :param state: The current state of the system
        :param delta_f: The steering angle in RADIANS
        :return: None
        """
        raise NotImplementedError
        # new_state = state + delta_f
        # return new_state

    def dynamics_continuous(self, state: np.ndarray, delta_f: float) -> np.ndarray:
        """
        Contains the system dynamics -> can be a non-linear model
        should be a CONTINUOUS TIME model.
        :param state: The current state of the system
        :param delta_f: The steering angle in RADIANS
        :return: None
        """
        x, y, psi, gamma = state
        u = np.tan(delta_f)
        dx = self.v * np.cos(psi)
        dy = self.v * np.sin(psi)
        dpsi = self.v / self.l1 * u
        dgamma = (self.v / self.l1 + (self.v * self.l12) / (self.l1 * self.l2) * np.cos(
            gamma)) * u - self.v / self.l2 * np.sin(gamma)

        return np.array([dx, dy, dpsi, dgamma]) * self.dt + state

    def get_log(self, delta_f) -> dict[str, np.ndarray]:
        """
        Creates a log of the state, inputs and calculates the position and orientation of the trailer
        :param delta_f: The steering angle in radians
        :return: dict{'car': [x_car, y_car, psi_car, gamma], 'trailer': [x_tr, y_tr, psi_tr, gamma], 'inputs': [delta_f, v]}
        """
        psi_car = self.state[2]
        gamma = self.state[3]
        P_car = self.state[:2]
        P_towbar = P_car - np.array([np.cos(psi_car), np.sin(psi_car)]) * self.l12
        psi_tr = psi_car - gamma
        P_trailer = P_towbar - np.array([np.cos(psi_tr), np.sin(psi_tr)]) * self.l2

        log = dict()
        log['car'] = self.state
        log['trailer'] = np.hstack((P_trailer, psi_tr, gamma))
        log['inputs'] = np.array([delta_f, self.v])
        return log

    def step(self, delta_f) -> dict[str, np.ndarray]:
        """
        Updates the state with the input commands
        :param delta_f: The steering angle in RADIANS
        :return: The log data [state, inputs] = [x, y, psi, v, delta_f, v]
        """
        # TODO: Check input constraints on delta_f
        if self.use_CT:
            self.state = self.dynamics_continuous(self.state, delta_f)
        else:
            self.state = self.dynamics_discrete(self.state, delta_f)

        return self.get_log(delta_f)


class CarTrailerSimWithAcc:
    def __init__(self, use_CT: bool = True, dt: float = 0.01) -> None:
        """
        The class with the model in it, which can be updated for every timestep.

        :param use_CT: Whether to use the continuous time dynamics or the discretized system
        :param dt: The timestep to use in the continuous time dynamics
        """
        self.time = 0
        self.l1 = CarTrailerDimension.l1
        self.l2 = CarTrailerDimension.l2
        self.l12 = CarTrailerDimension.l12
        # state = [x, y, psi, gamma, v]
        self.state = np.zeros(5)
        self.use_CT = use_CT
        self.dt = dt if use_CT else None
        # Constraints --> Need to set some meaningful values
        self.x_lower, self.x_upper = -np.inf, np.inf  # m
        self.y_lower, self.y_upper = -np.inf, np.inf  # m
        self.psi_lower, self.psi_upper = -np.pi, np.pi  # rad
        self.gamma_lower, self.gamma_upper = -np.pi / 4, np.pi / 4  # rad
        self.v_lower, self.v_upper = -10, 10  # m/s
        self.delta_lower, self.delta_upper = -np.pi / 4, np.pi / 4  # rad
        self.acc_lower, self.acc_upper = -4, 3  # m/s^2

    def reset(self, state: Union[np.ndarray, list] = np.zeros(5)) -> None:
        assert np.array(state).shape == (5,), f"The state should have shape (5,), but has shape{np.array(state).shape}"
        self.state = state

    def dynamics_discrete(self, state: np.ndarray, control_input: Union[np.ndarray, list]) -> np.ndarray:
        """
        Contains the system dynamics -> can be a non-linear model
        should be a DISCRETE TIME model.
        :param state: The current state of the system
        :param control_input: A 1D array with to elements: [acceleration, steering angle]
        :return: None
        """
        raise NotImplementedError

    def dynamics_continuous(self, state: np.ndarray, control_input: Union[np.ndarray, list]) -> np.ndarray:
        """
        Contains the system dynamics -> can be a non-linear model
        should be a CONTINUOUS TIME model.
        :param state: The current state of the system
        :param control_input: A 1D array with to elements: [acceleration, steering angle]
        :return: None
        """
        assert np.array(control_input).shape == (2,),\
            f"The input should have shape (2,), but has shape{np.array(control_input).shape}"
        x, y, psi, gamma, v = state
        a, delta_f = control_input
        u = np.tan(delta_f)
        dx = v * np.cos(psi)
        dy = v * np.sin(psi)
        dpsi = v / self.l1 * u
        dgamma = (v / self.l1 + (v * self.l12) / (self.l1 * self.l2) * np.cos(
            gamma)) * u - v / self.l2 * np.sin(gamma)
        dv = a

        return np.array([dx, dy, dpsi, dgamma, dv]) * self.dt + state

    def get_log(self, control_input: Union[np.ndarray, list]) -> dict[str, np.ndarray]:
        """
        Creates a log of the state, inputs and calculates the position and orientation of the trailer
        :param control_input: A 1D array with to elements: [acceleration, steering angle]
        :return: dict{'car': [x_car, y_car, psi_car, gamma], 'trailer': [x_tr, y_tr, psi_tr, gamma], 'inputs': [delta_f, v]}
        """
        psi_car, gamma, v = self.state[2: 5]
        a, delta_f = control_input
        P_car = self.state[:2]
        P_towbar = P_car - np.array([np.cos(psi_car), np.sin(psi_car)]) * self.l12
        psi_tr = psi_car - gamma
        P_trailer = P_towbar - np.array([np.cos(psi_tr), np.sin(psi_tr)]) * self.l2

        log = dict()
        log['car'] = self.state
        log['trailer'] = np.hstack((P_trailer, psi_tr, gamma))
        log['inputs'] = np.array([a, delta_f])
        return log

    def step(self, control_input: Union[np.ndarray, list]) -> dict[str, np.ndarray]:
        """
        Updates the state with the input commands
        :param control_input: A 1D array with to elements: [acceleration, steering angle]
        :return: The log data [state, inputs] = [x, y, psi, v, delta_f, v]
        """
        # TODO: Check input constraints on delta_f and acceleration
        # TODO: Check constraints on state
        if self.use_CT:
            self.state = self.dynamics_continuous(self.state, control_input)
        else:
            self.state = self.dynamics_discrete(self.state, control_input)

        self.time += self.dt
        return self.get_log(control_input)
