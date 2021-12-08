""" Logs for milp_main.py
"""
import csv
import os.path

from helpers import *

OUTPUT_PATH = "../output/"
INPUT_PATH = "../input/"
PRINT_TAB_SIZE = 8


class Recorder:
    csv_file_path = OUTPUT_PATH + "gurobi_hcran.csv"


class RecordWriter(Recorder):
    filter_list = ["Objective Function", "DU:", "Ren:", "Total:", "Fossil:",
                   "Batt:", "Unstored:", "Transfer:", "Should:", "GE:",
                   "Sold:", "BSON:", "BSCRF:", "BSAssigned:", "Traffic:"]
    filter_list_readable = ["Objective Function",
                            "Active DU",
                            "Renewable Energy Consumption per Cloud",
                            "Total Energy Cost",
                            "Grid Energy Consumption per Cloud",
                            "Remaining Energy in a Battery per Cloud",
                            "Unstored Energy in a Battery per Cloud",
                            "Transferred Energy btw. Sites",
                            "Energy that should be in a Batt",
                            "Generated Energy",
                            "Sold Energy",
                            "Base Station Switch On",
                            "Base Station CRF Active",
                            "Base Station Assignment",
                            "Traffic Rates"
                            ]

    def __init__(self):
        self.log_file = open(OUTPUT_PATH + "_rlbdfs.dat", 'a')
        self.record_data = []

    def log_finish(self):
        self.log_file.close()
        record_header = ["Method", "Scenario", "Iteration", "Type", "Value"]
        if not os.path.isfile(self.csv_file_path):
            with open(self.csv_file_path, 'a') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(record_header)
        with open(self.csv_file_path, 'a') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', lineterminator='\n', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerows(self.record_data)

    @staticmethod
    def set_filter(filter, site, t):
        return "{}{},{}".format(filter, site, t)

    @staticmethod
    def set_filter_3(filter, site1, site2, t):
        return "{},{},{}".format(filter, site1, site2, t)

    def append_record_data(self, type_name, type_value):
        self.record_data.append([type_name, type_value])

    def print_header(self, str_header, list_dump):
        self.log_data("{:" + PRINT_TAB_SIZE + "}\t", *(str_header,))
        for t in list_dump:
            self.log_data("{:" + PRINT_TAB_SIZE + "}\t", *(t,))
        self.log_data("\n")

    def log_data(self, log_string, *log_args):
        self.log_file.write(log_string.format(*log_args))


class RecordReader(Recorder):
    def __init__(self, splitting_methods):
        self.time_slot = NUMBER_OF_TIME_SLOT_IN_ONE_DAY
        self.splitting_methods = splitting_methods
        self.iteration_index_len = NUMBER_OF_SIMULATION_DAY
        self.number_of_site = N_OF_EC

    @staticmethod
    def get_color_index(method_string):
        return 0

    @staticmethod
    def get_label_prefix(method_string):
        label_prefix = "nothing"
        return label_prefix


class Printer:
    def __init__(self, milp_solver):
        self.milp_solver = milp_solver
        pass

    def init_the_record_writer(self):
        self.rw = RecordWriter()

    def _print_general_info(self):
        log_string = "======== Static Energy Consumption(CC/EC):{}/{} ======== \n"
        log_args = (NUMBER_OF_TIME_SLOT_IN_ONE_DAY * self.milp_solver.P_CC_STA, NUMBER_OF_TIME_SLOT_IN_ONE_DAY * N_OF_EC * self.milp_solver.P_EC_STA)
        self.rw.log_data(log_string, *log_args)

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
