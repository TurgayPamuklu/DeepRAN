"""Traffic Module.
This module contains only one class which is used to create a random user traffic.

"""

import math
import random

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

from constants import *

__author__ = 'turgay.pamuklu'


INPUT_FOLDER = '../input/'
MIN_USER_DEMAND = 10


class CityMapGenerator:
    gcioe = None
    EXTRA_RANDOM_SCEN = 10

    def __init__(self, gcioe):
        self.gcioe = gcioe

    def get_new_city_zones(self, zone_count, traffic_scen):

        random.seed(traffic_scen+3+self.EXTRA_RANDOM_SCEN)

        # ------------------------------
        number_of_hot_points = 2 * zone_count
        number_of_samples = 10000
        x_axis = [0 for x in range(number_of_hot_points)]
        y_axis = [0 for x in range(number_of_hot_points)]
        X = [0 for x in range(number_of_hot_points)]
        Y = [0 for x in range(number_of_hot_points)]
        values = [0 for x in range(number_of_hot_points)]
        positions = [0 for x in range(number_of_hot_points)]
        kernel = [0 for x in range(number_of_hot_points)]
        distribution_on_grid = [0 for x in range(number_of_hot_points)]
        for i in range(number_of_hot_points):
            meanvalue_x = 1
            modevalue_x = np.sqrt(2 / np.pi) * meanvalue_x
            meanvalue_y = 1
            modevalue_y = np.power(2 / np.pi, 1 / (i + 2)) * meanvalue_y
            x_axis[i] = np.random.rayleigh(10, number_of_samples)
            y_axis[i] = np.random.rayleigh(0.001, number_of_samples)

            X[i], Y[i] = np.mgrid[x_axis[i].min():x_axis[i].max():self.gcioe * 1j, y_axis[i].min():y_axis[i].max():self.gcioe * 1j]
            positions[i] = np.vstack([X[i].ravel(), Y[i].ravel()])
            values[i] = np.vstack([x_axis[i], y_axis[i]])

            kernel[i] = stats.gaussian_kde(values[i])
            distribution_on_grid[i] = np.reshape(kernel[i](positions[i]).T, X[i].shape)

            # '''
            if i == 6:
                distribution_on_grid[i] = np.rot90(distribution_on_grid[i])
            if i == 7:
                distribution_on_grid[i] = np.fliplr(distribution_on_grid[i])
            if i == 8:
                distribution_on_grid[i] = np.flipud(distribution_on_grid[i])
            # '''
            #'''
            if i == 0:
                x_offset = 0  # random.randint(0, self.gcioe/2)
                y_offset = 0  # random.randint(0, self.gcioe/2)
            elif i == 1:
                x_offset = 3
                y_offset = 20
            elif i == 2:
                x_offset = 20
                y_offset = 20
            elif i == 3:
                x_offset = 10
                y_offset = 13
            elif i == 4:
                x_offset = 22
                y_offset = 0
            else:
            # '''
                x_offset = random.randint(0, self.gcioe/2)
                y_offset = random.randint(0, self.gcioe/2)

            temp_copy = np.copy(distribution_on_grid[i])
            row_size = int(self.gcioe)
            for x_index in range(row_size):
                for y_index in range(row_size):
                    distribution_on_grid[i][x_index][y_index] = temp_copy[(x_index - x_offset) % row_size][(y_index - y_offset) % row_size]
                    #if distribution_on_grid[i][x_index][y_index] < self.gcioe/(8-i):
                    #    distribution_on_grid[i][x_index][y_index] = 0

        distribution_combined = [[0 for x in range(row_size)] for x in range(row_size)]
        zone_dist_general = [[0 for x in range(row_size)] for x in range(row_size)]
        for x_index in range(row_size):
            for y_index in range(row_size):
                for i in range(0, len(distribution_on_grid)):
                    if distribution_on_grid[i][x_index][y_index] > distribution_combined[x_index][y_index]:
                        distribution_combined[x_index][y_index] = distribution_on_grid[i][x_index][y_index]
                        zone_dist_general[x_index][y_index] = (i % 5) + 1

        for x_index in range(row_size):
            for y_index in range(row_size):
                if self.__is_in_border((x_index, y_index)):
                    zone_dist_general[x_index][y_index] = 0
        for x_index in range(row_size):
            for y_index in range(row_size):
                if zone_dist_general[x_index][y_index] == 0:
                    distribution_combined[x_index][y_index] = 0

        return zone_dist_general, distribution_combined

    def __is_in_border(self, coordinates):
        for i in coordinates:  # both for x and y coordinates
            if i < 3 or i >= self.gcioe - 3:
                return True
        return False

    def __is_in_range(self, coordinates):
        for i in coordinates:  # both for x and y coordinates
            if i < 0 or i >= self.gcioe:
                return False
        return True


def calculate_ones_in_a_matrix(f1):
    """Not Used.
    """
    macro_one = 0
    for x in range(300):
        total_one = 0
        for y in range(300):
            if f1[x][y] == 1:
                total_one += 1
            elif f1[x][y] != 0:
                raise Exception("Houston we have a problem: SW Bug!!")
        print("number of 1 in the row " + str(x) + " is:" + str(total_one))
        macro_one += total_one
    print("macro_one is:" + str(macro_one))


def show_matrix(f2):
    plt.imshow(f2)
    plt.show()


class Traffic:
    """This class creates a user traffic.

    * It is called by Main.
    * It is created a random traffic when it is called.
    * It uses:

        * a bmp image which represents the user distribution
        * __get_a_random_traffic_pattern_for_one_day method for simulating random distributions of the traffic.

    * Main Class save this object with save_tr() method.
    * create_city_and_fossil_deployment call load_tr() to load saved Traffic Object.
    * create_city_and_fossil_deployment initializes CityGenerator with the Traffic Object.
    * CityGenerator call:

        * self.user_traffic_demand_for_sim_duration = tr.get_traffic()
        * self.max_user_traffic_demand = tr.get_max_user_traffic_demand()

    methods to get user_traffic_demand_for_sim_duration matrices (grid_x, grid_y, time_slot_of_the_current_day)

    INITIAL METHOD:

    * Saves the initialization parameters:

        * number_of_time_frames_in_one_day: 24 for one hour time slices
        * grid_count_in_one_edge: depends on the working region

    * It calls __calculate_user_traffic_demand_for_one_year() method for the whole needed methods

    """
    IMG_SZ = 300
    gcioe = None
    ZONE_COUNT = 5
    user_traffic_demand_for_one_year = None
    max_user_traffic_demand = None
    BASED_USER_TRAFFIC_VALUE = 350.0  # 750  # old one ise 25000
    # 3000 should be maximum value of user traffic
    max_user_traffic_value = None

    zone_dist = None

    def __init__(self, grid_count_in_one_edge, traffic_scen):
        self.traffic_scen = traffic_scen
        self.max_user_traffic_value = self.BASED_USER_TRAFFIC_VALUE
        self.gcioe = grid_count_in_one_edge
        cg = CityMapGenerator(self.gcioe)
        self.zone_dist, self.kernel_distribution = cg.get_new_city_zones(self.ZONE_COUNT, traffic_scen)
        self.user_traffic_demand_for_one_year = np.array([[[[0 for x in range(self.gcioe)]
                                                            for x in range(self.gcioe)]
                                                           for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
                                                          for x in range(NUMBER_OF_SIMULATION_DAY)], dtype=float)
        self.max_user_traffic_demand = np.array([[0 for x in range(self.gcioe)]
                                                 for x in range(self.gcioe)], dtype=float)
        self.__calculate_user_traffic_demand_for_one_year_new()
        self.__calculate_mean_user_traffic_demand()

    def get_max_user_traffic_demand(self):
        return self.max_user_traffic_demand

    def get_user_traffic_demand_for_sim_duration(self):
        return self.user_traffic_demand_for_one_year

    def get_user_traffic_demand_in_a_specif_time_slot(self, day, time_slot):
        return self.user_traffic_demand_for_one_year[day][time_slot]

    def __get_a_random_traffic_pattern_for_one_day(self):
        """This method creates traffic patterns for a day period which represents the user mobile usage.
    """
        PEAK_TRAFFIC_RATE = 0.5  # it is between (0,1)
        ABRUPTNESS_OF_THE_TRAFFIC = 3  # 1, 3 or 5
        peak_hour_definer = random.random() * math.pi + 3 * math.pi / 4
        result = []
        for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            result.append((PEAK_TRAFFIC_RATE / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                          (1 + math.sin(math.pi * time_interval / (
                              NUMBER_OF_TIME_SLOT_IN_ONE_DAY / 2) + peak_hour_definer)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        return result

    def __get_kernel_distribution_from_location(self, x_axis, y_axis):
        return self.kernel_distribution[x_axis][y_axis]

    def __get_zone_number_from_location(self, x_axis, y_axis):
        return self.zone_dist[x_axis][y_axis]

    def __calculate_user_traffic_demand_for_one_year_new(self):
        traffic_rate_of_one_day = [[] for x in range(self.ZONE_COUNT)]
        user_arrival_rate_of_one_year = [
            [[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(self.ZONE_COUNT)] for x in
            range(NUMBER_OF_SIMULATION_DAY)]
        for index in range(0, self.ZONE_COUNT):  # create 5 different user traffic for one day
            traffic_rate_of_one_day[index] = self.__get_a_random_traffic_pattern_for_one_day()
        for i in range(NUMBER_OF_SIMULATION_DAY):  # for each day
            for j in range(self.ZONE_COUNT):  # for each ZONE_COUNT
                for k in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):  # for each time frame
                    user_arrival_rate_of_one_year[i][j][k] = self.traffic_scen * (np.random.poisson(traffic_rate_of_one_day[j][k] * 60))  # create a poisson arrival rate

        for i in range(NUMBER_OF_SIMULATION_DAY):
            for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                for x_axis in range(self.gcioe):
                    for y_axis in range(self.gcioe):
                        zone_no = self.__get_zone_number_from_location(x_axis, y_axis)
                        if zone_no == 0:
                            self.user_traffic_demand_for_one_year[i][j][x_axis][y_axis] = MIN_USER_DEMAND
                        else:
                            zone_no -= 1
                            if i % 7 == 5 or i % 7 == 6:
                                data_size = 1 * 1024 * random.expovariate(1 / (self.max_user_traffic_value * 0.5))  # weekend
                            else:
                                data_size = 1 * 1024 * random.expovariate(1 / self.max_user_traffic_value)
                            self.user_traffic_demand_for_one_year[i][j][x_axis][y_axis] = data_size * user_arrival_rate_of_one_year[i][zone_no][j]
                            if self.user_traffic_demand_for_one_year[i][j][x_axis][y_axis] == 0:
                                self.user_traffic_demand_for_one_year[i][j][x_axis][
                                    y_axis] = MIN_USER_DEMAND  # to provide coverage

    def __calculate_user_traffic_demand_for_one_year(self):
        """Main method calls from the traffic init.
        """
        traffic_rate_of_one_day = [[] for x in range(self.ZONE_COUNT)]
        traffic_rate_of_one_year = [
            [[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(self.ZONE_COUNT)] for x in
            range(NUMBER_OF_SIMULATION_DAY)]
        for index in range(0, self.ZONE_COUNT):  # create 5 different user traffic for one day
            traffic_rate_of_one_day[index] = self.__get_a_random_traffic_pattern_for_one_day()

        for i in range(NUMBER_OF_SIMULATION_DAY):  # for each day
            for j in range(self.ZONE_COUNT):  # for each ZONE_COUNT
                for k in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):  # for each time frame
                    poisson = (np.random.poisson(10)) / 140.0  # create a poisson random value
                    traffic_rate_of_one_year[i][j][k] = traffic_rate_of_one_day[j][k] + poisson  # add this value to the one year

        for i in range(NUMBER_OF_SIMULATION_DAY):
            for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                for x_axis in range(self.gcioe):
                    for y_axis in range(self.gcioe):
                        zone_no = self.__get_zone_number_from_location(x_axis, y_axis)
                        if zone_no == 0:
                            self.user_traffic_demand_for_one_year[i][j][x_axis][y_axis] = MIN_USER_DEMAND
                        else:
                            zone_no -= 1
                            if i % 7 == 5 or i % 7 == 6:
                                traffic_value = self.max_user_traffic_value * self.__get_kernel_distribution_from_location(x_axis, y_axis) * 0.5  # we have lower traffic at weekend
                            else:
                                traffic_value = self.max_user_traffic_value * self.__get_kernel_distribution_from_location(x_axis, y_axis)
                            self.user_traffic_demand_for_one_year[i][j][x_axis][y_axis] = traffic_value * traffic_rate_of_one_year[i][zone_no][j]
                            if self.user_traffic_demand_for_one_year[i][j][x_axis][y_axis] == 0:
                                self.user_traffic_demand_for_one_year[i][j][x_axis][
                                    y_axis] = MIN_USER_DEMAND  # to provide coverage

    def __calculate_max_user_traffic_demand(self):
        """Calculate max traffic of a day for each grid separately.
    """
        for x_axis in range(self.gcioe):
            for y_axis in range(self.gcioe):
                max = 0
                for i in range(NUMBER_OF_SIMULATION_DAY):
                    for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                        if max < self.user_traffic_demand_for_one_year[i][j][x_axis][y_axis]:
                            max = self.user_traffic_demand_for_one_year[i][j][x_axis][y_axis]
                self.max_user_traffic_demand[x_axis][y_axis] = max

    def __calculate_mean_user_traffic_demand(self):
        """Calculate max traffic of a day for each grid separately.
    """
        mean_val_1 = np.mean(self.user_traffic_demand_for_one_year, 0)
        max_val_1 = np.max(self.user_traffic_demand_for_one_year, 0)
        mean_val_1 = (mean_val_1 * 9 + max_val_1) / 10
        mean_val_2 = np.max(mean_val_1, 0)
        self.max_user_traffic_demand = mean_val_2

    def get_max_user_traffic_demand_for_each_hours(self):
        """Calculate max traffic of a day for each grid and time slot separately.
    """
        max_user_traffic_demand_for_each_hour = np.array([[[0 for x in range(self.gcioe)]
                                                           for x in range(self.gcioe)]
                                                          for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)])
        for x_axis in range(self.gcioe):
            for y_axis in range(self.gcioe):
                for time_slot in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    max_traffic = 0
                    for i in range(NUMBER_OF_SIMULATION_DAY):
                        if max_traffic < self.user_traffic_demand_for_one_year[i][time_slot][x_axis][y_axis]:
                            max_traffic = self.user_traffic_demand_for_one_year[i][time_slot][x_axis][y_axis]
                    max_user_traffic_demand_for_each_hour[time_slot][x_axis][y_axis] = max_traffic
        return max_user_traffic_demand_for_each_hour

    @staticmethod
    def get_a_random_traffic_pattern_for_monitor():
        """This method creates traffic patterns for a day period which represents the user mobile usage.
    """
        PEAK_TRAFFIC_RATE = 0.5  # it is between (0,1)
        ABRUPTNESS_OF_THE_TRAFFIC = 3  # 1, 3 or 5
        peak_hour_definer = random.random() * math.pi + 3 * math.pi / 4
        result = []
        for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            result.append((PEAK_TRAFFIC_RATE / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                          (1 + math.sin(math.pi * time_interval / (
                              NUMBER_OF_TIME_SLOT_IN_ONE_DAY / 2) + peak_hour_definer)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            poisson = (np.random.poisson(10)) / 140.0  # create a poisson random value
            result[time_interval] += poisson
        return result

    @staticmethod
    def get_a_random_traffic_pattern(number_of_time_slot=NUMBER_OF_TIME_SLOT_IN_ONE_DAY, number_of_day=1):
        """This method creates traffic patterns for a day period which represents the user mobile usage.
    """
        PEAK_TRAFFIC_RATE = 0.5  # it is between (0,1)
        ABRUPTNESS_OF_THE_TRAFFIC = 3  # 1, 3 or 5
        peak_hour_definer = random.random() * math.pi + 3 * math.pi / 4
        result = []
        for time_interval in range(0, number_of_time_slot):
            result.append((PEAK_TRAFFIC_RATE / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                          (1 + math.sin(math.pi * time_interval / (
                                  number_of_time_slot / 2) + peak_hour_definer)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        for time_interval in range(0, number_of_time_slot):
            poisson = (np.random.poisson(10)) / 140.0  # create a poisson random value
            result[time_interval] += poisson

        result_for_more_than_one_day = [[0 for x in range(number_of_time_slot)] for x in range(number_of_day)]
        for i in range(number_of_day):  # for each day
            for k in range(number_of_time_slot):  # for each time frame
                poisson = (np.random.poisson(10)) / 140.0  # create a poisson random value
                result_for_more_than_one_day[i][k] = result[k] + poisson  # add this value to the one year
        return result_for_more_than_one_day

    @staticmethod
    def get_traffic_pattern_for_rfs(number_of_time_slot=NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
        """This method creates traffic patterns for a day period which represents the user mobile usage. """
        PEAK_TRAFFIC_RATE = 1.0  # it is between (0,1)
        ABRUPTNESS_OF_THE_TRAFFIC = 3  # 1, 3 or 5
        peak_hour_definer = random.random() * math.pi + 3 * math.pi / 4
        result = []
        for time_interval in range(0, number_of_time_slot):
            result.append((PEAK_TRAFFIC_RATE / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                          (1 + math.sin(math.pi * time_interval / (
                                  number_of_time_slot / 2) + peak_hour_definer)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        for time_interval in range(0, number_of_time_slot):
            poisson = (np.random.poisson(10)) / 140.0  # create a poisson random value
            result[time_interval] += poisson
            # result[time_interval] *= PEAK_TRAFFIC_PER_HOUR_PER_MBYTE
            # result[time_interval] *= USER_CHUNK_SIZE

        return result
