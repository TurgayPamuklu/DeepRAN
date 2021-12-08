"""Input Module.
Obsolute functions that are used once in a while for Cplex

"""

__author__ = 'turgay.pamuklu'

from city import *
from operators import CityConfiguration
from output import *


class CplexOperator():
    city_configuration_list = None

    def __init__(self, number_of_time_slot, c, assigning, bs_deployed_and_active, renewable_usage_ratio):
        self.number_of_time_slot = number_of_time_slot
        self.c = c  # c is not added to the CityConfiguration because CityConfiguration is created for each time_slot_of_the_current_day
        # but city object is just one
        self.city_configuration_list = []
        self.total_renewable_usage_ratio = renewable_usage_ratio
        self.total_bs_deployed_and_active = bs_deployed_and_active
        for time_slice in range(number_of_time_slot):
            f = self.__create_cplex_time_slice(c, self.c.user_traffic[time_slice % 24], assigning[time_slice],
                                               bs_deployed_and_active[time_slice])
            self.city_configuration_list.append(f)

    def __create_cplex_time_slice(self, c, u_d, assigning, bs_deployed_and_active):
        f = CityConfiguration(c.bs_count, u_d)
        f.assigning = assigning
        f.bs_deployed_and_active = bs_deployed_and_active
        f.remaining_bs_capacity = f.calculate_remaining_bs_capacity(c)
        return f


class CplexOutputData():
    NUMBER_OF_TIME_SLOT = 48

    def __init__(self):
        self.cplex_results_path = CPLEX_PATH

    def __init__(self, folder_name):
        self.cplex_results_path = CPLEX_PATH + folder_name

    def get_cplex_operator(self):
        co = load_city_after_deployment()
        assigning = self.get_assigning_from_cplex_output_file()
        bs_deployed_and_active, renewable_usage_ratio = self.get_deployed_and_active_from_cplex_output_file(co.bs_count)
        return CplexOperator(self.NUMBER_OF_TIME_SLOT, co, assigning, bs_deployed_and_active, renewable_usage_ratio)



    def get_deployed_and_active_from_cplex_output_file(self, bs_count):
        SOLAR_AWAKE_FILE = 'solarAwake.out'
        bs_deployed_and_active = [[False for x in range(bs_count)] for x in
                                  range(self.NUMBER_OF_TIME_SLOT)]
        bs_ren_usage_ratio = [[0.0 for x in range(bs_count)] for x in
                              range(self.NUMBER_OF_TIME_SLOT)]
        f = open(self.cplex_results_path + SOLAR_AWAKE_FILE, 'r')
        lines = f.readlines()
        f.close()
        number_of_original_time_slice = None
        for l in lines:
            t, bs_no, state, renewable_usage_ratio = l.split(" ")
            t = int(t) - 1
            bs_no = int(bs_no) - 1
            state = int(state)
            if state == 1:
                state = True
            else:
                state = False
            bs_deployed_and_active[t][bs_no] = state
            bs_ren_usage_ratio[t][bs_no] = float(renewable_usage_ratio)
            number_of_original_time_slice = t
        if number_of_original_time_slice == self.NUMBER_OF_TIME_SLOT / 2 - 1:  # means 2 days system
            for i in range(self.NUMBER_OF_TIME_SLOT / 2):
                bs_deployed_and_active[self.NUMBER_OF_TIME_SLOT / 2 + i] = bs_deployed_and_active[i]
                bs_ren_usage_ratio[self.NUMBER_OF_TIME_SLOT / 2 + i] = bs_ren_usage_ratio[i]
        elif number_of_original_time_slice == self.NUMBER_OF_TIME_SLOT - 1:  # means one day system
            pass  # never mind
        else:
            raise Exception("Aiiie!!! Houston we have a problem!")
        return bs_deployed_and_active, bs_ren_usage_ratio


    def get_assigning_from_cplex_output_file(self):
        assigning = [[[0 for x in range(CityBeforeDeployment.GRID_COUNT_IN_ONE_EDGE)] for x in
                      range(CityBeforeDeployment.GRID_COUNT_IN_ONE_EDGE)] for x in
                     range(self.NUMBER_OF_TIME_SLOT)]
        ASSIGN_MAP_FILE = 'assignmap.out'
        f = open(self.cplex_results_path + ASSIGN_MAP_FILE, 'r')
        lines = f.readlines()
        f.close()
        for l in lines:
            t, j, i = l.split(" ")
            t = int(t) - 1
            j = int(j)
            i = int(i) - 1
            x, y = CoordinateConverter.get_xy_for_cplex(j)
            assigning[t][x][y] = i
        return assigning

