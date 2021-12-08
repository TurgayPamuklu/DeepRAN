"""Midhaul Heuristic Module.
Heuristics for Journal 3.

"""

from datetime import datetime

from hcran_generic import HcranGeneric
from hcran_monitor import *
from midhaul import Midhaul

MAGIC_NUMBER = -999987.53463


class MidhaulHeuristic(HcranGeneric):
    def __init__(self, city_name, traffic_scen, splitting_method, day):
        self.midhaul_generic = Midhaul(self)
        HcranGeneric.__init__(self, city_name, traffic_scen, splitting_method)
        self.day = day  # getting the current it is important to calculate remaining battery energy
        self.unstored_energy = [[0 for x in self.r_t] for x in self.r_cloud]
        self.reserved_energy = [[MAGIC_NUMBER for x in self.r_t] for x in self.r_cloud]

        self.du_load = np.array([[0 for x in self.r_t] for x in self.r_du], dtype='float')

    # DECISION VARIABLES
    def add_variables(self):
        self.decision_s = [[0 for x in self.r_t] for x in self.r_cloud]  # amount of renewable energy consumption
        self.decision_a = np.array([[0 for x in self.r_t] for x in self.r_du], dtype='bool')
        self.decision_m = np.array([[[[0 for x in self.r_t] for x in self.r_up] for x in self.r_du] for x in self.r_i], dtype='bool')

        self.decision_be = np.array([[0 for x in self.r_t] for x in self.r_cloud], dtype='float')  # amount of remaining renewable energy in battery

        if self.ENERGY_TRANSFER_AVAILABLE:
            self.decision_x = [[[0 for x in self.r_t] for x in self.r_cloud] for x in self.r_cloud]

        self.decision_p = [[0 for x in self.r_t] for x in self.r_cloud]

    def _calculate_batt_and_unstored_in_next_time_slot(self, r, t, next_battery_energy):
        if next_battery_energy > self.battery_capacity[r]:
            self.decision_be[r][t] = self.battery_capacity[r]
            self.unstored_energy[r][t] = next_battery_energy - self.battery_capacity[r]
        else:
            self.decision_be[r][t] = next_battery_energy
            self.unstored_energy[r][t] = 0
        '''
        if self.decision_be[r][t] < 0:
            print "Aiee"
        '''

    def update_the_battery_state(self):
        for r in self.r_cloud:
            for t in self.r_t:
                if t == 0:  # initial time
                    current_battery_energy = self.initial_battery_energy[r]
                else:
                    current_battery_energy = self.decision_be[r][t - 1]
                next_battery_energy = current_battery_energy + self.ge[r][t] - self.decision_s[r][t]
                self._calculate_batt_and_unstored_in_next_time_slot(r, t, next_battery_energy)

    def _delay_constraint_check_pass(self, user_index, time_index):
        current_number_of_function_operated_in_cs = 0
        for d in self.r_du_in_cc:
            for f in self.r_up:
                if self.decision_m[user_index][d][f][time_index] == 1:
                    current_number_of_function_operated_in_cs += 1
        next_number_of_function_operated_in_cs = current_number_of_function_operated_in_cs + 1
        if next_number_of_function_operated_in_cs > self.delay_threshold[user_index][time_index]:
            return False
        else:
            return True

    def _is_fossil_consumption(self, r, t):
        if r == self.cc_index:
            du_set = self.r_du_in_cc
            static_cons = self.PC_CC_STATIC
            dynamic_cons = self.PC_CC_DU
        else:
            du_set = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
            static_cons = self.PC_EC_STATIC
            dynamic_cons = self.PC_EC_DU
        number_of_active_du = 0
        for d in du_set:
            number_of_active_du += self.decision_a[d][t]
        total_energy_consumption = int(static_cons + number_of_active_du * dynamic_cons)
        if total_energy_consumption - self.decision_s[r][t] > 0:
            return True
        else:
            return False

    def _offload_the_function(self, i, d, f, t, rs2cs=True):
        self.decision_m[i][d][f][t] = 0
        self.du_load[d][t] -= self.traffic_load[i][t]
        if self._is_there_any_assignment_in_this_du(d, t) is False:
            self.decision_a[d][t] = False

        if rs2cs:
            du_range = self.r_du_in_cc
            capacity = self.L_CC
        else:
            r = self._get_site_from_user(i)
            du_range = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
            capacity = self.L_EC

        for d_newhost in du_range:
            if self.du_load[d_newhost][t] + self.traffic_load[i][t] <= capacity:
                self.du_load[d_newhost][t] += self.traffic_load[i][t]
                # print "i:{} t:{} d_newhost:{} self.du_load[d_newhost][t]:{}".format(i, t, d_newhost, self.du_load[d_newhost][t])
                self.decision_m[i][d_newhost][f][t] = 1
                self.decision_a[d_newhost][t] = 1
                break

    def _revise_the_du_assignment(self, r, t):
        if r == self.cc_index:
            user_set = self.r_i
            du_set = self.r_du_in_cc
            capacity = self.L_CC
        else:
            user_set = list(range(r * self.NUMBER_OF_UE_PER_EC, (r + 1) * self.NUMBER_OF_UE_PER_EC))
            du_set = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
            capacity = self.L_EC
        decision_m_copy = np.copy(self.decision_m)
        for d in du_set:
            self.decision_a[d][t] = 0
            self.du_load[d][t] = 0
            for i in user_set:
                for f in self.r_up:
                    self.decision_m[i][d][f][t] = 0
        current_du_index = r * self.n_of_du_per_ec
        for i in user_set:
            for f in self.r_up:
                for check_du in du_set:
                    if decision_m_copy[i][check_du][f][t] == 1:
                        if self.du_load[current_du_index][t] + self.traffic_load[i][t] <= capacity:
                            self.du_load[current_du_index][t] += self.traffic_load[i][t]
                        else:
                            current_du_index += 1
                        self.decision_m[i][self.r_du[current_du_index]][f][t] = 1
                        break

        # print "sum of activation :{}".format( np.sum(self.decision_m))
        for d in du_set:
            if self._is_there_any_assignment_in_this_du(d, t):
                self.decision_a[d][t] = 1

    def offloading_to_server_site_experimental(self):
        for t in self.r_t:
            number_of_active_du_per_site, total_number_of_active_du_cs, total_number_of_active_du_rs = self.calculate_number_of_active_du_per_site(self.decision_a)
            total_consumption = self.calculate_total_consumption(number_of_active_du_per_site)
            fossil_consumption = self.calculate_fossil_consumption_in_specific_time(t, total_consumption)
            for r in self.r_edge_cloud:
                print("site:{} fossil_consumption:{}".format(r, fossil_consumption[r]))
            ordered_remote_site = np.argsort(fossil_consumption, axis=-1)[::-1]
            print("ordered_remote_site:{}".format(ordered_remote_site))
            ordered_remote_site = ordered_remote_site[1:21]
            print("ordered_remote_site:{}".format(ordered_remote_site))
            # self._offloading_to_server_site(self.r_edge_cloud, t)
            self._offloading_to_server_site(ordered_remote_site, t)

    def _offloading_to_server_site(self, ordered_remote_site, t):
        # print "TIME_SLOT:{}".format(t)
        for r in ordered_remote_site:
            if r == self.cc_index:
                continue
            # print "REMOTE SITE:{}".format(r)
            du_set_in_r = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
            du_set_in_r_reverse = du_set_in_r[::-1]
            user_set_in_r = list(range(r * self.NUMBER_OF_UE_PER_EC, (r + 1) * self.NUMBER_OF_UE_PER_EC))

            copy_m = np.copy(self.decision_m)
            copy_a = np.copy(self.decision_a)
            copy_du_load = np.copy(self.du_load)
            prev_active_du, prev_fossil_consumption = self.get_active_du_and_fossil_consumption(t)
            # prev_active_du = self.calculate_number_of_active_du_specific_site(r, t, self.decision_a)

            for d in du_set_in_r_reverse:
                if self.decision_a[d][t] == 0:
                    continue

                for i in user_set_in_r:
                    for f in self.r_up:
                        if self.decision_m[i][d][f][t] == 1:
                            if self._delay_constraint_check_pass(i, t):
                                self._offload_the_function(i, d, f, t)
            self._revise_the_du_assignment(r, t)
            active_du = self.calculate_number_of_active_du_specific_site(r, t, self.decision_a)

            if True:
                active_du, fossil_consumption = self.get_active_du_and_fossil_consumption(t)
                # if prev_active_du <= active_du or prev_fossil_consumption <= fossil_consumption:
                if prev_active_du <= active_du:
                    # print "TIME[{}] We could not empty the du:{} in RS:{} prev:{} active:{}".format(t, d, r, prev_active_du, active_du)
                    self.decision_m = np.copy(copy_m)
                    self.decision_a = np.copy(copy_a)
                    self.du_load = np.copy(copy_du_load)
                else:
                    pass
                    # print "TIME[{}] Empty DU:{} in RS:{} prev:{} active:{}".format(t, d, r, prev_active_du, active_du)

    def offloading_to_server_site(self):
        for t in self.r_t:
            # print "TIME_SLOT:{}".format(t)
            for r in self.r_edge_cloud:
                # print "REMOTE SITE:{}".format(r)
                du_set_in_r = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
                du_set_in_r_reverse = du_set_in_r[::-1]
                user_set_in_r = list(range(r * self.NUMBER_OF_UE_PER_EC, (r + 1) * self.NUMBER_OF_UE_PER_EC))
                copy_m = np.copy(self.decision_m)
                copy_a = np.copy(self.decision_a)
                copy_du_load = np.copy(self.du_load)
                prev_active_du = self.calculate_number_of_active_du_specific_site(r, t, self.decision_a)
                for d in du_set_in_r_reverse:
                    if self.decision_a[d][t] == 0:
                        continue

                    for i in user_set_in_r:
                        for f in self.r_up:
                            if self.decision_m[i][d][f][t] == 1:
                                if self._delay_constraint_check_pass(i, t):
                                    self._offload_the_function(i, d, f, t)
                self._revise_the_du_assignment(r, t)
                active_du = self.calculate_number_of_active_du_specific_site(r, t, self.decision_a)

                if True:
                    if prev_active_du <= active_du:
                        # print "TIME[{}] We could not empty the du:{} in RS:{} prev:{} active:{}".format(t, d, r, prev_active_du, active_du)
                        self.decision_m = np.copy(copy_m)
                        self.decision_a = np.copy(copy_a)
                        self.du_load = np.copy(copy_du_load)
                    else:
                        pass
                        # print "TIME[{}] Empty DU:{} in RS:{} prev:{} active:{}".format(t, d, r, prev_active_du, active_du)

    def _calculate_unstored_energy(self):
        unstored_energy = [[0 for x in self.r_t] for x in self.r_cloud]
        for r in self.r_cloud:
            for t in self.r_t:
                if t == 0:
                    remaining_battery_energy_before_consumption = self.initial_battery_energy[r]
                else:
                    remaining_battery_energy_before_consumption = self.decision_be[r][t - 1]
                energy_in_an_unlimited_battery = remaining_battery_energy_before_consumption + self.ge[r][t] - self.decision_s[r][t]
                if energy_in_an_unlimited_battery > self.battery_capacity[r]:
                    unstored_energy[r][t] = energy_in_an_unlimited_battery - self.battery_capacity[r]
                else:
                    unstored_energy[r][t] = 0
        return unstored_energy

    def sold_energy(self):
        self.decision_p = [[0 for x in self.r_t] for x in self.r_cloud]
        unstored_energy = self._calculate_unstored_energy()
        for r in self.r_cloud:
            for t in self.r_t:
                self.decision_p[r][t] = unstored_energy[r][t]

    def get_active_du_and_fossil_consumption(self, t):
        active_du = self.calculate_number_of_active_du_specific_site(self.cc_index, t, self.decision_a)
        number_of_active_du_per_site, total_number_of_active_du_cs, total_number_of_active_du_rs = self.calculate_number_of_active_du_per_site(self.decision_a)
        total_consumption = self.calculate_total_consumption(number_of_active_du_per_site)
        fossil_consumption = self.calculate_fossil_consumption_total_in_specific_time(t, total_consumption)
        return active_du, fossil_consumption

    def user_migration(self):
        unstored_energy = self._calculate_unstored_energy()
        for t in self.r_t:
            if unstored_energy[self.cc_index][t] > 0:
                for r in self.r_edge_cloud:
                    if unstored_energy[r][t] < 0:
                        pass
                        print("RS2CS Migration R:{} T:{} CS uns:{} RS uns:{}".format(r, t, unstored_energy[self.cc_index][t], unstored_energy[r][t]))
            else:
                copy_m = np.copy(self.decision_m)
                copy_a = np.copy(self.decision_a)
                copy_du_load = np.copy(self.du_load)
                prev_active_du, prev_fossil_consumption = self.get_active_du_and_fossil_consumption(t)
                for r in self.r_edge_cloud:
                    if unstored_energy[r][t] > 0:
                        print("CS2RS Migration R:{} T:{} CS uns:{} RS uns:{}".format(r, t, unstored_energy[self.cc_index][t], unstored_energy[r][t]))
                        # find the user set that is related with RS but serve in CS
                        du_set_in_r_reverse = self.r_du_in_cc[::-1]
                        user_set_in_r = list(range(r * self.NUMBER_OF_UE_PER_EC, (r + 1) * self.NUMBER_OF_UE_PER_EC))

                        for d in du_set_in_r_reverse:
                            if self.decision_a[d][t] == 0:
                                continue
                            '''
                            if not self._is_fossil_consumption(self.cc_index, t):
                                continue
                            '''
                            for i in user_set_in_r:
                                for f in self.r_up:
                                    if self.decision_m[i][d][f][t] == 1:
                                        # print "Migration::t:{}  d:{} i:{} f:{}".format(t, d, i, f)
                                        rs2cs = False
                                        self._offload_the_function(i, d, f, t, rs2cs)
                self._revise_the_du_assignment(self.cc_index, t)
                active_du, fossil_consumption = self.get_active_du_and_fossil_consumption(t)
                # if prev_active_du <= active_du or prev_fossil_consumption <= fossil_consumption:
                if prev_active_du <= active_du:
                    print("TIME[{}] MIGRATION CANCELLED! in CS prev_active:{} active:{} prev_fossil_consumption:{} fossil_consumption:{}" \
                          .format(t, prev_active_du, active_du, prev_fossil_consumption, fossil_consumption))
                    self.decision_m = np.copy(copy_m)
                    self.decision_a = np.copy(copy_a)
                    self.du_load = np.copy(copy_du_load)
                else:
                    pass
                    print("TIME[{}] MIGRATION COMPLETED! in CS prev_active:{} active:{} prev_fossil_consumption:{} fossil_consumption:{}" \
                          .format(t, prev_active_du, active_du, prev_fossil_consumption, fossil_consumption))

    def initial_ren_en_assignment(self, site_list):
        ordered_energy_price_time_slot = np.argsort(self.energy_prices_per_hour, axis=-1)
        ordered_energy_price_time_slot = ordered_energy_price_time_slot[::-1]
        number_of_active_du_per_site, total_number_of_active_du_cs, total_number_of_active_du_rs = self.calculate_number_of_active_du_per_site(self.decision_a)
        total_energy_consumption = self.calculate_total_consumption(number_of_active_du_per_site)
        for r in site_list:
            for current_t in ordered_energy_price_time_slot:
                if self.reserved_energy[r][current_t] == MAGIC_NUMBER:
                    availableEn = self.ge[r][current_t]
                else:
                    availableEn = - max(self.reserved_energy[r][current_t], 0)
                if current_t == 0:
                    next_battery_energy = self.initial_battery_energy[r] + availableEn
                else:
                    next_battery_energy = self.decision_be[r][current_t - 1] + availableEn
                if next_battery_energy >= total_energy_consumption[r][current_t]:
                    self.decision_s[r][current_t] = total_energy_consumption[r][current_t]
                else:
                    self.decision_s[r][current_t] = next_battery_energy

                self.update_the_battery_state()

                if current_t != 0:  # if it is the first time slot we did not need to think about the previous day
                    # in the "current_t" we spend renewable energy (decision_s) so we will update the needed energy in "current_t-1" according to this new consumption
                    new_need = max(self.decision_s[r][current_t] - self.ge[r][current_t], 0)
                    for t in range(current_t - 1, 0, -1):
                        if self.reserved_energy[r][t] == MAGIC_NUMBER:
                            self.reserved_energy[r][t] = new_need - self.ge[r][t]
                            new_need = self.reserved_energy[r][t]
                        else:
                            self.reserved_energy[r][t] += new_need
                        if self.reserved_energy[r][t] <= 0:
                            break
                        if self.reserved_energy[r][t] > self.battery_capacity[r]:
                            raise Exception("Aiee! SW Bug!")
                # needed energy changes  in "current_t-1", the previous time slots are depend on it so we have to update them also

    def initial_du_assignment(self):
        for t in self.r_t:
            for r in self.r_edge_cloud:
                self._initial_du_assignment(r, t)

    def _initial_du_assignment(self, r, t):
        du_set_in_r = list(range(r * self.n_of_du_per_ec, (r + 1) * self.n_of_du_per_ec))
        user_set_in_r = list(range(r * self.NUMBER_OF_UE_PER_EC, (r + 1) * self.NUMBER_OF_UE_PER_EC))
        current_du_index = r * self.n_of_du_per_ec
        for i in user_set_in_r:
            for f in self.r_up:
                if self.du_load[current_du_index][t] + self.traffic_load[i][t] > self.L_EC:
                    current_du_index += 1
                self.du_load[current_du_index][t] += self.traffic_load[i][t]
                self.decision_m[i][self.r_du[current_du_index]][f][t] = 1
        # print "sum of activation :{}".format( np.sum(self.decision_m))

        for d in du_set_in_r:
            if self._is_there_any_assignment_in_this_du(d, t):
                self.decision_a[d][t] = 1

        # print "sum of active du :{}".format(np.sum(self.decision_a))

    def _get_site_from_du(self, d):
        if d >= self.n_of_du_per_ec * self.cc_index:
            return self.cc_index
        else:
            site_no = d / self.n_of_du_per_ec
        return int(site_no)

    def _get_site_from_user(self, i):
        site_no = i / self.NUMBER_OF_UE_PER_EC
        return int(site_no)

    def _is_there_any_assignment_in_this_du(self, d, t):
        r = self._get_site_from_du(d)
        if r == self.cc_index:
            user_set = self.r_i
        else:
            user_set = list(range(r * self.NUMBER_OF_UE_PER_EC, (r + 1) * self.NUMBER_OF_UE_PER_EC))
        for i in user_set:
            for f in self.r_up:
                # print "r:{} i:{} d:{} f:{} t:{}".format(r,i,d,f,t)
                if self.decision_m[i][d][f][t] == 1:
                    return True
        return False

    def print_variables(self):
        self.init_the_record_writer()
        self._print_general_info()
        ########################################################################################################
        # Getting DECISION VARIABLES
        number_of_active_du_per_site, total_number_of_active_du_cs, total_number_of_active_du_rs = self.calculate_number_of_active_du_per_site(self.decision_a)

        if self.ENERGY_TRANSFER_AVAILABLE:
            energy_transfer_matrix = [[[0 for x in self.r_t] for x in self.r_cloud] for x in self.r_cloud]
            for t in self.r_t:
                for i in self.r_cloud:
                    for j in self.r_cloud:
                        energy_transfer_matrix[i][j][t] += int(self.decision_x[i][j][t])
            self._print_variables_3(RecordWriter.filter_list[7], energy_transfer_matrix)

        total_consumption = self.calculate_total_consumption(number_of_active_du_per_site)
        fossil_consumption = self.calculate_fossil_consumption(total_consumption)

        unstored_energy = self._calculate_unstored_energy()
        self._print_total_number_of_active_du(total_number_of_active_du_cs, total_number_of_active_du_rs)
        self._print_variables(RecordWriter.filter_list[1], number_of_active_du_per_site)

        obj_val = self.calculate_the_obj_val(self.decision_a, self.decision_s, self.decision_p)
        self.rw.log_data("Objective Value:{}\n", *(obj_val,))
        self.rw.append_record_data(RecordWriter.filter_list[0], obj_val)

        for i in range(10):
            print("i:{} Threshold:{}".format(i, self.delay_threshold[i][0]))
        for d in self.r_du_in_cc:
            for f in self.r_up:
                if self.decision_m[0][d][f][0] == True:
                    print("CS:: d:{} self.decision_m[0][d][f][0]:{}".format(d, self.decision_m[0][d][f][0]))

        self._print_variables(RecordWriter.filter_list[2], self.decision_s)
        self._print_variables(RecordWriter.filter_list[3], total_consumption)
        self._print_variables(RecordWriter.filter_list[4], fossil_consumption)
        self._print_variables(RecordWriter.filter_list[5], self.decision_be)
        self._print_variables(RecordWriter.filter_list[6], unstored_energy)
        self._print_variables(RecordWriter.filter_list[8], self.reserved_energy)
        self._print_variables(RecordWriter.filter_list[9], self.ge)
        self._print_variables(RecordWriter.filter_list[10], self.decision_p)

        '''
        for du_index in self.r_du:
            print "DU[{}] Load: {}".format(du_index, self.du_load[du_index])
        '''

        self.rw.log_finish()


if __name__ == '__main__':
    sm = "Heuristic_Renewable"
    CREATE_TRAFFIC_DATA = True
    if CREATE_TRAFFIC_DATA:
        for ts in traffic_scenarios:
            print("Creating Data for ts rate {} and {} days...".format(ts, NUMBER_OF_SIMULATION_DAY))
            gg = MidhaulHeuristic("istanbul", ts, sm, 0)
            gg.midhaul_generic.gurobi_create_data(NUMBER_OF_SIMULATION_DAY)
        print("Process is finished successfully")
        exit(0)

    remaining_battery_energy_from_previous_day = None
    for city_name in city_name_list:
        for traffic_scen in traffic_scenarios:
            for day in range(NUMBER_OF_SIMULATION_DAY):
                gg = MidhaulHeuristic(city_name, traffic_scen, sm, day)
                gg.set_initial_battery_energy(remaining_battery_energy_from_previous_day)
                print("========  HEURISTIC SOLVE START:{} day:{}======== ".format(datetime.now(), day))
                print("HEURISTIC SOLVE LOAD DATA:{}".format(datetime.now()))
                gg.gurobi_load_data()  # GRB_GIVEN
                print("HEURISTIC SOLVE add_variables:{}".format(datetime.now()))
                gg.add_variables()  # GRB_DECISION

                print("HEURISTIC SOLVE initial_du_assignment:{}".format(datetime.now()))
                gg.initial_du_assignment()  # GRB_CONSTRAINTS
                print("HEURISTIC SOLVE update_the_battery_state:{}".format(datetime.now()))
                gg.update_the_battery_state()
                print("HEURISTIC SOLVE print_variables:{}".format(datetime.now()))
                # gg.print_variables()
                print("HEURISTIC SOLVE initial_ren_en_assignment for remote sites:{}".format(datetime.now()))
                gg.initial_ren_en_assignment(gg.r_edge_cloud)
                print("HEURISTIC SOLVE offloading_to_server_site:{}".format(datetime.now()))
                if True:
                    gg.offloading_to_server_site()
                else:
                    gg.offloading_to_server_site_experimental()
                print("HEURISTIC SOLVE initial_ren_en_assignment for server site:{}".format(datetime.now()))
                gg.initial_ren_en_assignment([gg.cc_index])
                print("HEURISTIC SOLVE user_migration:{}".format(datetime.now()))
                gg.user_migration()
                print("HEURISTIC SOLVE sold_energy:{}".format(datetime.now()))
                gg.sold_energy()
                print("HEURISTIC SOLVE RESULTS:{}".format(datetime.now()))
                gg.print_variables()

    print("That's all Folk'")
