"""Base Station Module.
The Classes in this module are responsible for simulating a base station.

"""

import numpy as np

from constants import *


class Transmitter:
    """This class represents the transmitter of a base station.

    * It is created by the CityGenerator Class at its initial step.
    * The CityGenerator Class calls the get_path_loss_table method to get the signal strength table.

    """
    BANDWIDTH = 20000000  # Hz
    NOISE = -174.0  # dBm
    MIN_RX_POWER = -120  # it changes the range of the transmitter.
    grid_width = None  # this parameter is the unit value of a one grid width it is given by the city Obj.

    def __init__(self, grid_width, bs_type):
        """Transmitter class initial method.
        It sets the grid_width field.
        """
        self.bs_type = bs_type
        if self.bs_type == BSType.MACRO:
            self.tx_power = 10 * np.log10(20 * 1000)  # 20W --> 20000 mW
        else:
            self.tx_power = 10 * np.log10(6.3 * 1000)  # 6.3W --> 6300 mW

        self.grid_width = grid_width
        self.range_table = self.__get_path_loss_table()

    @staticmethod
    def __is_in_range(coor, grid_count_in_one_edge):
        for i in coor:  # both for x and y coordinates
            if i < 0 or i >= grid_count_in_one_edge:
                return False
        return True

    @staticmethod
    def __get_grid_distance(row, column):
        """This function calculates the distance between point(row, column) and the origin.
        """
        distance = np.sqrt(row ** 2 + column ** 2)
        if distance == 0:  # if the grid is the origin itself make it minimum distance
            distance = 0.5
        return distance

    @staticmethod
    def __write_path_loss(range_table, max_range_in_a_line, row, column, path_loss):
        """This function assigns the path_loss value to the each side of the origin.
        In this table the origin is at the (max_range_in_a_line, max_range_in_a_line)
        """
        range_table[max_range_in_a_line + row][max_range_in_a_line + column] = path_loss
        range_table[max_range_in_a_line - row][max_range_in_a_line + column] = path_loss
        range_table[max_range_in_a_line + row][max_range_in_a_line - column] = path_loss
        range_table[max_range_in_a_line - row][max_range_in_a_line - column] = path_loss

    @staticmethod
    def __get_max_range():
        """This function returns the value 20. Normally it should be calculate maximum range which depends on the
        TX_POWER and MIN_RX_POWER.
        """
        # max_path_loss = self.MIN_RX_POWER - self.tx_power
        # max_distance_logarithmic = (max_path_loss - 19.1) / 43.3
        # max_real_distance = 10 ** max_distance_logarithmic
        # max_grid_distance = max_real_distance / self.grid_width
        # return (max_grid_distance+20)
        if JOURNAL3:
            return 5
        else:
            return 20

    def __get_path_loss(self, grid_distance):
        """This function returns the path_loss value of the distance which is given as a parameter.
        """
        real_distance = grid_distance * self.grid_width
        if self.bs_type == BSType.MACRO:
            path_loss = - (19.124 + 39.086 * np.log10(real_distance))
            # path_loss = -(19.1 + 43.3 * np.log10(real_distance))
        else:
            path_loss = - (29.948 + 36.7 * np.log10(real_distance))
            # path_loss = - (32.58 + 36.7 * np.log10(real_distance))
        return path_loss

    def __get_path_loss_table(self):
        """This function returns the path loss values table
        """
        max_range = self.__get_max_range()  # it returns the value 20
        max_range_in_a_line = int(np.around(max_range + 0.5))  # it assigns the value 20
        matrix_edge = 14
        range_table = np.array([[self.NOISE for x in range(matrix_edge)] for x in range(matrix_edge)])
        # create a path_loss_table which fills by the INFINITELY_SMALL values
        for row in range(max_range_in_a_line + 2):
            for column in range(max_range_in_a_line + 2):  # for each grid
                grid_distance = self.__get_grid_distance(row, column)  # get the distance
                path_loss = self.__get_path_loss(grid_distance)  # get the path_loss for this grid
                if self.tx_power + path_loss >= self.MIN_RX_POWER:  # if signal is enough for receiving by the grid
                    self.__write_path_loss(range_table, max_range_in_a_line, row, column, path_loss)  # set the value
        return range_table

    def calculate_service_rate_overall(self, service_rate, bs_coor, grid_count_in_one_edge):
        edge_size_of_the_range_table = self.range_table.shape[0]
        for x_r in range(edge_size_of_the_range_table + 1):
            for y_r in range(edge_size_of_the_range_table + 1):
                origin = int((edge_size_of_the_range_table - 1) / 2)
                r_coor = (x_r - origin, y_r - origin)
                abs_coor = (bs_coor[0] + r_coor[0], bs_coor[1] + r_coor[1])
                if self.__is_in_range(abs_coor, 5) is True:
                    if service_rate[abs_coor[0]][abs_coor[1]] != INFINITELY_SMALL:
                        raise Exception("Houston we have a problem: we have a location that is already serviced by another BS!!")
                    service_rate[abs_coor[0]][abs_coor[1]] = self.__get_service_rate(x_r, y_r)

    def __get_service_rate(self, x_r, y_r):
        INTERFERENCE_METHOD = False
        path_loss = self.range_table[x_r][y_r]
        if path_loss == self.NOISE:  # for a better diagnosing of data
            shannon_cap = INFINITELY_SMALL
        else:
            rx_power = self.tx_power + path_loss
            if INTERFERENCE_METHOD:
                # return rx power only!!
                shannon_cap = rx_power
            else:
                snr_db = rx_power - self.NOISE
                snr = 10 ** (snr_db / 10)
                spectral_eff = np.log10(1.0 + snr) / np.log10(2)
                shannon_cap = self.BANDWIDTH * spectral_eff

        return shannon_cap
