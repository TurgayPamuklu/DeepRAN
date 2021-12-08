"""Input Module.
Obsolute functions that are used once in a while for Cplex

"""
__author__ = 'turgay.pamuklu'

from copy import deepcopy

from constants import *
from input import CplexOutputData
from monitor import CplexPlotter
from monitor import MonitorAssignment
from operators import CityConfiguration
from output import Output

MAX_NUMBER_OF_SLOT_BY_REN_ENERGY_NON_RESTRICTED = 10
MAX_NUMBER_OF_SLOT_BY_REN_ENERGY_RESTRICTED = 5
NOON_TIME_SLOT = 14
METHOD2_TYPES = ['traffic_aware', 'full_day', 'half_day']


class Method2Operator():
    city_configuration_list = None
    active_count_of_bs = None
    type = None
    max_slot_by_ren = None

    def __init__(self, c, type):
        self.c = c  # c is not added to the CityConfiguration because CityConfiguration is created for each time slot
        # but city object is just one
        u_d_max_user_traffic_demand_for_each_hours = self.c.tr.get_max_user_traffic_demand_for_each_hours()
        self.active_count_of_bs = [0 for x in range(self.c.bs_count)]
        self.type = type
        if self.type == METHOD2_TYPES[2]:  # 'half_day':
            self.max_slot_by_ren = MAX_NUMBER_OF_SLOT_BY_REN_ENERGY_RESTRICTED
        else:
            self.max_slot_by_ren = MAX_NUMBER_OF_SLOT_BY_REN_ENERGY_NON_RESTRICTED
        self.city_configuration_list = []
        for day in range(NUMBER_OF_SIMULATION_DAY):
            for time_slot in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                # todo: we  have to modify nominal energy calculation for method 2
                utd_for_a_specific_time_slot = u_d_max_user_traffic_demand_for_each_hours[time_slot]  # this value is the maximum t_r
                # for each specific hours of a day
                f = self.__create_a_time_slot(c, utd_for_a_specific_time_slot)
                self.city_configuration_list.append(f)

    def __create_a_time_slot(self, c, utd_for_a_specific_time_slot):
        f = CityConfiguration(c.bs_count, -1)
        f.assigning = deepcopy(c.assigning)
        f.remaining_bs_capacity = f.calculate_remaining_bs_capacity(c)
        return f

    def get_number_of_bs_active(self):
        active_bs = [0 for x in range(len(self.active_count_of_bs))]
        if self.type == METHOD2_TYPES[2]:  # 'RESTRICTED':
            self.calculate_active_count_of_bses_by_start_and_end(0, NOON_TIME_SLOT, 0)
            for i in range(len(self.active_count_of_bs)):
                active_bs[i] = self.active_count_of_bs[i]
            self.calculate_active_count_of_bses_by_start_and_end(NOON_TIME_SLOT, 23, 0)
            for i in range(len(self.active_count_of_bs)):
                active_bs[i] += self.active_count_of_bs[i]
        else:
            self.calculate_active_count_of_bses(0)
            for i in range(len(self.active_count_of_bs)):
                active_bs[i] = self.active_count_of_bs[i]
        return active_bs

    def get_number_of_bs_consume_fossil_energy(self):
        consumed_fossil_energy = [0 for x in range(len(self.active_count_of_bs))]
        if self.type == METHOD2_TYPES[2]:  # 'RESTRICTED':
            self.calculate_active_count_of_bses_by_start_and_end(0, NOON_TIME_SLOT, 0)
            for i in range(len(self.active_count_of_bs)):
                consumed_fossil_energy[i] = max(self.active_count_of_bs[i] - self.max_slot_by_ren, 0)
            self.calculate_active_count_of_bses_by_start_and_end(NOON_TIME_SLOT, 23, 0)
            for i in range(len(self.active_count_of_bs)):
                consumed_fossil_energy[i] += max(self.active_count_of_bs[i] - self.max_slot_by_ren, 0)
        else:
            self.calculate_active_count_of_bses(0)
            for i in range(len(self.active_count_of_bs)):
                consumed_fossil_energy[i] = max(self.active_count_of_bs[i] - self.max_slot_by_ren, 0)
        return consumed_fossil_energy

    def calculate_active_count_of_bses_by_start_and_end(self, start, end, not_started_operations_len):
        for i in range(len(self.active_count_of_bs)):
            self.active_count_of_bs[i] = 0
        for i in range(start, end):
            conf = self.city_configuration_list[i]
            for bs_index in conf.bs_deployed_and_active:
                self.active_count_of_bs[bs_index] += 1

        for i in range(len(self.active_count_of_bs)):
            self.active_count_of_bs[i] -= not_started_operations_len

    def calculate_active_count_of_bses(self, not_started_operations_len):
        self.calculate_active_count_of_bses_by_start_and_end(0, 23, not_started_operations_len)

    def __get_fossil_and_ren_groups_for_non_restricted_method(self, time_of_the_day):
        fossil_group = []
        ren_group = []
        not_started_operations_len = len(self.city_configuration_list) - time_of_the_day
        # in the beginning we assume all bses are active so we need to subtract operations that not started yet
        self.calculate_active_count_of_bses(not_started_operations_len)

        for bs_index in range(self.c.bs_count):
            if self.active_count_of_bs[bs_index] > self.max_slot_by_ren:
                fossil_group.append(bs_index)
            else:
                ren_group.append(bs_index)
        return fossil_group, ren_group

    def __get_fossil_and_ren_groups_for_restricted_method(self, number_of_operation):
        fossil_group = []
        ren_group = []
        if number_of_operation < NOON_TIME_SLOT:
            not_started_operations_len = NOON_TIME_SLOT - number_of_operation
            self.calculate_active_count_of_bses_by_start_and_end(0, NOON_TIME_SLOT, not_started_operations_len)
        else:
            not_started_operations_len = 23 - number_of_operation
            self.calculate_active_count_of_bses_by_start_and_end(NOON_TIME_SLOT, 23, not_started_operations_len)

        for bs_index in range(self.c.bs_count):
            if self.active_count_of_bs[bs_index] > self.max_slot_by_ren:
                fossil_group.append(bs_index)
            else:
                ren_group.append(bs_index)
        return fossil_group, ren_group

    def __get_fossil_and_ren_groups_trivial(self):  # always return the same
        fossil_group = []
        ren_group = list(range(0, self.c.bs_count))
        return fossil_group, ren_group

    def get_fossil_and_ren_groups(self, conf_no):
        if self.type == METHOD2_TYPES[2]:  # 'RESTRICTED':
            fossil_group, ren_group = self.__get_fossil_and_ren_groups_for_restricted_method(conf_no)
        elif self.type == METHOD2_TYPES[1]:  # 'NON_RESTRICTED':
            fossil_group, ren_group = self.__get_fossil_and_ren_groups_for_non_restricted_method(conf_no)
        else:  # trivial
            fossil_group, ren_group = self.__get_fossil_and_ren_groups_trivial()
        return fossil_group, ren_group


def cplex_solutions_2_cplex_operator():
    for conf in CPLEX_CONF:
        cod = CplexOutputData(conf + '/')
        cp_op = cod.get_cplex_operator()
        save_cplex_operator(cp_op, conf)


def cplex_output_results():
    cr = range(len(CPLEX_CONF))
    tr = range(48)
    ren = [[0.0 for x in tr] for x in cr]
    awake = [[0 for x in tr] for x in cr]
    for c in cr:
        cp_op = load_cplex_operator(CPLEX_CONF[c])
        for t in tr:  # for each time slice
            ren[c][t] = sum(cp_op.total_renewable_usage_ratio[t]) / 0.37
            awake[c][t] = len(cp_op.total_bs_deployed_and_active[t])
    cp = CplexPlotter()
    # cp.plot_awake_vs_hour(awake, CPLEX_CONF_STR)
    cp.plot_ren_vs_hour(ren, CPLEX_CONF_STR)
    cp.show()
    print(ren)


def cplex_output_show_assignment():
    co = load_city_after_deployment()
    cod = CplexOutputData()
    cp_op = cod.get_cplex_operator()
    m = MonitorAssignment()
    m.show_assignment_all(cp_op, co)
    m.show()


# ----------- METHOD 2 -----------------------------------------------------------

def show_method2():
    m2_op_trivial = load_method2_operator(METHOD2_TYPES[0])
    m2_op_non_restricted = load_method2_operator(METHOD2_TYPES[1])
    m2_op_restricted = load_method2_operator(METHOD2_TYPES[2])

    '''
    fossil_dist_non_restricted = m2_op_non_restricted.get_number_of_bs_consume_fossil_energy()
    fossil_dist_restricted = m2_op_restricted.get_number_of_bs_consume_fossil_energy()
    fossil_dist_trivial = m2_op_trivial.get_number_of_bs_consume_fossil_energy()
    '''
    non_restricted = m2_op_non_restricted.get_number_of_bs_active()
    restricted = m2_op_restricted.get_number_of_bs_active()
    trivial = m2_op_trivial.get_number_of_bs_active()

    cp = CplexPlotter()
    data = []
    data_labels = []
    trivial = trivial[:len(trivial) / 2:]
    data.append(trivial)
    data_labels.append('Traffic Aware')
    non_restricted = non_restricted[:len(non_restricted) / 2:]
    data.append(non_restricted)
    data_labels.append('Normal Heur.')
    restricted = restricted[:len(restricted) / 2:]
    data.append(restricted)
    data_labels.append('Restricted Heur.')
    cp.plot_fossil_vs_bses(data, data_labels)
    cp.show()

    print(sum(m2_op_non_restricted.get_number_of_bs_consume_fossil_energy()))
    print(sum(m2_op_restricted.get_number_of_bs_consume_fossil_energy()))
    print(sum(m2_op_trivial.get_number_of_bs_consume_fossil_energy()))


def run_method2(restriction_type):
    co = load_city_after_deployment()
    method2_operator = Method2Operator(co, restriction_type)
    number_of_configuration = len(method2_operator.city_configuration_list)  # in other name it is number of time slots
    macro_bses, micro_bses = co.get_macro_micro_list()
    # todo: we should not use ordered time slots with restricted method!!!
    # ordered_time_slots_for_number_of_awake_bs = get_order_of_time_slots(co)
    # conf_no = ordered_time_slots_for_number_of_awake_bs[i]

    for i in range(number_of_configuration):
        fossil_group, ren_group = method2_operator.get_fossil_and_ren_groups(i)
        for j in range(4):
            if j == 0:
                tabu_list = ren_group + macro_bses  # Switch Off Micro Fossil Group:: Macro and Ren are in Tabu List
            elif j == 1:
                tabu_list = ren_group + micro_bses  # Switch Off Macro Fossil Group:: Micro and Ren are in Tabu List
            elif j == 2:
                tabu_list = fossil_group + macro_bses  # Switch Off Micro Ren Group:: Macro and Fossil are in Tabu List
            else:
                tabu_list = fossil_group + micro_bses  # Switch Off Macro Ren Group:: Micro and Fossil are in Tabu List
            while True:
                ind = method2_operator.city_configuration_list[i].get_least_effective_bs(
                    tabu_list)  # ren_group is tabu_list
                if ind == -1:
                    break
                method2_operator.city_configuration_list[i].remove_least_effective_bs(ind, method2_operator.c.can_bs_list)

    save_method2_operator(method2_operator, restriction_type)


def cplex_related_operations():
    Output.out_cplex()
    # cplex_output_show_assignment()
    # cplex_solutions_2_cplex_operator()
    # cplex_output_results()