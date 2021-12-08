"""Output Module.
Methods in this module are responsible for saving/loading classes and creating pre-data for glpk.

"""
import csv

import numpy as np

from city import City
from helpers import CoordinateConverter, SaatliMaarifTakvimi
from helpers import SHC
from renewableEnergy import Battery
from snapshot import *

__author__ = 'turgay.pamuklu'


def get_j(x_coor, y_coor):
    return x_coor * City.GRID_COUNT_IN_ONE_EDGE + y_coor


POWER_CONSUMPTION_FILE = 'powerConsumption.dat'
TRAFFIC_FILE = 'trafficLoad.dat'
SERVICE_RATE_FILE = 'serviceRate.dat'
GENERATED_ENERGY_FILE = 'generatedEnergy.dat'
OUTPUT_PATH = "../output/"


class Output(object):
    @staticmethod
    def output_file_name():
        return OUTPUT_PATH + 'batt_all.csv'

    @staticmethod
    def is_the_last_location(x_coor, y_coor):
        return x_coor == (CoordinateConverter.GRID_COUNT_IN_ONE_EDGE - 1) and y_coor == (
            CoordinateConverter.GRID_COUNT_IN_ONE_EDGE - 1)

    @staticmethod
    def out_cplex(output_format='GAMS'):
        snapshot = Snapshot()
        snapshot.set_traffic_scen_folder(traffic_scenarios[0])
        f = open(OUTPUT_PATH + POWER_CONSUMPTION_FILE, 'w')
        co = snapshot.load_city_after_deployment()
        power_cons_list = [0 for x in range(co.bs_count)]
        for i in range(co.bs_count):
            if co.bs_types[i] == BSType.MICRO:
                power_cons_list[i] = Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO
            else:
                power_cons_list[i] = Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO
        if output_format is 'GAMS':
            for bs in range(co.bs_count):
                f.write("{0:<d} {1:.0f}\n".format(bs + 1, power_cons_list[bs]))
        else:
            f.write("pc = [ ")
            for bs in range(co.bs_count):
                if bs == co.bs_count - 1:
                    f.write("{0:<10.2f}\t".format(power_cons_list[bs]))
                else:
                    f.write("{0:<10.2f},\t".format(power_cons_list[bs]))
            f.write("];\n")
        f.close()

        f = open(OUTPUT_PATH + TRAFFIC_FILE, 'w')
        tr = snapshot.load_tr()

        if output_format is 'GAMS':
            u_d = tr.get_user_traffic_demand_for_sim_duration()
            for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    for i in range(NUMBER_OF_SIMULATION_DAY):
                        for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                            coor = CoordinateConverter.get_coor_for_gams(x_coor, y_coor)
                            time_slice = i * NUMBER_OF_TIME_SLOT_IN_ONE_DAY + j + 1
                            f.write("{0:<d}.{1:<d} {2:.0f}\n".format(coor, time_slice, u_d[i][j][x_coor][y_coor]))
        else:
            u_d = tr.get_user_traffic_demand_for_sim_duration()
            time_range = NUMBER_OF_TIME_SLOT_IN_ONE_DAY * NUMBER_OF_SIMULATION_DAY
            u_d_for_multiple_days = np.array([[[0 for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                               for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                              for x in range(time_range)], dtype=float)
            for day in range(NUMBER_OF_SIMULATION_DAY):
                for hour_of_a_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    u_d_for_multiple_days[day * hour_of_a_day + hour_of_a_day] = u_d[day][hour_of_a_day]

            f.write("ud = [ \n")
            for t in range(time_range):
                f.write("[\t")
                for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                        if Output.is_the_last_location(x_coor, y_coor):
                            f.write("{0:<10.2f}\t".format(u_d_for_multiple_days[t][x_coor][y_coor]))
                        else:
                            f.write("{0:<10.2f},\t".format(u_d_for_multiple_days[t][x_coor][y_coor]))
                if t == (time_range - 1):
                    f.write("]\n")
                else:
                    f.write("],\n")
            f.write("];\n")
        f.close()

        f = open(OUTPUT_PATH + SERVICE_RATE_FILE, 'w')
        co = snapshot.load_city_after_deployment()
        s_r = co.service_rate
        if output_format is 'GAMS':
            for bs in range(co.bs_count):
                for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                        coor = CoordinateConverter.get_coor_for_gams(x_coor, y_coor)
                        f.write("{0:d}.{1:d} {2:.0f}\n".format(bs + 1, coor, s_r[bs][x_coor][y_coor]))
        else:
            f.write("sr = [ \n")
            for bs in range(co.bs_count):
                f.write("[\t")
                for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                        if Output.is_the_last_location(x_coor, y_coor):
                            f.write("{0:.2f}\t".format(s_r[bs][x_coor][y_coor]))
                        else:
                            f.write("{0:.2f},\t".format(s_r[bs][x_coor][y_coor]))
                if bs == (co.bs_count - 1):
                    f.write("]\n")
                else:
                    f.write("],\n")
            f.write("];\n")
        f.close()

        f = open(OUTPUT_PATH + GENERATED_ENERGY_FILE, 'w')
        snapshot.set_solar_data_path('istanbul')
        solar_energy = snapshot.load_solar_energy()
        if output_format is 'GAMS':
            for i in range(NUMBER_OF_SIMULATION_DAY):
                for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    time_slice = i * NUMBER_OF_TIME_SLOT_IN_ONE_DAY + j + 1
                    f.write("{0:d} {1:.0f}\n".format(time_slice, solar_energy.harvest_the_solar_energy(i, j, 1)))
        else:
            f.write("ge = [ \n")
            for i in range(NUMBER_OF_SIMULATION_DAY):
                for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    f.write("{0:.2f}\t".format(solar_energy.harvest_the_solar_energy(i, j, 1)))
            f.write("];\n")
        f.close()

    @staticmethod
    def out_glpk():
        snapshot = Snapshot()
        GLPK_PATH = 'C:/Users/turgay.pamuklu/Google Drive/PhD/glpkProj/'
        snapshot.set_traffic_scen_folder(1)
        f = open(GLPK_PATH + TRAFFIC_FILE, 'w')
        tr = snapshot.load_tr()
        u_d = tr.get_user_traffic_demand_for_sim_duration()
        NUMBER_OF_SIMULATING_DAYS = 2
        u_d_for_multiple_days = np.array([[[0 for x in range(City.GRID_COUNT_IN_ONE_EDGE)]
                                           for x in range(City.GRID_COUNT_IN_ONE_EDGE)]
                                          for x in
                                          range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY * NUMBER_OF_SIMULATING_DAYS)],
                                         dtype=float)
        u_d_for_multiple_days = u_d + u_d

        f.write("param u_d :\t")
        for x_coor in range(City.GRID_COUNT_IN_ONE_EDGE):
            for y_coor in range(City.GRID_COUNT_IN_ONE_EDGE):
                j = get_j(x_coor, y_coor)
                f.write("{0:<10}\t".format(j + 1))
        f.write(":=")
        for t in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY * NUMBER_OF_SIMULATING_DAYS):
            f.write("\n{0:<10}\t".format(t + 1))
            for x_coor in range(City.GRID_COUNT_IN_ONE_EDGE):
                for y_coor in range(City.GRID_COUNT_IN_ONE_EDGE):
                    f.write("{0:<10.2f}\t".format(u_d_for_multiple_days[t][x_coor][y_coor]))
        f.write(";\nend;\n")
        f.close()

        f = open(GLPK_PATH + SERVICE_RATE_FILE, 'w')
        co = snapshot.load_city_after_deployment()
        s_r = co.service_rate
        f.write("param s_r :\t")
        for x_coor in range(City.GRID_COUNT_IN_ONE_EDGE):
            for y_coor in range(City.GRID_COUNT_IN_ONE_EDGE):
                j = get_j(x_coor, y_coor)
                f.write("{0:<10}\t".format(j + 1))
        f.write(":=")
        for bs in range(co.bs_count):
            f.write("\n{0:<10}\t".format(bs + 1))
            for x_coor in range(City.GRID_COUNT_IN_ONE_EDGE):
                for y_coor in range(City.GRID_COUNT_IN_ONE_EDGE):
                    f.write("{0:<10.2f}\t".format(s_r[bs][x_coor][y_coor]))
        f.write(";\nend;\n")
        f.close()

    @staticmethod
    def write_the_all_history_logs_to_a_single_file(iteration_no):
        print("write_the_all_history_logs_to_a_single_file starts")
        snapshot = Snapshot()
        SIZE_OF_COMMON_FIELDS = len(SHC.COMMON_BATTERY_RECORDS)
        FIELD_OF_EACH_CONF = len(SHC.BATTERY_RECORDS_FOR_EACH_CONF)
        op_method_list = CalibrationParameters().get_parameters()
        FIELD_COUNT = SIZE_OF_COMMON_FIELDS + len(op_method_list) * FIELD_OF_EACH_CONF
        ROW_COUNT = NUMBER_OF_SIMULATION_DAY * 24
        row_list = [[0 for x in range(FIELD_COUNT)] for x in
                    range(ROW_COUNT)]
        smf = SaatliMaarifTakvimi()
        header = SHC.COMMON_BATTERY_RECORDS[:]
        for conf_index in range(len(op_method_list)):
            conf_name = snapshot.log_file_name(op_method_list[conf_index], iteration_no[conf_index])
            field_offset = SIZE_OF_COMMON_FIELDS + conf_index * FIELD_OF_EACH_CONF
            header += SHC.BATTERY_RECORDS_FOR_EACH_CONF
            for i in range(field_offset, field_offset + FIELD_OF_EACH_CONF):
                header[i] += conf_name
            bh = snapshot.load_battery_history(conf_name)
            number_of_bs = len(bh)
            for bs_index in range(number_of_bs):
                for time_slot in range(len(bh[0])):  # for each time slot
                    if conf_index == 0 and bs_index == 0:  # we write common fields (date & harvested en.) once for the whole bses and configurations
                        smf.yapragi_kopar()
                        row_list[time_slot][0] = smf.month_of_the_year + 1
                        row_list[time_slot][1] = smf.day_of_the_month
                        row_list[time_slot][2] = smf.hour_of_the_day
                        row_list[time_slot][3] = bh[0][time_slot][0] * number_of_bs  # harvested energy

                    if bh[bs_index][time_slot][1] == 'Awake':  # fifth column informs the number of awake bs
                        row_list[time_slot][field_offset] += 1
                    row_list[time_slot][field_offset + 1] += bh[bs_index][time_slot][2]  # field 2 --> fossil_energy_consumption
                    row_list[time_slot][field_offset + 2] += bh[bs_index][time_slot][3]  # field 3 --> ren_energy_consumption
                    row_list[time_slot][field_offset + 3] += bh[bs_index][time_slot][4]  # field 4 --> wasted_energy
                    # row_list[time_slot][field_offset + 4] += bh[bs_index][time_slot][5]  # field 5 --> remaining_energy
                    # row_list[time_slot][field_offset + 5] += bh[bs_index][time_slot][6]  # field 6 --> renewable_usage_ratio

        with open(Output.output_file_name(), 'wb') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', ineterminator='\n', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header)
            csv_writer.writerows(row_list)
