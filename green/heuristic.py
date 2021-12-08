"""Heuristic Module.
Heuristics for Journal 1

"""
__author__ = 'turgay.pamuklu'

import numpy as np

from helpers import CoordinateConverter
from renewableEnergy import Battery
from snapshot import *


class BI(object):
    # ITERATION HISTORY
    HIST_TOTAL = 0
    HIST_CAPITAL = 1
    HIST_OPERATIONAL = 2
    # BATTERY INFO
    PANEL_SIZE = 0
    BATTERY_SIZE = 1
    # BATTERY LIFECYCLE COLUMN DATA
    BS_INDEX = 0
    AWAKE_RATIO = 1
    FOSSIL_CONS = 2
    RENEWABLE_CONS = 3
    WASTED_ENERGY = 4
    REMAINING_ENERGY = 5
    RENEWABLE_RATIO = 6
    REMAINING_ENERGY_WBO = 7
    SOLAR_POT = 8
    BAT_POT = 9
    SOLAR_POT_R = 10
    BAT_POT_R = 11
    REMAINING_ENERGY_WBO_R = 12
    LIFECYCYLE_FIELD_SIZE = (REMAINING_ENERGY_WBO_R + 1)
    # TABU INFO
    # BS_INDEX = 0 it is same with lifcycle column data
    TABU_INITIAL_VAL = 1


class E(object):
    # year of deployment is 2019
    # year of deployment is 2019
    BATTERY_COST_OF_2500KW_SIZE = 500  # price in  2020: 500  # (only one li-ion batt) ref: mendeley
    SOLAR_PANEL_COST_OF_1KW_SIZE = 1000  # price in 2020: 1000  # ref: mendeley
    YEARS_OF_LIFE_CYCLE = 15  # 20
    ELECTRICITY_COST_KW_PER_HOUR = 0.16  # price in 2015: 0.1  # %4 per year 0.12 in 2019 # average between 2019-2039
    NUMBER_OF_DAYS_IN_A_YEAR = 365
    SIM_TIME_IN_ONE_YEAR = NUMBER_OF_DAYS_IN_A_YEAR / float(NUMBER_OF_SIMULATION_DAY)
    LIFE_TIME_ENERGY_COST = ELECTRICITY_COST_KW_PER_HOUR * SIM_TIME_IN_ONE_YEAR * YEARS_OF_LIFE_CYCLE * 0.001
    MAX_PANEL_SIZE = 8
    MAX_BATTERY_SIZE = 12
    CARBON_RATE = 0.703  # tonne

    THRESHOLD_CALIBRATION_FOR_IP = 1
    THRESHOLD_CALIBRATION_FOR_DP = 1
    THRESHOLD_CALIBRATION_FOR_IB = 1
    THRESHOLD_CALIBRATION_FOR_DB = 1


class OptimizationForCapitalExpenditure():
    bs_lifecycle_data = None
    size_of_sp_and_batt = None
    INCREMENTING_PANEL_SIZE = 1
    CHOOSE_START_VAL = 100  # 5
    COOLING_FACTOR = 4
    iteration_no = None
    lowest_total_expenditure = 1e16
    tabu_for_bat_dec = []
    tabu_for_sol_dec = []
    tabu_for_sol_inc = []
    TABU_TIMEOUT_VALUE = 4
    iteration_history = []
    NEW_PANEL_SELECTION_METHOD = False
    RANDOM_SELECT_HEURISTIC = False
    MANUAL_SELECT_HEURISTIC = False
    EACH_POTENTIAL = True
    STANDARD_METHOD = True

    def __init__(self, operational_method, city, iteration_no=0):
        self.iteration_no = iteration_no
        self.city = city
        self.iteration_history = []
        self.clean_tabu_lists()
        self.operational_method = operational_method
        pass

    def get_iteration_no(self):
        return self.iteration_no

    def clean_tabu_lists(self):
        self.tabu_for_bat_dec = []
        self.tabu_for_sol_dec = []
        self.tabu_for_sol_inc = []

    def update_battery_info(self):
        snapshot = Snapshot()
        bh = snapshot.load_battery_history(snapshot.log_file_name(self.operational_method, self.iteration_no))
        bh_previous = None
        if self.iteration_no != 0:
            bh_previous = snapshot.load_battery_history(snapshot.log_file_name(self.operational_method, self.iteration_no - 1))
        self.size_of_sp_and_batt = snapshot.load_size_of_sp_and_batt(snapshot.log_file_name(self.operational_method, self.iteration_no))
        self.bs_lifecycle_data = self.sum_values_of_each_time_slots(bh, bh_previous)

        self.__update_tabu_list(self.tabu_for_bat_dec)
        self.__update_tabu_list(self.tabu_for_sol_dec)
        self.__update_tabu_list(self.tabu_for_sol_inc)
        # print "-- update_battery_info next iteration number is: {}".format(self.iteration_no)

    def increase_iteration_no(self):
        self.iteration_no += 1

    def return_backward(self):
        snapshot = Snapshot()
        self.clean_tabu_lists()
        backward_iteration_no = self.iteration_no - 3
        bh = snapshot.load_battery_history(snapshot.log_file_name(self.operational_method, backward_iteration_no))
        ssb = snapshot.load_size_of_sp_and_batt(snapshot.log_file_name(self.operational_method, backward_iteration_no))
        self.increase_iteration_no()
        snapshot.save_battery_history(bh, snapshot.log_file_name(self.operational_method, self.iteration_no))
        snapshot.save_size_of_sp_and_batt(ssb, snapshot.log_file_name(self.operational_method, self.iteration_no))
        self.update_battery_info()
        lowest_total_expenditure, current_total_expenditure, previous_total_expenditure = self.calculating_total_expenditure()
        print("RETURN BACKWARD:: it:{} :: current te:{} / previous te:{}".format(self.iteration_no, current_total_expenditure,
                                                                                 previous_total_expenditure))

    def __update_tabu_list(self, tabu_list):
        for x in tabu_list[:]:
            if self.iteration_no - x[BI.TABU_INITIAL_VAL] > self.TABU_TIMEOUT_VALUE:
                tabu_list.remove(x)

    def __is_in_tabu_list(self, tabu_list, bs_index):
        for x in tabu_list:
            if x[BI.BS_INDEX] == bs_index:
                return True
        return False

    def dump_panel_size_and_battery_size_map(self):
        for i in range(len(self.size_of_sp_and_batt)):
            bs = self.size_of_sp_and_batt[i]
            print("{}:: panel_size:{} battery_size:{}".format(i, bs[BI.PANEL_SIZE], bs[BI.BATTERY_SIZE]))

    def dump_life_cycle_data_per_bs_types(self):
        snapshot = Snapshot()
        co = snapshot.load_city_after_deployment()
        macro_list, micro_list = co.get_macro_micro_list()
        n_of_macro = len(macro_list)
        n_of_micro = len(micro_list)

        macro_awake_ratio = 0
        macro_fos_consumption = 0
        macro_ren_consumption = 0
        for i in macro_list:
            macro_awake_ratio += self.bs_lifecycle_data[i][BI.AWAKE_RATIO]
            macro_fos_consumption += self.bs_lifecycle_data[i][BI.FOSSIL_CONS]
            macro_ren_consumption += self.bs_lifecycle_data[i][BI.RENEWABLE_CONS]
        macro_awake_ratio /= n_of_macro

        micro_awake_ratio = 0
        micro_fos_consumption = 0
        micro_ren_consumption = 0
        for i in micro_list:
            micro_awake_ratio += self.bs_lifecycle_data[i][BI.AWAKE_RATIO]
            micro_fos_consumption += self.bs_lifecycle_data[i][BI.FOSSIL_CONS]
            micro_ren_consumption += self.bs_lifecycle_data[i][BI.RENEWABLE_CONS]
        micro_awake_ratio /= n_of_micro

        print("# of MACRO BS:{} # of MICRO BS:{}".format(n_of_macro, n_of_micro))
        print("# of macro_awake_ratio:{} # of micro_awake_ratio:{}".format(macro_awake_ratio, micro_awake_ratio))
        print("# of macro_fos_cons:{} # of micro_fos_cons:{}".format(macro_fos_consumption, micro_fos_consumption))
        print("# of macro_ren_cons:{} # of micro_ren_cons:{}".format(macro_ren_consumption, micro_ren_consumption))

    def calculating_total_expenditure(self, diagnosing=None):
        snapshot = Snapshot()
        fossil_cons_of_the_system = 0
        for bs in self.bs_lifecycle_data:
            fossil_cons_of_the_system += bs[BI.FOSSIL_CONS]
        operational_expenditure = fossil_cons_of_the_system * E.LIFE_TIME_ENERGY_COST
        battery_size_of_the_system = 0
        panel_size_of_the_system = 0
        for bs in self.size_of_sp_and_batt:
            battery_size_of_the_system += bs[BI.BATTERY_SIZE]
            panel_size_of_the_system += bs[BI.PANEL_SIZE]
        battery_size_of_the_system /= Battery.INCREMENTING_BATTERY_SIZE
        panel_size_of_the_system /= self.INCREMENTING_PANEL_SIZE
        capital_expenditure = battery_size_of_the_system * E.BATTERY_COST_OF_2500KW_SIZE + panel_size_of_the_system * E.SOLAR_PANEL_COST_OF_1KW_SIZE
        total_expenditure = capital_expenditure + operational_expenditure
        print("PANEL_SIZE:{} BATTERY_SIZE:{}".format(panel_size_of_the_system, battery_size_of_the_system))
        print("TOT:{} CAP:{} OP:{}".format(total_expenditure, capital_expenditure, operational_expenditure))
        if not diagnosing:
            if len(self.iteration_history) == 0:
                previous_expenditure = INFINITELY_BIG
            else:
                previous_expenditure = self.iteration_history[-1][BI.HIST_TOTAL]
            self.iteration_history.append((total_expenditure, capital_expenditure, operational_expenditure))
            snapshot.save_iteration_history(self.iteration_history, snapshot.log_file_name(self.operational_method))
            if total_expenditure < self.lowest_total_expenditure:
                self.lowest_total_expenditure = total_expenditure

            return self.lowest_total_expenditure, total_expenditure, previous_expenditure

    def random_panel_and_battery_sizes(self):
        self.size_of_sp_and_batt = []
        for bs_no in range(self.city.bs_count):
            panel_size = np.random.randint(E.MAX_PANEL_SIZE)
            if panel_size == 0:
                battery_size = 0;
            else:
                battery_size = np.random.randint(1, E.MAX_BATTERY_SIZE)
            self.size_of_sp_and_batt.append((panel_size, battery_size))

    def increase_size_of_panels(self):
        sorted_list_by_solar_energy_potential = self.__sort_by_solar_energy_potential()
        candidate_list = []
        # max_increasing_choose_size = len(sorted_list_by_solar_energy_potential) - (10 + self.iteration_no)
        max_increasing_choose_size = self.CHOOSE_START_VAL - (self.iteration_no * self.COOLING_FACTOR)
        # max_increasing_choose_size = 5
        if self.RANDOM_SELECT_HEURISTIC:
            candidate_list = np.random.randint(self.city.bs_count, size=max_increasing_choose_size)
        elif self.MANUAL_SELECT_HEURISTIC:
            candidate_list = [117, 114, 0, 88, 73, 121, 52, 10, 59, 128, 0]
            # [ 99, 117, 114,  35,   0,  88,  18,  25,  32, 123,  50,  25, 127,  73, 121,  52,  10,  59, 128,   0]
        else:
            for i in range(max_increasing_choose_size):
                bs = sorted_list_by_solar_energy_potential[i]
                solar_potential = bs[BI.SOLAR_POT]
                if solar_potential * E.LIFE_TIME_ENERGY_COST > E.SOLAR_PANEL_COST_OF_1KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_IP:
                    bs_index = int(bs[BI.BS_INDEX])
                    candidate_list.append(bs_index)
                else:
                    print("increase_size_of_panels fails:: solar_potential:{}  * E.LIFE_TIME_ENERGY_COST:{} is lower than: {}".format(
                        solar_potential,
                        E.LIFE_TIME_ENERGY_COST,
                        E.SOLAR_PANEL_COST_OF_1KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_IP))
                    break

        '''
        print "1. it_no:{} Number of Increased Solar Panels: {}".format(self.iteration_no, len(candidate_list))
        print "1. it_no:{} Selected Panels: {}".format(self.iteration_no, candidate_list)

        for bs_index in candidate_list:
            print "{}::{}".format(bs_index, self.city.bs_locations[bs_index])
        '''

        # MIN_ALLOWED_DISTANCE_FOR_CHOOSING = 8       # traffic scenario 2&3
        MIN_ALLOWED_DISTANCE_FOR_CHOOSING = 8
        bs_list_that_have_range_between_them = []
        while len(candidate_list) != 0:
            bs_list_that_have_range_between_them.append(candidate_list[0])
            list_for_interation = np.copy(candidate_list)
            for bs_index in list_for_interation:
                bs_index_compared = bs_list_that_have_range_between_them[-1]
                distance = CoordinateConverter.get_distance_between_two_bs(self.city.bs_locations[bs_index], self.city.bs_locations[bs_index_compared])
                # print "{}{}: distance:{}".format(self.city.bs_locations[bs_index_compared], self.city.bs_locations[bs_index], distance)
                if distance < MIN_ALLOWED_DISTANCE_FOR_CHOOSING:
                    candidate_list.remove(bs_index)
        candidate_list = bs_list_that_have_range_between_them

        print("2. it_no:{} Number of Increased Solar Panels: {}".format(self.iteration_no, len(candidate_list)))
        print("2. it_no:{} Selected Panels: {}".format(self.iteration_no, candidate_list))
        '''
        for bs_index in candidate_list:
            print "{}::{}".format(bs_index, self.city.bs_locations[bs_index])
        '''

        if len(candidate_list) == 0:
            return False  # we could not find any batteries to reduce its size
        else:
            for bs_index in candidate_list:
                if self.STANDARD_METHOD:
                    battery_size = self.size_of_sp_and_batt[bs_index][BI.BATTERY_SIZE]  # we have to read battery size to assign tuple
                else:  # we increase both panel and battery sizes
                    old_battery_size = self.size_of_sp_and_batt[bs_index][BI.BATTERY_SIZE]
                    battery_size = old_battery_size + Battery.INCREMENTING_BATTERY_SIZE
                old_panel_size = self.size_of_sp_and_batt[bs_index][BI.PANEL_SIZE]  # we have to read solar panel to assign tuple
                new_panel_size = old_panel_size + self.INCREMENTING_PANEL_SIZE
                self.size_of_sp_and_batt[bs_index] = (new_panel_size, battery_size)
                self.tabu_for_sol_dec.append((bs_index, self.iteration_no))

            return True

    def decrease_size_of_panels(self):
        sorted_list_by_solar_energy_potential = self.__sort_by_solar_energy_potential('ascending')
        selected_solar_panels_list = []
        # max_decreasing_choose_size = len(sorted_list_by_solar_energy_potential) - (10 + self.iteration_no)
        # max_decreasing_choose_size = self.CHOOSE_START_VAL - (self.iteration_no * self.COOLING_FACTOR)
        max_decreasing_choose_size = 3
        if self.RANDOM_SELECT_HEURISTIC:
            selected_solar_panels_list = np.random.randint(self.city.bs_count, size=max_decreasing_choose_size)
        else:
            for i in range(max_decreasing_choose_size):
                bs = sorted_list_by_solar_energy_potential[i]
                solar_potential = bs[BI.SOLAR_POT_R]
                if solar_potential * E.LIFE_TIME_ENERGY_COST < E.SOLAR_PANEL_COST_OF_1KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_DP:
                    bs_index = bs[BI.BS_INDEX]
                    selected_solar_panels_list.append(bs_index)
                else:
                    print("decrease_size_of_panels fails:: solar_potential:{}  * E.LIFE_TIME_ENERGY_COST:{} is higher than: {}".format(
                        solar_potential,
                        E.LIFE_TIME_ENERGY_COST,
                        E.SOLAR_PANEL_COST_OF_1KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_DP))
                    break
        print("it_no:{} Number of Decreased Solar Panels: {}".format(self.iteration_no, len(selected_solar_panels_list)))
        print("it_no:{} Selected Panels: {}".format(self.iteration_no, selected_solar_panels_list))
        if len(selected_solar_panels_list) == 0:
            return False
        else:
            for bs_index_float in selected_solar_panels_list:
                bs_index = int(bs_index_float)
                old_battery_size = self.size_of_sp_and_batt[bs_index][BI.BATTERY_SIZE]
                old_panel_size = self.size_of_sp_and_batt[bs_index][BI.PANEL_SIZE]
                new_panel_size = old_panel_size - self.INCREMENTING_PANEL_SIZE
                if new_panel_size == 0:
                    new_battery_size = 0
                else:
                    new_battery_size = max(old_battery_size - Battery.INCREMENTING_BATTERY_SIZE, Battery.INCREMENTING_BATTERY_SIZE)
                self.size_of_sp_and_batt[bs_index] = (new_panel_size, new_battery_size)
                self.tabu_for_sol_inc.append((bs_index, self.iteration_no))
            return True

    def increase_size_of_batteries(self):
        sorted_list_by_wasted_energy_potential = self.__sort_by_wasted_energy_potential()
        selected_batteries_list = []
        # max_increasing_choose_size = len(sorted_list_by_wasted_energy_potential)  - (10 + self.iteration_no)
        # max_increasing_choose_size = self.CHOOSE_START_VAL - (self.iteration_no * self.COOLING_FACTOR)
        max_increasing_choose_size = 10
        if self.RANDOM_SELECT_HEURISTIC:
            selected_batteries_list = np.random.randint(self.city.bs_count, size=max_increasing_choose_size)
        else:
            for i in range(max_increasing_choose_size):
                bs = sorted_list_by_wasted_energy_potential[i]
                wasted_potential = bs[BI.BAT_POT]
                if wasted_potential * E.LIFE_TIME_ENERGY_COST > E.BATTERY_COST_OF_2500KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_IB:
                    bs_index = bs[BI.BS_INDEX]
                    selected_batteries_list.append(bs_index)
                else:
                    print("increase_size_of_batteries fails:: wasted_potential:{}  * E.LIFE_TIME_ENERGY_COST:{} is lower than: {}".format(
                        wasted_potential,
                        E.LIFE_TIME_ENERGY_COST,
                        E.BATTERY_COST_OF_2500KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_IB))
                    break
        print("it_no:{} Number of Increased Batteries: {}".format(self.iteration_no, len(selected_batteries_list)))
        print("it_no:{} Selected Batteries: {}".format(self.iteration_no, selected_batteries_list))
        if len(selected_batteries_list) == 0:
            return False
        else:
            for bs_index_float in selected_batteries_list:
                bs_index = int(bs_index_float)
                panel_size = self.size_of_sp_and_batt[bs_index][BI.PANEL_SIZE]  # we have to read solar panel to assign tuple
                old_battery_size = self.size_of_sp_and_batt[bs_index][BI.BATTERY_SIZE]
                new_battery_size = old_battery_size + Battery.INCREMENTING_BATTERY_SIZE
                self.size_of_sp_and_batt[bs_index] = (panel_size, new_battery_size)
                self.tabu_for_bat_dec.append((bs_index, self.iteration_no))
            return True

    def decrease_size_of_batteries(self):
        return False  # we could not find any batteries to reduce its size
        sorted_list_by_wasted_energy_potential = self.__sort_by_wasted_energy_potential("ascending")
        selected_batteries_list = []
        # max_decreasing_choose_size = len(sorted_list_by_wasted_energy_potential) - (10 + self.iteration_no)
        max_decreasing_choose_size = self.CHOOSE_START_VAL - (self.iteration_no * self.COOLING_FACTOR)
        if self.RANDOM_SELECT_HEURISTIC:
            selected_batteries_list = np.random.randint(self.city.bs_count, size=max_decreasing_choose_size)
        else:
            for i in range(max_decreasing_choose_size):
                bs = sorted_list_by_wasted_energy_potential[i]
                wasted_potential = bs[BI.BAT_POT_R]
                if wasted_potential * E.LIFE_TIME_ENERGY_COST < E.BATTERY_COST_OF_2500KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_DB:
                    bs_index = bs[BI.BS_INDEX]
                    selected_batteries_list.append(bs_index)
                else:
                    print("decrease_size_of_batteries fails:: wasted_potential:{}  * E.LIFE_TIME_ENERGY_COST:{} is higher than: {}".format(
                        wasted_potential,
                        E.LIFE_TIME_ENERGY_COST,
                        E.BATTERY_COST_OF_2500KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_DB))
                    break
        print("it_no:{} Number of Decreased Batteries: {}".format(self.iteration_no, len(selected_batteries_list)))
        print("it_no:{} Selected Batteries: {}".format(self.iteration_no, selected_batteries_list))
        if len(selected_batteries_list) == 0:
            return False  # we could not find any batteries to reduce its size
        else:
            for bs_index_float in selected_batteries_list:
                bs_index = int(bs_index_float)
                panel_size = self.size_of_sp_and_batt[bs_index][BI.PANEL_SIZE]  # we have to read solar panel to assign tuple
                old_battery_size = self.size_of_sp_and_batt[bs_index][BI.BATTERY_SIZE]
                new_battery_size = old_battery_size - Battery.INCREMENTING_BATTERY_SIZE
                if new_battery_size != 0:  # we always have a minimum size of batteries in a bs which have a solar panel
                    self.size_of_sp_and_batt[bs_index] = (panel_size, new_battery_size)
                    self.tabu_for_bat_inc.append((bs_index, self.iteration_no))
                else:  # sanity check
                    raise Exception("Houston we have a problem: SW Bug!!")
            return True

    def __sort_by_solar_energy_potential(self, order='descending'):
        sorted_list_for_solar_panel = np.copy(self.bs_lifecycle_data)
        if order is 'descending':
            self.__sort_battery_list(sorted_list_for_solar_panel, 'f8', 'descending')
            sorted_list_by_solar_energy_potential = []
            for i in range(len(sorted_list_for_solar_panel)):
                bs_index = sorted_list_for_solar_panel[i][BI.BS_INDEX]
                bs_index = int(bs_index)
                if int(self.size_of_sp_and_batt[bs_index][BI.PANEL_SIZE]) != E.MAX_PANEL_SIZE:
                    sorted_list_by_solar_energy_potential.append(sorted_list_for_solar_panel[i])
            return sorted_list_by_solar_energy_potential
        else:
            self.__sort_battery_list(sorted_list_for_solar_panel, 'f10', 'ascending')
            return sorted_list_for_solar_panel

    def __sort_by_wasted_energy_potential(self, order='descending'):  # BI.BAT_POT
        sorted_list_by_wasted_energy = np.copy(self.bs_lifecycle_data)
        if order is 'descending':
            # wasted_potential
            self.__sort_battery_list(sorted_list_by_wasted_energy, 'f9', 'descending')
        else:  # wasted_potential_r
            self.__sort_battery_list(sorted_list_by_wasted_energy, 'f11', 'ascending')
        # for bs in sorted_list_by_wasted_energy:
        # print "bs:{}:: fc is {} we is {} potential is {}".format(bs[0], bs[2], bs[4], bs[8])
        return sorted_list_by_wasted_energy

    def __sort_battery_list(self, l, sort_column='f0', order='ascending'):
        temp2 = l.ravel().view('float, float, float, float, float, float, float, float, float, float, float, float, float')
        temp2.sort(order=[sort_column])
        if order == 'descending':
            l[:] = l[::-1]

    @staticmethod
    def __fill_the_row_list(row_list, bh, bs_index):
        time_slot_size = len(bh[0])
        row_list[bs_index][BI.BS_INDEX] = bs_index
        for time_slot in range(time_slot_size):  # for each time slot
            if bh[bs_index][time_slot][1] == 'Awake':  # fifth column informs the number of awake bs
                row_list[bs_index][BI.AWAKE_RATIO] += 1
            row_list[bs_index][BI.FOSSIL_CONS] += bh[bs_index][time_slot][2]
            # field 2 --> fossil_energy_consumption
            row_list[bs_index][BI.RENEWABLE_CONS] += bh[bs_index][time_slot][3]
            # field 3 --> ren_energy_consumption
            row_list[bs_index][BI.WASTED_ENERGY] += bh[bs_index][time_slot][4]
            # field 4 --> wasted_energy
            row_list[bs_index][BI.REMAINING_ENERGY] += bh[bs_index][time_slot][5]
            # field 5 --> remaining_energy
            row_list[bs_index][BI.RENEWABLE_RATIO] += bh[bs_index][time_slot][6]
            # field 6 --> renewable_usage_ratio
            row_list[bs_index][BI.REMAINING_ENERGY_WBO] += bh[bs_index][time_slot][7]
            row_list[bs_index][BI.REMAINING_ENERGY_WBO_R] += bh[bs_index][time_slot][8]

        row_list[bs_index][BI.AWAKE_RATIO] /= time_slot_size
        row_list[bs_index][BI.RENEWABLE_RATIO] /= time_slot_size

    def sum_values_of_each_time_slots(self, bh, bh_old):
        number_of_bs = len(bh)
        field_size = len(bh[0][0])
        row_list = np.array([[0 for x in range(BI.LIFECYCYLE_FIELD_SIZE)] for x in range(number_of_bs)], dtype='float')
        row_list_old = np.array([[0 for x in range(BI.LIFECYCYLE_FIELD_SIZE)] for x in range(number_of_bs)], dtype='float')
        for bs_index in range(number_of_bs):
            OptimizationForCapitalExpenditure.__fill_the_row_list(row_list, bh, bs_index)
            if bh_old != None:
                OptimizationForCapitalExpenditure.__fill_the_row_list(row_list_old, bh_old, bs_index)
            if self.NEW_PANEL_SELECTION_METHOD:
                # ------------- INCREASING SOLAR PANEL SIZE ::: SORTING PARAMETER: RENEWABLE_CONS --------------------
                bs_previous_solar_panel_size = self.size_of_sp_and_batt[bs_index][BI.PANEL_SIZE]
                if self.__is_in_tabu_list(self.tabu_for_sol_inc, bs_index):
                    ren_energy_potential = INFINITELY_SMALL
                    row_list[bs_index][BI.SOLAR_POT] = INFINITELY_SMALL
                    # note: bses that have no solar panel has no chance to selected to increase their solar panel sizes
                    # in future we will adding harvesting energy as a parameter to adding a solar panel or we may log their previous ren_energy
                    pass
                elif bh_old is None:  # first iteration
                    ren_energy_potential = row_list[bs_index][BI.FOSSIL_CONS]
                else:
                    ren_energy_potential = row_list[bs_index][BI.RENEWABLE_CONS] - row_list_old[bs_index][BI.RENEWABLE_CONS]
                row_list[bs_index][BI.SOLAR_POT] = min(ren_energy_potential, row_list[bs_index][BI.FOSSIL_CONS])
                    # field 7 --> potential reducing of fossil energy cons.
            else:
                # ------------- INCREASING SOLAR PANEL SIZE ::: SORTING PARAMETER: RENEWABLE_CONS --------------------
                bs_previous_solar_panel_size = self.size_of_sp_and_batt[bs_index][BI.PANEL_SIZE]
                if bs_previous_solar_panel_size == 0 or self.__is_in_tabu_list(self.tabu_for_sol_inc, bs_index):
                    ren_energy_potential = INFINITELY_SMALL  # note: only for print
                    row_list[bs_index][BI.SOLAR_POT] = INFINITELY_SMALL
                    pass
                else:
                    bs_new_solar_panel_size = bs_previous_solar_panel_size + self.INCREMENTING_PANEL_SIZE
                    panel_size_increasing_ratio = bs_new_solar_panel_size / float(bs_previous_solar_panel_size)
                    total_consumption = row_list[bs_index][BI.RENEWABLE_CONS] + row_list[bs_index][BI.FOSSIL_CONS]
                    ren_energy_potential = (panel_size_increasing_ratio - 1) * total_consumption
                    row_list[bs_index][BI.SOLAR_POT] = min(ren_energy_potential, row_list[bs_index][BI.FOSSIL_CONS])
                    # field 7 --> potential reducing of fossil energy cons.

            # ------------- INCREASING BATTERY SIZE ::: SORTING PARAMETER: WASTED_ENERGY --------------------
            bs_previous_battery_size = self.size_of_sp_and_batt[bs_index][BI.BATTERY_SIZE]
            if bs_previous_battery_size == 0:
                wasted_energy_potential = INFINITELY_SMALL
                row_list[bs_index][BI.BAT_POT] = INFINITELY_SMALL
                pass
            else:
                wasted_energy_potential = row_list[bs_index][BI.WASTED_ENERGY]
                row_list[bs_index][BI.BAT_POT] = min(wasted_energy_potential, row_list[bs_index][BI.FOSSIL_CONS])

            # ------------- DECREASING SOLAR PANEL SIZE ::: SORTING PARAMETER: RENEWABLE_CONS --------------------
            bs_previous_solar_panel_size = self.size_of_sp_and_batt[bs_index][BI.PANEL_SIZE]
            if bs_previous_solar_panel_size == 0 or self.__is_in_tabu_list(self.tabu_for_sol_dec, bs_index):
                row_list[bs_index][BI.SOLAR_POT_R] = INFINITELY_BIG
            else:
                bs_new_solar_panel_size = bs_previous_solar_panel_size - self.INCREMENTING_PANEL_SIZE
                panel_size_decreasing_ratio = bs_new_solar_panel_size / float(bs_previous_solar_panel_size)
                ren_energy_potential_r = (1 - panel_size_decreasing_ratio) * row_list[bs_index][BI.RENEWABLE_CONS]
                row_list[bs_index][BI.SOLAR_POT_R] = ren_energy_potential_r
            # field 9 --> potential increasing of fossil energy cons.

            # "ok don't reduce the battery size itself, do it with decreasing of the solar panel size"

            '''
            print "BS[#:{}]:: S:{}/{} R:{} F:{} SP:{} W:{} BP:{}".format(bs_index,
                                                                         bs_previous_solar_panel_size,
                                                                         bs_previous_battery_size,
                                                                         row_list[bs_index][BI.RENEWABLE_CONS],
                                                                         row_list[bs_index][BI.FOSSIL_CONS],
                                                                         ren_energy_potential,
                                                                         row_list[bs_index][BI.WASTED_ENERGY],
                                                                         wasted_energy_potential)
            '''
        return row_list
