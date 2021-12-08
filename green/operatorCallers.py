"""operatorCallers module
The classes in this module are responsible to call simulator functions (Journal 1).
"""

import random
from datetime import datetime

import numpy as np

from heuristic import E
from heuristic import OptimizationForCapitalExpenditure
from operators import RenewableOperator
from operators import run_the_system_for_one_day
from renewableEnergy import Battery
from snapshot import *

__author__ = 'turgay.pamuklu'


class PreOperator(object):

    @staticmethod
    def operate_renewable_city_for_same_panel_and_batteries(co, operational_method, iteration_no, same_battery_size, same_solar_size):
        snapshot = Snapshot()
        cal_val = CalibrationParameters.__dict__[operational_method]
        battery_info_list = []
        for x in range(co.bs_count):
            if co.bs_types[x] == BSType.MACRO:
                battery_info_list.append((same_solar_size, same_battery_size))
            else:  # micro base stations are always have a battery size 2500kWh
                # battery_info_list.append((0, 0))
                battery_info_list.append((1, 2500))
        ro = RenewableOperator(co, battery_info_list, cal_val)
        battery_info_list, battery_history_list = ro.operate_sim_duration()
        snapshot.save_size_of_sp_and_batt(battery_info_list, snapshot.log_file_name(operational_method, iteration_no))
        snapshot.save_battery_history(battery_history_list, snapshot.log_file_name(operational_method, iteration_no))

    @staticmethod
    def operate_renewable_city(co, operational_method, iteration_no, size_of_solar_panels_and_batteries=None):
        snapshot = Snapshot()
        cal_val = CalibrationParameters.__dict__[operational_method]
        if size_of_solar_panels_and_batteries is None:
            if iteration_no == 0:
                size_of_solar_panels_and_batteries = []
                for x in range(co.bs_count):
                    size_of_solar_panels_and_batteries.append((1, 2500))  # old method
                    '''
                    if co.bs_types[x] == BSType.MACRO:
                        size_of_solar_panels_and_batteries.append((3, 12500))
                    else:
                        size_of_solar_panels_and_batteries.append((1, 2500))
                    '''
            else:
                size_of_solar_panels_and_batteries = snapshot.load_size_of_sp_and_batt(snapshot.log_file_name(operational_method, iteration_no))
        ro = RenewableOperator(co, size_of_solar_panels_and_batteries, cal_val)
        size_of_solar_panels_and_batteries, battery_history_list = ro.operate_sim_duration()
        snapshot.save_size_of_sp_and_batt(size_of_solar_panels_and_batteries, snapshot.log_file_name(operational_method, iteration_no))
        snapshot.save_battery_history(battery_history_list, snapshot.log_file_name(operational_method, iteration_no))

    @staticmethod
    def greedy_remove_deployed_base_stations(s):
        bs_list_that_we_try_to_undeploy = np.copy(s.bs_deployed_and_active)
        comp_val_list = np.array([0 for x in range(s.c.bs_count)])
        run_the_system_for_one_day(s.bs_deployed_and_active,
                                   s.assigning,
                                   s.remaining_bs_capacity,
                                   s.nsr,
                                   bs_list_that_we_try_to_undeploy,
                                   comp_val_list,
                                   s.c.can_bs_list)

    @staticmethod
    def run_only_one_iteration(co):
        base_iteration_no = 100
        battery_info_list = []
        for x in range(co.bs_count):
            battery_info_list.append((0, 0))
        ro = RenewableOperator(co, battery_info_list, 0)
        battery_info_list, battery_history_list = ro.operate_sim_duration()
        print("bs count:{}".format(co.bs_count))
        (ren_con_total, fossil_con_total) = ro.get_consumption_data(NUMBER_OF_SIMULATION_DAY)

        print("ren_con_total: {} fossil_con_total: {} TOTAL: {}".format(ren_con_total,
                                                                        fossil_con_total,
                                                                        fossil_con_total + ren_con_total))
        tco = fossil_con_total * E.LIFE_TIME_ENERGY_COST
        print("TCO: {}".format(tco))

        if False:
            operational_method = 'fossil'
            snapshot = Snapshot()
            snapshot.save_size_of_sp_and_batt(battery_info_list, snapshot.log_file_name(operational_method, 0))
            snapshot.save_battery_history(battery_history_list, snapshot.log_file_name(operational_method, 0))

        return co, ro, tco

    @staticmethod
    def calibrate_renewable_city(co, battery_info_list):
        snapshot = Snapshot()
        lowest_fossil_consumption = 10000000000.0
        lfc_cal = -1
        base_iteration_no = 100
        operational_method = 'hybrid_with_traffic_sizing'
        for calibration_val in np.arange(1, 1.1, 0.2):
            iteration_no = base_iteration_no + calibration_val
            ro = RenewableOperator(co, battery_info_list, calibration_val)
            battery_info_list, battery_history_list = ro.operate_sim_duration()

            (ren_con_total, fossil_con_total) = ro.get_consumption_data(NUMBER_OF_SIMULATION_DAY)
            if fossil_con_total < lowest_fossil_consumption:
                lfc_cal = calibration_val
                lowest_fossil_consumption = fossil_con_total
            print("cv: {} --> ren_con_total: {} fossil_con_total: {} TOTAL: {}".format(calibration_val, ren_con_total,
                                                                                       fossil_con_total,
                                                                                       fossil_con_total + ren_con_total))
            print("operational expenditure: {}".format(fossil_con_total * E.LIFE_TIME_ENERGY_COST))

            snapshot.save_size_of_sp_and_batt(battery_info_list, snapshot.log_file_name(operational_method, iteration_no))
            snapshot.save_battery_history(battery_history_list, snapshot.log_file_name(operational_method, iteration_no))

        print("the lowest fossil consumption index:{} value:{}".format(lfc_cal, lowest_fossil_consumption))
        return co, ro


class DecisionValues(object):
    INC_SOLAR = [0]
    INC_BAT = [1]
    DEC_SOLAR = [2]
    ALL = [0, 1, 2]


class DeploymentHeuristics(object):

    @staticmethod
    def get_decision(tabu_vals, decision_step):
        if decision_step < 3:
            return decision_step
        else:
            return DeploymentHeuristics.get_random_decision(tabu_vals)

    @staticmethod
    def get_random_decision(tabu_vals):
        print("--get_random_decision tabu_vals:{}".format(tabu_vals))
        rand_val = random.randint(0, 2)
        while rand_val in tabu_vals:
            rand_val = random.randint(0, 2)
        return rand_val

    @staticmethod
    def diagnose_operational_methods(city_after_deployment, op_method_for_loading_size_of_batt_and_panels, op_method_for_comparing, it_no):
        snapshot = Snapshot()
        ofce = OptimizationForCapitalExpenditure(op_method_for_loading_size_of_batt_and_panels, city_after_deployment, it_no)
        ofce.update_battery_info()
        print("Op Method for Loading:{}{}:: ".format(op_method_for_loading_size_of_batt_and_panels, it_no))
        ofce.calculating_total_expenditure(True)
        cal_val = CalibrationParameters.__dict__[op_method_for_comparing]
        size_of_solar_panels_and_batteries = snapshot.load_size_of_sp_and_batt(
            snapshot.log_file_name(op_method_for_loading_size_of_batt_and_panels, it_no))
        ro = RenewableOperator(city_after_deployment, size_of_solar_panels_and_batteries, cal_val)
        battery_history_list = ro.operate_sim_duration()
        print("Op Method for Comparing:{}{}:: ".format(op_method_for_loading_size_of_batt_and_panels, it_no))
        ofce.bs_lifecycle_data = ofce.sum_values_of_each_time_slots(battery_history_list)
        ofce.calculating_total_expenditure(True)

    @staticmethod
    def simulate_with_same_size_solar_and_batteries(city_after_deployment, operational_method):
        ofce = OptimizationForCapitalExpenditure(operational_method, city_after_deployment, 0)
        for panel_size in range(1, E.MAX_PANEL_SIZE + 1):
            for battery_size_index in range(1, E.MAX_BATTERY_SIZE + 1):
                battery_size = battery_size_index * Battery.INCREMENTING_BATTERY_SIZE
                iteration_no = (panel_size - 1) * E.MAX_BATTERY_SIZE + battery_size_index - 1
                print('------- ITERATION NO:{} at:{} battery_size:{}-------'.format(iteration_no, datetime.now(), battery_size))
                PreOperator.operate_renewable_city_for_same_panel_and_batteries(city_after_deployment, operational_method, iteration_no, battery_size,
                                                                                panel_size)
                ofce.update_battery_info()
                lowest_total_expenditure, current_total_expenditure, previous_total_expenditure = ofce.calculating_total_expenditure()
                print("current_total_expenditure:{} and previous_total_expenditure:{}".format(current_total_expenditure, previous_total_expenditure))
                ofce.increase_iteration_no()

    @staticmethod
    def simulate_with_zero_size_solar_and_batteries(city_after_deployment):
        operational_method = 'traffic_aware'
        ofce = OptimizationForCapitalExpenditure(operational_method, city_after_deployment, 0)
        panel_size = 0
        battery_size_index = 0

        battery_size = battery_size_index * Battery.INCREMENTING_BATTERY_SIZE
        iteration_no = 0
        print('------- ITERATION NO:{} at:{} battery_size:{}-------'.format(iteration_no, datetime.now(), battery_size))
        PreOperator.operate_renewable_city_for_same_panel_and_batteries(city_after_deployment, operational_method, iteration_no, battery_size,
                                                                        panel_size)
        ofce.update_battery_info()
        lowest_total_expenditure, current_total_expenditure, previous_total_expenditure = ofce.calculating_total_expenditure()
        print("current_total_expenditure:{} and previous_total_expenditure:{}".format(current_total_expenditure, previous_total_expenditure))

    @staticmethod
    def simulate_random_heuristic(city_after_deployment, operational_method):
        snapshot = Snapshot()
        cal_val = CalibrationParameters.__dict__[operational_method]
        ofce = OptimizationForCapitalExpenditure(operational_method, city_after_deployment, 0)
        for i in range(100):
            ofce.random_panel_and_battery_sizes()
            ro = RenewableOperator(city_after_deployment, ofce.size_of_sp_and_batt, cal_val)
            size_of_solar_panels_and_batteries, battery_history_list = ro.operate_sim_duration()
            snapshot.save_size_of_sp_and_batt(size_of_solar_panels_and_batteries, snapshot.log_file_name(operational_method, ofce.iteration_no))
            snapshot.save_battery_history(battery_history_list, snapshot.log_file_name(operational_method, ofce.iteration_no))
            ofce.update_battery_info()
            lowest_total_expenditure, current_total_expenditure, previous_total_expenditure = ofce.calculating_total_expenditure()
            print("it:{} :: current te:{} / previous te:{}".format(ofce.get_iteration_no(), current_total_expenditure, previous_total_expenditure))
            ofce.increase_iteration_no()
            snapshot.save_size_of_sp_and_batt(ofce.size_of_sp_and_batt, snapshot.log_file_name('hybrid', ofce.get_iteration_no()))

    @staticmethod
    def simulate_optimization_calibration(city_after_deployment, operational_method, size_of_solar_panels_and_batteries):
        ofce = OptimizationForCapitalExpenditure(operational_method, city_after_deployment, 0)
        print('------- OP_METHOD:{} ITERATION NO:{} at:{} -------'.format(operational_method, ofce.get_iteration_no(), datetime.now()))
        # 15 years simulation !!
        PreOperator.operate_renewable_city(city_after_deployment, operational_method, ofce.get_iteration_no(), size_of_solar_panels_and_batteries)
        size_of_solar_panels_and_batteries = None  # if we call simulate method for a calibration purpose, we have to assign None to this variable
        # DUMP & CALCULATIONS
        ofce.update_battery_info()
        # ofce.dump_life_cycle_data_per_bs_types()
        # ofce.dump_panel_size_and_battery_size_map()
        lowest_total_expenditure, current_total_expenditure, previous_total_expenditure = ofce.calculating_total_expenditure()
        # DEPLOYMENT DECISIONS
        print("it:{} :: current te:{} / previous te:{}".format(ofce.get_iteration_no(), current_total_expenditure, previous_total_expenditure))


    @staticmethod
    def multi_test(operational_method):
        print("operational_method is:{}".format(operational_method))

    @staticmethod
    def simulate(city_after_deployment, operational_method):
        ofce = OptimizationForCapitalExpenditure(operational_method, city_after_deployment, 0)
        total_expenditure_reduce_count = 0
        decision_step = 0
        snapshot = Snapshot()
        while decision_step <= 3:
            print('------- OP_METHOD:{} ITERATION NO:{} Decision Step:{} at:{} -------'.format(operational_method, ofce.get_iteration_no(), decision_step, datetime.now()))
            # sys.stdout.flush()
            # 15 years simulation !!
            PreOperator.operate_renewable_city(city_after_deployment, operational_method, ofce.get_iteration_no())
            # DUMP & CALCULATIONS
            ofce.update_battery_info()
            # ofce.dump_life_cycle_data_per_bs_types()
            # ofce.dump_panel_size_and_battery_size_map()
            lowest_total_expenditure, current_total_expenditure, previous_total_expenditure = ofce.calculating_total_expenditure()
            # DEPLOYMENT DECISIONS
            print("it:{} :: current te:{} / previous te:{}".format(ofce.get_iteration_no(), current_total_expenditure, previous_total_expenditure))
            if current_total_expenditure > previous_total_expenditure:
                total_expenditure_reduce_count += 1
                if total_expenditure_reduce_count >= 2:  # 2 times
                    total_expenditure_reduce_count = 0
                    print(
                        '2 fails in a row, we will return the battery&panel size configuration to the three iterations before the current iteration')
                    decision_step += 1
            else:
                total_expenditure_reduce_count = 0
            we_change_deployment_decisions = False
            while not we_change_deployment_decisions:
                if decision_step == 0 or decision_step == 2:
                    print('Decision: INC_SOLAR')
                    we_change_deployment_decisions = ofce.increase_size_of_panels()
                    if we_change_deployment_decisions is False:
                        decision_step += 1
                        print("---------------------------------------------------------------------")
                elif decision_step == 1 or decision_step == 3:
                    print('Decision: INC_BAT')
                    we_change_deployment_decisions = ofce.increase_size_of_batteries()
                    if we_change_deployment_decisions is False:
                        decision_step += 1
                        print("---------------------------------------------------------------------")
                else:
                    break

            ofce.increase_iteration_no()
            snapshot.save_size_of_sp_and_batt(ofce.size_of_sp_and_batt, snapshot.log_file_name(operational_method, ofce.get_iteration_no()))
        print("Simulate ends:{}".format(datetime.now()))
        #sys.stdout.flush()

