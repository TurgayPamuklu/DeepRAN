"""Crosshaul Module.
Creating Parent Class for Grove Journal.

"""

from traffic import *


class Crosshaul():
    def __init__(self, generic_object):
        self.g = generic_object
        print("Crosshaul")

    # Creating Traffic Data
    def create_traffic(self):
        # USER DEMANDS Avg. per Month
        for k in self.g.r_ec:
            tr = Traffic.get_traffic_pattern_for_rfs(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)
            user_list_in_k = range(k * self.g.number_of_ue_per_ec, (k + 1) * self.g.number_of_ue_per_ec)
            for user in user_list_in_k:
                self.g.traffic_load[user] = tr

        delay_threshold_for_all_day = [[0 for x in range(self.g.n_of_time_slot)] for x in range(self.g.number_of_ue)]
        for user in range(self.g.number_of_ue):
            for time_slot in range(self.g.n_of_time_slot):
                # delay_threshold_for_all_day[user][time_slot] = np.random.randint(0, self.g.n_of_up_function + 1)
                delay_threshold_for_all_day[user][time_slot] = np.random.randint(self.g.n_of_up_function - 1, self.g.n_of_up_function + 1)
        self.g.snapshot.save_tr_cran(self.g.traffic_load, delay_threshold_for_all_day)

    # Loading Traffic and Solar Energy
    def load_data(self):
        # LOAD TRAFFIC
        self.g.traffic_load, self.g.delay_threshold = self.g.snapshot.load_tr_cran()
        self.g.traffic_load = [[x * self.g.traffic_load_multiplier for x in y] for y in self.g.traffic_load]
        # LOAD SOLAR ENERGY
        self.g.load_solar_energy()

    def calculate_the_obj_val(self, decision_a, decision_s, decision_p):
        calculated_obj = self.g._calculate_the_obj_val(decision_a, decision_s, decision_p)
        self.g.rw.log_data("Calculated Obj Val:{}\n", *(calculated_obj,))
        return calculated_obj
