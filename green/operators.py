"""operators module
The classes in this module are responsible to simulate and operate the city (Journal 1).
Also Operational Algorithms are implemented in this module.
"""
from copy import deepcopy

import numpy as np

from city import CityBeforeDeployment
from constants import *
from helpers import CoordinateConverter
from performanceCalculator import *
from renewableEnergy import Battery
from snapshot import Snapshot

__author__ = 'turgay.pamuklu'



@PerformanceCalculator
def test_np_where_performance(assigning, least_eff_bs_index):
    return np.where(assigning == least_eff_bs_index)


# bs_dep_act, assigning, rem_bs_cap, sorted_nsr,    nsr_list,        macro_bs,  comp_val_list, can_bs_list
# @jit((uint32[:], uint32[:, :], float64[:],  float32[:, :, :], uint32[:], float64[:], uint32[:, :]))
def run_the_system_for_one_day(awake_bs_list,
                               assigning,
                               remaining_bs_capacity,
                               nsr_list,
                               can_bs_list_that_should_try_to_sleep,
                               comp_val_list,
                               can_bs_list_that_can_be_assigned_to_the_locations):
    number_of_base_stations = len(can_bs_list_that_should_try_to_sleep)
    number_of_can_bs_that_should_try_to_sleep = sum(can_bs_list_that_should_try_to_sleep)
    size_of_can_bs_list_that_can_be_assigned_to_the_locations = can_bs_list_that_can_be_assigned_to_the_locations.shape[2]
    # print "run_the_system_for_one_day before loop time:{}".format(datetime.now())
    while True:
        # begin:: select least effective base station
        if number_of_can_bs_that_should_try_to_sleep == 0:
            break
        # least_eff_cap = -1e20
        least_eff_cap = 0
        least_eff_bs_index = -1
        for i in range(number_of_base_stations):
            if can_bs_list_that_should_try_to_sleep[i]:
                fit_val = remaining_bs_capacity[i] - comp_val_list[i]
                if fit_val > least_eff_cap:
                    least_eff_cap = fit_val
                    least_eff_bs_index = i
        # if least_eff_bs_index == -1:
        #    raise Exception("Aieee! something goes wrong!")
        # remove the least significant base station
        can_bs_list_that_should_try_to_sleep[least_eff_bs_index] = 0
        number_of_can_bs_that_should_try_to_sleep -= 1
        awake_bs_list[least_eff_bs_index] = 0
        # find the locations that assigned this base station
        # locations_that_assigned_to_the_removed_bs = test_np_where_performance(assigning, least_eff_bs_index)
        locations_that_assigned_to_the_removed_bs = np.where(assigning == least_eff_bs_index)
        len_of_ltattrb = len(locations_that_assigned_to_the_removed_bs[0])
        for index_of_location in range(len_of_ltattrb):
            # for each of this location
            x_coor = locations_that_assigned_to_the_removed_bs[0][index_of_location]
            y_coor = locations_that_assigned_to_the_removed_bs[1][index_of_location]
            we_found_a_candidate_base_station = False
            for can_order in range(size_of_can_bs_list_that_can_be_assigned_to_the_locations):
                can_index = can_bs_list_that_can_be_assigned_to_the_locations[x_coor][y_coor][can_order]
                if can_index == -1:  # we could not assign any one of the awake base station to this location
                    break
                if not awake_bs_list[can_index]:
                    continue
                nsr = nsr_list[x_coor][y_coor][can_order]
                if remaining_bs_capacity[can_index] - nsr >= 0:
                    remaining_bs_capacity[can_index] -= nsr
                    assigning[x_coor][y_coor] = can_index
                    # relocated_locations.append((x_coor, y_coor))
                    we_found_a_candidate_base_station = True
                    # we found a candidate base station
                    break
            if not we_found_a_candidate_base_station:
                # we could not found a candidate base station
                for iol in range(index_of_location):
                    # relocate each location to the least eff base station
                    x_coor = locations_that_assigned_to_the_removed_bs[0][iol]
                    y_coor = locations_that_assigned_to_the_removed_bs[1][iol]
                    temp_assigned_bs = assigning[x_coor][y_coor]
                    for bs_order in range(size_of_can_bs_list_that_can_be_assigned_to_the_locations):
                        if can_bs_list_that_can_be_assigned_to_the_locations[x_coor][y_coor][bs_order] == temp_assigned_bs:
                            break
                    remaining_bs_capacity[temp_assigned_bs] += nsr_list[x_coor][y_coor][bs_order]
                    assigning[x_coor][y_coor] = least_eff_bs_index
                # update least eff base station as a must deployed bs
                awake_bs_list[least_eff_bs_index] = 1
                break
    # print "run_the_system_for_one_day after loop time:{}".format(datetime.now())


# bs_dep_act, assigning, rem_bs_cap, sorted_nsr,    nsr_list,        macro_bs, micro_bs, comp_val_list, can_bs_list
# @jit((uint32[:], uint32[:, :], float64[:],  float32[:, :, :], uint32[:], uint32[:], float64[:], uint32[:, :]))
def pre_run_the_system_for_one_day(awake_bs_list,
                                   assigning,
                                   remaining_bs_capacity,
                                   nsr_list,
                                   macro_bs,
                                   micro_bs,
                                   comp_val_list,
                                   can_bs_list):
    # configuration.must_deployed_bs_list RETURN it
    # configuration.assigning  RETURN it
    # configuration.remaining_bs_capacity RETURN it
    # configuration.remaining_bs_capacity
    # configuration.sorted_nsr
    # configuration.nsr
    run_the_system_for_one_day(awake_bs_list,
                               assigning,
                               remaining_bs_capacity,
                               nsr_list,
                               micro_bs,
                               comp_val_list,
                               can_bs_list)

    run_the_system_for_one_day(awake_bs_list,
                               assigning,
                               remaining_bs_capacity,
                               nsr_list,
                               macro_bs,
                               comp_val_list,
                               can_bs_list)

class CityConfiguration:
    """CityConfiguration Class.
        * This class stores the city configuration which are time related and different in each time slice.
        * It also manage the change of these configurations between the consecutive time slices which is actually change of assigning decision:

            * _assign_the_most_effected_bs_to_the_locations_ method.
            * _reassign_the_least_eff_bs_to_the_locations_ method.

        * It also returns data that need to decide next configuration change in the city like

            * calculate_remaining_bs_capacity method.
            * get_least_effective_bs method.

        * FossilDeployment is directly inherited from this class.
        * Operator classes creates Fossil class for the initial configuration for each time slices.

    """
    COMPARE_CONSTANT = 1  # 1e-9
    BS_UTILIZATION = 0.8
    remaining_bs_capacity = None
    bs_deployed_and_active = None
    assigning = None
    must_deployed_bs_list = None
    bs_count = None
    configuration_no = None
    nsr = None

    def __init__(self, bs_count, configuration_no, nsr):
        self.bs_count = bs_count
        self.must_deployed_bs_list = []
        self.remaining_bs_capacity = np.array([self.BS_UTILIZATION for x in range(self.bs_count)])
        self.bs_deployed_and_active = np.ones(self.bs_count, dtype='int32')
        self.configuration_no = configuration_no
        self.nsr = nsr

    def calculate_remaining_bs_capacity(self, can_bs_list):
        """read operation, used by the Operator Classes.
            * creates the remaining_bs_capacity[bs_count] array
            * calculate the nominal_service_rate for each grid
            * subtract nominal_service_rate from the remaining_bs_capacity of the bs which is assigned to that grid
        """
        remaining_bs_capacity = np.array([self.BS_UTILIZATION for x in range(self.bs_count)])
        for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
            for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                assigned_bs_index = self.assigning[x_coor][y_coor]
                assigned_bs_order = np.where(can_bs_list[x_coor][y_coor] == assigned_bs_index)
                if assigned_bs_index != -1:
                    remaining_bs_capacity[assigned_bs_index] -= self.nsr[x_coor][y_coor][assigned_bs_order[0][0]]
        return remaining_bs_capacity

    @PerformanceCalculator
    def get_least_effective_bs(self, tabu_bs_list=None, battery_list=None, calibration_val=None):
        """Used by FossilDeployment and FossilOperator
        RenewableOperator is used get_least_fit_bs(self, time_slot_of_the_current_day) instead of this method
        """
        least_eff_cap = -200.0
        least_eff_bs_index = -1
        for i in self.bs_deployed_and_active:
            if i not in self.must_deployed_bs_list:
                if tabu_bs_list is None or i not in tabu_bs_list:
                    if battery_list is None:  # fossil operation
                        fit_val = self.remaining_bs_capacity[i]
                    else:
                        batt_util = battery_list[i].get_battery_utilization()
                        comp_val = (batt_util ** 2) * calibration_val * self.COMPARE_CONSTANT
                        fit_val = self.remaining_bs_capacity[i] - comp_val
                    if fit_val > least_eff_cap:
                        least_eff_cap = fit_val
                        least_eff_bs_index = i
        return least_eff_bs_index


    def is_there_any_unassigned_location(self):
        """Used by FossilDeployment, FossilOperator and RenewableOperator
        * Looking for each grid in the assigning field
        * if any value is -1

            * return True

        * otherwise False

        """

        for row in self.assigning:
            for val in row:
                if val == -1:
                    return True
        return False


    # @PerformanceCalculator
    def _reassign_the_least_eff_bs_to_the_locations_(self, list_of_bs_coordinates, least_bs):
        """Used by FossilDeployment, FossilOperator and RenewableOperator
            * if we remove a bs that should be deployed then by this method we reassign the grids to the bs
            * for each grid
                * if we already assign another bs to this bs
                    * update the remaining_bs_capacity[temp_assigned_bs]
                * assigning[x_coor][y_coor] = least_bs
        """
        for i in list_of_bs_coordinates:
            x_coor = i[0]
            y_coor = i[1]
            temp_assigned_bs = self.assigning[x_coor][y_coor]
            if temp_assigned_bs != -1:
                can_index = np.where(self.c.can_bs_list[x_coor][y_coor] == temp_assigned_bs)
                self.remaining_bs_capacity[temp_assigned_bs] += self.nsr[x_coor][y_coor][can_index[0]]
            self.assigning[x_coor][y_coor] = least_bs

    @PerformanceCalculator
    def remove_least_effective_bs(self, least_eff_bs_index):
        """Used by FossilDeployment
        * remove the bs_deployed_and_active[least_eff_bs_index]
        * store the location of the grids which are assigned to the least_eff_bs_index in the assigned_list field
        * for each grid in the assigned_list field call _assign_the_most_effected_bs_to_the_locations_
        * if any grid in the  assigned_list field could not be assigned

            * call _reassign_the_least_eff_bs_to_the_locations_
            * add least_eff_bs_index to the  must_deployed_bs_list
            * add least_eff_bs_index to the  bs_deployed_and_active

        * otherwise update the remaining_bs_capacity[least_eff_bs_index]

        """
        self.bs_deployed_and_active.remove(least_eff_bs_index)
        locations_that_assigned_to_the_removed_bs = np.where(self.assigning == least_eff_bs_index)
        len_of_ltattrb = len(locations_that_assigned_to_the_removed_bs[0])
        relocated_locations = []
        for i in range(len_of_ltattrb):
            x_coor = locations_that_assigned_to_the_removed_bs[0][i]
            y_coor = locations_that_assigned_to_the_removed_bs[1][i]
            we_assigned_the_location = self._assign_the_most_effected_bs_to_the_locations_(x_coor, y_coor)
            if we_assigned_the_location is True:
                relocated_locations.append((x_coor, y_coor))
            else:  # we failed to remove this base station we reassigned the locations to this base station and redeploy it again
                self._reassign_the_least_eff_bs_to_the_locations_(relocated_locations, least_eff_bs_index)
                self.must_deployed_bs_list.append(least_eff_bs_index)
                self.bs_deployed_and_active.append(least_eff_bs_index)
                return
        self.remaining_bs_capacity[least_eff_bs_index] = self.BS_UTILIZATION


class FossilOperator():
    """
    This class use to simulate a city which is already deployed by fossil base stations.
        * The main purpose of this class is creating city configurations (CityConfiguration() class) for each time slice separately.
        * CityConfiguration class methods are responsible for the remaining operations
        * It creates by operate_fossil_city() method in the main module.
        * In the operate_fossil_city() method methods of the CityConfiguration class is used to reduce the awake bs count for different time slices.
    """

    city_configuration_list = None

    def __init__(self, c):
        self.c = c  # c is not added to the CityConfiguration because CityConfiguration is created for each time slot
        # but city object is just one
        self.city_configuration_list = []
        # print "fossil operate __init__ starts at:{}".format(datetime.now())
        snapshot = Snapshot()
        nsr = snapshot.load_nominal_service_rate()
        for day in range(NUMBER_OF_SIMULATION_DAY):
            for time_slot in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                configuration_no = day * NUMBER_OF_TIME_SLOT_IN_ONE_DAY + time_slot
                f = self.__create_fossil_time_slice(c, configuration_no, nsr[configuration_no])
                self.city_configuration_list.append(f)
                # print "fossil operate __init__ ends at:{}".format(datetime.now())

    def __create_fossil_time_slice(self, c, configuration_no, nsr):
        f = CityConfiguration(c.bs_count, configuration_no, nsr)
        # print "__create_fossil_time_slice configuration_no:{} assigning:{}".format(configuration_no, c.assigning)
        f.assigning = deepcopy(c.assigning)
        if False:
            f.remaining_bs_capacity = f.calculate_remaining_bs_capacity(c.can_bs_list)
        else:
            f.remaining_bs_capacity = np.array([f.BS_UTILIZATION for x in range(f.bs_count)])
            unassigned_location = 0
            for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    for bs_index in range(len(c.can_bs_list[x_coor][y_coor])):
                        bs_no = c.can_bs_list[x_coor][y_coor][bs_index]
                        if bs_no == -1:
                            # print "Aiee! Houston we have a problem! :: unassigned location {}".format(bs_no)
                            f.assigning[x_coor][y_coor] = -1
                            unassigned_location += 1
                        new_remaining_bs_capacity = f.remaining_bs_capacity[bs_no] - f.nsr[x_coor][y_coor][bs_index]
                        if new_remaining_bs_capacity >= 0:
                            f.remaining_bs_capacity[bs_no] = new_remaining_bs_capacity
                            f.assigning[x_coor][y_coor] = bs_no
                            break
            '''
            if unassigned_location != 0:
                print "configuration_no:{} unassigned location size:{}".format(configuration_no, unassigned_location)
            '''
        return f

    def get_energy_consumption_per_bs(self):
        number_of_awake_count = [0 for x in range(self.c.bs_count)]
        energy_consumption = [0 for x in range(self.c.bs_count)]
        for c in self.city_configuration_list:
            for bs_index in c.bs_deployed_and_active:
                number_of_awake_count[bs_index] += 1
        for bs_index in range(self.c.bs_count):
            if self.c.bs_types[bs_index] == bs_index is BSType.MICRO:
                energy_consumption[bs_index] = number_of_awake_count[bs_index] * Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO
            else:
                energy_consumption[bs_index] = number_of_awake_count[bs_index] * Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO
        return energy_consumption, number_of_awake_count


class RenewableOperator(FossilOperator):
    """
    This class use to simulate a city which is already deployed by renewable base stations.
        * The Class is inherited from FossilOperator and the main differences are the new fields and methods for simulating Battery.
        * It also have heuristic methods for optimization:
            * get_least_fit_bs
        * Also have methods that simulate a day / month (called by operate_renewable_city()):
            * run_the_system_for_one_day()
            * operate_one_month
        * It creates by operate_renewable_city / calibrate_renewable_city() methods in the main module.
        * In this main module methods, methods of the Fossil class is used to reduce the awake bs count for different time slices.
    """
    battery_list = None
    calibration_val = None

    def __init__(self, c, battery_info_list, calibration_val):
        snapshot = Snapshot()
        solar_energy = snapshot.load_solar_energy()
        self.c = c
        self.calibration_val = calibration_val
        FossilOperator.__init__(self, self.c)
        self.battery_list = []
        for bs in range(self.c.bs_count):
            battery = Battery(solar_energy, battery_info_list[bs][0], battery_info_list[bs][1], c.bs_types[bs])
            self.battery_list.append(battery)

    def get_consumption_data(self, number_of_day):
        """read operation, return ren_con_total, fossil_con_total
        """
        num_awake_bs_total = 0
        ren_con_total = 0
        fossil_con_total = 0
        wasted_en_total = 0
        generated_energy_total = 0
        num_awake_bs = [0 for x in range(self.c.bs_count)]
        fossil_con = [0 for x in range(self.c.bs_count)]
        ren_con = [0 for x in range(self.c.bs_count)]
        wasted_en = [0 for x in range(self.c.bs_count)]
        generated_energy = [0 for x in range(self.c.bs_count)]
        print("get_consumption_data-> bs_count:{}".format(self.c.bs_count))
        for i in range(self.c.bs_count):
            for time_slice in range(number_of_day * NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                generated_energy[i] += self.battery_list[i].flash_memory.history[time_slice][0]
                if self.battery_list[i].flash_memory.history[time_slice][1] is 'Awake':
                    num_awake_bs[i] += 1
                fossil_con[i] += self.battery_list[i].flash_memory.history[time_slice][2]
                ren_con[i] += self.battery_list[i].flash_memory.history[time_slice][3]
                wasted_en[i] += self.battery_list[i].flash_memory.history[time_slice][4]
            generated_energy_total += generated_energy[i]
            num_awake_bs_total += num_awake_bs[i]
            ren_con_total += ren_con[i]
            fossil_con_total += fossil_con[i]
            wasted_en_total += wasted_en[i]
            should_be_lower_than_10000 = abs(generated_energy[i] - (ren_con[i] + wasted_en[i]))
            # if should_be_lower_than_10000 > 100001:
            # print "{}:: wasted_en:{} ren_con_total:{} generated_energy:{} fossil_con:{}".format(i, wasted_en[i], ren_con[i], generated_energy[i], fossil_con[i])
            #    print "should be should_be_lower_than_10000:{} ".format(should_be_lower_than_10000)
        # print "wasted_en:{} ren_con_total:{} generated_energy:{}".format(wasted_en_total, ren_con_total, generated_energy_total)
        print("num_awake_bs:{}".format(num_awake_bs_total))
        print("num_awake:{}".format(num_awake_bs))
        zero_awake_bs_count = 0
        fifty_awake_bs_count = 0
        unassigned_bs_list = []
        for i in range(self.c.bs_count):
            if num_awake_bs[i] == 0:
                unassigned_bs_list.append(self.c.bs_locations[i])
                zero_awake_bs_count += 1
            if num_awake_bs[i] < 50:
                fifty_awake_bs_count += 1
        print("zero_awake_bs_count:{}".format(zero_awake_bs_count))
        print("zero_awake_bs_locations:{}".format(unassigned_bs_list))
        print("fifty_awake_bs_count:{}".format(fifty_awake_bs_count))
        return ren_con_total, fossil_con_total

    @PerformanceCalculator
    def operate_sim_duration(self):
        """read operation, modified get_least_effective_bs() method for renewable optimization which also consider the
         battery level.
        """
        # self.sanity_check_nsr()

        for day in range(NUMBER_OF_SIMULATION_DAY):  # NUMBER_OF_SIMULATION_DAY
            self.run_the_system_for_one_day(day)
            '''
            if day % 2 == 0:
                print "Simulation Day: {}".format(day)
            '''

        battery_history_list = []
        battery_info_list = []
        for bl in self.battery_list:  # appending all the bses battery history
            battery_history_list.append(bl.flash_memory.history)
            battery_info_list.append((bl.panel_size, bl.battery_size))
        return battery_info_list, battery_history_list

    def sanity_check_nsr(self):
        nsr_prev = None
        for conf_no in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY * NUMBER_OF_SIMULATION_DAY):
            nsr_cur = self.city_configuration_list[conf_no].nsr
            if conf_no != 0:
                if np.array_equal(nsr_prev, nsr_cur):
                    raise Exception("Aiee! we found the same nsr in two different time slot nsr_prev:{} !".format(conf_no))
            nsr_prev = nsr_cur

    # @PerformanceCalculator
    def run_the_system_for_one_day(self, day):
        """Simulate one day of the system.
        * Get the least effective Micro Base Station
        * Remove it if this operation is feasible
        * If you could not find any candidate Micro Base Station
        * Stop Loop and Make the same loop for Macro Base Stations
        * Update Battery Info
        """
        mac, mic = self.c.get_macro_micro_list_as_numpy_arrays()
        for time_slot in range(day * NUMBER_OF_TIME_SLOT_IN_ONE_DAY,
                               (day + 1) * NUMBER_OF_TIME_SLOT_IN_ONE_DAY):  # for each hour
            macro_bses = np.copy(mac)
            micro_bses = np.copy(mic)
            batt_list_len = len(self.battery_list)
            comp_val_list = np.array([-1.0 for x in range(batt_list_len)])
            # old_remaining_bs_cap = self.city_configuration_list[time_slot].remaining_bs_capacity.tolist()
            # print "time:{}:old_remaining_bs_cap:{}".format(time_slot % NUMBER_OF_TIME_SLOT_IN_ONE_DAY, old_remaining_bs_cap)
            for i in range(batt_list_len):
                comp_val_list[i] = self.battery_list[i].get_battery_utilization() ** 2
                comp_val_list[i] = comp_val_list[i] * self.calibration_val * CityConfiguration.COMPARE_CONSTANT
            pre_run_the_system_for_one_day(self.city_configuration_list[time_slot].bs_deployed_and_active,
                                           self.city_configuration_list[time_slot].assigning,
                                           self.city_configuration_list[time_slot].remaining_bs_capacity,
                                           self.city_configuration_list[time_slot].nsr,
                                           macro_bses,
                                           micro_bses,
                                           comp_val_list,
                                           self.c.can_bs_list)
            # new_remaining_bs_cap = self.city_configuration_list[time_slot].remaining_bs_capacity.tolist()
            # print "time:{}:new_remaining_bs_cap:{}".format(time_slot % NUMBER_OF_TIME_SLOT_IN_ONE_DAY, new_remaining_bs_cap)
            for i in range(self.c.bs_count):
                if self.city_configuration_list[time_slot].bs_deployed_and_active[i]:
                    self.battery_list[i].consume_power(self.city_configuration_list[time_slot].remaining_bs_capacity[
                                                           i])  # reducing battery power and updating the flash of the battery
                self.battery_list[
                    i].increase_the_time_slot()  # needs to changing battery & solar power states also for logging


class FossilDeployment(CityConfiguration):
    """
    This class is used to find the best places for the bs in a city according to user traffic and service rates.
        * It is called by create_city_and_fossil_deployment() method in main.
        * It has greedy function methods to find best places for the bses.
    """
    EPSILON = -1e100
    c = None  # city before deployment

    def __init__(self, c):
        self.c = c  # non deployed premature city
        # we create only one city configuration because we focus only one time slot.
        # we select bs_count and user_traffic as BS_CANDIDATE_COUNT and max_user_traffic_demand respectively.
        snapshot = Snapshot()
        nsr = snapshot.load_nominal_service_rate()
        CityConfiguration.__init__(self, CityBeforeDeployment.BS_CANDIDATE_COUNT, 0, nsr)
        # self.c.tr.get_max_user_traffic_demand()
        self.assigning = np.array([[-1 for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)] for x in
                                   range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)])

    @staticmethod
    def __ignore_coors(x_axis, y_axis):
        if x_axis == 14 and y_axis == 20:
            pass

    def greedy_deployment_for_every_grid(self):
        """Assign the each location to the most effected bs
        * _assign_the_most_effected_bs_to_the_locations_ method controls the bc_remaining_capacity, so optimization
        result will be changed by decision of the starting point.
        """
        bs_list_len = self.c.can_bs_list.shape[2]
        for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
            for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                # self.__ignore_coors(x_axis, y_axis)
                for can_bs_order in range(bs_list_len):
                    can_index = self.c.can_bs_list[x_coor][y_coor][can_bs_order]
                    nsr = self.nsr[x_coor][y_coor][can_bs_order]
                    if self.remaining_bs_capacity[can_index] - nsr >= 0:
                        self.remaining_bs_capacity[can_index] -= nsr
                        self.assigning[x_coor][y_coor] = can_index
                        break
                if self.assigning[x_coor][y_coor] == -1:
                    raise Exception("Aieee! we should not be here!")

    def remove_unassigned_bses(self):
        """After the greedy_deployment_for_every_grid method, main calls this function to remove bses which are assigned
        to any grid.
        """
        for i in range(self.c.BS_CANDIDATE_COUNT):
            if self.remaining_bs_capacity[i] == self.BS_UTILIZATION:
                if i in self.assigning:
                    raise Exception("Houston we have a problem: SW Bug!!")
                self.bs_deployed_and_active[i] = 0
