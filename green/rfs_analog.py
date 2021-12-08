"""Rfs Module.
Uncompleted/Cancelled RFS Journal Implementation (Journal 2).

"""

from datetime import datetime

import numpy as np

from baseStation import Transmitter
from helpers import CoordinateConverter
from snapshot import *


class RfsAnalog:
    def __init__(self, n_of_cell_per_ec, n_of_ec, n_of_ue_per_ec, traffic_scen):
        self.traffic_scen = traffic_scen
        self.n_of_cell_per_ec = n_of_cell_per_ec
        self.n_of_ec = n_of_ec
        self.n_of_ue_per_ec = n_of_ue_per_ec
        self.edge_size_of_a_ec_zone = int(np.sqrt(self.n_of_ue_per_ec))
        self.rfs_nsr = np.array([[[INFINITELY_SMALL for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
                                  for x in range(self.n_of_cell_per_ec)]
                                 for x in range(self.n_of_ue_per_ec * self.n_of_ec)], dtype='float32')

        self.bs_coors = list(range(n_of_cell_per_ec))
        self.bs_coors[0] = (2, 2)
        self.bs_coors[1] = (0, 0)
        self.bs_coors[2] = (0, 4)
        self.bs_coors[3] = (4, 4)
        self.bs_coors[4] = (4, 0)

        self.service_rate = self.__get_service_rate_table()
        self.service_rate *= BITSEC_2_MBYTEHOUR
        pass

    def _get_coordinate_of_a_user_by_index(self, user_nominal_index):
        x_coor = int(user_nominal_index / self.edge_size_of_a_ec_zone)
        y_coor = int(user_nominal_index % self.edge_size_of_a_ec_zone)
        return x_coor, y_coor

    def create_rfs_nsr(self):
        snapshot = Snapshot()
        snapshot.set_traffic_scen_folder(self.traffic_scen)
        tr, threshold = snapshot.load_tr_cran()
        print("create_nominal_service_rate starts at:{}".format(datetime.now()))
        # In a Loop
        for ec_index in range(self.n_of_ec):
            for user_in_ec in range(ec_index, (1 + ec_index) * self.n_of_ue_per_ec):
                user_nominal_index = int(user_in_ec % self.n_of_ue_per_ec)
                x_coor, y_coor = self._get_coordinate_of_a_user_by_index(user_nominal_index)
                tr_of_a_user = tr[user_in_ec]
                number_of_time_slot = len(tr_of_a_user)
                for t in range(number_of_time_slot):
                    for bs_index in range(self.n_of_cell_per_ec):
                        val = tr_of_a_user[t] / self.service_rate[bs_index][x_coor][y_coor]
                        self.rfs_nsr[user_in_ec][bs_index][t] = val

        snapshot.save_nominal_service_rate(self.rfs_nsr)

    def __get_service_rate_table(self):
        n_of_user_in_one_side = 5
        service_rate = np.array([[[INFINITELY_SMALL for x in range(n_of_user_in_one_side)]
                                  for x in range(n_of_user_in_one_side)]
                                 for x in range(self.n_of_cell_per_ec)])
        macro_bs_transmitter = Transmitter(CoordinateConverter.GRID_WIDTH, BSType.MACRO)  # BSType.MACRO MAX_TX_POWER: 20
        micro_bs_transmitter = Transmitter(CoordinateConverter.GRID_WIDTH, BSType.MICRO)  # BSType.MICRO MAX_TX_POWER: 6.3

        for bs_index in range(self.n_of_cell_per_ec):
            bs_coor = self.bs_coors[bs_index]
            if bs_index == 0:
                macro_bs_transmitter.calculate_service_rate_overall(service_rate[bs_index], bs_coor, None)
            else:
                micro_bs_transmitter.calculate_service_rate_overall(service_rate[bs_index], bs_coor, None)
        return service_rate
