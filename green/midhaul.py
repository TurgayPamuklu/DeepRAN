"""Midhaul Module.
Creating Parent Class for Journal 3.

"""

from traffic import *


class Midhaul():
    def __init__(self, generic_object):
        self.g = generic_object
        print("Midhaul")

    # Creating Traffic Data
    def gurobi_create_data(self, number_of_day):
        # USER DEMANDS Avg. per Month
        for r in self.g.r_ec:
            traffic_per_rs = Traffic.get_a_random_traffic_pattern(self.g.n_of_time_slot, number_of_day)
            user_set_in_r = list(range(r * self.g.number_of_ue_per_ec, (r + 1) * self.g.number_of_ue_per_ec))
            for user in user_set_in_r:
                self.g.traffic_load[user] = traffic_per_rs
        delay_threshold_for_all_day = [[[0 for x in range(self.g.n_of_time_slot)] for x in range(number_of_day)] for x in range(self.g.number_of_ue)]
        for user in range(self.g.number_of_ue):
            for day in range(number_of_day):
                for time_slot in range(self.g.n_of_time_slot):
                    delay_threshold_for_all_day[user][day][time_slot] = np.random.randint(0, self.g.n_of_up_function + 1)
                    # delay_threshold_for_all_day[user][day][time_slot] = 1
        self.g.snapshot.save_tr_cran(self.g.traffic_load, delay_threshold_for_all_day)

    # Loading Traffic and Solar Energy
    def gurobi_load_data(self):
        self.g.traffic_load = [[1 for x in range(self.g.n_of_time_slot)] for x in range(self.g.number_of_ue)]  # redefinition need after create_data
        traffic_for_all_day, delay_threshold_for_all_day = self.g.snapshot.load_tr_cran()
        different_traffic_load_for_each_remote_site = True  # we do not use traffic_load_multiplier that we assigned in __init__
        if different_traffic_load_for_each_remote_site:
            traffic_load_multiplier_per_rs = [5, 3, 10, 1, 4, 5, 2, 9, 3, 6, 6, 3, 6, 1, 4, 2, 2, 7, 1, 4]
            for r in self.g.r_ec:
                user_set_in_r = list(range(r * self.g.number_of_ue_per_ec, (r + 1) * self.g.number_of_ue_per_ec))
                for user_index in user_set_in_r:
                    for time_slot in range(self.g.n_of_time_slot):
                        self.g.traffic_load[user_index][time_slot] = traffic_for_all_day[user_index][self.g.day][time_slot] * 0.1 * traffic_load_multiplier_per_rs[r]
                        self.g.delay_threshold[user_index][time_slot] = delay_threshold_for_all_day[user_index][self.g.day][time_slot]
        else:
            if "Static" in self.g.splitting_method:
                for user_index in range(len(traffic_for_all_day)):
                    self.g.traffic_load[user_index][0] = max(
                        traffic_for_all_day[user_index][self.g.day]) * 0.2 * self.g.traffic_load_multiplier
            else:
                for user_index in range(len(traffic_for_all_day)):
                    for time_slot in range(self.g.n_of_time_slot):
                        self.g.traffic_load[user_index][time_slot] = traffic_for_all_day[user_index][self.g.day][time_slot] * 0.1 * self.g.traffic_load_multiplier
                        self.g.delay_threshold[user_index][time_slot] = delay_threshold_for_all_day[user_index][self.g.day][time_slot]

        self.g.load_solar_energy()

    def calculate_the_obj_val(self, decision_a, decision_s, decision_p):
        self.g._calculate_the_obj_val(decision_a, decision_s, decision_p)
        calculated_obj = self.g._calculate_the_obj_val(decision_a, decision_s, decision_p)
        self.g.rw.log_data("Calculated Obj Val:{}\n", *(calculated_obj,))
        return calculated_obj
