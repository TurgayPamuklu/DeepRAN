"""HcranGenericGurobi Module.
Super/Base Gurobi Class for Journal 3 ( Midhaul) and Journal 4 (Crosshaul).

"""

from gurobipy import *  # GRB_INIT

from hcran_generic import HcranGeneric


class HcranGenericGurobi(HcranGeneric):
    def __init__(self, city_name, traffic_scen, splitting_method, instance_index, day):
        HcranGeneric.__init__(self, city_name, traffic_scen, splitting_method, instance_index, day)
        self.m = None  # Model
        # RU capacity in RS

        # OPTIMIZATION PARAMETERS
        self.m = Model()  # GRB_INIT
        self.m.params.MIPGap = 0.20
        self.m.params.TimeLimit = 4 * 60 * 60
        self.m.params.NumericFocus = 1
        self.m.params.MIPFocus = 3  # 3
        self.m.params.Threads = 2

    # DECISION VARIABLES
    def _add_variables(self):
        for r in self.r_cloud:  # amount of solar_energy_consumption decision
            for t in self.r_t:
                self.decision_s[r][t] = self.m.addVar(lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="decision_s_%d,%d" % (r, t))
        for d in self.r_du:  # DU on/off decision
            for t in self.r_t:
                self.decision_a[d][t] = self.m.addVar(vtype=GRB.BINARY, name="decision_a_%d,%d" % (d, t))
        for i in self.r_i:  # User DU assignment decision
            for d in self.r_du:
                for f in self.r_up:
                    for t in self.r_t:
                        self.decision_m[i][d][f][t] = self.m.addVar(vtype=GRB.BINARY, name="decision_m_%d,%d,%d,%d" % (i, d, f, t))

        if "BatteryAware" in self.splitting_method:  # Remaining Energy in Battery Decision
            for r in self.r_cloud:
                for t in self.r_t:
                    # self.decision_be[r][t] = self.m.addVar(lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="decision_be_%d,%d" % (r, t))
                    self.decision_be[r][t] = self.m.addVar(lb=0.0, ub=self.battery_capacity[r], vtype=GRB.CONTINUOUS, name="decision_be_%d,%d" % (r, t))

        for r in self.r_cloud:  # energy selling
            for t in self.r_t:
                self.decision_p[r][t] = self.m.addVar(lb=0.0, ub=self.battery_capacity[r], vtype=GRB.CONTINUOUS, name="decision_p_%d,%d" % (r, t))

        if self.ENERGY_TRANSFER_AVAILABLE:
            for i in self.r_cloud:
                for j in self.r_cloud:
                    for t in self.r_t:
                        self.decision_x[i][j][t] = self.m.addVar(lb=0.0, ub=self.battery_capacity[r], vtype=GRB.CONTINUOUS, name="decision_x_%d,%d,%d" % (i, j, t))

        self.m.update()

    def _add_constraints(self):
        BIG_M = 1e5
        ############################# ONE SIDE METHOD LIMITATIONS #############################
        if "OnlyCS" in self.splitting_method:
            for t in self.r_t:
                for k in self.r_ec:
                    du_set_in_k = list(range(k * self.n_of_du_per_ec, (k + 1) * self.n_of_du_per_ec))
                    user_set_in_k = list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec))
                    for d in du_set_in_k:
                        self.m.addConstr(self.decision_a[d][t] == 0)
                        for f in self.r_up:
                            self.m.addConstr(quicksum(self.decision_m[i][d][f][t] for i in user_set_in_k) == 0)

        if "OnlyRS" in self.splitting_method:
            for t in self.r_t:
                for d in self.r_du_in_cc:
                    self.m.addConstr(self.decision_a[d][t] == 0)
                    for f in self.r_up:
                        self.m.addConstr(quicksum(self.decision_m[i][d][f][t] for i in self.r_i) == 0)

        # DU CAPACITY AND SWITCH ON/OFF CONSTRAINTS (J3:16-19)#############################
        for t in self.r_t:
            for k in self.r_k:
                du_set_in_k = list(range(k * self.n_of_du_per_ec, (k + 1) * self.n_of_du_per_ec))
                user_set_in_k = list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec))
                small_cell_set_in_k = list(range(k * self.n_of_cell_per_ec + 1, (k + 1) * self.n_of_cell_per_ec))
                for d in du_set_in_k:
                    # print("t:{} k:{} d:{}".format(t, k, d))
                    if hasattr(self, 'decision_h'):  # J3 Problem
                        self.m.addConstr(quicksum(self.traffic_load[i][t] * self.INV_UPSILON * self.decision_m[i][d][f][t] for f in self.r_up for i in user_set_in_k)
                                         - quicksum(self.INV_OMEGA * self.decision_h[j][t] for j in small_cell_set_in_k)
                                         <= self.L_EC, name="RS:%d Capacity Constraint T:%d  DU:%d" % (t, k, d))  # DU Cap. in RS
                    else:
                        self.m.addConstr(quicksum(self.traffic_load[i][t] * self.INV_UPSILON * self.decision_m[i][d][f][t] for f in self.r_up for i in user_set_in_k)
                                         <= self.L_EC, name="RS:%d Capacity Constraint T:%d  DU:%d" % (t, k, d))  # DU Cap. in RS

                    self.m.addConstr(BIG_M * self.decision_a[d][t] - quicksum(self.decision_m[i][d][f][t] for f in self.r_up for i in user_set_in_k)
                                     >= 0, name="RS:%d Activity Constraint T:%d DU:%d" % (t, k, d))  # DU Activity Constraint

            for d in self.r_du_in_cc:  # GRB_CONSTRAINTS
                self.m.addConstr(quicksum(self.traffic_load[i][t] * self.INV_UPSILON * self.decision_m[i][d][f][t] for f in self.r_up for i in self.r_i)
                                 <= self.L_CC, name="CS Capacity Constraint T:%d DU:%d" % (t, d))  # DU Cap. in CS
                self.m.addConstr(BIG_M * self.decision_a[d][t] - quicksum(self.decision_m[i][d][f][t] for f in self.r_up for i in self.r_i)
                                 >= 0, name="CS Activity Constraint T:%d DU:%d" % (t, d))  # DU Activity Constraint

        DELAY_CONSTRAINT = True
        if DELAY_CONSTRAINT:
            if False:
                # Delay Constraint
                for t in self.r_t:
                    for k in self.r_ec:
                        du_set_in_k = list(range(k * self.n_of_du_per_ec, (k + 1) * self.n_of_du_per_ec))
                        user_set_in_k = list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec))
                        small_cell_set_in_k = list(range(k * self.n_of_cell_per_ec + 1, (k + 1) * self.n_of_cell_per_ec))
                        for i in user_set_in_k:
                            if hasattr(self, 'decision_g'):  # J3 Problem
                                D_FROM_SC = self.D_MWAVE * quicksum(self.decision_g[j][t] for j in small_cell_set_in_k)
                            else:
                                D_FROM_SC = 0
                            D_PROCESS = self.traffic_load[i][t] * self.DU_GOPS_PERF * self.SMALL_OMEGA
                            D_RSF = self.traffic_load[i][t] * self.D_RSF_TRSF * self.D_RSF_NRSF
                            D_NOF = self.D_NOF_TOF * self.D_NOF_CONS * 10E3 * quicksum(self.decision_m[i][d][f][t] for f in self.r_up for d in self.r_du_in_cc)
                            Delay = self.D_CONS_FROM_EC + D_FROM_SC + D_PROCESS + D_RSF + D_NOF
                            '''
                            print("t:{} k:{} i:{} D_FROM_SC:{} D_PROCESS:{} D_RSF:{} D_NOF:{} Delay:{} self.delay_thrshold:{}"
                                  .format(t, k, i, self.D_FROM_SC, self.D_PROCESS, self.D_RSF, self.D_NOF, self.Delay, self.delay_threshold[i][t]))
                            '''
                            self.m.addConstr(Delay <= self.delay_threshold[i][t])
            else:
                for t in self.r_t:
                    for r in self.r_ec:
                        du_set_in_r = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
                        user_set_in_r = list(range(r * self.number_of_ue_per_ec, (r + 1) * self.number_of_ue_per_ec))
                        for i in user_set_in_r:
                            self.m.addConstr(quicksum(self.decision_m[i][d][f][t] for f in self.r_up for d in self.r_du_in_cc) <= self.delay_threshold[i][t])
                            # self.m.addConstr(quicksum(self.decision_m[i][d][f][t] for f in self.r_up for d in du_set_in_r) <= 0)

        # UP Assigning/Usage Constraint (J3:20)
        for t in self.r_t:
            for k in self.r_k:
                du_set_in_k = list(range(k * self.n_of_du_per_ec, (k + 1) * self.n_of_du_per_ec))
                user_set_in_k = list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec))
                for i in user_set_in_k:
                    self.m.addConstr(quicksum(self.decision_m[i][d][f][t] for f in self.r_up for d in du_set_in_k)
                                     + quicksum(self.decision_m[i][d][f][t] for f in self.r_up for d in self.r_du_in_cc)
                                     == self.n_of_up_function, name="UP Usage Constraint T:%d User:%d" % (t, i))  # DU Cap. in RS

        # # Solar Panel and Battery Limitation
        if "BatteryAware" in self.splitting_method:
            if "OnlyCS" in self.splitting_method:
                site_list = [self.cc_index]
            elif "OnlyRS" in self.splitting_method:
                site_list = list(range(self.n_of_ec))
            else:
                site_list = self.r_cloud
            if not self.ENERGY_TRANSFER_AVAILABLE:
                print("BatteryAware: Solar Panel and Battery Limitation Constraint\n")
                for k in site_list:  # (J3:21-22)
                    for t in self.r_t:
                        if t == 0:  # initial time
                            current_battery_energy = self.initial_battery_energy[k]
                        else:
                            current_battery_energy = self.decision_be[k][t - 1]
                        self.m.addConstr(self.decision_be[k][t] == current_battery_energy - self.decision_s[k][t] - self.decision_p[k][t] + self.ge[k][t])
            else:
                for k in site_list:
                    other_site_list = [n for n in site_list if n is not k]
                    for t in self.r_t:
                        if t == 0:  # initial time
                            current_battery_energy = self.initial_battery_energy[k]
                        else:
                            current_battery_energy = self.decision_be[k][t - 1]
                        self.m.addConstr(self.decision_be[k][t] == current_battery_energy - self.decision_s[k][t] - self.decision_p[k][t] + self.ge[k][t]
                                         - quicksum(self.decision_x[k][other_sites][t] for other_sites in other_site_list)
                                         + quicksum(self.energy_transfer_efficiency * self.decision_x[other_sites][k][t] for other_sites in other_site_list))
                        self.m.addConstr(quicksum(self.decision_x[k][other_sites][t] for other_sites in other_site_list) <= current_battery_energy)

        elif 'TrafficAware' in self.splitting_method:
            for k in self.r_cloud:
                for t in self.r_t:
                    self.m.addConstr(self.decision_s[k][t] == 0)  # we will calculate these values in after solving the problem
                    self.m.addConstr(self.decision_p[k][t] == 0)
        else:
            for k in self.r_cloud:
                self.m.addConstr(quicksum(self.decision_s[k][t] for t in self.r_t) <= self.battery_capacity[k])  # batteryCapacityLimit
                self.m.addConstr(quicksum(self.decision_s[k][t] for t in self.r_t) <= quicksum(self.ge[k][t] for t in self.r_t))  # SolarPanelHarvestedEnergyLimit

        # Don't make unnecessary Renewable Energy Usage MaxRenUsageLimit (J3:25-26) (J3:23-24 is limited by definition)
        for t in self.r_t:
            for k in self.r_ec:
                du_set_in_k = list(range(k * self.n_of_du_per_ec, (k + 1) * self.n_of_du_per_ec))
                self.m.addConstr(self.decision_s[k][t] <= self.P_EC_STA + self.P_EC_DU * quicksum(self.decision_a[d][t] for d in du_set_in_k))
            self.m.addConstr(self.decision_s[self.cc_index][t] <= self.P_CC_STA + self.P_CC_DU * quicksum(self.decision_a[d][t] for d in self.r_du_in_cc))

        # Don't make unnecessary assigning operations CONSTRAINTS
        for t in self.r_t:
            for k in self.r_ec:
                du_set_that_user_can_be_assigned = list(range(k * self.n_of_du_per_ec, (k + 1) * self.n_of_du_per_ec)) + list(self.r_du_in_cc)
                du_set_out_r = [n for n in self.r_du if n not in du_set_that_user_can_be_assigned]
                user_set_in_k = list(range(k * self.number_of_ue_per_ec, (k + 1) * self.number_of_ue_per_ec))
                for i in user_set_in_k:
                    self.m.addConstr(quicksum(self.decision_m[i][d][f][t] for f in self.r_up for d in du_set_out_r) == 0)
