"""Helpers Module.
Common Modules used by several projects/modules

"""

__author__ = 'turgay.pamuklu'

import numpy as np


class SHC(object):  # SimulationHistoryConstants
    LIST_OF_MONTHS_IN_A_YEAR = range(1, 13)
    COMMON_BATTERY_RECORDS = ['m', 'd', 'h', 'he']
    BATTERY_RECORDS_FOR_EACH_CONF = ['abc', 'fec', 'rec', 'we']
    NUMBER_OF_DAYS_IN_MONTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class SaatliMaarifTakvimi(object):
    def __init__(self):
        self.month_of_the_year = 0
        self.day_of_the_month = 1
        self.hour_of_the_day = -1
        self.season = 0

    def yapragi_kopar(self):
        self.hour_of_the_day += 1
        if self.hour_of_the_day == 24:
            self.hour_of_the_day = 0
            self.day_of_the_month += 1
        if self.day_of_the_month > SHC.NUMBER_OF_DAYS_IN_MONTHS[self.month_of_the_year]:
            self.day_of_the_month = 1
            self.month_of_the_year += 1
            if self.month_of_the_year % 3 == 0:
                self.season += 1
            if self.month_of_the_year == 12:
                self.month_of_the_year = 0
                self.season = 0



class CoordinateConverter(object):
    CITY_EDGE = 3000  # 3km
    GRID_WIDTH = 75  # 40
    GRID_COUNT_IN_ONE_EDGE = int(CITY_EDGE / GRID_WIDTH)
    GRID_COUNT = GRID_COUNT_IN_ONE_EDGE * GRID_COUNT_IN_ONE_EDGE

    @staticmethod
    def get_xy_for_cplex(j):
        j -= 1  # cplex starts the index from 1
        return CoordinateConverter.get_xy(j)

    @staticmethod
    def get_xy(j):
        x_coor = j / CoordinateConverter.GRID_COUNT_IN_ONE_EDGE
        y_coor = j % CoordinateConverter.GRID_COUNT_IN_ONE_EDGE
        return x_coor, y_coor

    @staticmethod
    def get_coor(x_coor, y_coor):
        return x_coor * CoordinateConverter.GRID_COUNT_IN_ONE_EDGE + y_coor

    @staticmethod
    def get_coor_for_gams(x_coor, y_coor):
        return x_coor * CoordinateConverter.GRID_COUNT_IN_ONE_EDGE + y_coor + 1

    @staticmethod
    def get_bs_index_rfs(x_coor, y_coor):
        if x_coor == 2 and y_coor == 2:
            return 0
        else:
            return x_coor * CoordinateConverter.GRID_COUNT_IN_ONE_EDGE + y_coor + 1

    @staticmethod
    def get_size_of_coor():
        return CoordinateConverter.GRID_COUNT_IN_ONE_EDGE * CoordinateConverter.GRID_COUNT_IN_ONE_EDGE

    @staticmethod
    def get_distance_between_two_bs(coor1, coor2):
        row1 = coor1[0]
        row2 = coor2[0]
        column1 = coor1[1]
        column2 = coor2[1]
        distance = np.sqrt((row1 - row2) ** 2 + (column1 - column2) ** 2)
        return distance
