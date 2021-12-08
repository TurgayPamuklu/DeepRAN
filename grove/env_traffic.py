""" traffşc module.
Classes in this module are responsible for user traffic.

"""

import math
import random

import matplotlib.pyplot as plt
from matplotlib import rcParams

from helpers import *

PEAK_TRAFFIC_PER_EMBB = 1.0
PEAK_TRAFFIC_PER_URLLC = 0.1
EMBB_SAME_PATTERN = True


class Traffic:
    """ This class creates a user traffic.
    """

    @staticmethod
    def create_and_save_traffic(ts=1):
        snapshot = Snapshot()
        snapshot.set_traffic_data_path(ts)
        traffic_load = np.array([[[[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
                                   for x in range(NUMBER_OF_SIMULATION_DAY)]
                                  for x in range(N_OF_PACKET_TYPE)]
                                 for x in range(N_OF_EC)], dtype='float')
        for k in range(N_OF_EC):
            # urllc, embb = Traffic.get_traffic_pattern_poisson()
            urllc, embb = Traffic.get_traffic_pattern_seasonal_change()
            traffic_load[k][PacketType.URLLC] = urllc
            traffic_load[k][PacketType.EMBB] = embb
        snapshot.save_tr(traffic_load)

    @staticmethod
    def get_traffic_pattern_poisson():
        PEAK_TRAFFIC_RATE = 1.0
        ABRUPTNESS_OF_THE_TRAFFIC = 3  # 1, 3 or 5
        peak_hour_definer = random.random() * math.pi + 3 * math.pi / 4
        one_day = [0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
        embb = np.array([[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
                         for x in range(NUMBER_OF_SIMULATION_DAY)], dtype='float')
        urllc = np.array([[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
                          for x in range(NUMBER_OF_SIMULATION_DAY)], dtype='float')
        for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            one_day[time_interval] = ((PEAK_TRAFFIC_RATE / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                                      (1 + math.sin(math.pi * time_interval / (
                                              NUMBER_OF_TIME_SLOT_IN_ONE_DAY / 2)
                                                    + peak_hour_definer)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        for number_of_day in range(0, NUMBER_OF_SIMULATION_DAY):
            for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                poisson = (np.random.poisson(10)) / 140.0  # create a poisson random value
                urllc[number_of_day][time_interval] = (one_day[time_interval] + poisson) * PEAK_TRAFFIC_PER_URLLC
                embb[number_of_day][time_interval] = (one_day[time_interval] + poisson) * PEAK_TRAFFIC_PER_EMBB
        return urllc, embb

    @staticmethod
    def plt_traffic_in_a_year_period(traffic_data):
        rcParams['pdf.fonttype'] = 42
        rcParams['ps.fonttype'] = 42
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        traffic_data *= 10
        ax.plot(traffic_data)
        ax.set_xlim((0, 364))
        fig.tight_layout()
        plt.xlabel('Days of a Year', fontsize=16)
        plt.ylabel('Normalized Traffic Load', fontsize=16)
        plt.show()
        fig.savefig("../figures/" + 'traffic.pdf', format='pdf', bbox_inches='tight')

    @staticmethod
    def calculate_seasonal_decay():
        OFFSET = 1.0
        PEAK_TRAFFIC_RATE_1 = 0.25
        PEAK_TRAFFIC_RATE_2 = 0.25
        ABRUPTNESS_OF_THE_TRAFFIC = 9  # 1, 3 or 5
        peak_day_definer_1 = 9
        peak_day_definer_2 = 270
        summer_decay = np.array([0 for x in range(NUMBER_OF_SIMULATION_DAY)], dtype='float')
        for number_of_day in range(0, NUMBER_OF_SIMULATION_DAY):
            summer_decay[number_of_day] = ((PEAK_TRAFFIC_RATE_1 / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                                           (1 + math.sin(math.pi * number_of_day / (
                                                   NUMBER_OF_SIMULATION_DAY / 2)
                                                         + peak_day_definer_1)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        for number_of_day in range(0, NUMBER_OF_SIMULATION_DAY):
            summer_decay[number_of_day] += (1 - PEAK_TRAFFIC_RATE_2) + ((PEAK_TRAFFIC_RATE_2 / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                                                                        (1 + math.sin(math.pi * number_of_day / (
                                                                                NUMBER_OF_SIMULATION_DAY / 2)
                                                                                      + peak_day_definer_2)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        # Traffic.plt_traffic_in_a_year_period(summer_decay)
        # print(summer_decay)
        return summer_decay

    @staticmethod
    def get_average_traffic(traffic_load):
        return_value = np.array([[[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
                                  for x in range(N_OF_PACKET_TYPE)]
                                 for x in range(N_OF_EC)], dtype='float')
        for r in range(N_OF_EC):
            for i in range(N_OF_PACKET_TYPE):
                for number_of_day in range(0, NUMBER_OF_SIMULATION_DAY):
                    for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                        return_value[r][i][time_interval] += traffic_load[r][i][number_of_day][time_interval]
        for r in range(N_OF_EC):
            for i in range(N_OF_PACKET_TYPE):
                for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    return_value[r][i][time_interval] = return_value[r][i][time_interval] / NUMBER_OF_SIMULATION_DAY
        return return_value

    @staticmethod
    def get_traffic_pattern_seasonal_change():
        PEAK_TRAFFIC_RATE = 1.0
        ABRUPTNESS_OF_THE_TRAFFIC = 7  # 1, 3 or 5
        peak_hour_definer = random.random() * math.pi + 3 * math.pi / 4
        one_day_urllc = [0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
        one_day_embb = [0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
        embb = np.array([[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
                         for x in range(NUMBER_OF_SIMULATION_DAY)], dtype='float')
        urllc = np.array([[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
                          for x in range(NUMBER_OF_SIMULATION_DAY)], dtype='float')
        for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            one_day_urllc[time_interval] = ((PEAK_TRAFFIC_RATE / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                                            (1 + math.sin(math.pi * time_interval / (
                                                    NUMBER_OF_TIME_SLOT_IN_ONE_DAY / 2)
                                                          + peak_hour_definer)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        if EMBB_SAME_PATTERN:
            one_day_embb = one_day_urllc
        else:
            for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                one_day_embb[time_interval] = ((PEAK_TRAFFIC_RATE / (2 ** ABRUPTNESS_OF_THE_TRAFFIC)) *
                                               (1 + math.sin(math.pi * time_interval / (
                                                       NUMBER_OF_TIME_SLOT_IN_ONE_DAY / 2)
                                                             + peak_hour_definer)) ** ABRUPTNESS_OF_THE_TRAFFIC)
        summer_decay = Traffic.calculate_seasonal_decay()
        for number_of_day in range(0, NUMBER_OF_SIMULATION_DAY):
            for time_interval in range(0, NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                poisson = (np.random.poisson(10)) / 140.0  # create a poisson random value
                urllc[number_of_day][time_interval] = (one_day_urllc[time_interval] + poisson) * PEAK_TRAFFIC_PER_URLLC * summer_decay[number_of_day]
                embb[number_of_day][time_interval] = (one_day_embb[time_interval] + poisson) * PEAK_TRAFFIC_PER_EMBB * summer_decay[number_of_day]
        return urllc, embb
