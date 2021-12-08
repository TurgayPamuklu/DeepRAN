""" GUROBI Implementation for RLDFS ICC Paper.
"""
from gurobipy import *  # GRB_INIT

from env_traffic import Traffic
from printer import *


class Rlbdfs_Gurobi():
    def __init__(self, conf, method):
        if method == "TA":
            self.consume_ren_immediately = True
        else:
            self.consume_ren_immediately = False

        self.printer = Printer(self)
        self.conf = conf
        self.set_ranges()
        self.traffic_load = None
        self.ge = [[0 for x in self.r_t] for x in self.r_cloud]
        self.initial_battery_energy = [0 for x in self.r_cloud]
        # OPTIMIZATION PARAMETERS
        self.m = Model()  # GRB_INIT
        self.m.params.MIPGap = 0.02
        self.m.params.TimeLimit = 4 * 60 * 60
        self.m.params.NumericFocus = 1
        self.m.params.MIPFocus = 3  # 3
        self.m.params.Threads = 2

    # Loading Traffic and Solar Energy
    def load_data(self, traffic_rate, city):
        # LOAD TRAFFIC
        ts = 1
        snapshot = Snapshot()
        snapshot.set_traffic_data_path(ts)
        self.traffic_load = snapshot.load_tr()

        snapshot.set_solar_data_path(city)
        solar_energy = snapshot.load_solar_energy()

        if AVERAGE_GIVEN_DATA:
            self.traffic_load = Traffic.get_average_traffic(self.traffic_load)
            self.traffic_load = self.traffic_load * traffic_rate
            for r in self.r_cloud:
                sp = self.conf[r][0]
                self.ge[r] = solar_energy.get_average_regeneration_energy_in_a_day(sp)
        for r in self.r_cloud:
            self.initial_battery_energy[r] = 0

    def set_ranges(self):
        self.r_ec = range(N_OF_EC)
        self.r_cloud = range(N_OF_CLOUD)
        self.r_t = range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)
        self.r_f = range(N_OF_URF)
        self.r_i = range(N_OF_PACKET_TYPE)

    # DECISION VARIABLES
    def set_decision_variables(self):
        # Init variables
        if not self.consume_ren_immediately:
            self.decision_s = [[0 for x in self.r_t] for x in self.r_cloud]
            self.decision_b = [[0 for x in self.r_t] for x in self.r_cloud]
            self.decision_excessive = [[0 for x in self.r_t] for x in self.r_cloud]
        self.decision_a = [[[[0 for x in self.r_f] for x in self.r_t] for x in self.r_i] for x in self.r_cloud]

        if self.consume_ren_immediately:
            self.static_s = [[0 for x in self.r_t] for x in self.r_cloud]
            self.static_b = [[0 for x in self.r_t] for x in self.r_cloud]

        if not self.consume_ren_immediately:
            for r in self.r_cloud:  # amount of solar_energy_consumption decision
                for t in self.r_t:
                    self.decision_s[r][t] = self.m.addVar(lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="decision_s_%d,%d" % (r, t))
                    self.decision_b[r][t] = self.m.addVar(lb=0.0, ub=self.conf[r][1], vtype=GRB.CONTINUOUS, name="decision_b_%d,%d" % (r, t))
                    self.decision_excessive[r][t] = self.m.addVar(lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="decision_excessive_%d,%d" % (r, t))

        for r in self.r_ec:
            for i in self.r_i:
                for t in self.r_t:
                    for f in self.r_f:
                        self.decision_a[r][i][t][f] = self.m.addVar(vtype=GRB.BINARY, name="decision_a_%d,%d,%d,%d" % (r, i, t, f))

        self.m.update()

    def set_constraints(self):
        # # BENCHMARK: ONLY_EC ##########################################
        # for r in self.r_ec:
        #     for i in [PacketType.EMBB]:    # URLLC packets are always processed at EC side
        #         for t in self.r_t:
        #             for f in self.r_f:
        #                 self.m.addConstr(self.decision_a[r][i][t][f] == 1)

        for r in self.r_ec:
            for i in [PacketType.URLLC]:  # URLLC packets are always processed at EC side
                # for i in self.r_i:    # URLLC packets are always processed at EC side
                for t in self.r_t:
                    for f in self.r_f:
                        self.m.addConstr(self.decision_a[r][i][t][f] == 1)

        for r in self.r_ec:
            for i in [PacketType.EMBB]:  # EMBB packets are splitted btw. EC and CC
                for t in self.r_t:
                    for f1 in self.r_f:
                        self.m.addConstr((1 - self.decision_a[r][i][t][f1]) * quicksum(self.decision_a[r][i][t][f2] for f2 in list(filter(lambda x: x >= f1, self.r_f))) == 0)

        if not self.consume_ren_immediately:
            for r in self.r_cloud:
                for t in self.r_t:
                    if t == 0:  # initial time
                        current_battery_energy = self.initial_battery_energy[r]
                    else:
                        current_battery_energy = self.decision_b[r][t - 1]
                    self.m.addConstr(self.decision_b[r][t] == current_battery_energy - self.decision_s[r][t] - self.decision_excessive[r][t] + self.ge[r][t])

            for t in self.r_t:
                for r in self.r_cloud:
                    self.m.addConstr(self.decision_s[r][t] <= self.__consume_total_energy_cons(r, t))

    def set_objective_function(self):
        cost_CC = 0
        cost_EC = 0
        for t in self.r_t:
            for r in self.r_ec:
                grid_cons_EC = self.__consume_total_energy_cons(r, t)
                if not self.consume_ren_immediately:
                    grid_cons_EC -= self.decision_s[r][t]
                cost_EC += grid_cons_EC * PowerCons.ELEC_PRICE[t]
            grid_cons_CC = self.__consume_total_energy_cons(CC_INDEX, t)
            if not self.consume_ren_immediately:
                grid_cons_CC -= self.decision_s[CC_INDEX][t]
            cost_CC += grid_cons_CC * PowerCons.ELEC_PRICE[t]

        self.m.setObjective(cost_EC + cost_CC, GRB.MINIMIZE)

    def calculate_objective_function(self, a, s):
        cost_CC = 0
        cost_EC = 0
        for t in self.r_t:
            for r in self.r_ec:
                power_cons_EC = self.__print_total_energy_cons(r, t, a)
                grid_cons = power_cons_EC - s[r][t]
                cost_EC += grid_cons * PowerCons.ELEC_PRICE[t]
                # print("t:{} r:{} power_cons_EC:{} grid_cons:{} cost_EC:{}".format(t, r, power_cons_EC, grid_cons, cost_EC))
            power_cons_CC = self.__print_total_energy_cons(CC_INDEX, t, a)
            grid_cons = power_cons_CC - s[CC_INDEX][t]
            cost_CC += grid_cons * PowerCons.ELEC_PRICE[t]
            # print("t:{} power_cons_CC:{} grid_cons:{} cost_CC:{}".format(t, r, power_cons_CC, grid_cons, cost_CC))
        # print("{} :: cost_CC:{} cost_EC:{} total:{}".format(self.conf, cost_CC, cost_EC, cost_EC+cost_CC))
        return cost_CC, cost_EC, cost_EC + cost_CC

    def __calculate_process_load_for_print(self, ec_index, time, a):
        if ec_index == CC_INDEX:
            process_load = sum(self.traffic_load[r_index][PacketType.EMBB][time] *
                               (N_OF_URF - sum(a[r_index][PacketType.EMBB][time][f] for f in self.r_f)) for r_index in self.r_ec)
        else:
            du_urllc_load = self.traffic_load[ec_index][PacketType.URLLC][time] * N_OF_URF
            du_embb_load = self.traffic_load[ec_index][PacketType.EMBB][time] * sum(a[ec_index][PacketType.EMBB][time][f] for f in self.r_f)
            process_load = du_urllc_load + du_embb_load
        return process_load

    def __calculate_process_load(self, ec_index, time):
        if ec_index == CC_INDEX:
            # process_load = quicksum(self.traffic_load[r_index][PacketType.EMBB][time] *
            #                         (N_OF_URF-0) for r_index in self.r_ec)
            # process_load = quicksum(self.traffic_load[r_index][PacketType.EMBB][time] *
            #                         (N_OF_URF-quicksum(self.decision_a[r_index][PacketType.EMBB][time][f] for f in self.r_f)) for r_index in self.r_ec)
            process_load = 0
            for r_index in self.r_ec:
                for f in self.r_f:
                    process_load += self.traffic_load[r_index][PacketType.EMBB][time] * (1 - self.decision_a[r_index][PacketType.EMBB][time][f])
        else:
            du_urllc_load = self.traffic_load[ec_index][PacketType.URLLC][time] * N_OF_URF
            du_embb_load = self.traffic_load[ec_index][PacketType.EMBB][time] * quicksum(self.decision_a[ec_index][PacketType.EMBB][time][f] for f in self.r_f)
            process_load = du_urllc_load + du_embb_load
        return process_load

    def __consume_total_energy_cons(self, ec_index, time):
        process_load = self.__calculate_process_load(ec_index, time)
        return self.__consume_total_energy_generic(ec_index, process_load)

    def __print_total_energy_cons(self, ec_index, time, a):
        process_load = self.__calculate_process_load_for_print(ec_index, time, a)
        return self.__consume_total_energy_generic(ec_index, process_load)

    def __consume_total_energy_generic(self, ec_index, process_load):
        total_process_gops = process_load * PowerCons.USER_CHUNK_SIZE * PowerCons.GOPS_VALUE_PER_URF
        total_process_energy_cons = total_process_gops / PowerCons.GOPS_2_WATT_CONVERTER
        if ec_index != CC_INDEX:
            static_cons = PowerCons.P_EC_STA
            dynamic_cons = total_process_energy_cons * PowerCons.P_EC_DYN
        else:
            static_cons = PowerCons.P_CC_STA
            dynamic_cons = total_process_energy_cons * PowerCons.P_CC_DYN * PowerCons.CENTRALIZATION_FACTOR
        total_energy_consumption = static_cons + dynamic_cons
        return total_energy_consumption

    def print_variables(self):
        self.printer.init_the_record_writer()
        # self.printer._print_general_info()

        if self.m.status == GRB.Status.INF_OR_UNBD:
            self.printer.rw.log_data("Model is infeasible or unbounded\n", None)
            self.printer.rw.log_finish()
            return
        if self.m.status == GRB.Status.INFEASIBLE:
            self.printer.rw.log_data("Model is Infeasible\n", None)
            self.printer.rw.log_finish()
            return
        if self.m.status == GRB.Status.INFEASIBLE:
            self.printer.rw.log_data("Model is Unbounded\n", None)
            self.printer.rw.log_finish()
            return

        # self.plot_network()
        self.printer.rw.log_data("Objective Value From Solver:{}\n", *(self.m.objVal,))

        self.printer.rw.log_data("MIPGap:{}\n", *(self.m.MIPGap,))
        self.printer.rw.append_record_data("MIPGap", self.m.MIPGap)

        ########################################################################################################
        # Getting DECISION VARIABLES
        # Init variables
        print_s = [[0 for x in self.r_t] for x in self.r_cloud]
        print_b = [[0 for x in self.r_t] for x in self.r_cloud]
        print_excessive = [[0 for x in self.r_t] for x in self.r_cloud]
        print_a = [[[[0 for x in self.r_f] for x in self.r_t] for x in self.r_i] for x in self.r_ec]
        number_of_active_urf = [[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(N_OF_CLOUD)]

        for r in self.r_ec:
            for i in self.r_i:
                for t in self.r_t:
                    for f in self.r_f:
                        name = "decision_a_%d,%d,%d,%d" % (r, i, t, f)
                        print_a[r][i][t][f] = int(self.m.getVarByName(name).x)

        total_consumption = [[0 for x in self.r_t] for x in self.r_cloud]
        for t in self.r_t:
            for r in self.r_cloud:
                total_consumption[r][t] = self.__print_total_energy_cons(r, t, print_a)

        if not self.consume_ren_immediately:
            for r in self.r_cloud:  # amount of solar_energy_consumption decision
                for t in self.r_t:
                    name = "decision_s_%d,%d" % (r, t)
                    print_s[r][t] = float(self.m.getVarByName(name).x)
                    name = "decision_b_%d,%d" % (r, t)
                    print_b[r][t] = float(self.m.getVarByName(name).x)
                    name = "decision_excessive_%d,%d" % (r, t)
                    print_excessive[r][t] = float(self.m.getVarByName(name).x)
            cost_CC, cost_EC, cost_total = self.calculate_objective_function(print_a, print_s)
        else:
            fossil_consumption = [[0 for x in self.r_t] for x in self.r_cloud]
            unstored_energy = [[0 for x in self.r_t] for x in self.r_cloud]
            for t in self.r_t:
                for r in self.r_cloud:
                    if t == 0:
                        amount_of_solar_energy = int(self.initial_battery_energy[r] + self.ge[r][t])
                    else:
                        amount_of_solar_energy = int(print_b[r][t - 1] + self.ge[r][t])
                    if total_consumption[r][t] - amount_of_solar_energy > 0:
                        print_s[r][t] = amount_of_solar_energy
                        fossil_consumption[r][t] = total_consumption[r][t] - amount_of_solar_energy
                    else:
                        fossil_consumption[r][t] = 0
                        print_s[r][t] = total_consumption[r][t]
                    if amount_of_solar_energy - print_s[r][t] > self.conf[r][1]:
                        unstored_energy[r][t] = amount_of_solar_energy - print_s[r][t] - self.conf[r][1]
                        print_b[r][t] = self.conf[r][1]
                    else:
                        unstored_energy[r][t] = 0
                        print_b[r][t] = amount_of_solar_energy - print_s[r][t]
            cost_CC, cost_EC, cost_total = self.calculate_objective_function(print_a, print_s)

        number_of_active_urf = [[0.0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(N_OF_CLOUD)]
        renewable_energy_ratio = [[0.0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(N_OF_CLOUD)]
        for r in self.r_ec:
            for t in self.r_t:
                number_of_active_urf[r][t] = sum(print_a[r][PacketType.EMBB][t])
        for r in self.r_cloud:
            for t in self.r_t:
                renewable_energy_ratio[r][t] = print_s[r][t] / total_consumption[r][t]

        self.printer.rw.log_finish()
        hehhe = sum(self.ge[r])
        print("number of active urf::\n{}".format(number_of_active_urf))
        return self.conf, cost_CC, cost_EC, cost_total, renewable_energy_ratio, number_of_active_urf

    def run_solver(self):
        print("RUN...")
        self.m.optimize()


if __name__ == '__main__':
    print("MILP Solve starts...")
    cost_print = []
    # action_table = [(None, None)]
    action_table = dict()
    for city in city_name_list:
        for traffic_rate in traffic_rate_list:
            for conf in PowerCons.get_solar_panel_and_battery_for_each_cloud():
                for ren_consume_method in method_list_milp:  # TA means consume_ren_immediately
                    print("SP_BATT_CONF:{} TR:{} city:{} Method:{}".format(conf, traffic_rate, city, ren_consume_method))
                    rg = Rlbdfs_Gurobi(conf, ren_consume_method)
                    rg.set_ranges()
                    rg.load_data(1, city)
                    rg.set_decision_variables()
                    rg.set_objective_function()
                    rg.set_constraints()
                    rg.run_solver()
                    conf, cost_CC, cost_EC, cost_total, renewable_energy_ratio, number_of_active_urf = rg.print_variables()
                    cost_print.append((conf, cost_CC, cost_EC, cost_total))
                    ec_index = 0  # todo: we record only the same size of battery and solar panel
                    conf_name = "{}_{}_{}_{}_{}".format(conf[ec_index][0], conf[ec_index][1], ren_consume_method,
                                                        traffic_rate, city)
                    action_table[conf_name] = (renewable_energy_ratio, number_of_active_urf)
    for item in cost_print:
        t2 = (item[0], round(item[1], 2), round(item[2], 2), round(item[3], 2))
        print("Cost:{}".format(t2))

    snapshot = Snapshot()
    snapshot.save_actions(action_table, "milp")

    print("MILP Solutions Ends...")
    sys.exit(0)
