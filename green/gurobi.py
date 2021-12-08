"""Crosshaul Module.
Creating Gurobi Class for Journal 1.

"""

from datetime import datetime
from multiprocessing import Process

from gurobipy import *  # GRB_INIT

from helpers import *
from heuristic import E
from renewableEnergy import Battery
from snapshot import *


class GreenGurobi:  # CONSTANTS
    NUMBER_OF_BASE_STATION = None
    NUMBER_OF_USER_LOCATION = 1600
    NUMBER_OF_DAYS = 4
    NUMBER_OF_TIME_SLICE_PER_DAY = 24
    NUMBER_OF_TIME_SLICE = NUMBER_OF_TIME_SLICE_PER_DAY * NUMBER_OF_DAYS
    RHO = 0.8
    C_S = E.SOLAR_PANEL_COST_OF_1KW_SIZE  # 1000 # GRB_GIVEN
    C_B = E.BATTERY_COST_OF_2500KW_SIZE  # 500
    N_Y = E.YEARS_OF_LIFE_CYCLE  # 15
    C_E = E.ELECTRICITY_COST_KW_PER_HOUR * 0.001  # 0.16 * 0.001
    A_B = 2500  # INCREMENTING_BATTERY_SIZE

    pc = None
    sr = None
    method = None
    number_of_time_slice_for_input = None
    co = None

    m = None  # Model

    def __init__(self, co, method):
        self.co = co
        self.NUMBER_OF_BASE_STATION = self.co.bs_count
        self.method = method
        if self.method == 'MonthlyAverage':
            self.number_of_time_slice_for_input = 12 * self.NUMBER_OF_TIME_SLICE_PER_DAY
        elif self.method == 'SeasonlyAverage':
            self.number_of_time_slice_for_input = 4 * self.NUMBER_OF_TIME_SLICE_PER_DAY
        else:
            self.number_of_time_slice_for_input = self.NUMBER_OF_TIME_SLICE

        self.ge = [1 for x in range(self.number_of_time_slice_for_input)]
        self.ud = [[1 for x in range(self.NUMBER_OF_USER_LOCATION)] for x in range(self.number_of_time_slice_for_input)]

        self.r_i = list(range(self.NUMBER_OF_BASE_STATION))  # GRB_RANGE
        self.r_j = list(range(self.NUMBER_OF_USER_LOCATION))
        self.r_t = list(range(self.NUMBER_OF_TIME_SLICE))

        self.r_y = list(range(self.NUMBER_OF_DAYS))
        self.r_d = list(range(self.NUMBER_OF_TIME_SLICE_PER_DAY))

        # Init variables
        self.decision_x = [[0 for x in self.r_t] for x in self.r_i]
        self.decision_r = [[0 for x in self.r_t] for x in self.r_i]
        self.decision_z = [[[0 for x in self.r_t] for x in self.r_j] for x in self.r_i]
        self.decision_s = [0 for x in self.r_i]
        self.decision_b = [0 for x in self.r_i]

        self.m = Model()  # GRB_INIT
        #   self.m.params.MIPGap = 0.01
        self.m.params.TimeLimit = 12 * 60 * 60
        self.m.params.NumericFocus = 1
        # self.m.params.MIPFocus = 1
        # self.m.params.Heuristics = 0.25
        # self.m.params.Method = 2
        # self.m.params.NodeMethod = 2

    @staticmethod
    def print_header(r_t):
        print(("{:4}".format("BS")), end=' ')
        for t in r_t:
            print(("{:4}".format(t)), end=' ')
        print()

    def gurobi_load_data(self):
        snapshot = Snapshot()
        # POWER CONSUMPTION OF EACH BASE STATION
        if Battery.OLD_SKOOL_POWER_CONSUMPTION:
            self.pc = [0 for x in range(self.co.bs_count)]
        else:
            self.pc_static = [0 for x in range(self.co.bs_count)]
            self.pc_dynamic = [0 for x in range(self.co.bs_count)]
        for i in range(self.co.bs_count):
            if Battery.OLD_SKOOL_POWER_CONSUMPTION:
                if self.co.bs_types[i] == BSType.MICRO:
                    self.pc[i] = Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO
                else:
                    self.pc[i] = Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO
            else:
                if self.co.bs_types[i] == BSType.MICRO:
                    self.pc_static[i] = Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO_STATIC
                    self.pc_dynamic[i] = Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO_DYNAMIC
                else:
                    self.pc_static[i] = Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_STATIC
                    self.pc_dynamic[i] = Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_DYNAMIC

        # en_cons = (self.pc_static[i] + quicksum((self.ud[t][j] / self.sr[i][j]) * self.decision_z[i][j][t] for j in self.r_j) * self.pc_dynamic[i])

        # SERVICE RATE OF BASE STATIONS
        self.co = snapshot.load_city_after_deployment()
        s_r = self.co.service_rate
        self.sr = [[1 for x in range(self.NUMBER_OF_USER_LOCATION)] for x in range(self.NUMBER_OF_BASE_STATION)]
        for bs in range(self.co.bs_count):
            for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    self.sr[bs][CoordinateConverter.get_coor(x_coor, y_coor)] = s_r[bs][x_coor][y_coor] + 1

        if self.method == 'MonthlyAverage':
            # USER DEMANDS Avg. per Month
            tr = snapshot.load_tr()
            u_d = tr.get_user_traffic_demand_for_sim_duration()
            time_range = 12 * NUMBER_OF_TIME_SLOT_IN_ONE_DAY
            u_d_for_multiple_days = [[[0 for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                      for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                     for x in range(time_range)]
            smf = SaatliMaarifTakvimi()
            for day in range(365):
                for hour_of_a_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    u_d_for_multiple_days[NUMBER_OF_TIME_SLOT_IN_ONE_DAY * smf.month_of_the_year + hour_of_a_day] += u_d[day][hour_of_a_day] / SHC.NUMBER_OF_DAYS_IN_MONTHS[smf.month_of_the_year]
                    smf.yapragi_kopar()

            for t in range(time_range):
                for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                        self.ud[t][CoordinateConverter.get_coor(x_coor, y_coor)] = u_d_for_multiple_days[t][x_coor][y_coor]

            # GENERATED SOLAR ENERGY
            solar_energy = snapshot.load_solar_energy()
            smf = SaatliMaarifTakvimi()
            for i in range(365):
                for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    self.ge[NUMBER_OF_TIME_SLOT_IN_ONE_DAY * smf.month_of_the_year + j] += solar_energy.harvest_the_solar_energy(i, j, 1) / SHC.NUMBER_OF_DAYS_IN_MONTHS[smf.month_of_the_year]
                    smf.yapragi_kopar()
        elif self.method == 'SeasonlyAverage':
            # USER DEMANDS Avg. per Season
            tr = snapshot.load_tr()
            u_d = tr.get_user_traffic_demand_for_sim_duration()
            time_range = 4 * NUMBER_OF_TIME_SLOT_IN_ONE_DAY
            u_d_for_multiple_days = [[[0 for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                      for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                     for x in range(time_range)]
            smf = SaatliMaarifTakvimi()
            for day in range(365):
                for hour_of_a_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    u_d_for_multiple_days[NUMBER_OF_TIME_SLOT_IN_ONE_DAY * smf.season + hour_of_a_day] += u_d[day][hour_of_a_day] / (SHC.NUMBER_OF_DAYS_IN_MONTHS[smf.month_of_the_year] * 3)
                    smf.yapragi_kopar()

            for t in range(time_range):
                for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                        self.ud[t][CoordinateConverter.get_coor(x_coor, y_coor)] = u_d_for_multiple_days[t][x_coor][y_coor]

            # GENERATED SOLAR ENERGY
            solar_energy = snapshot.load_solar_energy()
            smf = SaatliMaarifTakvimi()
            for i in range(365):
                for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    self.ge[NUMBER_OF_TIME_SLOT_IN_ONE_DAY * smf.season + j] += solar_energy.harvest_the_solar_energy(i, j, 1) / (SHC.NUMBER_OF_DAYS_IN_MONTHS[smf.month_of_the_year] * 3)
                    smf.yapragi_kopar()
        elif self.method == 'SimTime':
            # USER DEMANDS
            tr = snapshot.load_tr()
            u_d = tr.get_user_traffic_demand_for_sim_duration()
            time_range = self.NUMBER_OF_TIME_SLICE
            u_d_for_multiple_days = [[[0 for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                      for x in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE)]
                                     for x in range(time_range)]

            start_day = 0
            for day in range(start_day, start_day + self.NUMBER_OF_DAYS):
                for hour_of_a_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    u_d_for_multiple_days[(day - start_day) * NUMBER_OF_TIME_SLOT_IN_ONE_DAY + hour_of_a_day] = u_d[day][hour_of_a_day]

            for t in range(time_range):
                for x_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                    for y_coor in range(CoordinateConverter.GRID_COUNT_IN_ONE_EDGE):
                        self.ud[t][CoordinateConverter.get_coor(x_coor, y_coor)] = u_d_for_multiple_days[t][x_coor][y_coor]

            # GENERATED SOLAR ENERGY
            solar_energy = snapshot.load_solar_energy()
            for i in range(start_day, start_day + self.NUMBER_OF_DAYS):
                for j in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    t = (i - start_day) * NUMBER_OF_TIME_SLOT_IN_ONE_DAY + j
                    self.ge[t] = solar_energy.harvest_the_solar_energy(i, j, 1)

    def add_variables(self):
        for i in self.r_i:
            for t in self.r_t:
                self.decision_x[i][t] = self.m.addVar(vtype=GRB.BINARY, name="decision_x_%d,%d" % (i, t))
                self.decision_x[i][t].start = 1
        for i in self.r_i:
            for t in self.r_t:
                self.decision_r[i][t] = self.m.addVar(lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS, name="decision_r_%d,%d" % (i, t))
                # self.decision_r[i][t] = self.m.addVar(vtype=GRB.BINARY, name="decision_r_%d,%d" % (i, t))
                self.decision_r[i][t].start = 0.0
        for i in self.r_i:
            for j in self.r_j:
                for t in self.r_t:
                    self.decision_z[i][j][t] = self.m.addVar(vtype=GRB.BINARY, name="decision_z_%d,%d,%d" % (i, j, t))
        for i in self.r_i:
            self.decision_s[i] = self.m.addVar(lb=0, ub=6, vtype=GRB.INTEGER, name="decision_s_%d" % i)
            self.decision_s[i].start = 0
        for i in self.r_i:
            self.decision_b[i] = self.m.addVar(lb=0, ub=8, vtype=GRB.INTEGER, name="decision_b_%d" % i)
            self.decision_b[i].start = 0
        self.m.update()

    def add_constraints(self):
        # Add constraints
        for j in self.r_j:
            for t in self.r_t:
                self.m.addConstr(quicksum(self.sr[i][j] * self.decision_z[i][j][t] for i in self.r_i) >= self.ud[t][j])  # DEMAND
                self.m.addConstr(quicksum(self.decision_z[i][j][t] for i in self.r_i) <= 1)  # AssignMaxOneBS

        for i in self.r_i:
            for t in self.r_t:
                self.m.addConstr(quicksum((self.ud[t][j] / self.sr[i][j]) * self.decision_z[i][j][t] for j in self.r_j) <= self.RHO)  # ctCapacityBS
                self.m.addConstr(self.decision_x[i][t] * self.NUMBER_OF_USER_LOCATION - quicksum(self.decision_z[i][j][t] for j in self.r_j) >= 0)  # shouldBeActiveIfItisAssignedAnyLocation

        for y in self.r_y:
            r_specific_day = list(range(y * self.NUMBER_OF_TIME_SLICE_PER_DAY, (y + 1) * self.NUMBER_OF_TIME_SLICE_PER_DAY))
            for i in self.r_i:
                if Battery.OLD_SKOOL_POWER_CONSUMPTION:
                    self.m.addConstr(quicksum(self.pc[i] * self.decision_r[i][t] for t in r_specific_day) <= self.decision_b[i] * self.A_B)  # batteryCapacityLimit
                    self.m.addConstr(quicksum(self.pc[i] * self.decision_r[i][t] for t in r_specific_day) <= self.decision_s[i] * quicksum(self.ge[t] for t in r_specific_day))  # generatedEnergyLimit
                else:
                    self.m.addConstr(quicksum((self.pc_static[i] + self.pc_dynamic[i]) * self.decision_r[i][t] for t in r_specific_day) <= self.decision_b[i] * self.A_B)  # batteryCapacityLimit
                    self.m.addConstr(quicksum((self.pc_static[i] + self.pc_dynamic[i]) * self.decision_r[i][t] for t in r_specific_day) <= self.decision_s[i] * quicksum(
                        self.ge[t] for t in r_specific_day))  # generatedEnergyLimit

                    '''
                    self.m.addConstr(quicksum((self.pc_static[i] + quicksum((self.ud[t][j] / self.sr[i][j]) * self.decision_z[i][j][t] for j in self.r_j) * self.pc_dynamic[i])
                                              * self.decision_r[i][t] for t in r_specific_day) <= self.decision_b[i] * self.A_B)  # batteryCapacityLimit
                    self.m.addConstr(quicksum((self.pc_static[i] + quicksum((self.ud[t][j] / self.sr[i][j]) * self.decision_z[i][j][t] for j in self.r_j) * self.pc_dynamic[i])
                                              * self.decision_r[i][t] for t in r_specific_day) <= self.decision_s[i] * quicksum(self.ge[t] for t in r_specific_day))  # generatedEnergyLimit
                    '''
    def set_objective_function(self):
        COMPARISON_CONSTANT = 365 / self.NUMBER_OF_DAYS
        if Battery.OLD_SKOOL_POWER_CONSUMPTION:

            self.m.setObjective(self.C_S * quicksum(self.decision_s[i] for i in self.r_i) +
                                self.C_B * quicksum(self.decision_b[i] for i in self.r_i) +
                                COMPARISON_CONSTANT * self.N_Y * self.NUMBER_OF_TIME_SLICE * self.C_E * quicksum(
                self.pc[i] * (1 - self.decision_r[i][t]) * self.decision_x[i][t] for i in self.r_i for t in self.r_t))
        else:
            '''
            self.m.setObjective(self.C_S * quicksum(self.decision_s[i] for i in self.r_i) +
                                self.C_B * quicksum(self.decision_b[i] for i in self.r_i) +
                                COMPARISON_CONSTANT * self.N_Y * self.NUMBER_OF_TIME_SLICE * self.C_E * quicksum(
                (self.pc_static[i]* self.decision_x[i][t] + quicksum((self.ud[t][j] / self.sr[i][j]) * self.decision_z[i][j][t] for j in self.r_j) * self.pc_dynamic[i])
                * (1 - self.decision_r[i][t])  for i in self.r_i for t in self.r_t))
            '''
            self.m.setObjective(self.C_S * quicksum(self.decision_s[i] for i in self.r_i) +
                                self.C_B * quicksum(self.decision_b[i] for i in self.r_i) +
                                COMPARISON_CONSTANT * self.N_Y * self.NUMBER_OF_TIME_SLICE * self.C_E * quicksum(
                (self.pc_static[i] + self.pc_dynamic[i]) * (1 - self.decision_r[i][t]) * self.decision_x[i][t] for i in self.r_i for t in self.r_t))

    def add_constraints_one_day(self):
        # Add constraints
        for j in self.r_j:
            for t in self.r_t:
                self.m.addConstr(quicksum(self.sr[i][j] * self.decision_z[i][j][t] for i in self.r_i) >= self.ud[t][j])  # DEMAND
                self.m.addConstr(quicksum(self.decision_z[i][j][t] for i in self.r_i) <= 1)  # AssignMaxOneBS

        for i in self.r_i:
            for t in self.r_t:
                self.m.addConstr(quicksum((self.ud[t][j] / self.sr[i][j]) * self.decision_z[i][j][t] for j in self.r_j) <= self.RHO)  # ctCapacityBS
                self.m.addConstr(self.decision_x[i][t] * self.NUMBER_OF_USER_LOCATION - quicksum(self.decision_z[i][j][t] for j in self.r_j) >= 0)  # shouldBeActiveIfItisAssignedAnyLocation

        for i in self.r_i:
            self.m.addConstr(quicksum(self.pc[i] * self.decision_r[i][t] for t in self.r_t) <= self.decision_b[i] * self.A_B)  # batteryCapacityLimit
            self.m.addConstr(quicksum(self.pc[i] * self.decision_r[i][t] for t in self.r_t) <= self.decision_s[i] * quicksum(self.ge[t] for t in self.r_t))  # generatedEnergyLimit

    def set_objective_function_one_day(self):
        COMPARISON_CONSTANT = 365 / self.NUMBER_OF_DAYS
        self.m.setObjective(self.C_S * quicksum(self.decision_s[i] for i in self.r_i) +
                            self.C_B * quicksum(self.decision_b[i] for i in self.r_i) +
                            COMPARISON_CONSTANT * self.N_Y * self.NUMBER_OF_TIME_SLICE * self.C_E * quicksum(
                                self.pc[i] * (1 - self.decision_r[i][t]) * self.decision_x[i][t] for i in self.r_i for t in self.r_t))

    def solve_the_problem(self):
        self.m.optimize()

    def print_variables(self):
        print("DECISION ACTIVE BASE STATIONS:::")
        self.print_header(self.r_t)
        for i in self.r_i:
            if Battery.OLD_SKOOL_POWER_CONSUMPTION:
                if self.pc_static[i] >= Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_STATIC:
                    bs_type = 'M'
                else:
                    bs_type = ''
            else:
                if self.pc_static[i] >= Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_STATIC:
                    bs_type = 'M'
                else:
                    bs_type = ''
            print(("{:2}{:2}".format(i, bs_type)), end=' ')
            for t in self.r_t:
                name = "decision_x_%d,%d" % (i, t)
                v = self.m.getVarByName(name)
                print(("{:4}".format(int(v.x))), end=' ')
            print()

        print("DECISION RENEWABLE ENERGY RATIO:::")
        self.print_header(self.r_t)
        for i in self.r_i:
            if self.pc_static[i] >= Battery.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_STATIC:
                bs_type = 'M'
            else:
                bs_type = ''
            print(("{:2}{:2}".format(i, bs_type)), end=' ')
            for t in self.r_t:
                name = "decision_r_%d,%d" % (i, t)
                v = self.m.getVarByName(name)
                print(("{:4}".format(float(v.x))), end=' ')
            print()
        size_of_sp_and_batt = []
        size_of_solar_panels = [0 for x in self.r_i]
        size_of_batteries = [0 for x in self.r_i]
        capital_expenditure = 0
        print("DECISION SOLAR PANEL SIZE:::")
        self.print_header(self.r_i)
        print(("{:4}".format("")))
        for i in self.r_i:
            name = "decision_s_%d" % i
            v = self.m.getVarByName(name)
            capital_expenditure += int(v.x) * self.C_S
            size_of_solar_panels[i] = int(v.x)
            print(("{:4}".format(int(v.x))), end=' ')
        print()

        print("DECISION BATTERY SIZE:::")
        self.print_header(self.r_i)
        print(("{:4}".format("")))
        for i in self.r_i:
            name = "decision_b_%d" % i
            v = self.m.getVarByName(name)
            capital_expenditure += int(v.x) * self.C_B
            size_of_batteries[i] = int(v.x)
            print(("{:4}".format(int(v.x))), end=' ')
        print()

        for i in self.r_i:
            size_of_sp_and_batt.append((size_of_solar_panels[i], size_of_batteries[i] * self.A_B))
        snapshot.save_size_of_sp_and_batt(size_of_sp_and_batt, snapshot.log_file_name('gurobi', 0))

        print(("CAPEX:{}".format(capital_expenditure)))


def multi_test_gurobi(traffic_scen, city_name, traffic_index=None):
    print("--------------- traffic_scen:{} city_name:{} traffic_index:{}---------------".format(traffic_scen, city_name, traffic_index))
    snapshot = Snapshot()
    snapshot.set_traffic_scen_folder(traffic_scen, traffic_index)
    snapshot.set_solar_data_path(city_name)
    snapshot.set_results_folder(traffic_scen, city_name, "GUROBI", traffic_index)
    city_after_deployment = snapshot.load_city_after_deployment()

    gg = GreenGurobi(city_after_deployment, 'SeasonlyAverage')
    print("GUROBI SOLVE LOAD DATA:{}".format(datetime.now()))
    gg.gurobi_load_data()  # GRB_GIVEN
    print("GUROBI SOLVE add_variables:{}".format(datetime.now()))
    gg.add_variables()  # GRB_DECISION
    print("GUROBI SOLVE add_constraints:{}".format(datetime.now()))
    gg.add_constraints()  # GRB_CONSTRAINTS
    print("GUROBI SOLVE set_objective_function:{}".format(datetime.now()))
    gg.set_objective_function()  # GRB_OBJ
    print("GUROBI SOLVE solve_the_problem:{}".format(datetime.now()))
    gg.solve_the_problem()  # GRB_RUN
    gg.print_variables()  # GRB_RSLT


if __name__ == '__main__':
    snapshot = Snapshot()
    # snapshot.create_results_folders_for_gurobi()
    print("RenDep GUROBI SOLVE START:{}".format(datetime.now()))
    multi_process = True
    if multi_process:
        processes = []
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                low_limit = 6
                high_limit = 10
                max_high_limit = 10
                for traffic_index in range(low_limit, high_limit):
                    processes.append(Process(target=multi_test_gurobi, args=(traffic_scen, city_name, traffic_index)))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
    else:
        for traffic_scen in traffic_scenarios:
            snapshot.set_traffic_scen_folder(traffic_scen)
            city_after_deployment = snapshot.load_city_after_deployment()
            for city_name in city_name_list:
                snapshot.set_solar_data_path(city_name)
                snapshot.set_results_folder(traffic_scen, city_name, "GUROBI")
                print("======== traffic_scen:{} city_name:{}".format(traffic_scen, city_name))
                gg = GreenGurobi(city_after_deployment, 'SeasonlyAverage')
                print("GUROBI SOLVE LOAD DATA:{}".format(datetime.now()))
                gg.gurobi_load_data()  # GRB_GIVEN
                print("GUROBI SOLVE add_variables:{}".format(datetime.now()))
                gg.add_variables()  # GRB_DECISION
                print("GUROBI SOLVE add_constraints:{}".format(datetime.now()))
                gg.add_constraints()  # GRB_CONSTRAINTS
                print("GUROBI SOLVE set_objective_function:{}".format(datetime.now()))
                gg.set_objective_function()  # GRB_OBJ
                print("GUROBI SOLVE solve_the_problem:{}".format(datetime.now()))
                gg.solve_the_problem()  # GRB_RUN
                gg.print_variables()  # GRB_RSLT

    print("GUROBI SOLVE END:{}".format(datetime.now()))
