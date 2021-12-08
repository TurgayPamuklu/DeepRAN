"""Rfs Module.
Uncompleted/Cancelled RFS Journal Implementation (Journal 2).

"""

from hcran_generic import *
from traffic import *


class RenFuncSplit(HcranGeneric):

    def __init__(self):
        self.rfs_nsr = None
        # Init variables
        self.decision_g = [[0 for x in self.r_t] for x in self.r_j]
        self.decision_h = [[0 for x in self.r_t] for x in self.r_j]
        self.decision_z = [[[0 for x in self.r_t] for x in self.r_j] for x in self.r_i]  # ijt

    # Creating Traffic Data
    def create_traffic(self):
        # USER DEMANDS Avg. per Month
        for user in self.r_i:
            self.traffic_load[user] = Traffic.get_traffic_pattern_for_rfs(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)

        delay_threshold_for_all_day = [[0 for x in range(self.n_of_time_slot)] for x in range(self.number_of_ue)]
        for user in range(self.number_of_ue):
            for time_slot in range(self.n_of_time_slot):
                delay_threshold_for_all_day[user][time_slot] = np.random.randint(250, (100 + self.n_of_up_function * 100)) * 1E-3
                # delay_threshold_for_all_day[user][time_slot] = np.random.randint(250, (251)) * 1E-3
        self.snapshot.save_tr_cran(self.traffic_load, delay_threshold_for_all_day)

    # Loading Traffic and Solar Energy
    def load_data(self):
        # LOAD TRAFFIC
        self.traffic_load, self.delay_threshold = self.snapshot.load_tr_cran()
        # LOAD NFS_SNR
        self.rfs_nsr = self.snapshot.load_nominal_service_rate()
        '''
        for ec_index in range(self.n_of_ec):
            for user_in_ec in range(ec_index, (1+ec_index)*self.number_of_ue_per_ec):
                for t in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    for bs_index in range(self.n_of_cell_per_ec):
                        print("user_in_ec:{} bs_index:{} t:{} nsr:{}".format(ec_index, user_in_ec, t, self.rfs_nsr[user_in_ec][bs_index][t]))
        '''
        # LOAD SOLAR ENERGY
        self.load_solar_energy()

    def _print_variables_cells(self, filter, data_normal):
        data = [[int(x) for x in y] for y in data_normal]
        total_in_a_site = [0 for x in self.r_j]
        filter_index = RecordWriter.filter_list.index(filter)
        self.rw.log_data("---- " + RecordWriter.filter_list_readable[filter_index] + " ----\n")
        self.rw.print_header("TIME", self.r_t)
        for site in self.r_j:
            self.rw.log_data("-CELL[{}]\t", *(site,))
            for t in self.r_t:
                total_in_a_site[site] += data[site][t]
                self.rw.log_data("{:" + PRINT_TAB_SIZE + "}\t", *(data[site][t],))
                self.rw.append_record_data(RecordWriter.set_filter(filter, site, t), data[site][t])
            self.rw.log_data("\n")
        self.rw.log_data("TOTAL Value Per Cell:\t")
        for site in self.r_j:
            self.rw.log_data("{:" + PRINT_TAB_SIZE + "}\t", *(total_in_a_site[site],))
        self.rw.log_data("TOTAL:{:" + PRINT_TAB_SIZE + "}\n", *(sum(total_in_a_site),))

    def calculate_the_obj_val(self, decision_a, decision_s, decision_p, decision_g, decision_h):
        self.__calculate_the_obj_val(self, decision_a, decision_s, decision_p)
        power_cons_SC = 0
        for t in self.r_t:
            for j in self.r_j:
                power_cons_SC += decision_g[j][t] * self.P_SC_ANALOG + decision_h[j][t] * self.P_SC_BB
        calculated_obj = self.__calculate_the_obj_val(self, decision_a, decision_s, decision_p)
        calculated_obj += power_cons_SC
        self.rw.log_data("Power Consumption in SCs:{}\n", *(power_cons_SC,))
        self.rw.log_data("Calculated Obj Val:{}\n", *(calculated_obj,))
        return calculated_obj

