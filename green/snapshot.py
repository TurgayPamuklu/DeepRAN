"""Snapshot Module.
Pickles for several record data.

"""

import glob
import os
import pickle as pickle

from constants import *

__author__ = 'turgay.pamuklu'


class Snapshot(object):
    # COMMON FUNCTIONS
    def __init__(self):
        abs_path = os.path.abspath(__file__)
        if "code" in abs_path:
            parent_folder = '../../../'
        else:
            parent_folder = '../../../../../'

        self.results_folder_base = parent_folder + 'phd_data/simulation_results/traffic_scen_'
        self.prev_results_folder_base = parent_folder + 'phd_data/simulation_results/prev_data/traffic_scen_'
        self.results_folder = None
        self.traffic_scen_folder_base = parent_folder + 'phd_data/snapshots/traffic_scen_'
        self.traffic_scen_folder = None
        self.solar_data_base = parent_folder + 'phd_data/snapshots/solar_data/'
        self.solar_data_path = None

        self.other_folder = parent_folder + 'phd_data/simulation_results/other/'

    def create_traffic_scen_folder(self):
        for traffic_scen in traffic_scenarios:
            for extra in range(10):
                self.traffic_scen_folder = self.traffic_scen_folder_base + str(traffic_scen) + '_' + str(extra) + '/'
                os.makedirs(self.traffic_scen_folder)

    def _create_results_folders(self, extension_type, with_index=True):
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                if with_index:
                    for traffic_index in range(10):
                        self.results_folder = self.results_folder_base + str(traffic_scen) + '_' + str(traffic_index) + '_' + city_name + extension_type + '/'
                        os.makedirs(self.results_folder)
                else:
                    self.results_folder = self.results_folder_base + str(traffic_scen) + '_' + city_name + extension_type + '/'
                    os.makedirs(self.results_folder)

    def create_results_folders(self):
        extension_type = ''
        self._create_results_folders(extension_type)

    def create_results_folders_for_same_panel_size_and_batteries(self):
        extension_type = '_same'
        self._create_results_folders(extension_type)

    def create_results_folders_for_random_panel_size_and_batteries(self):
        extension_type = '_random'
        self._create_results_folders(extension_type)

    def create_results_folders_for_gurobi(self):
        extension_type = '_base'
        self._create_results_folders(extension_type, True)

    def set_results_folder(self, traffic_scen, city_name, data_type, traffic_index=None):
        if data_type is "PREV_DATA":  # standard results
            self.results_folder = self.prev_results_folder_base + str(traffic_scen) + '_' + city_name + '/'
        elif data_type is "STANDARD":  # standard results
            if traffic_index is None:
                self.results_folder = self.results_folder_base + str(traffic_scen) + '_' + city_name + '/'
            else:
                self.results_folder = self.results_folder_base + str(traffic_scen) + '_' + str(traffic_index) + '_' + city_name + '/'
        elif data_type is "RANDOM":
            self.results_folder = self.results_folder_base + str(traffic_scen) + '_' + city_name + '_random' + '/'
        elif data_type is "BASE" or data_type is "GUROBI":
            if traffic_index is None:
                self.results_folder = self.results_folder_base + str(traffic_scen) + '_' + city_name + '_base' + '/'
            else:
                self.results_folder = self.results_folder_base + str(traffic_scen) + '_' + str(traffic_index) + '_' + city_name + '_base' + '/'

        elif data_type is "SAME_PANEL_SIZE":  # "SAME_PANEL_SIZE" same panel & battery size
            self.results_folder = self.results_folder_base + str(traffic_scen) + '_' + city_name + '_same' + '/'
        else:
            raise Exception("Aiee! set_results_folder {} type is not implemented!".format(data_type))

    def set_traffic_scen_folder(self, traffic_scen, traffic_index=None):
        if traffic_index is None:
            self.traffic_scen_folder = self.traffic_scen_folder_base + str(traffic_scen) + '/'
        else:
            self.traffic_scen_folder = self.traffic_scen_folder_base + str(traffic_scen) + '_' + str(traffic_index) + '/'

    def set_solar_data_path(self, city_name):
        self.solar_data_path = self.solar_data_base + 'solar_energy_' + city_name + '.pkl'

    def _save_pickle(self, c, path):
        with open(path, 'wb') as output:
            pickle.dump(c, output, pickle.HIGHEST_PROTOCOL)

    def _load_pickle(self, path):
        with open(path, 'rb') as input:
            c = pickle.load(input)
            return c

    def log_file_name(self, operational_method, iter_no=0):
        return '_' + operational_method + '_it_' + str(iter_no)

    # RESULTS RELATED FUNCTIONS
    def save_iteration_history(self, c, conf_string):
        path = self.results_folder + "iteration_history" + conf_string + ".pkl"
        self._save_pickle(c, path)

    def load_iteration_history(self, conf_string):
        name = self.results_folder + "iteration_history" + conf_string + ".pkl"
        return self._load_pickle(name)

    def load_iteration_history_of_same_size_solar_and_batteries(self, conf_string):
        NUMBER_OF_BATT = 12
        NUMBER_OF_PANEL = 8
        ih = []
        hist = self.load_iteration_history(conf_string)
        for i in range(0, NUMBER_OF_PANEL):
            ih.append(hist[i * NUMBER_OF_BATT:(i + 1) * NUMBER_OF_BATT])
        return ih

    def save_size_of_sp_and_batt(self, c, conf_string):
        path = self.results_folder + 'ssb' + conf_string + '.pkl'
        self._save_pickle(c, path)

    def load_size_of_sp_and_batt(self, conf_string):
        path = self.results_folder + 'ssb' + conf_string + '.pkl'
        return self._load_pickle(path)

    def save_battery_history(self, c, conf_string):
        path = self.results_folder + 'bh' + conf_string + '.pkl'
        self._save_pickle(c, path)

    def load_battery_history(self, conf_string):
        path = self.results_folder + 'bh' + conf_string + '.pkl'
        return self._load_pickle(path)

    def delete_battery_history(self, conf_string):
        path = self.results_folder + 'bh' + conf_string + '.pkl'
        os.remove(path)

    def delete_all_battery_history_in_a_folder(self):
        path = self.results_folder + "bh*"
        for filename in glob.glob(path):
            os.remove(filename)

    # TRAFFIC RELATED FUNCTIONS
    def load_nominal_service_rate(self):
        nsr_file_name = self.traffic_scen_folder + 'nsr.pkl'
        nsr = self._load_pickle(nsr_file_name)
        return nsr

    def save_nominal_service_rate(self, nsr):
        nsr_file_name = self.traffic_scen_folder + 'nsr.pkl'
        self._save_pickle(nsr, nsr_file_name)

    def save_city_after_deployment(self, co):
        path = self.traffic_scen_folder + 'city_operator.pkl'
        self._save_pickle(co, path)

    def load_city_after_deployment(self):
        path = self.traffic_scen_folder + 'city_operator.pkl'
        return self._load_pickle(path)

    def save_tr(self, c):
        path = self.traffic_scen_folder + 'tr.pkl'
        self._save_pickle(c, path)

    def load_tr(self):
        path = self.traffic_scen_folder + 'tr.pkl'
        return self._load_pickle(path)

    # Solar Data Functions
    def save_solar_energy(self, c):
        self._save_pickle(c, self.solar_data_path)

    def load_solar_energy(self):
        return self._load_pickle(self.solar_data_path)

    # Other Functions
    def save_method2_operator(self, method2_op, name):
        path = self.other_folder + 'method2_operator_' + name + '.pkl'
        self._save_pickle(method2_op, path)

    def load_method2_operator(self, name):
        path = self.other_folder + 'method2_operator_' + name + '.pkl'
        return self._load_pickle(path)

    def save_cplex_operator(self, cplex_op, name):
        path = self.other_folder + 'cplex_operator_' + name + '.pkl'
        self._save_pickle(cplex_op, path)

    def load_cplex_operator(self, name):
        path = self.other_folder + 'cplex_operator_' + name + '.pkl'
        return self._load_pickle(path)

    def save_fossil_operator(self, fo):
        path = self.other_folder + 'fossil_operator.pkl'
        self._save_pickle(fo, path)

    def load_fossil_operator(self):
        path = self.other_folder + 'fossil_operator.pkl'
        return self._load_pickle(path)

    def save_tr_cran(self, c, threshold):
        path = self.traffic_scen_folder + 'tr_cran.pkl'
        self._save_pickle(c, path)
        path = self.traffic_scen_folder + 'tr_treshold.pkl'
        self._save_pickle(threshold, path)

    def load_tr_cran(self):
        path = self.traffic_scen_folder + 'tr_cran.pkl'
        tr_cran = self._load_pickle(path)
        path = self.traffic_scen_folder + 'tr_treshold.pkl'
        tr_threshold = self._load_pickle(path)
        return tr_cran, tr_threshold

    def save_unassigned_bses(self, c):
        path = self.other_folder + 'unassigned_bses.pkl'
        self._save_pickle(c, path)

    def load_unassigned_bses(self):
        path = self.other_folder + 'unassigned_bses.pkl'
        return self._load_pickle(path)
