import random
from collections import deque

import numpy as np
from keras import backend as K
from keras.layers import Dense
from keras.models import Sequential
from tensorflow.keras.optimizers import Adam

from helpers import *


class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99
        self.learning_rate = 0.001

        # model network-->>action=NN.predict(state)
        self.model = self._build_model()

        # target network -->>target=NN.predict(state)
        self.target_model = self._build_model()

        self.update_target_model()

    def _huber_loss(self, target, prediction):
        # sqrt(1+error^2)-1
        error = prediction - target
        return K.mean(K.sqrt(1 + K.square(error)) - 1, axis=-1)

    def _build_model(self):

        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss=self._huber_loss,
                      optimizer=Adam(lr=self.learning_rate))
        return model

    def update_target_model(self):
        # copy weights from model to target_model
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):

        # select random action with prob=epsilon else action=maxQ
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])  # returns action

    def replay(self, batch_size):

        # sample random transitions
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:

            # calculate target for each minibatch
            target = self.model.predict(state)

            if done:
                target[0][action] = reward
            else:
                # action from model network
                a = self.model.predict(next_state)[0]
                # target from target network
                t = self.target_model.predict(next_state)[0]
                target[0][action] = reward + self.gamma * t[np.argmax(a)]  # belmann

            # train model network
            self.model.fit(state, target, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)

    def get_discrete_state(self, remaining_energy, traffic_load, time_slot):
        s = remaining_energy + traffic_load + [time_slot]
        state = np.array(s)
        # self.diagnose_state_distribution(sch_delay)
        return state


class States:
    remaining_energy_level = None
    time_slot = None
    traffic_load = None
    ELEC_PRICE_STATE = False  # not implemented with traffic_load!!
    print("ELEC_PRICE_STATE:{}".format(ELEC_PRICE_STATE))

    def __init__(self, batt):
        # print("--Init: States Class--")
        self.QUANTIZATION_REM_EN = 2 # 0.2
        self.QUANTIZATION_TR_LOAD = 0 # 5
        self.batt = batt
        self.remaining_energy_level = np.array([x * self.QUANTIZATION_REM_EN for x in range(1)]) * self.batt
        # self.remaining_energy_level = np.array([x * self.QUANTIZATION_REM_EN for x in range(6)]) * self.batt
        self.time_slot = np.array([x for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)])
        # self.traffic_load = np.array([x for x in range(6)])
        self.traffic_load = np.array([x for x in range(1)])
        if self.ELEC_PRICE_STATE:
            self.elec_price = np.array([x for x in range(3)])
            self.size = self.time_slot.size * self.remaining_energy_level.size * self.elec_price.size
        else:
            self.size = self.time_slot.size * self.remaining_energy_level.size * self.traffic_load.size
        pass

    def get_discrete_state_elec_price(self, time_slot):
        price = PowerCons.ELEC_PRICE[time_slot]
        if price == 0.29:
            return 0
        elif price == 0.46:
            return 1
        elif price == 0.70:
            return 2
        else:
            print("Aieee!! Houston we have a problem!")
            exit(0)

    def get_remaining_en_level_list(self):
        return self.remaining_energy_level

    def get_state_shape(self):
        if self.ELEC_PRICE_STATE:
            return self.remaining_energy_level.size, self.time_slot.size, self.elec_price
        else:
            return self.remaining_energy_level.size, self.time_slot.size, self.traffic_load.size

    def get_combined_state(self, rem_en, ts, traffic_load, elec_price=0):
        if self.ELEC_PRICE_STATE:
            return rem_en * self.time_slot.size * self.elec_price.size + ts * self.elec_price.size + elec_price
        else:
            return rem_en * self.time_slot.size * self.traffic_load.size + ts * self.traffic_load.size + traffic_load


class StatesEC(States):
    def __init__(self, batt):
        # print("--Init: StatesEC Class--")
        States.__init__(self, batt)
        pass


class StatesCC(States):
    def __init__(self, batt):
        # print("--Init: StatesCC Class--")
        States.__init__(self, batt)
        pass


class Actions:
    if DEBUGGING_ALLOW:
        ACTION_REN_EN_RATIO_LIST = [0, 0.5, 1]
        # ACTION_REN_EN_RATIO_LIST = [1]
        # ACTION_REN_EN_RATIO_LIST = [x * 0.1 for x in range(11)]
        # ACTION_REN_EN_RATIO_LIST = [1]
        # ACTION_REN_EN_RATIO_LIST = [0, 0.25, 0.50, 0.75, 1]
    else:
        ACTION_REN_EN_RATIO_LIST = [0, 0.5, 1]
    renewable_energy_ratio = None

    def __init__(self, learning_method):
        if learning_method in method_list_static:
            self.renewable_energy_ratio = np.array([1.0])
        else:
            self.renewable_energy_ratio = np.array([1.0])  # fixme
            # if DEBUGGING_ALLOW:
            #     self.renewable_energy_ratio = np.array([1.0])
            # else:
            #     self.renewable_energy_ratio = np.array(self.ACTION_REN_EN_RATIO_LIST)

    def get_renewable_energy_ratio(self, action):
        return self.renewable_energy_ratio[action % len(self.renewable_energy_ratio)]


class ActionsEC(Actions):
    number_of_urf_usage = None
    if DEBUGGING_ALLOW:
        ACTION_NUMBER_OF_URF_LIST = [1]
    else:
        ACTION_NUMBER_OF_URF_LIST = [0, 1, 2, 3]
        # ACTION_NUMBER_OF_URF_LIST = [0, 1]

    def __init__(self, learning_method):
        # print("--Init: ActionsEC Class--")
        Actions.__init__(self, learning_method)
        if learning_method == "CRAN":
            a = np.array([0])
        elif learning_method == "URF1":
            a = np.array([1])
        elif learning_method == "URF2":
            a = np.array([2])
        elif learning_method == "DRAN":
            a = np.array([3])
        else:
            a = np.array(self.ACTION_NUMBER_OF_URF_LIST)
        self.number_of_urf_usage = a
        self.size = self.renewable_energy_ratio.size * self.number_of_urf_usage.size
        pass

    def get_action_shape(self):
        return self.number_of_urf_usage.size, self.renewable_energy_ratio.size

    def get_number_of_active_urf(self, action):
        return self.number_of_urf_usage[int(np.floor(action / self.renewable_energy_ratio.size))]

    def get_action_index(self, urf_index, renewable_energy_ratio):
        return urf_index * self.renewable_energy_ratio.size + renewable_energy_ratio


class ActionsCC(Actions):
    def __init__(self, learning_method):
        # print("--Init: ActionsCC Class--")
        Actions.__init__(self, learning_method)
        self.size = self.renewable_energy_ratio.size
        pass

    def get_action_shape(self):
        return self.renewable_energy_ratio.size

    def get_action_index(self, renewable_energy_ratio):
        return renewable_energy_ratio


class Cloud:
    def __init__(self):
        # print("--Init: Cloud Class--")
        self.q_table = None

    # @PerformanceCalculator
    def get_discrete_state(self, remaining_energy, time_slot, traffic_load):
        # combined_state = self.states.get_combined_state(rem_level, time_slot, elec_price)
        # print("Input:\n", remen_ratio, traffic_load, time_slot)
        rem_level = int(np.rint(remaining_energy / (self.states.QUANTIZATION_REM_EN * self.states.batt)))
        tl_level = int(np.rint(traffic_load * self.states.QUANTIZATION_TR_LOAD))
        if tl_level > 5:
            tl_level = 5
        combined_state = self.states.get_combined_state(rem_level, time_slot, tl_level)
        # print("Output:\n", rem_level, tl_level, combined_state)
        return combined_state


class CloudCC(Cloud):
    def __init__(self, batt, learning_method):
        Cloud.__init__(self)
        self.actions = ActionsCC(learning_method)
        self.states = StatesCC(batt)
        # self.q_table = np.random.uniform(low=-2000.0, high=-1500.0, size=(self.states.size, self.actions.size))
        self.q_table = np.array([[-1.0 for x in range(self.actions.size)] for x in range(self.states.size)])
        act_no = self.actions.get_action_index(self.actions.renewable_energy_ratio.size - 1)
        for state_index in range(self.states.size):
            self.q_table[state_index][act_no] = -0.01
        pass

    # @PerformanceCalculator
    def disaggr_action(self, action):
        # number_of_active_urf = self.actions.get_number_of_active_urf(action)
        renewable_energy_ratio = self.actions.get_renewable_energy_ratio(action)
        return renewable_energy_ratio, None


class CloudEC(Cloud):
    def __init__(self, batt, learning_method):
        Cloud.__init__(self)
        self.actions = ActionsEC(learning_method)
        self.states = StatesEC(batt)
        WEIGHTED_Q_TABLE_INIT = False
        # self.q_table = np.random.uniform(low=-2000.0, high=-1500.0, size=(self.states.size, self.actions.size))
        self.q_table = np.array([[-10.0 for x in range(self.actions.size)] for x in range(self.states.size)])
        if WEIGHTED_Q_TABLE_INIT:
            for ren_cons_index in range(self.actions.renewable_energy_ratio.size):
                for urf_index in range(self.actions.number_of_urf_usage.size):
                    if ren_cons_index == self.actions.renewable_energy_ratio.size - 1:
                        promoting_reward = 0.99
                    else:
                        promoting_reward = 0.2
                    if urf_index == 2 or urf_index == 3:
                        promoting_reward = promoting_reward * 0.8
                    if urf_index == 1:
                        promoting_reward = promoting_reward * 0.9
                    if urf_index == 0:
                        promoting_reward = promoting_reward * 1

                    act_no = self.actions.get_action_index(urf_index, ren_cons_index)
                    for state_index in range(self.states.size):
                        self.q_table[state_index][act_no] += promoting_reward
        pass

    # @PerformanceCalculator
    def disaggr_action(self, action):
        number_of_active_urf = self.actions.get_number_of_active_urf(action)
        renewable_energy_ratio = self.actions.get_renewable_energy_ratio(action)
        return renewable_energy_ratio, number_of_active_urf
