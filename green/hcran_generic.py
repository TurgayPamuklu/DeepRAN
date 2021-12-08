"""HcranGeneric Module.
Creating Main Class for Journal 2 and Grove Journal .

"""

import random
from datetime import datetime

from hcran_monitor import RecordWriter
from snapshot import *


class HcranGeneric:
    rw = None  # RecordWriter

    @staticmethod
    def is_instance_a_parameter():
        if REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER or SOLAR_PANEL_SIZE_AS_A_MULTIPLIER or DU_CAPACITY_SIZE_AS_A_MULTIPLIER:
            return True
        else:
            return False

    def __init__(self, city_name, traffic_scen, splitting_method, instance_index, day):
        if HcranGeneric.is_instance_a_parameter():
            self.record_parameter = instance_index * 1000 + day
        else:
            self.record_parameter = day
        self.day = day
        self.log_file = None
        self.traffic_load_multiplier = traffic_scen
        self.city_name = city_name
        self.traffic_scen = traffic_scen
        self.scenario = "{}_{}".format(self.city_name, self.traffic_scen)
        self.snapshot = Snapshot()
        self.snapshot.set_solar_data_path(city_name)
        if JOURNAL4:
            self.snapshot.set_traffic_scen_folder(1)  # in Grove journal (JOURNAL4) we use the same traffic folder
            # but we multiply the each traffic value to increase the traffic rates.
        else:
            self.snapshot.set_traffic_scen_folder(traffic_scen)
        self.ENERGY_TRANSFER_AVAILABLE = False

        self.splitting_method = splitting_method
        self.energy_prices_per_hour = [0.29] * 6 + [0.46] * 11 + [0.70] * 5 + [0.29] * 2  # turkey pricing system

        self.n_of_hours_per_day = 24

        self.n_of_time_slot = self.n_of_hours_per_day
        self.n_of_sc_per_ec = 4  # Number of Small Cell per each Edge Cloud
        self.n_of_cell_per_ec = self.n_of_sc_per_ec + 1
        # self.n_of_ec = 8 * (2 ** (traffic_scen - 1))  # Number of Remote Site
        self.n_of_ec = 6 * self.remote_site_multiplier  # Number of Remote Site
        self.n_of_cloud = self.n_of_ec + 1  # (ECs + CC)

        self.cc_index = self.n_of_ec  # Index that show cs (it is at the end RSes)

        self.n_of_du_per_ec = 25 * self.traffic_load_multiplier  # 2                                                                               # Number of DUs in one RS
        self.n_of_du_in_cc = 25 * self.traffic_load_multiplier  # 6                                                                               # Number of DUs in CS
        self.n_of_du_in_all_ec = self.n_of_du_per_ec * self.n_of_ec  # Number of DU in all RS
        self.n_of_du = self.n_of_du_in_all_ec + self.n_of_du_in_cc  # Number of DU in Network
        self.n_of_up_function = 4  # Number of User Process/Function

        self.number_of_ue_per_ec = 50  # Number of User in one RS
        self.number_of_ue = self.number_of_ue_per_ec * self.n_of_ec  # Total Number of User

        if DU_CAPACITY_SIZE_AS_A_MULTIPLIER:
            du_cap_multiplier = instance_index
        else:
            du_cap_multiplier = 1
        self.L_EC = 10 * du_cap_multiplier  # 15  # DU capacity in RS number of URF that can be processed in a DU
        self.L_CC = 50 * 1  # 50

        self.traffic_load = [[1 for x in range(self.n_of_time_slot)] for x in range(self.number_of_ue)]  # only for definition we will load real traffic data later
        self.delay_threshold = [[0 for x in range(self.n_of_time_slot)] for x in range(self.number_of_ue)]

        self.ge = [[0 for x in range(self.n_of_time_slot)]
                   for x in range(self.n_of_cloud)]

        # power constants for SC
        P_SC_RF = 2.6
        P_SC_PA = 71.4
        self.P_SC_ANALOG = P_SC_RF + P_SC_PA
        P_CPU = 25  # 200 GOPS  GOPS to Watt Conversion 8
        P_OFDM = 20  # 160 GOPS
        P_FILTER = 10  # 80 GOPS
        self.P_SC_BB = P_CPU + P_OFDM + P_FILTER
        # power constants for EC
        P_EC_RF = 9.18
        P_EC_PA = 1100.0
        P_EC_OVERHEAD = (P_EC_RF + P_EC_PA) * 0.1
        P_EC_DU_STA = 750.0
        self.P_EC_STA = 500.0  # 750.0 P_EC_RF + P_EC_PA + P_EC_OVERHEAD + P_EC_DU_STA
        self.P_EC_DU = 400.0
        # power constants for CC
        self.P_CC_STA = 1000.0
        self.P_CC_DU = 400.0

        # Delay Calculations
        self.D_OPTICAL = 0.4E-3
        self.D_MWAVE = 30E-6
        self.D_SWITCH = 5.2E-6
        self.D_CONS_FROM_EC = self.D_OPTICAL + self.D_SWITCH * 2
        # D_FROM_SC = self.decision_g * self.D_MWAVE
        self.DU_GOPS_PERF = 333E-6  # 300 GOPS per second
        # D_PROCESS = Traffic_load_All_2_GOPS * self.DU_GOPS_PERF
        self.D_RSF_TRSF = 1E-3  # 1ms radio subframe
        self.D_RSF_NRSF = 4E-5
        # D_RSF = self.D_RSF_TRSF * self.D_RSF_NRSF * Traffic_Load_All
        self.D_NOF_TOF = 125E-6
        self.D_NOF_CONS = 81E-3
        # D_NOF = self.D_NOF_TOF * self.D_NOF_CONS * Traffic_load_AT_CC
        # Delay = self.D_CONS_FROM_EC + D_FROM_SC + D_PROCESS + D_RSF + D_NOF
        # Other Constants
        self.SMALL_OMEGA = 0.5  # 0.5 ENERGY_SELLING_PENALTY
        self.RHO = 0.9  # BS utilization value
        self.INV_UPSILON = 1  # (5.0 / (USER_CHUNK_SIZE * PEAK_TRAFFIC_PER_HOUR_PER_MBYTE))   # 1e-15 #  user chunk size Traffic Rate to GOPS Converter
        self.INV_OMEGA = 10  # CRF to GOPS Converter (1 CRF equals to 3 URF)

        # GRB_RANGE Defining ranges for improving readibility in later code
        self.r_t = range(self.n_of_time_slot)
        self.r_i = range(self.number_of_ue)  # i == r_user
        self.r_j = range(self.n_of_cell_per_ec * self.n_of_ec)  # SCs + ECs
        self.r_k = range(self.n_of_ec)  # k == r_k
        self.r_ec = range(self.n_of_ec)
        self.r_cloud = range(self.n_of_cloud)
        self.r_du = range(self.n_of_du)
        self.r_du_in_cc = range(self.n_of_du_in_all_ec, self.n_of_du)
        self.r_up = range(self.n_of_up_function)

        self.solar_panel_size = [0 for x in self.r_cloud]
        self.battery_capacity = [0 for x in self.r_cloud]

        RANDOM_SOLAR_PANEL_SIZE = False
        if PURE_GRID:
            for k in self.r_k:
                self.solar_panel_size[k] = 0
                self.battery_capacity[k] = 0
            self.solar_panel_size[self.cc_index] = 0
            self.battery_capacity[self.cc_index] = 0
        elif RANDOM_SOLAR_PANEL_SIZE:
            random.seed(8)  # same seed:: battery and solar panel sizing
            for r in self.r_k:
                self.solar_panel_size[r] = (random.randint(0, 25) % 5) * 5
                if self.solar_panel_size[r] == 0:
                    self.battery_capacity[r] = 0
                else:
                    self.battery_capacity[r] = (random.randint(1, 4)) * 2500
            self.solar_panel_size[self.cc_index] = 20
            self.battery_capacity[self.cc_index] = 10000
        else:
            if SOLAR_PANEL_SIZE_AS_A_MULTIPLIER:
                solar_panel_multiplier = instance_index
            else:
                solar_panel_multiplier = 1
            for k in self.r_k:
                self.solar_panel_size[k] = 20 * solar_panel_multiplier
                self.battery_capacity[k] = 20000 * solar_panel_multiplier
            self.solar_panel_size[self.cc_index] = 80 * solar_panel_multiplier
            self.battery_capacity[self.cc_index] = 50000 * solar_panel_multiplier

        # Init variables
        self.decision_s = [[0 for x in self.r_t] for x in self.r_cloud]
        self.decision_a = [[0 for x in self.r_t] for x in self.r_du]
        self.decision_m = [[[[0 for x in self.r_t] for x in self.r_up] for x in self.r_du] for x in self.r_i]  # idft
        if self.ENERGY_TRANSFER_AVAILABLE:
            self.energy_transfer_efficiency = 0.9  # 0.9  # energy transfer loss between two sites
            self.decision_x = [[[0 for x in self.r_t] for x in self.r_cloud] for x in self.r_cloud]  # x[i][j][t] -> energy transfer from i to j in time slot t
        if "BatteryAware" in self.splitting_method:
            self.decision_be = [[0 for x in self.r_t] for x in self.r_cloud]
        self.decision_p = [[0 for x in self.r_t] for x in self.r_cloud]

        self.remaining_battery_energy = [[0 for x in self.r_t] for x in self.r_cloud]  # Note: readable decision_be for BatteryAware
        self.initial_battery_energy = None

    def load_solar_energy(self):
        # LOAD SOLAR ENERGY
        if "NonRenewable" in self.splitting_method:
            for time_slot in self.r_t:
                for k in self.r_cloud:
                    self.ge[k][time_slot] = 0
        else:
            solar_energy = self.snapshot.load_solar_energy()
            ren_en_per_hour = []
            if NUMBER_OF_SIMULATION_DAY == 1:  # AVERAGE SOLAR
                if "Static" in self.splitting_method:
                    # GENERATED SOLAR ENERGY
                    day_period_en = solar_energy.get_average_regeneration_energy_in_a_day(1)
                    total_ren_en = sum(day_period_en)
                    for k in self.r_cloud:
                        self.ge[k][0] = total_ren_en * self.solar_panel_size[k]
                else:
                    ren_en_per_hour = solar_energy.get_average_regeneration_energy_in_a_day(1)
                    for t in range(self.n_of_hours_per_day):
                        for k in self.r_cloud:
                            self.ge[k][t] = ren_en_per_hour[t] * self.solar_panel_size[k]
            else:  # Get energy for different days
                if NUMBER_OF_SIMULATION_DAY == 12:  # for each month
                    ren_en_per_hour = solar_energy.get_average_regeneration_energy_in_a_month_per_hour(self.day, 1)
                elif NUMBER_OF_SIMULATION_DAY == 4:  # for each second month of a season
                    ren_en_per_hour = solar_energy.get_average_regeneration_energy_in_a_month_per_hour(self.day * 3, 1)
                else:  # otherwise get the first x days in a year
                    for hour_of_the_day in range(self.n_of_hours_per_day):
                        ren_en_per_hour.append(solar_energy.harvest_the_solar_energy(self.day, hour_of_the_day, 1))
                for hours in range(self.n_of_hours_per_day):
                    for k in self.r_cloud:
                        ren_en_per_time_slot = ren_en_per_hour[hours]
                        self.ge[k][hours] = ren_en_per_time_slot * self.solar_panel_size[k]

    # Setting Battery Energy
    def set_initial_battery_energy(self, initial_battery_energy=None):
        INITIAL_BATTERY_IS_ALWAYS_ZERO = True
        if INITIAL_BATTERY_IS_ALWAYS_ZERO:
            initial_battery_energy = []
            for i in self.r_cloud:
                initial_battery_energy.append(0)
        else:
            if self.day == 0:
                initial_battery_energy = []
                for i in self.r_cloud:
                    initial_battery_energy.append(0)
                '''
                initial_battery_energy.append(self.battery_capacity[0])
                initial_battery_energy.append(self.battery_capacity[1])
                initial_battery_energy.append(self.battery_capacity[2])
                initial_battery_energy.append(self.battery_capacity[3])
                initial_battery_energy.append(self.battery_capacity[4])
                '''
        self.initial_battery_energy = initial_battery_energy

    # Getting Battery Energy
    def get_remaining_battery_energy(self):
        remaining_battery_energy = []
        for site in self.r_cloud:
            remaining_battery_energy.append(self.remaining_battery_energy[site][23])  # it will not work for Traffic aware!
        return remaining_battery_energy

    def init_the_record_writer(self):
        self.rw = RecordWriter(self.splitting_method, self.scenario, self.record_parameter, self.number_of_ue_per_ec)

    def _print_general_info(self):
        log_string = "========  GUROBI START at:{} Splitting Method:{} City:{} Traffic_Scen:{} ======== \n"
        log_args = (datetime.now(), self.splitting_method, self.city_name, self.traffic_scen)
        self.rw.log_data(log_string, *log_args)

        log_string = "======== Traffic Load Multiplier:{} Day:{} ======== \n"
        log_args = (self.traffic_load_multiplier, self.day)
        self.rw.log_data(log_string, *log_args)

        log_string = "======== Panel Sizes:{} Battery Capacities :{} ======== \n"
        log_args = (self.solar_panel_size, self.battery_capacity)
        self.rw.log_data(log_string, *log_args)

        log_string = "======== DU Cap (CS/RS):{}/{} ======== \n"
        log_args = (self.L_CC, self.L_EC)
        self.rw.log_data(log_string, *log_args)

        self.rw.log_data("======== Initial Battery Energy:{}/{} ======== \n", *self.initial_battery_energy)

        log_string = "======== Static Energy Consumption(CC/EC):{}/{} ======== \n"
        log_args = (self.n_of_time_slot * self.P_CC_STA, self.n_of_time_slot * self.n_of_ec * self.P_EC_STA)
        self.rw.log_data(log_string, *log_args)

    def _print_total_number_of_active_du(self, total_number_of_active_du_cs, total_number_of_active_du_rs):
        ########################################################################################################
        # Print and recording operations
        self.rw.log_data("CC DU Energy Consumption:{}\n", *(total_number_of_active_du_cs * self.P_CC_DU,))
        self.rw.log_data("EC DU Energy Consumption:{}\n", *(total_number_of_active_du_rs * self.P_EC_DU,))

    def calculate_total_consumption(self, number_of_active_du_per_site):
        total_consumption = [[0 for x in self.r_t] for x in self.r_cloud]
        for t in self.r_t:
            for r in self.r_cloud:
                if r == self.cc_index:
                    total_consumption[r][t] = int(self.P_CC_STA + number_of_active_du_per_site[r][t] * self.P_CC_DU)
                else:
                    total_consumption[r][t] = int(self.P_EC_STA + number_of_active_du_per_site[r][t] * self.P_EC_DU)
        return total_consumption

    def calculate_fossil_consumption(self, total_consumption):
        fossil_consumption = [[0 for x in self.r_t] for x in self.r_cloud]
        for r in self.r_cloud:
            for t in self.r_t:
                fossil_consumption[r][t] = total_consumption[r][t] - self.decision_s[r][t]
                if fossil_consumption[r][t] < 0:
                    fossil_consumption[r][t] = 0
        return fossil_consumption

    def calculate_fossil_consumption_in_specific_time(self, t, total_consumption):
        fossil_consumption = [0 for x in self.r_cloud]
        for r in self.r_cloud:
            fossil_consumption[r] = total_consumption[r][t] - self.decision_s[r][t]
            if fossil_consumption[r] < 0:
                fossil_consumption[r] = 0
        return fossil_consumption

    def calculate_fossil_consumption_total_in_specific_time(self, t, total_consumption):
        fossil_consumption = self.calculate_fossil_consumption_in_specific_time(t, total_consumption)
        return sum(fossil_consumption)

    def _print_variables_3(self, filter, data):
        filter_index = RecordWriter.filter_list.index(filter)
        self.rw.log_data("---- " + RecordWriter.filter_list_readable[filter_index] + " ----\n")
        self.rw.print_header("TIME", self.r_t)
        for sender_site in self.r_cloud:
            self.rw.log_data("-------------------------------SENDER SITE [{}]-------------------------------\n", *(sender_site,))
            for receiver_site in self.r_cloud:
                self.rw.log_data("--RECEIVER SITE [{}]--", *(receiver_site,))
                for t in self.r_t:
                    self.rw.log_data("{:" + PRINT_TAB_SIZE + "}", *(data[sender_site][receiver_site][t],))
                    self.rw.append_record_data(RecordWriter.set_filter_3(filter, sender_site, receiver_site, t), data[sender_site][receiver_site][t])
                self.rw.log_data("\n")

    def _print_variables(self, filter, data_normal):
        data = [[int(x) for x in y] for y in data_normal]
        total_in_a_site = [0 for x in self.r_cloud]
        filter_index = RecordWriter.filter_list.index(filter)
        self.rw.log_data("---- " + RecordWriter.filter_list_readable[filter_index] + " ----\n")
        self.rw.print_header("TIME", self.r_t)
        for site in self.r_cloud:
            self.rw.log_data("-SITE[{}]\t", *(site,))
            for t in self.r_t:
                total_in_a_site[site] += data[site][t]
                self.rw.log_data("{:" + PRINT_TAB_SIZE + "}\t", *(data[site][t],))
                self.rw.append_record_data(RecordWriter.set_filter(filter, site, t), data[site][t])
            self.rw.log_data("\n")
        self.rw.log_data("TOTAL Value Per Site:\t")
        for site in self.r_cloud:
            self.rw.log_data("{:" + PRINT_TAB_SIZE + "}\t", *(total_in_a_site[site],))
        self.rw.log_data("TOTAL:{:" + PRINT_TAB_SIZE + "}\n", *(sum(total_in_a_site),))

    def _calculate_the_obj_val(self, decision_a, decision_s, decision_p):
        cc_sta_price = 0
        cc_dyn_price = 0
        cc_renewable_energy_profit = 0
        cc_sold_profit = 0
        for t in self.r_t:
            cc_sta_price += self.P_CC_STA * self.energy_prices_per_hour[t]
        for t in self.r_t:
            number_of_active_du = 0
            for d in self.r_du_in_cc:
                number_of_active_du += decision_a[d][t]
            cc_dyn_price += self.P_CC_DU * number_of_active_du * self.energy_prices_per_hour[t]
            cc_renewable_energy_profit += decision_s[self.cc_index][t] * self.energy_prices_per_hour[t]
            cc_sold_profit += decision_p[self.cc_index][t] * self.SMALL_OMEGA * self.energy_prices_per_hour[t]

        ec_static_price = 0
        ec_dynamic_price = 0
        ec_renewable_energy_profit = 0
        ec_sold_profit = 0
        for r in self.r_k:
            du_set_in_r = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
            for t in self.r_t:
                ec_static_price += self.P_EC_STA * self.energy_prices_per_hour[t]
            for t in self.r_t:
                number_of_active_du = 0
                for d in du_set_in_r:
                    number_of_active_du += decision_a[d][t]
                ec_dynamic_price += self.P_EC_DU * number_of_active_du * self.energy_prices_per_hour[t]
                ec_renewable_energy_profit += decision_s[r][t] * self.energy_prices_per_hour[t]
                ec_sold_profit += decision_p[r][t] * self.SMALL_OMEGA * self.energy_prices_per_hour[t]

        calculated_obj = cc_sta_price + cc_dyn_price - cc_renewable_energy_profit - cc_sold_profit
        calculated_obj += ec_static_price + ec_dynamic_price - ec_renewable_energy_profit - ec_sold_profit

        self.rw.log_data("static_price:{}\t{}\n", *(cc_sta_price, ec_static_price))
        self.rw.log_data("dynamic_price:{}\t{}\n", *(cc_dyn_price, ec_dynamic_price))
        self.rw.log_data("renewable_energy_profit:{}\t{}\n", *(cc_renewable_energy_profit, ec_renewable_energy_profit))
        self.rw.log_data("sold_profit:{}\t{}\n", *(cc_sold_profit, ec_sold_profit))

        return calculated_obj

    def calculate_number_of_active_du_specific_site(self, r, t, du_activity):
        number_of_active_du = 0
        if r == self.cc_index:
            d_range = self.r_du_in_cc
        else:
            d_range = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
        for d in d_range:
            number_of_active_du += du_activity[d][t]
        return number_of_active_du

    def calculate_number_of_active_du_per_site(self, du_activity):
        number_of_active_du_per_site = [[0 for x in self.r_t] for x in self.r_cloud]
        total_number_of_active_du_cs = 0
        total_number_of_active_du_rs = 0
        for t in self.r_t:
            for d in self.r_du_in_cc:
                total_number_of_active_du_cs += du_activity[d][t]
                number_of_active_du_per_site[self.cc_index][t] += du_activity[d][t]
        for t in self.r_t:
            for r in self.r_k:
                du_set_in_r = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
                for d in du_set_in_r:
                    total_number_of_active_du_rs += du_activity[d][t]
                    number_of_active_du_per_site[r][t] += du_activity[d][t]
        return number_of_active_du_per_site, total_number_of_active_du_cs, total_number_of_active_du_rs

    def _get_cloud_from_du(self, d):
        if d >= self.n_of_du_per_ec * self.cc_index:
            return self.cc_index
        else:
            ec_no = d / self.n_of_du_per_ec
        return int(ec_no)

    def _get_cloud_from_user(self, i):
        ec_no = i / self.number_of_ue_per_ec
        return int(ec_no)
