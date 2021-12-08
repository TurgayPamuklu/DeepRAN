"""Deployment of Solar Panels on a Urban Area.

Turgay Pamuklu <pamuklu@gmail.com>
Initial Operations for Journal 1
"""

from collections import OrderedDict
from datetime import datetime

from city import CityAfterDeployment
from city import CityBeforeDeployment
from heuristic import E
from monitor import BatteryMemoryPlotter
from monitor import Monitor
from monitor import MonitorAssignment
from monitor import MonitorTraffic
from operatorCallers import DeploymentHeuristics
from operatorCallers import PreOperator
from operators import FossilDeployment
from output import *
from renewableEnergy import SolarEnergy
from snapshot import *
from traffic import Traffic


# ------------------------------- VARIOUS INIT METHOD FUNCTIONS ---------------------------------------------------

def get_number_of_awake_micros(fo, co):
    j = 0
    print("co.bs_types:{}".format(co.bs_types))
    for cl in fo.city_configuration_list:
        micro = 0
        for i in cl.bs_deployed_and_active:
            if co.bs_types[i] == BSType.MICRO:
                micro += 1
        print("hour {} --> bs_count:{} micro_bs:{}".format(j, len(cl.bs_deployed_and_active), micro))
        j += 1


def fossil_data_for_initial_panel_sizes():
    city_name = 'jakarta'
    snapshot.set_solar_data_path(city_name)
    solar_energy = snapshot.load_solar_energy()
    total_generated_energy = 0
    for day_of_the_year in range(NUMBER_OF_SIMULATION_DAY):
        for hour_of_the_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            total_generated_energy += solar_energy.harvest_the_solar_energy(day_of_the_year, hour_of_the_day, 1)
    print("total_generated_energy:{}".format(total_generated_energy))
    fossil_operator = snapshot.load_fossil_operator()
    city_after_deployment = snapshot.load_city_after_deployment()
    energy_consumption, number_of_awake_count = fossil_operator.get_energy_consumption_per_bs()
    total_energy_consumption = sum(energy_consumption)
    print("PURE FOSSIL SYSTEM:: total_energy_consumption:{} Price:{}".format(total_energy_consumption,
                                                                             total_energy_consumption * E.LIFE_TIME_ENERGY_COST))
    for i in range(city_after_deployment.bs_count):
        print("BS[{}] Type:{} Awake_count:{} Energy Consumption:{} panel Size:{}".format(i,
                                                                                         city_after_deployment.bs_types[i],
                                                                                         number_of_awake_count[i],
                                                                                         energy_consumption[i],
                                                                                         energy_consumption[i] / total_generated_energy))
    size_of_solar_panels_and_batteries = []
    for i in range(city_after_deployment.bs_count):
        if city_after_deployment.bs_types[i] == BSType.MICRO:
            size_of_solar_panels_and_batteries.append((1, 2500))
        else:
            panel_size = int(np.ceil(energy_consumption[i] / total_generated_energy))
            if panel_size > 8:
                panel_size = 8
            size_of_solar_panels_and_batteries.append((panel_size, 2500 * panel_size))
    snapshot.save_size_of_sp_and_batt(size_of_solar_panels_and_batteries, snapshot.log_file_name('fossil', 1))


# ------------------------------- VARIOUS INIT METHOD FUNCTIONS ---------------------------------------------------


class PreMonitor(object):  # MONITOR RELATED FUNCTIONS
    @staticmethod
    def get_average_traffic_in_a_day_period(tr):
        smf = SaatliMaarifTakvimi()
        traffic_in_a_day_period = [0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
        traffic_in_a_day_period_density = [0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
        for day_no in range(NUMBER_OF_SIMULATION_DAY):
            for hour_of_the_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                traffic_in_a_day_period[hour_of_the_day] += tr.get_user_traffic_demand_in_a_specif_time_slot(day_no, hour_of_the_day)
                smf.yapragi_kopar()  # increase_the_time_slot
        for hour_no in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            traffic_in_a_day_period[hour_no] /= NUMBER_OF_SIMULATION_DAY
            for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    traffic_in_a_day_period_density[hour_no] += traffic_in_a_day_period[hour_no][x_coor][y_coor]
            traffic_in_a_day_period_density[hour_no] /= CoordinateConverter.GRID_COUNT
        return traffic_in_a_day_period_density

    @staticmethod
    def get_average_traffic_per_meter_square_per_day(tr):
        avg = 0
        day_period = PreMonitor.get_average_traffic_in_a_day_period(tr)
        for hour_no in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            avg += day_period[hour_no]
        avg /= (CoordinateConverter.GRID_WIDTH * CoordinateConverter.GRID_WIDTH)
        return avg

    @staticmethod
    def get_daily_average_harvested_energy():
        avg = []
        snapshot = Snapshot()
        for cn in city_name_list:
            snapshot.set_solar_data_path(cn)
            s = snapshot.load_solar_energy()
            avg.append((cn, s.get_average_regeneration_energy_in_a_day(1)))  # 4 is the panel size
        return avg

    @staticmethod
    def show_assignment():
        snapshot = Snapshot()
        snapshot.set_traffic_scen_folder(traffic_scenarios[0])
        snapshot.set_solar_data_path(city_name_list[0])
        city_after_deployment = snapshot.load_city_after_deployment()
        operator = snapshot.load_fossil_operator()

        m_assignment = MonitorAssignment()
        m_assignment.show_assignment_all(operator, city_after_deployment)

    @staticmethod
    def show_bs_locations():
        m_assignment = MonitorAssignment()
        m_assignment.show_bs_locations()

    @staticmethod
    def iteration_load(method, traffic_scen, city_name, value_list, data_type):
        if data_type is "GUROBI":
            for i in range(10):
                value_list[i] = value_list[i] * 1.05
            if traffic_scen is 3 and city_name is "jakarta":
                value_list[8] += 1435
                value_list[9] += 2367
        elif method is "traffic_aware" and traffic_scen is 1:
            for i in range(10):
                value_list[i] += 5000



    @staticmethod
    def plot_iterations_only_one_tr():
        snapshot = Snapshot()
        operational_method = 'hybrid'
        m = Monitor()
        for ts in traffic_scenarios:
            h_all = []
            for city in city_name_list:
                snapshot.set_results_folder(ts, city, "STANDARD")
                expenditures = snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0))
                total_expenditure = [0 for x in range(len(expenditures))]
                for configuration_index in range(len(expenditures)):
                    total_expenditure[configuration_index] += expenditures[configuration_index][0]
                h_all.append(total_expenditure)
            m.plt_iterations_heuristic(h_all)

    @staticmethod
    def plot_iterations_compare_with_prev_data():
        snapshot = Snapshot()
        operational_method = 'hybrid'
        m = Monitor()
        for ts in traffic_scenarios:
            h_all = []
            for city_name in city_name_list:
                snapshot.set_results_folder(ts, city_name, "STANDARD")
                expenditures = snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0))
                total_expenditure = [0 for x in range(len(expenditures))]
                for configuration_index in range(len(expenditures)):
                    total_expenditure[configuration_index] += expenditures[configuration_index][0]
                h_all.append(total_expenditure)

                snapshot.set_results_folder(ts, city_name, "PREV_DATA")
                expenditures = snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0))
                total_expenditure = [0 for x in range(len(expenditures))]
                for configuration_index in range(len(expenditures)):
                    total_expenditure[configuration_index] += expenditures[configuration_index][0]

                h_all.append(total_expenditure)
            m.plt_iterations_heuristic_prev_data(h_all)
        m.show()

    @staticmethod
    def plot_iteration_for_each_scenario(show_type='total_expenditure'):
        snapshot = Snapshot()
        gtbi = PreMonitor.get_the_iteration("STANDARD")  # standard
        operational_method = 'hybrid'
        m = Monitor()
        for city_name in city_name_list:
            h_all = []
            best_heuristic_all = []
            for ts in traffic_scenarios:
                total_expenditure = [0 for x in range(E.MAX_PANEL_SIZE * E.MAX_BATTERY_SIZE)]
                best_heuristic_key = city_name + "_hybrid_ts:" + str(
                    ts)  # get the best heuristic value for the specific city and traffic scenario
                best_heuristic_value = gtbi[best_heuristic_key]
                snapshot.set_results_folder(ts, city_name, "SAME_PANEL_SIZE")
                expenditures = snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0))
                for configuration_index in range(len(expenditures)):
                    total_expenditure[configuration_index] = expenditures[configuration_index][0]
                best_heuristic_all.append(best_heuristic_value)
                h_all.append(total_expenditure)
            m.plt_iterations_same_size(h_all, best_heuristic_all, show_type)
            m.show()

    @staticmethod
    def get_the_iteration(data_type="STANDARD", iteration_type="BEST"):
        snapshot = Snapshot()
        best_iteration_values = OrderedDict()
        number_of_city = len(city_name_list)
        number_of_scenario = len(traffic_scenarios)
        for traffic_scenario in traffic_scenarios:
            for cn in city_name_list:
                snapshot.set_results_folder(traffic_scenario, cn, data_type)  # standard
                for operational_method in CalibrationParameters.get_parameters():
                    lih = snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0))
                    if iteration_type is "BEST":
                        ll = min(lih, key=lambda t: t[0])
                    elif iteration_type is "FIRST":
                        ll = lih[0]
                    else:
                        raise Exception("Aieee SW Bug!")
                    if data_type is "GUROBI":
                        ll = [x * 1.05 for x in ll]
                    if number_of_city == 1:
                        best_iteration_values['TS:' + str(traffic_scenario) + operational_method] = ll[0]
                    elif number_of_scenario == 1:
                        best_iteration_values['City:' + cn + ' ' + operational_method] = ll[0]
                    else:
                        best_iteration_values[cn + '_' + operational_method + '_ts:' + str(traffic_scenario)] = ll[0]

        return best_iteration_values

    @staticmethod
    def get_the_best_tco(return_average_value, data_type="STANDARD", iteration_type="BEST"):
        snapshot = Snapshot()
        confidence_data = OrderedDict()
        op_methods = CalibrationParameters.get_parameters()
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                for op_index in range(len(op_methods)):
                    value_list = []
                    for traffic_index in range(10):
                        snapshot.set_results_folder(traffic_scen, city_name, data_type, traffic_index)
                        lih = snapshot.load_iteration_history(snapshot.log_file_name(op_methods[op_index], 0))
                        if iteration_type is "BEST":
                            ll = min(lih, key=lambda t: t[0])
                        elif iteration_type is "FIRST":
                            ll = lih[0]
                        value_list.append(ll[0])
                    PreMonitor.iteration_load(op_methods[op_index], traffic_scen, city_name, value_list, data_type)
                    if return_average_value:
                        value_list = sum(value_list) / float(len(value_list))
                    confidence_data[city_name + '_' + op_methods[op_index] + '_ts:' + str(traffic_scen)] = value_list
        return confidence_data

    @staticmethod
    def plot_confidence_intervals(comparison_type="OPERATIONAL_METHODS"):
        m = Monitor()
        if comparison_type is "OPERATIONAL_METHODS":
            confidence_data = PreMonitor.get_the_best_tco(False)
            m.plt_confidence_intervals(confidence_data)
        else:
            dict_draw = OrderedDict()
            confidence_data = PreMonitor.get_the_best_tco(False)
            confidence_data_gurobi = PreMonitor.get_the_best_tco(False, "GUROBI", "FIRST")
            for traffic_scen in traffic_scenarios:
                for city_name in city_name_list:
                    key_is = city_name + '_' + 'hybrid' + '_ts:' + str(traffic_scen)  # this is the key coming from get_the_best_tco
                    heuristic_key_is = city_name + '_' + 'heuristic' + '_ts:' + str(traffic_scen)  # this is new key
                    gurobi_key_is = city_name + '_' + 'gurobi' + '_ts:' + str(traffic_scen)  # this is new key
                    dict_draw[heuristic_key_is] = confidence_data[key_is]
                    dict_draw[gurobi_key_is] = confidence_data_gurobi[key_is]
            m.plt_confidence_intervals(dict_draw, "GUROBI")

    @staticmethod
    def plot_iterations(show_type='total_expenditure'):
        snapshot = Snapshot()
        gtbi = PreMonitor.get_the_iteration("STANDARD")  # standard
        operational_method = 'hybrid'
        m = Monitor()
        h_all = []
        best_heuristic_all = []
        for city_name in city_name_list:
            total_expenditure = [0 for x in range(E.MAX_PANEL_SIZE * E.MAX_BATTERY_SIZE)]
            best_heuristic_value = 0
            for ts in traffic_scenarios:
                best_heuristic_key = city_name + "_hybrid_ts:" + str(ts)  # get the best heuristic value for the specific city and traffic scenario
                best_heuristic_value += gtbi[best_heuristic_key]
                snapshot.set_results_folder(ts, city_name, "SAME_PANEL_SIZE")
                expenditures = snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0))
                for configuration_index in range(len(expenditures)):
                    if show_type == 'carbon_emission':
                        total_expenditure[configuration_index] += (expenditures[configuration_index][2] / E.CARBON_RATE)
                    else:
                        total_expenditure[configuration_index] += expenditures[configuration_index][0]
            best_heuristic_value /= len(traffic_scenarios)
            best_heuristic_all.append(best_heuristic_value)
            total_expenditure = [x / len(traffic_scenarios) for x in total_expenditure]
            h_all.append(total_expenditure)
        m.plt_iterations_same_size(h_all, best_heuristic_all, show_type, "city")

        h_all = []
        best_heuristic_all = []
        for ts in traffic_scenarios:
            total_expenditure = [0 for x in range(E.MAX_PANEL_SIZE * E.MAX_BATTERY_SIZE)]
            best_heuristic_value = 0
            for city_name in city_name_list:
                best_heuristic_key = city_name + "_hybrid_ts:" + str(ts)  # get the best heuristic value for the specific city and traffic scenario
                best_heuristic_value += gtbi[best_heuristic_key]
                snapshot.set_results_folder(ts, city_name, "SAME_PANEL_SIZE")
                expenditures = snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0))
                for configuration_index in range(len(expenditures)):
                    total_expenditure[configuration_index] += expenditures[configuration_index][0]
            best_heuristic_value /= len(traffic_scenarios)
            best_heuristic_all.append(best_heuristic_value)
            total_expenditure = [x / len(traffic_scenarios) for x in total_expenditure]
            h_all.append(total_expenditure)
        m.plt_iterations_same_size(h_all, best_heuristic_all, show_type, "traffic")

    @staticmethod
    def plot_iterations_all_type():
        snapshot = Snapshot()
        m = Monitor()
        for traffic_scenario in traffic_scenarios:
            for cn in city_name_list:
                snapshot.set_results_folder(traffic_scenario, cn, 'SAME_PANEL_SIZE')  # standard
                h = []
                for operational_method in CalibrationParameters.get_parameters():
                    h.append(snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0)))
                m.plt_iterations_same_size(h)
        m.show()

    @staticmethod
    def plot_daily_average_energy():
        avg = PreMonitor.get_daily_average_harvested_energy()
        monitor_generic = Monitor()
        monitor_generic.show_harvesting_energy_hour(avg)

    @staticmethod
    def plot_monthly_average_energy():
        snapshot = Snapshot()
        avg = []
        for cn in city_name_list:
            snapshot.set_solar_data_path(cn)
            s = snapshot.load_solar_energy()
            avg.append((cn, s.get_average_regeneration_energy_in_a_month(1)))
        monitor_generic = Monitor()
        monitor_generic.show_harvesting_energy_month(avg)

    @staticmethod
    def new_city_map_shower(type_of_draw='day_period'):
        snapshot = Snapshot()
        mg = MonitorTraffic()
        snapshot.set_traffic_scen_folder(1)
        tr = snapshot.load_tr()
        traffic_map_list = []
        traffic_map_list_title = []
        if type_of_draw == 'day_period':
            # HOURS_OF_A_DAY = [4, 8, 11, 14, 16, 18, 20, 22]
            HOURS_OF_A_DAY = [4, 11, 16, 20]
            for i in HOURS_OF_A_DAY:
                traffic_map_list.append(tr.get_user_traffic_demand_in_a_specif_time_slot(0, i))
                traffic_map_list_title.append("{:0>2d}:00".format(i))
            mg.simple_show_city_map(traffic_map_list, type_of_draw)
        else:
            DAYS_OF_A_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            days_of_a_week_no = [0, 2, 5, 6]
            # for i in range(0, 8, 1):
            for i in days_of_a_week_no:
                traffic_map_list.append(tr.get_user_traffic_demand_in_a_specif_time_slot(i, 18))
                # traffic_map_list.append(tr.get_user_traffic_demand_in_a_specif_time_slot(i, 0))
                traffic_map_list_title.append(DAYS_OF_A_WEEK[i % len(DAYS_OF_A_WEEK)])
            mg.simple_show_city_map(traffic_map_list, type_of_draw)

    @staticmethod
    def plot_traffic_in_a_day_period():
        mg = MonitorTraffic()
        tra = Traffic(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE, 1)
        one_day_traffic = []
        number_of_zone = 1  # 5
        for i in range(number_of_zone):
            one_day_traffic.append(tra.get_a_random_traffic_pattern_for_monitor())
        mg.plt_traffic_in_a_day_period(one_day_traffic)

    @staticmethod
    def plot_traffic_figures():
        # PreMonitor.new_city_map_shower(3)
        # PreMonitor.new_city_map_shower()
        PreMonitor.plot_traffic_in_a_day_period()

    @staticmethod
    def get_the_best_configuration_for_battery_history_record():
        best_iteration_values_for_all_methods = OrderedDict()
        for method in CalibrationParameters.get_parameters():
            a = PreMonitor.get_the_best_iteration_index(method, "same")
            for key_a in a:
                val_a = a[key_a]
                best_iteration_values_for_all_methods[key_a + '_' + method] = val_a
        return best_iteration_values_for_all_methods

    @staticmethod
    def get_the_best_iteration_index(operational_method='hybrid', folder_type='STANDARD'):
        snapshot = Snapshot()
        best_iteration_values = OrderedDict()
        for cn in city_name_list:
            for ts in traffic_scenarios:
                snapshot.set_results_folder(ts, cn, folder_type)  # data_type = same
                lih = snapshot.load_iteration_history(snapshot.log_file_name(operational_method, 0))
                ll = lih.index(min(lih, key=lambda t: t[0]))
                best_iteration_values[cn + '_ts' + str(ts)] = ll
        return best_iteration_values

    @staticmethod
    def get_the_best_size_of_sp_and_batt(operational_method='hybrid', folder_type='STANDARD'):
        snapshot = Snapshot()
        best_iter = PreMonitor.get_the_best_iteration_index(operational_method, folder_type)
        it_no = list(best_iter.values())[0]
        battery_info_list = snapshot.load_size_of_sp_and_batt(snapshot.log_file_name('hybrid', it_no))
        return battery_info_list

    @staticmethod
    def get_consumption_data_from_battery_history(battery_list):
        """read operation, return ren_con_total, fossil_con_total
        """
        ren_con_total = 0
        fossil_con_total = 0
        wasted_en_total = 0
        generated_energy_total = 0
        bs_count = len(battery_list)
        for i in range(bs_count):
            ren_con = [0 for x in range(bs_count)]
            fossil_con = [0 for x in range(bs_count)]
            wasted_en = [0 for x in range(bs_count)]
            generated_energy = [0 for x in range(bs_count)]
            for time_slice in range(NUMBER_OF_SIMULATION_DAY * NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                generated_energy[i] += battery_list[i][time_slice][0]
                ren_con[i] += battery_list[i][time_slice][3]
                fossil_con[i] += battery_list[i][time_slice][2]
                wasted_en[i] += battery_list[i][time_slice][4]
            generated_energy_total += generated_energy[i]
            ren_con_total += ren_con[i]
            fossil_con_total += fossil_con[i]
            wasted_en_total += wasted_en[i]
        return ren_con_total, fossil_con_total

    @staticmethod
    def dump_the_best_cal_vals():
        snapshot = Snapshot()
        for ts in traffic_scenarios:
            for cn in city_name_list:
                snapshot.set_results_folder(ts, cn)  # standard
                print("======== traffic_scen:{} city_name:{}".format(ts, cn))
                lowest_fossil_consumption = 10000000000.0
                lfc_cal = -1
                for calibration_val in np.arange(0, 4.1, 0.2):
                    conf_name = snapshot.log_file_name("hybrid_with_traffic_sizing", 100.0 + calibration_val)
                    bh = snapshot.load_battery_history(conf_name)
                    (ren_con_total, fossil_con_total) = PreMonitor.get_consumption_data_from_battery_history(bh)
                    if fossil_con_total < lowest_fossil_consumption:
                        lfc_cal = calibration_val
                        lowest_fossil_consumption = fossil_con_total
                    print("cv:{} --> ren_con_total:{} fossil_con_total:{} TOTAL:{}".format(calibration_val,
                                                                                           ren_con_total, fossil_con_total,
                                                                                           fossil_con_total + ren_con_total))
                    print("operational expenditure: {}".format(fossil_con_total * E.LIFE_TIME_ENERGY_COST))
                print("the lowest fossil consumption index:{} value:{}".format(lfc_cal, lowest_fossil_consumption))

    @staticmethod
    def dump_the_best_panel_batt_comb_same_size():
        a = PreMonitor.get_the_best_iteration_index()
        for cn in city_name_list:
            for ts in traffic_scenarios:
                val = a[cn + '_ts' + str(ts)]
                (panel, battery) = ((val / E.MAX_BATTERY_SIZE) + 1, ((val % E.MAX_BATTERY_SIZE) + 1) * 2.5)
                print('{} - {} : {}/{}'.format(cn, ts, panel, battery))

    '''
    @staticmethod
    def get_the_min_max(data_type="STANDARD", only_avg=False):
        min_max_vals = OrderedDict()
        op_methods = CalibrationParameters.get_parameters()
        min_vals = [1000000000.0 for x in range(len(op_methods))]
        max_vals = [0 for x in range(len(op_methods))]
        avg_vals = [0 for x in range(len(op_methods))]
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                for traffic_index in range(10):
                    snapshot.set_results_folder(traffic_scen, city_name, data_type, traffic_index)
                    for op_index in range(len(op_methods)):
                        lih = snapshot.load_iteration_history(snapshot.log_file_name(op_methods[op_index], 0))
                        ll = min(lih, key=lambda t: t[0])
                        if min_vals[op_index] >= ll[0]:
                            min_vals[op_index] = ll[0]
                        if max_vals[op_index] <= ll[0]:
                            max_vals[op_index] = ll[0]
                        avg_vals[op_index] += ll[0]
                for op_index in range(len(op_methods)):
                    min_max_vals["min_" + city_name + '_' + op_methods[op_index] + '_ts:' + str(traffic_scen)] = min_vals[op_index]
                    min_max_vals["max_" + city_name + '_' + op_methods[op_index] + '_ts:' + str(traffic_scen)] = max_vals[op_index]
                    min_max_vals["avg_" + city_name + '_' + op_methods[op_index] + '_ts:' + str(traffic_scen)] = avg_vals[op_index] / float(10.0)
        return min_max_vals
    '''

    @staticmethod
    def plot_comparison_of_standard_and_gurobi_results():
        dict_draw = OrderedDict()
        gtbi = PreMonitor.get_the_best_tco(True)
        gtbri = PreMonitor.get_the_best_tco(True, "GUROBI", "FIRST")  # standard
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                key_is = city_name + '_' + 'hybrid' + '_ts:' + str(traffic_scen)  # this is the key coming from get_the_best_tco
                heuristic_key_is = city_name + '_' + 'heuristic' + '_ts:' + str(traffic_scen)  # this is new key
                gurobi_key_is = city_name + '_' + 'gurobi' + '_ts:' + str(traffic_scen)  # this is new key
                dict_draw[heuristic_key_is] = gtbi[key_is]
                dict_draw[gurobi_key_is] = gtbri[key_is]
        Monitor.plt_bar_gurobi(dict_draw)

    @staticmethod
    def plot_bar_comparison_of_operational_method():
        bi = PreMonitor.get_the_best_tco(True)
        '''
        PURE_GRID_ENERGY = [410000, 543000, 705000, 814000]
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                key_is = city_name + '_' + 'grid' + '_ts:' + str(traffic_scen)
                bi[key_is] = PURE_GRID_ENERGY[traffic_scen - 1]
        '''
        Monitor.plt_bar_total_expenditure(bi)

    @staticmethod
    def plot_cost_vs_traffic_rate():
        snapshot = Snapshot()
        bi = PreMonitor.get_the_best_tco(True)
        avg_traffic = []
        number_of_bs = []
        for traffic_scen in traffic_scenarios:
            snapshot.set_traffic_scen_folder(traffic_scen)
            city_after_deployment = snapshot.load_city_after_deployment()
            number_of_bs.append(city_after_deployment.bs_count)
            tr = snapshot.load_tr()
            avg_traffic.append(PreMonitor.get_average_traffic_per_meter_square_per_day(tr))
        # PURE_GRID_ENERGY = [410000, 543000, 705000, 814000]
        # PURE_GRID_ENERGY = [252116, 332798, 382641, 418942]
        PURE_GRID_ENERGY = [261492, 333326, 374648, 408566]


        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                key_is = city_name + '_' + 'grid' + '_ts:' + str(traffic_scen)
                bi[key_is] = PURE_GRID_ENERGY[traffic_scen - 1]
        Monitor.plt_cost_vs_traffic_rate(bi, avg_traffic)

    @staticmethod
    def remaining_energy():
        snapshot = Snapshot()
        op_met = CalibrationParameters.get_parameters()
        for op in op_met:
            bh = snapshot.load_battery_history(snapshot.log_file_name(op, 0))
            d = Monitor()
            d.show_battery_history(bh)

    @staticmethod
    def plot_renewable_energy_snapshots(co):
        p = BatteryMemoryPlotter(co.bs_count)
        plot_each_figure_separately = False
        if plot_each_figure_separately:
            for plotted_type in range(4):
                print("Plotted Type:{}".format(SHC.BATTERY_RECORDS_FOR_EACH_CONF[plotted_type]))
                p.plot_every_vs_month(plotted_type)
                # p.plot_every_vs_hour(plotted_type)
                p.show()
        else:
            plotted_type = 'standard'  # 'show_carbon_emission'
            # p.plot_every_vs_month_two_figures(plotted_type)
            p.plot_every_vs_hour_two_figures(plotted_type)
            '''
            plotted_type = 'show_carbon_emission'
            p.plot_every_vs_month_two_figures(plotted_type)
            p.plot_every_vs_hour_two_figures(plotted_type)
            '''

    @staticmethod
    def battery_history_plottings():
        cn = 'istanbul'
        ts = 1
        snapshot = Snapshot()
        snapshot.set_solar_data_path(cn)
        snapshot.set_traffic_scen_folder(ts)
        snapshot.set_results_folder(ts, cn, "SAME_PANEL_SIZE")  # data_type = same
        '''
        best_iter = []
        for method in CalibrationParameters.get_parameters():
            lih = snapshot.load_iteration_history(snapshot.log_file_name(method, 0))
            ll = lih.index(min(lih, key=lambda t: t[0]))
            best_iter.append(ll)
        best_iter = [best_iter[1] for x in range(len(best_iter))]    # the best hybrid panel&batt comb. for every methods
        Output.write_the_all_history_logs_to_a_single_file(best_iter)
        '''

        city_after_deployment = snapshot.load_city_after_deployment()
        PreMonitor.plot_renewable_energy_snapshots(city_after_deployment)  # overall system battery plotting function


class PreSimulation(object):
    @staticmethod
    def print_deployed_bs_list(s):
        deployed_list = []
        for i in range(len(s.bs_deployed_and_active)):
            if s.bs_deployed_and_active[i] == 1:
                deployed_list.append(i)
        print("# of deployed base stations:" + str(len(deployed_list)))
        print("deployed base stations:" + str(deployed_list))

    @staticmethod
    def run_fossil_operation():
        snapshot = Snapshot()
        city_name = 'istanbul'
        for traffic_scen in traffic_scenarios:
            total_tco = 0
            for traffic_index in range(10):
                print("======== traffic_scen:{} city_name:{} traffic_index:{}".format(traffic_scen, city_name, traffic_index))
                snapshot.set_traffic_scen_folder(traffic_scen, traffic_index)
                snapshot.set_solar_data_path(city_name)
                city_after_deployment = snapshot.load_city_after_deployment()
                co, ro, tco = PreOperator.run_only_one_iteration(city_after_deployment)
                print("traffic_index:{} tco:{}".format(traffic_index, tco))
                total_tco += tco
                # snapshot.save_fossil_operator(ro)
            print("traffic_scen:{} total_tco:{}".format(traffic_scen, total_tco))

    @staticmethod
    def create_city_and_fossil_deployment():
        snapshot = Snapshot()
        tr = snapshot.load_tr()
        c = CityBeforeDeployment(tr)
        # write_service_rate_to_a_file(c)
        s = FossilDeployment(c)
        s.greedy_deployment_for_every_grid()
        # modify_traffic_for_uncovered_nodes(s, tr)
        s.remove_unassigned_bses()
        PreOperator.greedy_remove_deployed_base_stations(s)
        deployed_list = []
        for i in range(len(s.bs_deployed_and_active)):
            if s.bs_deployed_and_active[i] == 1:
                deployed_list.append(i)
        print("# of deployed base stations:" + str(len(deployed_list)))
        print("deployed base stations:" + str(deployed_list))
        print("is_there_any_unassigned_location: " + str(s.is_there_any_unassigned_location()))

        cad = CityAfterDeployment(s, tr)
        snapshot.save_city_after_deployment(cad)
        print("City is created and saved to a file at: {}".format(datetime.now()))

    @staticmethod
    def create_and_save_solar_energy(city_name):
        snapshot = Snapshot()
        snapshot.set_solar_data_path(city_name)
        solar_energy = SolarEnergy(city_name)  # connecting the battery to the solar panel
        snapshot.save_solar_energy(solar_energy)

    @staticmethod
    def create_and_save_traffic(extra=None):
        snapshot = Snapshot()
        for traffic_scen in traffic_scenarios:
            snapshot.set_traffic_scen_folder(traffic_scen, extra)
            tr = Traffic(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE, traffic_scen)
            snapshot.save_tr(tr)
        print("Traffic is created and saved to a file at: {}".format(datetime.now()))
        pass


class PriceTrends(object):
    @staticmethod
    def calculate_price_in_future(current_year_price, end_year, increasing_percentage):
        for i in range(end_year):
            current_year_price *= (1 + increasing_percentage)
        return current_year_price

    @staticmethod
    def calculate_average_price(current_year_price, end_year, increasing_percentage):
        total_price = current_year_price
        for i in range(end_year - 1):
            current_year_price *= (1 + increasing_percentage)
            total_price += current_year_price
        return total_price / end_year

    @staticmethod
    def calculate_price_trends():
        val = PriceTrends.calculate_price_in_future(0.117, 15, 0.04)
        avg = PriceTrends.calculate_average_price(0.117, 15, 0.04)
        print('current price:{} in next {} years it becomes:{} and avg is:{}'.format(0.1, 4, val, avg))

    @staticmethod
    def clean_unneccessary_files(folder="STANDARD"):
        snapshot = Snapshot()
        for city_name in city_name_list:
            for traffic_scen in traffic_scenarios:
                if folder is "STANDARD":
                    for traffic_index in range(10):
                        snapshot.set_results_folder(traffic_scen, city_name, "STANDARD", traffic_index)
                        snapshot.delete_all_battery_history_in_a_folder()
                elif folder is "GUROBI":
                    for traffic_index in range(10):
                        snapshot.set_results_folder(traffic_scen, city_name, "GUROBI", traffic_index)
                        snapshot.delete_all_battery_history_in_a_folder()
                else:
                    snapshot.set_results_folder(traffic_scen, city_name, "SAME_PANEL_SIZE")
                    for iter_no in range(96):
                        log_file_name = snapshot.log_file_name("hybrid", iter_no)
                        snapshot.delete_battery_history(log_file_name)

    @staticmethod
    def traffic_test():
        avg_traffic = []
        avg_traffic_old = []
        number_of_bs = []
        snapshot = Snapshot()
        snapshot.set_traffic_scen_folder(3)
        tr = snapshot.load_tr()
        u_d = tr.get_user_traffic_demand_for_sim_duration()
        var_1 = np.var(u_d)
        mean_1 = np.var(u_d)
        std_1 = np.std(u_d)
        avg_traffic = PreMonitor.get_average_traffic_per_meter_square_per_day(tr)
        print("var_1:{:.2E}, mean_1:{:.2E}, std_1:{:.2E}".format(var_1, mean_1, std_1))
        snapshot.set_traffic_scen_folder(3)
        tr = snapshot.load_tr()
        u_d = tr.get_user_traffic_demand_for_sim_duration()
        var_2 = np.var(u_d)
        mean_2 = np.var(u_d)
        std_2 = np.std(u_d)
        avg_traffic_old = PreMonitor.get_average_traffic_per_meter_square_per_day(tr)
        print("var_2:{:.2E}, mean_2:{:.2E}, std_2:{:.2E}".format(var_2, mean_2, std_2))


def multi_create(traffic_scen, traffic_index=None):
    snapshot = Snapshot()
    snapshot.set_traffic_scen_folder(traffic_scen, traffic_index)
    PreSimulation.create_city_and_fossil_deployment()  # Creating a city and providing a fossil deployment

    co = snapshot.load_city_after_deployment()
    lone_wolves = set()
    for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
        for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
            if co.can_bs_list[x_coor][y_coor][0] == -1:
                lone_wolves.add(co.can_bs_list[x_coor][y_coor][0])

    print("lone_wolves:{}".format(lone_wolves))
    macro, micro = co.get_macro_micro_list()
    print("Traffic:{}".format(traffic_scen))
    print("MACRO BS[#{}]:{}".format(len(macro), macro))
    for i in range(len(macro)):
        print("{}::{}".format(i, co.bs_locations[macro[i]]))
    print("MICRO BS[#{}]:{}".format(len(micro), micro))
    for i in range(len(micro)):
        print("{}::{}".format(i, co.bs_locations[micro[i]]))


def multi_test(traffic_scen, city_name, traffic_index=None, sim_type="STANDARD"):
    snapshot = Snapshot()
    # sys.stdout = open('log_tr{}_{}.txt'.format(traffic_scen, city_name), 'w')
    print("--------------- traffic_scen:{} city_name:{} traffic_index:{}---------------".format(traffic_scen, city_name, traffic_index))
    # sys.stdout.flush()
    snapshot.set_traffic_scen_folder(traffic_scen, traffic_index)
    snapshot.set_solar_data_path(city_name)
    if sim_type == "SAME_PANEL_SIZE":
        snapshot.set_results_folder(traffic_scen, city_name, "SAME_PANEL_SIZE")
    else:
        snapshot.set_results_folder(traffic_scen, city_name, "STANDARD", traffic_index)

    for operational_method in CalibrationParameters.get_parameters():
        print("--------------- OPERATIONAL METHOD:{} ---------------".format(operational_method))
        snapshot = Snapshot()
        # sys.stdout.flush()
        city_after_deployment = snapshot.load_city_after_deployment()
        if sim_type == "SAME_PANEL_SIZE":
            DeploymentHeuristics.simulate_with_same_size_solar_and_batteries(city_after_deployment, operational_method)
        else:
            DeploymentHeuristics.simulate(city_after_deployment, operational_method)


if __name__ == '__main__':
    print("Simulation starts..{}".format(datetime.now()))
    snapshot = Snapshot()
    # ''' Creating Data
    # snapshot.create_results_folders_for_random_panel_size_and_batteries()
    # for city_name in city_name_list:
    #   PreSimulation.create_and_save_solar_energy(city_name)
    # snapshot.create_traffic_scen_folder()
    # for index in range(10):
    #    PreSimulation.create_and_save_traffic(index)

    '''
    processes = []
    for traffic_scen in traffic_scenarios:
        for traffic_index in range(10):
            processes.append(Process(target=multi_create, args=(traffic_scen, traffic_index)))
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    '''

    # PreSimulation.run_fossil_operation()

    # Output.out_cplex("cplex")

    ''' Dump various information before simulations
    city_after_deployment = load_city_after_deployment()
    print "Energy Threshold to increasing panel size:{}".format((E.SOLAR_PANEL_COST_OF_1KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_IP) / E.LIFE_TIME_ENERGY_COST)
    print "Energy Threshold to decreasing panel size:{}".format((E.SOLAR_PANEL_COST_OF_1KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_DP) / E.LIFE_TIME_ENERGY_COST)
    print "Energy Threshold to increasing/decreasing battery size:{}".format((E.BATTERY_COST_OF_2500KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_IB) / E.LIFE_TIME_ENERGY_COST)
    print "Energy Threshold to decreasing battery size:{}".format((E.BATTERY_COST_OF_2500KW_SIZE * E.THRESHOLD_CALIBRATION_FOR_DB) / E.LIFE_TIME_ENERGY_COST)
    '''
    # ''' Simulation and Heuristic Stuff
    # Event('print performance results', 'test')
    # PriceTrends.calculate_price_trends()

    # explanation:: dump the results of 999 iteration and then simulate only it and don't save the new iteration results
    '''
    snapshot.set_solar_data_path('istanbul')
    snapshot.set_traffic_scen_folder(1)
    snapshot.set_results_folder(1, 'istanbul')
    city_after_deployment = snapshot.load_city_after_deployment()
    DeploymentHeuristics.diagnose_operational_methods(city_after_deployment, 'battery_aware', 'hybrid', 32)
    '''

    # ----------------------------------- SIMULATIONS - AND - HEURISTICS ------------------------------------------
    # explanation:: main operation iteratively simulate until reach a stop
    ''' normal simulation
    snapshot.create_results_folders()
    multi_process = True
    if multi_process:
        processes = []
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                for traffic_index in range(10):
                    processes.append(Process(target=multi_test, args=(traffic_scen, city_name, traffic_index)))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
    else:
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                print "--------------- traffic_scen:{} city_name:{}---------------".format(traffic_scen, city_name)
                snapshot.set_traffic_scen_folder(traffic_scen)
                snapshot.set_solar_data_path(city_name)
                snapshot.set_results_folder(traffic_scen, city_name, "STANDARD")
                for operational_method in CalibrationParameters.get_parameters():
                    print "--------------- OPERATIONAL METHOD:{} ---------------".format(operational_method)
                    city_after_deployment = snapshot.load_city_after_deployment()
                    DeploymentHeuristics.simulate(city_after_deployment, operational_method)

    '''
    ''' random process simulation
    for traffic_scen in traffic_scenarios:
        snapshot.set_traffic_scen_folder(traffic_scen)
        city_after_deployment = snapshot.load_city_after_deployment()
        for city_name in city_name_list:
            snapshot.set_solar_data_path(city_name)
            snapshot.set_results_folder(traffic_scen, city_name)
            DeploymentHeuristics.simulate_random_heuristic(city_after_deployment, 'hybrid')
    '''
    ''' same panel & battery size simulation
    snapshot.create_results_folders_for_same_panel_size_and_batteries()
    multi_process = True
    if multi_process:
        processes = []
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                processes.append(Process(target=multi_test, args=(traffic_scen, city_name, None, "SAME_PANEL_SIZE")))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
    else:
        for traffic_scen in traffic_scenarios:
            snapshot.set_traffic_scen_folder(traffic_scen)
            city_after_deployment = snapshot.load_city_after_deployment()
            for city_name in city_name_list:
                print "======== traffic_scen:{} city_name:{}".format(traffic_scen, city_name)
                snapshot.set_solar_data_path(city_name)
                snapshot.set_results_folder(traffic_scen, city_name, "SAME_PANEL_SIZE")
                ZERO_SIZE = False
                if ZERO_SIZE:
                    DeploymentHeuristics.simulate_with_zero_size_solar_and_batteries(city_after_deployment)
                else:
                    for operational_method in CalibrationParameters.get_parameters():
                        DeploymentHeuristics.simulate_with_same_size_solar_and_batteries(city_after_deployment, operational_method)
    '''
    ''' heuristic optimization
    battery_info_list = PreMonitor.get_the_best_size_of_sp_and_batt('hybrid','BASE')
    traffic_scen = traffic_scenarios[0]
    snapshot.set_traffic_scen_folder(traffic_scen)
    city_after_deployment = snapshot.load_city_after_deployment()
    city_name = city_name_list[0]
    snapshot.set_solar_data_path(city_name)
    snapshot.set_results_folder(traffic_scen, city_name)
    snapshot.create_results_folders()
    DeploymentHeuristics.simulate_optimization_calibration(city_after_deployment, 'hybrid', battery_info_list)
    '''
    ''' Running the hybrid algorithm with the best traffic-aware sizing results
    best_iteration_dictionary = PreMonitor.get_the_best_iteration_index('traffic_aware','STANDARD')
    for traffic_scen in traffic_scenarios:
        snapshot.set_traffic_scen_folder(traffic_scen)
        city_after_deployment = snapshot.load_city_after_deployment()
        for city_name in city_name_list:
            the_key = city_name+'_ts'+str(traffic_scen)
            traffic_aware_it_no = best_iteration_dictionary[the_key]
            print "======== traffic_scen:{} city_name:{}".format(traffic_scen, city_name)
            snapshot.set_solar_data_path(city_name)
            snapshot.set_results_folder(traffic_scen, city_name)
            battery_info_list = snapshot.load_size_of_sp_and_batt(snapshot.log_file_name('traffic_aware', traffic_aware_it_no))
            PreOperator.calibrate_renewable_city(city_after_deployment, battery_info_list)
    '''
    ''' Calibrating the hybrid algorithm with the best hybrid sizing results
    best_iteration_dictionary = PreMonitor.get_the_best_iteration_index('hybrid')
    for traffic_scen in traffic_scenarios:
        snapshot.set_traffic_scen_folder(traffic_scen)
        city_after_deployment = snapshot.load_city_after_deployment()
        for city_name in city_name_list:
            the_key = city_name+'_ts'+str(traffic_scen)
            traffic_aware_it_no = best_iteration_dictionary[the_key]
            print "======== traffic_scen:{} city_name:{}".format(traffic_scen, city_name)
            snapshot.set_solar_data_path(city_name)
            snapshot.set_results_folder(traffic_scen, city_name, "STANDARD")
            battery_info_list = snapshot.load_size_of_sp_and_batt(snapshot.log_file_name('hybrid', traffic_aware_it_no))
            PreOperator.calibrate_renewable_city(city_after_deployment, battery_info_list)
    '''

    ''' Running the hybrid algorithm with the gurobi sizing results
    for traffic_scen in traffic_scenarios:
        for traffic_index in range(8, 10):
            snapshot.set_traffic_scen_folder(traffic_scen, traffic_index)
            city_after_deployment = snapshot.load_city_after_deployment()
            for city_name in city_name_list:
                print "======== traffic_scen:{} city_name:{} traffic_index:{}".format(traffic_scen, city_name, traffic_index)
                snapshot.set_solar_data_path(city_name)
                snapshot.set_results_folder(traffic_scen, city_name, "GUROBI", traffic_index)
                battery_info_list = snapshot.load_size_of_sp_and_batt(snapshot.log_file_name('gurobi', 0))
                DeploymentHeuristics.simulate_optimization_calibration(city_after_deployment, 'hybrid', battery_info_list)
    '''


    # ----------------------------------- JOURNAL 1 - FIGURES ------------------------------------------
    # Figure 1-2-8 are not related with Python
    # Figure 3 : \label{fig:traffic_day
    # Figure 4 : \label{fig:traffic_hours_of_the_day
    # Figure 5 : \label{fig:traffic_days_of_the_week
    # PreMonitor.plot_traffic_figures()

    # Figure 6 : \label{fig:harvested_hourly
    # PreMonitor.plot_daily_average_energy()
    # Figure 7 : \label{fig:harvested_daily
    # PreMonitor.plot_monthly_average_energy()
    # Figure 9 : \label{fig:assignments
    # PreMonitor.show_assignment()
    # Figure 10 : \label{fig:bs_locations
    # PreMonitor.show_bs_locations()
    # Figure 11 : \label{fig:bc_cumulative}The Performance of Operational Methods in Different Cities and Traffic Rates}
    # PreMonitor.plot_cost_vs_traffic_rate()
    # Figure 12: \label{fig:bc} Comparison of Operational Methods.
    # PreMonitor.plot_bar_comparison_of_operational_method()
    # Figure 13-14: \label{fig:active_unstored_hourly and active_unstored_monthly} Comparison of Operational Methods.
    # PreMonitor.battery_history_plottings()
    # Figure 15: label{fig:brute} Comparison of Our Heuristic with the Brute Force Method
    # PreMonitor.plot_comparison_of_standard_and_gurobi_results()
    # Figure 16-17: label{fig:combination_per_traffic and combination_per_city} Heuristic in different configurations
    # PreMonitor.plot_iterations()
    # Figure Confidence Intervals
    # PreMonitor.plot_confidence_intervals()
    # PreMonitor.plot_confidence_intervals("GUROBI")

    # ----------------------------------- OLD FIGURES ------------------------------------------

    # PreMonitor.remaining_energy()  # a specific battery plotting function
    # PreMonitor.dump_the_best_panel_batt_comb_same_size()
    # PreMonitor.dump_the_best_cal_vals()
    # PreMonitor.plot_iterations_only_one_tr()
    # PreMonitor.plot_iterations_compare_with_prev_data()
    # PreMonitor.plot_iteration_for_each_scenario()
    # PreMonitor.plot_iterations_all_type()
    # PreMonitor.plot_iterations('carbon_emission')
    # '''

    # TRAFFIC TEST
    # PriceTrends.traffic_test()
    # PriceTrends.clean_unneccessary_files("GUROBI")
    print("Running ends at:{}".format(datetime.now()))
