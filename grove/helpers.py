"""helpers module.
Classes in this module are general classes that are used often by other classes in the project.
DON'T comment the default configuration file!
__uncomment__  a configuration file to use it.
"""
import os
import pickle as pickle

import numpy as np

# from configuration.icc_city_traffic import *
# from configuration.icc_sizing import *
# from configuration.icc_sizing_continue import *
# from configuration.config_one_year_sim import *
# from configuration.battery_analyze import *
# from configuration.config_milp import *
from configuration.debugging import *
from configuration.default import *

# from configuration.debugging_dgx2 import *
# from configuration.sim_debug import *
# from configuration.one_year_sim_sizing import *
# from configuration.one_year_sim_city_traffic import *

VERY_BIG_NEGATIVE_VALUE = -100000.0
NUMBER_OF_TIME_SLOT_IN_ONE_DAY = 24  # we use each hour as a time slot
CC_INDEX = N_OF_EC
N_OF_CLOUD = (N_OF_EC + 1)
NUMBER_OF_UE_PER_EC = 1  # Number of User Chunk in one EC
N_OF_URF = 3
N_OF_PACKET_TYPE = 2
REWARD_NORMALIZER = -1000000.0
OUTPUT_FOLDER = '../output/'



class PowerCons:
    TRY2DOLLAR = 8
    ELEC_PRICE = [x / 8 for x in [0.25] * 6 + [0.52] * 11 + [0.87] * 5 + [0.25] * 2]
    # ELEC_PRICE = [x / 8 for x in [0.71] * 24]
    P_EC_STA = 5
    P_EC_DYN = 1
    P_CC_STA = 10
    P_CC_DYN = 1
    USER_CHUNK_SIZE = 10000
    GOPS_VALUE_PER_URF = 0.033
    GOPS_2_WATT_CONVERTER = 8
    CENTRALIZATION_FACTOR = 0.9
    SOLAR_PANEL_BASE = SOLAR_PANEL_BASE_CONF
    BATTERY_BASE = BATTERY_BASE_CONF
    SOLAR_PANEL_INCR = SOLAR_PANEL_BASE
    BATTERY_INCR = BATTERY_BASE
    SOLAR_PANEL_INSTANCE_SIZE = SOLAR_PANEL_INSTANCE_SIZE_CONF
    BATTERY_INSTANCE_SIZE = BATTERY_INSTANCE_SIZE_CONF
    CC_SIZING_MULTIPLIER = CC_SIZING_MULTIPLIER_CONF

    @staticmethod
    def get_solar_panel_instances():
        return_val = []
        for sp_index in np.arange(0, PowerCons.SOLAR_PANEL_INSTANCE_SIZE, 1):
            sp = PowerCons.SOLAR_PANEL_BASE + sp_index * PowerCons.SOLAR_PANEL_INCR
            sp = round(sp, 3)
            return_val.append(sp)
        return return_val

    @staticmethod
    def get_battery_instances():
        return_val = []
        for batt_index in np.arange(0, PowerCons.BATTERY_INSTANCE_SIZE, 1):
            batt = PowerCons.BATTERY_BASE + batt_index * PowerCons.BATTERY_INCR
            return_val.append(batt)
        return return_val

    @staticmethod
    def get_solar_panel_and_battery_for_each_cloud():
        return_tuple = []
        one_conf_tuple = []
        for sp_index in np.arange(0, PowerCons.SOLAR_PANEL_INSTANCE_SIZE, 1):
            for batt_index in np.arange(0, PowerCons.BATTERY_INSTANCE_SIZE, 1):
                sp = PowerCons.SOLAR_PANEL_BASE + sp_index * PowerCons.SOLAR_PANEL_INCR
                sp = round(sp, 3)
                batt = PowerCons.BATTERY_BASE + batt_index * PowerCons.BATTERY_INCR
                for r in range(N_OF_EC):
                    one_conf_tuple.append((sp, batt))
                one_conf_tuple.append((sp * PowerCons.CC_SIZING_MULTIPLIER, batt * PowerCons.CC_SIZING_MULTIPLIER))
                return_tuple.append(one_conf_tuple)
                one_conf_tuple = []
                # for r in range(N_OF_EC):
                #     one_conf_tuple.append((0, 0))
                # one_conf_tuple.append((sp * N_OF_CLOUD, batt * N_OF_CLOUD))
                # return_tuple.append(one_conf_tuple)
                # one_conf_tuple = []
                # for r in range(N_OF_EC):
                #     one_conf_tuple.append((round(sp*(7/6.0), 2), round(batt*(7/6.0), 2)))
                # one_conf_tuple.append((0, 0))
                # return_tuple.append(one_conf_tuple)
                # one_conf_tuple = []
        return return_tuple


class PacketType:
    URLLC = 0
    EMBB = 1


class LearningParameters:
    NUMBER_OF_EPISODES = NUMBER_OF_EPISODES_CONF
    SHOW_EVERY = SHOW_EVERY_CONF
    LEARNING_RATE_BASE = 0.1
    DISCOUNT_BASE = 0.9
    LEARNING_RATE_INCR = 0.05
    DISCOUNT_INCR = 0.05
    EPSILON = 0.5
    EPSILON_DECAY_VALUE = EPSILON / int(0.9 * NUMBER_OF_EPISODES)

    @staticmethod
    def initial_epsilon():
        return LearningParameters.EPSILON

    @staticmethod
    def decrement_epsilon(epsilon):
        epsilon -= LearningParameters.EPSILON_DECAY_VALUE
        return epsilon

    @staticmethod
    def get_rate_and_discount():
        LEARNING_RATE_SIZE = LEARNING_RATE_SIZE_CONF
        DISCOUNT_SIZE = DISCOUNT_SIZE_CONF
        return_tuple = []
        for learning_rate_index in np.arange(0, LEARNING_RATE_SIZE):
            for discount_index in np.arange(0, DISCOUNT_SIZE):
                learning_rate = LearningParameters.LEARNING_RATE_BASE + learning_rate_index * LearningParameters.LEARNING_RATE_INCR
                learning_rate = round(learning_rate, 2)
                discount = LearningParameters.DISCOUNT_BASE + discount_index * LearningParameters.DISCOUNT_INCR
                discount = round(discount, 2)
                return_tuple.append((learning_rate, discount))
        return return_tuple


# traffic_scenarios = [1, 2, 3]

class Snapshot:
    def __init__(self):
        abs_path = os.path.abspath(__file__)
        if "code" in abs_path:
            parent_folder = '../../../'
        else:
            parent_folder = '../../../../../'

        self.results_folder_base = parent_folder + 'phd_data/simulation_results/traffic_scen_'
        self.prev_results_folder_base = parent_folder + 'phd_data/simulation_results/prev_data/traffic_scen_'
        self.results_folder = "../output/results/"
        self.traffic_scen_folder_base = "../input/given_data/"
        self.traffic_scen_folder = None
        self.solar_data_base = "../input/given_data/"
        self.solar_data_path = None

        self.other_folder = parent_folder + 'phd_data/simulation_results/other/'

    def set_solar_data_path(self, city_name):
        self.solar_data_path = self.solar_data_base + 'solar_energy/' + city_name + '.pkl'

    def set_traffic_data_path(self, ts):
        self.traffic_scen_folder = self.traffic_scen_folder_base + 'traffic_data_' + str(ts) + '/'

    def _save_pickle(self, c, path):
        with open(path, 'wb') as output:
            pickle.dump(c, output, pickle.HIGHEST_PROTOCOL)

    def _load_pickle(self, path):
        with open(path, 'rb') as input:
            c = pickle.load(input)
            return c

    def save_tr(self, c):
        path = self.traffic_scen_folder + 'tr.pkl'
        self._save_pickle(c, path)

    def load_tr(self):
        path = self.traffic_scen_folder + 'tr.pkl'
        tr = self._load_pickle(path)
        return tr

    # Solar Data Functions
    def save_solar_energy(self, c):
        self._save_pickle(c, self.solar_data_path)

    def load_solar_energy(self):
        return self._load_pickle(self.solar_data_path)

    # Rewards
    def save_rewards(self, c, conf_string):
        path = self.results_folder + "rewards_" + conf_string + ".pkl"
        self._save_pickle(c, path)

    def load_rewards(self, conf_string):
        name = self.results_folder + "rewards_" + conf_string + ".pkl"
        return self._load_pickle(name)

    def save_battery_history(self, c, conf_string):
        path = self.results_folder + 'bh' + conf_string + '.pkl'
        self._save_pickle(c, path)

    def load_battery_history(self, conf_string):
        path = self.results_folder + 'bh' + conf_string + '.pkl'
        return self._load_pickle(path)

    # QTables
    def save_qtables(self, c, conf_string):
        path = self.results_folder + "qtables_" + conf_string + ".pkl"
        self._save_pickle(c, path)

    def load_qtables(self, conf_string):
        name = self.results_folder + "qtables_" + conf_string + ".pkl"
        return self._load_pickle(name)

    # QTables
    def save_actions(self, c, conf_string):
        path = self.results_folder + "actions_" + conf_string + ".pkl"
        self._save_pickle(c, path)

    def load_actions(self, conf_string):
        name = self.results_folder + "actions_" + conf_string + ".pkl"
        return self._load_pickle(name)

class CloudType(object):
    center = 0
    edge = 1
