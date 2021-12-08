"""City Module.
The Classes in this module are responsible for simulating the city where the base stations are deployed by an operator.

"""
from datetime import datetime

import numpy as np

from baseStation import Transmitter
from constants import *
from helpers import CoordinateConverter
from snapshot import Snapshot

__author__ = 'turgay.pamuklu'


class City:
    """This class provides the common fields and methods of the other City Classes

     * The other city classes are inherited from this class.

    """
    NON_RECEIVED_SIGNAL_BOUND = INFINITELY_SMALL

    service_rate = None
    can_bs_list = None
    bs_count = None
    bs_types = None
    # BS_TYPE = ['micro', 'macro']

    def is_macro_loc(self, bs_coor):
        macro_locs = [(5, 5), (4, 15), (7, 26), (6, 37),
                      (14, 6), (15, 15), (13, 28), (16, 37),
                      (25, 4), (24, 17), (27, 26), (24, 35),
                      (33, 5), (35, 14), (34, 33), (36, 36),
                      (5, 6), (18, 32), (9, 32), (13, 4), (4, 10), (8, 30), (9, 12), (16, 36), (35, 26), (18, 17), (24, 9), (27, 20), (30, 12), (24, 2),
                      (28, 25), (35, 27), (18, 14), (28, 31), (13, 19), (23, 33)
                      ]
        for i in macro_locs:
            if bs_coor[0] == i[0] and bs_coor[1] == i[1]:
                return True
        return False
        '''
        if bs_coor[0] % 6 == 3 and bs_coor[1] % 6 == 3:
            return True
        return False
        '''

    @staticmethod
    def __sort_nominal_service_rate(l, order='ascending'):
        # temp2 = l.ravel().view('int, float')
        np.sort(l)
        if order == 'descending':
            l[:] = l[::-1]

    @staticmethod
    def sanity_check_traffic(tr):
        tr_prev = None
        for day in range(NUMBER_OF_SIMULATION_DAY):
            for time_slot in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                tr_cur = tr.get_user_traffic_demand_in_a_specif_time_slot(day, time_slot)
                if tr_prev is not None:
                    if np.array_equal(tr_prev, tr_cur):
                        raise Exception("Aiee! we found the same nsr in two different time slot day:{} time_slot:{} !".format(day, time_slot))
                tr_prev = tr_cur

    @staticmethod
    def sanity_check_nsr_and_sorted_nsr(nsr, sorted_nsr):
        nsr_prev = None
        sorted_nsr_prev = None
        for conf_no in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY * NUMBER_OF_SIMULATION_DAY):
            nsr_cur = nsr[conf_no]
            sorted_nsr_cur = sorted_nsr[conf_no]
            if conf_no != 0:
                if np.array_equal(nsr_prev, nsr_cur):
                    raise Exception("Aiee! we found the same nsr in two different time slot nsr_prev:{} !".format(conf_no))
                if not np.array_equal(sorted_nsr_prev, sorted_nsr_cur):
                    raise Exception("Aiee! we found different sorted array in two different time slots nsr_prev:{} !".format(conf_no))
            nsr_prev = nsr_cur
            sorted_nsr_prev = sorted_nsr_cur

    def __create_nominal_service_rate(self, utd_for_a_specific_time_slot, nominal_service_rate):
        """ create the most important parameter to choose bses to sleep
        """
        can_bs_list_len = nominal_service_rate.shape[2]
        for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
            for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                for bs_index in range(can_bs_list_len):
                    bs_no = self.can_bs_list[x_coor][y_coor][bs_index]
                    if bs_no == -1:
                        break
                    val = utd_for_a_specific_time_slot[x_coor][y_coor] / self.service_rate[bs_no][x_coor][y_coor]
                    nominal_service_rate[x_coor][y_coor][bs_index] = val

    def create_nominal_service_rate(self, tr):
        """ create the most important parameter to choose bses to sleep
        """
        snapshot = Snapshot()
        # self.sanity_check_traffic(self.tr)
        can_bs_list_len = self.can_bs_list.shape[2]
        print("create_nominal_service_rate starts at:{}".format(datetime.now()))
        nsr = np.array([[[[self.NON_RECEIVED_SIGNAL_BOUND for x in range(can_bs_list_len)]
                          for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                         for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                        for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY * NUMBER_OF_SIMULATION_DAY)], dtype='float32')
        for day in range(NUMBER_OF_SIMULATION_DAY):
            if day % 10 == 0:
                print("Prepare traffic ratio:: day:{} time:{}".format(day, datetime.now()))
            for time_slot in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                configuration_no = day * NUMBER_OF_TIME_SLOT_IN_ONE_DAY + time_slot
                utd_for_a_specific_time_slot = tr.get_user_traffic_demand_in_a_specif_time_slot(day, time_slot)
                self.__create_nominal_service_rate(utd_for_a_specific_time_slot, nsr[configuration_no])

        # self.sanity_check_nsr_and_sorted_nsr(nsr, sorted_nsr)
        min_val = np.amin(nsr)
        max_val = np.amax(nsr)
        print("min:{} max:{}".format(min_val, max_val))

        snapshot.save_nominal_service_rate(nsr)

        print("create_nominal_service_rate ends at:{}".format(datetime.now()))

    def create_nominal_service_rate_max(self, tr):
        """ create the most important parameter to choose bses to sleep
        """
        snapshot = Snapshot()
        can_bs_list_len = self.can_bs_list.shape[2]
        print("create_nominal_service_rate starts at:{}".format(datetime.now()))
        nsr = np.array([[[self.NON_RECEIVED_SIGNAL_BOUND for x in range(can_bs_list_len)]
                         for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                        for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)])
        tr_max = tr.get_max_user_traffic_demand()
        self.__create_nominal_service_rate(tr_max, nsr)
        snapshot.save_nominal_service_rate(nsr)


class CityAfterDeployment(City):
    """This class is responsible to update the city data after the fossil deployment

     * Main class creates the CityOperator with fossilDeployment parameter.
     * City is saved by save_city_operator() method
     * The class load with load_city_operator() method and used by the FossilOperator() and RenewableOperator() methods.

    """

    def __init__(self, fossil_deployment, tr):
        (self.bs_count, self.bs_locations, self.service_rate, self.assigning,
         self.bs_types) = self.__foundation_of_the_new_city(
            fossil_deployment.c,
            fossil_deployment)
        self.create_candidate_bs_list()
        self.create_nominal_service_rate(tr)

    def get_macro_micro_list(self):
        macro_group = []
        micro_group = []
        for i in range(len(self.bs_types)):
            if self.bs_types[i] == BSType.MICRO:
                micro_group.append(i)
            else:
                macro_group.append(i)
        return macro_group, micro_group

    def get_macro_micro_list_as_numpy_arrays(self):
        macro_group = np.array([0 for x in range(len(self.bs_types))])
        micro_group = np.array([0 for x in range(len(self.bs_types))])
        for i in range(len(self.bs_types)):
            if self.bs_types[i] == BSType.MICRO:
                micro_group[i] = True
            else:
                macro_group[i] = True
        return macro_group, micro_group

    def create_candidate_bs_list(self):
        sr = self.service_rate
        b = 1 / sr
        b = np.transpose(b, axes=(1, 2, 0))
        sorted_nsr = np.argsort(b, axis=2)
        max_count = 0
        for x_coor in range(len(sr[0])):
            for y_coor in range(len(sr[0][0])):
                count = 0
                for bs_index in range(len(sr)):
                    if sr[bs_index][x_coor][y_coor] != INFINITELY_SMALL:
                        count += 1
                        if count > max_count:
                            max_count = count

        self.can_bs_list = np.array([[[-1 for x in range(max_count)]
                                      for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                     for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)])
        for x_coor in range(len(sr[0])):
            for y_coor in range(len(sr[0][0])):
                for sorted_count in range(CityBeforeDeployment.BS_CANDIDATE_COUNT):
                    bs_no = sorted_nsr[x_coor][y_coor][sorted_count]
                    if self.service_rate[bs_no][x_coor][y_coor] == INFINITELY_SMALL:
                        break
                    self.can_bs_list[x_coor][y_coor][sorted_count] = bs_no

    def __foundation_of_the_new_city(self, cty_gen, fossil_deployment):
        bs_locations_temp = np.array([(-1, -1) for x in range(cty_gen.bs_count)])
        bs_types_temp = np.array([0 for x in range(cty_gen.bs_count)])
        service_rate_temp = np.empty_like(cty_gen.service_rate)
        bs_new_index = 0
        new_assigning = np.array(
            [[-1 for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)] for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)])
        bs_index_look_up_table = [-1 for x in range(cty_gen.bs_count)]
        for bs_order in range(cty_gen.bs_count):
            if fossil_deployment.bs_deployed_and_active[bs_order]:
                bs_locations_temp[bs_new_index] = CoordinateConverter.get_xy(bs_order)
                if self.is_macro_loc(bs_locations_temp[bs_new_index]):
                    bs_types_temp[bs_new_index] = BSType.MACRO
                else:
                    bs_types_temp[bs_new_index] = BSType.MICRO
                service_rate_temp[bs_new_index] = cty_gen.service_rate[bs_order]
                bs_index_look_up_table[bs_order] = bs_new_index
                bs_new_index += 1
            '''
            remove_list_after_diagnose = [12, 28, 64, 71, 90, 27, 13, 44]
            if bs_new_index in remove_list_after_diagnose:
                print bs_index
                pass
            '''
        bs_locations = np.array([(-1, -1) for x in range(bs_new_index)])  # we create new bs_locations and service_rate because
        bs_types = np.array([-1 for x in range(bs_new_index)])
        service_rate = np.array(  # sizeof bs_locations_temp and service_rate_temp larger than bs_new_index
            [[[City.NON_RECEIVED_SIGNAL_BOUND for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
              for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
             for x in range(bs_new_index)])
        for i in range(bs_new_index):
            bs_locations[i] = bs_locations_temp[i]
            service_rate[i] = service_rate_temp[i]
            bs_types[i] = bs_types_temp[i]

        for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):  # reassign the locations from old bs_indexes to new bs_indexes
            for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                old_bs_index = fossil_deployment.assigning[x_coor][y_coor]
                new_assigning[x_coor][y_coor] = bs_index_look_up_table[old_bs_index]
        return bs_new_index, bs_locations, service_rate, new_assigning, bs_types


class CityBeforeDeployment(City):
    """This class is represented a city in which bses are deployed uniformly

     * __init__ creates the CityBeforeDeployment and then it gives this object to the FossilDeployment object.
     * FossilDeployment using the following fields:
        * max user_traffic_demand field in the traffic module (tr).
        * service_rate  which is created by its own method __get_service_rate_table (with the Transmitter module)
        * bs_candidate locations  which is created by its own method __get_bs_candidate_locations.
    """
    BS_CANDIDATE_COUNT = CoordinateConverter.GRID_COUNT

    def __init__(self, tr):
        self.bs_count = self.BS_CANDIDATE_COUNT
        self.service_rate = self.__get_service_rate_table()
        b = 1 / self.service_rate
        b = np.transpose(b, axes=(1, 2, 0))
        self.can_bs_list = np.argsort(b, axis=2)
        self.create_nominal_service_rate_max(tr)

    def __get_service_rate_table(self):
        service_rate = np.array([[[self.NON_RECEIVED_SIGNAL_BOUND for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                  for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                 for x in range(self.BS_CANDIDATE_COUNT)])
        macro_bs_transmitter = Transmitter(CoordinateConverter.GRID_WIDTH, BSType.MACRO)  # BSType.MACRO MAX_TX_POWER: 20
        micro_bs_transmitter = Transmitter(CoordinateConverter.GRID_WIDTH, BSType.MICRO)  # BSType.MICRO MAX_TX_POWER: 6.3
        for x_coor in range(0, CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
            for y_coor in range(0, CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                bs_coor = (x_coor, y_coor)
                bs_candidate_index = CoordinateConverter.get_coor(x_coor, y_coor)
                if self.is_macro_loc(bs_coor):
                    macro_bs_transmitter.calculate_service_rate_overall(service_rate[bs_candidate_index], bs_coor,
                                                                        CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)
                else:
                    micro_bs_transmitter.calculate_service_rate_overall(service_rate[bs_candidate_index], bs_coor,
                                                                        CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)
        return service_rate


