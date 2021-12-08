"""Monitor Module.
Printing, Recording and Plotting Classes for Journal 3 and Grove Journal

"""

import csv
import os.path
from collections import OrderedDict

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.ticker import AutoMinorLocator

from constants import *

CAPITAL_EXPENDITURE = 258000
MAINTANENCE_COST_J2 = 300.0
# 26593, 53187, 106375, 212750, 425500
CAPEX_SOLAR_PANEL = [106375, 212750, 425500, 851000, 1702000]
# 106375, 212750, 425500, 851000, 1702000

MAINTANENCE_COST = (300.0 * 7)  # 7 <= 6 RU + 1CU
OPEX_PER_YEAR_CONVERTER = 365.0
CAP_EFF_PER_YEAR_15 = CAPITAL_EXPENDITURE / 15.0
CAP_EFF_PER_DAY = CAP_EFF_PER_YEAR_15 / 365
WATT_2_KW_CORRECTION_RATE = 1000.0
MONTH_2_YEAR_CONVERTER = (365 / 12.0)
USD_TRY_CONVERTER = 7.0
DOLLAR_K_CONVERTER = (1 / USD_TRY_CONVERTER)
RESULTS_WITH_NON_RENEWABLE = False
OUTPUT_PATH = "../output/"
INPUT_PATH = "../input/"
PDF_FORMAT = True
FIGURES_PATH = "../figures/"


# FIGURES_PATH = "C:/Users/turgay.pamuklu/Google Drive/PhD/Reports/Journal 2/DER-HCRAN_Rev1/"
class Recorder:
    if PURE_GRID:
        csv_file_path = OUTPUT_PATH + "gurobi_hcran_pure_grid.csv"
    else:
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

    def __init__(self, splitting_method, scenario, day, number_of_ue_per_ec):
        OUTPUT_PATH = "../output/"
        self.splitting_method = splitting_method
        self.scenario = scenario
        self.day = day
        self.number_of_ue_per_ec = number_of_ue_per_ec
        self.log_file = open(OUTPUT_PATH + self.splitting_method + "_" + str(self.number_of_ue_per_ec) + "_hcran.dat", 'a')
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
        self.record_data.append([self.splitting_method, self.scenario, self.day, type_name, type_value])

    def print_header(self, str_header, list_dump):
        self.log_data("{:" + PRINT_TAB_SIZE + "}\t", *(str_header,))
        for t in list_dump:
            self.log_data("{:" + PRINT_TAB_SIZE + "}\t", *(t,))
        self.log_data("\n")

    def log_data(self, log_string, *log_args):
        self.log_file.write(log_string.format(*log_args))


class RecordReader(Recorder):
    def __init__(self, splitting_methods):
        self.time_slot = 24
        self.splitting_methods = splitting_methods
        self.iteration_index_len = NUMBER_OF_SIMULATION_DAY
        if JOURNAL3:
            self.number_of_site = 6
        elif JOURNAL4:
            self.number_of_site = 7
        else:
            self.number_of_site = 21

    @staticmethod
    def get_color_index(method_string):
        if JOURNAL4:
            if "PreRoute" in method_string:
                return 0
            elif "TrafficAware" in method_string:
                return 1
            elif "BatteryAware_Renewable" in method_string:
                return 2

    @staticmethod
    def get_label_prefix(method_string):
        if JOURNAL4:  # GROVE Journal
            if "PreRoute" in method_string:
                label_prefix = 'Static Routing'
            elif "TrafficAware" in method_string:
                label_prefix = 'Traffic Aware'
            elif "BatteryAware_Renewable" in method_string:
                label_prefix = 'Proposed Solution'
        elif JOURNAL3:
            if "SwitchOn" in method_string:
                label_prefix = 'Only Split MILP'
            elif "TrafficAware" in method_string:
                label_prefix = 'Default MILP'
            elif "BatteryAware_Renewable" in method_string:
                label_prefix = 'Proposed MILP'
        else:
            if "Non" in method_string:
                label_prefix = "Brown"
            elif "TrafficAware" in method_string:
                label_prefix = 'Standard MILP'
            elif "BatteryAware" in method_string:
                label_prefix = 'Green MILP'
            else:
                label_prefix = "Heuristic Method"
            if "OnlyCS" in method_string:
                label_prefix += "_Centralized"
            if "OnlyRS" in method_string:
                label_prefix += "_Distributed"
        return label_prefix

    def get_data_per_day(self, filter_string):
        dict_data = OrderedDict()
        if DU_CAPACITY_SIZE_AS_A_MULTIPLIER:
            iteration_list = [1, 2, 4, 8]
        else:
            iteration_list = range(self.iteration_index_len)
        data_for_all_city = OrderedDict()
        for city_name in city_name_list:
            for traffic_scen in traffic_scenarios:
                data_output = [[0 for x in iteration_list] for x in range(len(self.splitting_methods))]
                it_index_order = 0
                for iteration_index in iteration_list:
                    with open(RecordReader.csv_file_path, 'r') as csv_file:
                        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                        header = next(csv_reader)
                        filtered_comb = [p for p in csv_reader if filter_string in p[3] and iteration_index == int(float(p[2]))]
                        if filtered_comb is None:
                            continue
                        key = city_name + '_' + str(traffic_scen)
                        filtered = [p for p in filtered_comb if key in p[1]]
                        method_index = 0
                        for each_method in self.splitting_methods:
                            method_filter = [p for p in filtered if each_method == p[0]]
                            print("{}\tts:{}\t{}\tit:{}\tfilter:{}".format(city_name, traffic_scen, each_method, iteration_index, filter_string))
                            if filter_string != RecordWriter.filter_list[0]:
                                for site_index in range(self.number_of_site):
                                    for time in range(self.time_slot):
                                        print("site_index:{} time:{}".format(site_index, time))
                                        key = filter_string + '{},{}'.format(site_index, time)
                                        value = [p for p in method_filter if key in p[3]]
                                        if value == []:
                                            print("Aiee!!")
                                        data_output[method_index][it_index_order] += int(float(value[0][4]))
                            else:
                                value = [p for p in method_filter if filter_string in p[3]]
                                data_output[method_index][it_index_order] = int(float(value[0][4]))
                            method_index += 1
                    it_index_order += 1
                key_is = RecordReader.get_key(city_name, traffic_scen)
                data_for_all_city[key_is] = data_output
        return data_for_all_city

    @staticmethod
    def get_key(city_name, traffic_scen):
        return city_name + '_' + '_ts:' + str(traffic_scen)

    @staticmethod
    def get_key_by_method(method, site):
        return method + '_' + str(site)

    @staticmethod
    def get_key_by_method_and_day(method, site, day):
        return method + '_site_' + str(site) + '_day_' + str(day)

    @staticmethod
    def get_key_by_method_and_city(city_name, traffic_scen, method):
        return city_name + '_' + method + '_ts:' + str(traffic_scen)

    def get_data_by_time_slot(self, filter_string, city_name=city_name_list[0], traffic_scen=traffic_scenarios[0]):
        data_for_all_city = OrderedDict()
        data_with_each_iteration = OrderedDict()
        for iteration_index in range(self.iteration_index_len):
            print("get_data_by_time_slot -- > {} {} {}".format(city_name, traffic_scen, iteration_index))
            if JOURNAL3:
                iteration_index = 1
            with open(RecordReader.csv_file_path, 'r') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                # filtered_comb = op_title(lambda p: filter_string in p[3] and str(iteration_index) in p[2], csv_reader)
                header = next(csv_reader)
                filtered_comb = [p for p in csv_reader if iteration_index == int(p[2])]
                key = city_name + '_' + str(traffic_scen)
                filtered = [p for p in filtered_comb if key in p[1]]
                for each_method in self.splitting_methods:
                    method_filter = [p for p in filtered if each_method == p[0]]
                    for site_index in range(self.number_of_site):
                        data = [0 for x in range(self.time_slot)]
                        for time in range(self.time_slot):
                            # print("city_name:{} traffic_scen:{} each_method:{} iteration_index:{} site_index:{} time:{}".format(city_name,
                            #                             traffic_scen, each_method, iteration_index, site_index, time))
                            key = filter_string + '{},{}'.format(site_index, time)
                            value = [p for p in method_filter if key in p[3]]
                            data[time] += float(value[0][4])
                        key_is = RecordReader.get_key_by_method_and_day(each_method, site_index, iteration_index)
                        data_with_each_iteration[key_is] = data
        for each_method in self.splitting_methods:
            for site_index in range(self.number_of_site):
                data = [0 for x in range(self.time_slot)]
                for iteration_index in range(self.iteration_index_len):
                    key_is = RecordReader.get_key_by_method_and_day(each_method, site_index, iteration_index)
                    data = [data[x] + data_with_each_iteration[key_is][x] for x in range(self.time_slot)]
                key_is = RecordReader.get_key_by_method(each_method, site_index)
                data = [data[x] / NUMBER_OF_SIMULATION_DAY for x in range(self.time_slot)]
                data_for_all_city[key_is] = data
        return data_for_all_city

    def merge_the_iterations(self):
        csv_record_path = OUTPUT_PATH + "gurobi_hcran_new.csv"
        with open(csv_record_path, 'ab') as csv_record_file:
            csv_writer = csv.writer(csv_record_file, delimiter=',', quotechar='|', lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
            with open(RecordReader.csv_file_path, 'rb') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                for filter_string in RecordWriter.filter_list:
                    print(("op_title: {}".format(filter_string)))
                    filtered = [p for p in csv_reader if filter_string in p[3]]
                    method_index = 0
                    for each_method in self.splitting_methods:
                        print(("each_method:{}".format(each_method)))
                        method_filter = [p for p in filtered if each_method == p[0]]
                        for traffic_scen in traffic_scenarios:
                            for city_name in city_name_list:
                                print(("traffic_scen: {} city_name:{}".format(traffic_scen, city_name)))
                                key = city_name + '_' + str(traffic_scen)
                                value = [p for p in method_filter if key in p[1]]
                                if filter_string != RecordWriter.filter_list[0]:
                                    for site_index in range(self.number_of_site):
                                        print(("site_index: {}".format(site_index)))
                                        for time in range(self.time_slot):
                                            key = filter_string + '{},{}'.format(site_index, time)
                                            filtered_value = [p for p in value if key in p[3]]
                                            various_val = 0
                                            data_len = len(filtered_value)
                                            for iteration_index in range(data_len):
                                                if iteration_index == 0:
                                                    record_avg_row = filtered_value[iteration_index]
                                                various_val += float(filtered_value[iteration_index][4])
                                            avg_val = various_val / 12
                                            record_avg_row[4] = avg_val
                                            csv_writer.writerow(record_avg_row)
                                else:
                                    obj_val = 0
                                    data_len = len(value)
                                    for iteration_index in range(data_len):
                                        if iteration_index == 0:
                                            record_avg_row = value[iteration_index]
                                        obj_val += float(value[iteration_index][4])
                                    avg_val = obj_val / 12
                                    record_avg_row[4] = avg_val
                                    csv_writer.writerow(record_avg_row)

                        method_index += 1

    def get_data_by_iteration(self, filter_string, iteration_offset):
        dict_data = OrderedDict()
        if DU_CAPACITY_SIZE_AS_A_MULTIPLIER:
            iteration_list = [1, 2, 4, 8]
        else:
            iteration_list = range(self.iteration_index_len)
        data = [[0 for x in iteration_list] for x in range(len(self.splitting_methods))]
        with open(RecordReader.csv_file_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filtered = [p for p in csv_reader if filter_string in p[3]]
            method_index = 0
            for each_method in self.splitting_methods:
                method_filter = [p for p in filtered if each_method == p[0]]
                for traffic_scen in traffic_scenarios:
                    for city_name in city_name_list:
                        # print("traffic_scen:{} city:{} method:{}".format(traffic_scen, city_name, each_method))
                        key = city_name + '_' + str(traffic_scen)
                        value = [p for p in method_filter if key in p[1]]
                        if filter_string != RecordWriter.filter_list[0]:
                            various_val = 0
                            for site_index in range(self.number_of_site):
                                for time in range(self.time_slot):
                                    key = filter_string + '{},{}'.format(site_index, time)
                                    filtered_value = [p for p in value if key in p[3]]
                                    for iteration_index in iteration_list:
                                        various_val += float(filtered_value[iteration_index][4])
                            dict_data[city_name + '_' + each_method + '_ts:' + str(traffic_scen)] = various_val / 4
                        else:
                            obj_val = 0
                            if REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
                                filtered_value = [p for p in value if str(iteration_offset) in p[2]]
                                obj_val = float(filtered_value[0][4])
                            else:
                                for iteration_index in iteration_list:
                                    obj_val += float(value[iteration_offset * NUMBER_OF_SIMULATION_DAY + iteration_index][4])
                            if len(traffic_scenarios) > 1:
                                key_is = self.get_key_by_method_and_city(city_name, traffic_scen, each_method)
                            else:
                                key_is = self.get_key_by_method_and_city(city_name, iteration_offset, each_method)
                            DIVIDE_PER_SITE_PER_HOUR = False
                            if DIVIDE_PER_SITE_PER_HOUR:
                                dict_data[key_is] = obj_val / (self.number_of_site * self.time_slot)
                            else:
                                dict_data[key_is] = (obj_val / WATT_2_KW_CORRECTION_RATE) * MONTH_2_YEAR_CONVERTER * DOLLAR_K_CONVERTER

                method_index += 1
        return dict_data


class NetworkGraph():
    def __init__(self, cg1, cg2, cg4):
        self.cg1 = cg1
        self.cg2 = cg2
        self.cg4 = cg4

    @staticmethod
    def is_switch_node(node_id):
        if node_id > 100:
            return True
        else:
            return False

    def plot_network(self):
        self.cg = self.cg2
        switch_nodes = []
        cc_nodes = []
        ec_nodes = []
        ec_img = mpimg.imread(INPUT_PATH + "images/router.jpg")
        G = nx.DiGraph()
        for node_id in self.cg.node_list:
            G.add_node(node_id)
        for node in G.nodes():
            if node == self.cg.cc_index:
                cc_nodes.append(node)
            elif NetworkGraph.is_switch_node(node):
                switch_nodes.append(node)
            else:
                ec_nodes.append(node)

        for i, j in self.cg.links:
            G.add_edge(i, j)
        node_pos = nx.layout.spring_layout(G)
        fig, ax = plt.subplots(1, 1, figsize=(9, 7))

        # nx.draw_networkx(G, node_pos, node_color=node_col, node_size=400,
        #                  edge_color='black', width=0.4, arrows=False,
        #                  with_labels=True, labels=node_labels, node_shape=node_shape, alpha=0.3)
        labels_journal = ["Routers", "RU", "CU"]
        labels_thesis = ["Routers", "EC", "CC"]
        nx.draw_networkx_nodes(G, node_pos, nodelist=switch_nodes, node_color='blue', node_shape='o', node_size=300, label=labels_thesis[0])
        nx.draw_networkx_nodes(G, node_pos, nodelist=ec_nodes, node_color='red', node_shape='s', node_size=400, label=labels_thesis[1])
        nx.draw_networkx_nodes(G, node_pos, nodelist=cc_nodes, node_color='green', node_shape='*', node_size=1000, label=labels_thesis[2])
        nx.draw_networkx_edges(G, node_pos, width=0.4, arrows=False)
        # Draw the node labels
        # nx.draw_networkx_labels(G, node_pos,node_color=node_col)
        # Draw the edges
        # nx.draw_networkx_edges(G, node_pos, width=0.01)
        # Draw the edge labels
        # nx.draw_networkx_labels(G, node_pos, labels, font_size=16)
        # nx.draw_networkx_edge_labels(G, node_pos, edge_color=edge_col, edge_labels=self.cg.bw)
        # Remove the axis
        plt.axis('off')

        # Show the plot
        lgd = plt.legend(loc='center left', bbox_to_anchor=(0, 1), ncol=1, fancybox=True, shadow=True,
                         fontsize=Monitor.def_font_size + 4)
        # plt.legend()
        plt.show()
        fig.savefig(FIGURES_PATH + "topology" + '.pdf', format='pdf', bbox_inches='tight')

class Monitor:
    """Monitor Class.
    This class use the matplotlib to show graphics for the results that calculates by the other classes.

    """
    # patterns = ('-', '+', 'x', '\\', '*', 'o', 'O', '.')
    def_font_size = 16
    method_type_colors = ['red', 'green', 'blue', 'magenta']
    if JOURNAL3:
        method_type_labels = ['Default MILP', 'Only Split MILP', 'Proposed MILP']
        method_show_order = ['TrafficAware_Renewable_Dynamic', 'BatteryAware_SwitchOn_Dynamic', 'BatteryAware_Renewable_Dynamic']
        method_type_hatch = ['XXX', '\\\\', '\///']
    elif JOURNAL4:
        if RESULTS_WITH_NON_RENEWABLE:
            method_type_labels = ['Grid', 'Std. MILP', 'Green MILP', 'Heuristic']
            method_show_order = ['grid', 'TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic_PreRoute', 'BatteryAware_Renewable_Dynamic']
            method_type_hatch = ['..', 'XXX', '\\\\', '\///']
        else:
            method_type_labels = ['Static Routing', 'Traffic Aware', 'Proposed Solution']
            method_show_order = ['BatteryAware_Renewable_Dynamic_PreRoute', 'TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic']
            method_type_hatch = ['XXXXXX', '\\\\', '*']
            # method_type_hatch = ['XXXXXX', '\\\\', 'oo']
    else:
        if RESULTS_WITH_NON_RENEWABLE:
            method_type_labels = ['Grid', 'Std. MILP', 'Green MILP', 'Heuristic']
            method_show_order = ['grid', 'TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic', 'Heuristic_Renewable']
            method_type_hatch = ['..', 'XXX', '\\\\', '\///']
        else:
            method_type_labels = ['Standard MILP', 'Green-Aware MILP', 'Heuristic Approach']
            method_show_order = ['TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic', 'Heuristic_Renewable']
            method_type_hatch = ['XXX', '\\\\', '\///']
    method_type_lines = ['-', '--', '-.', '-', '--', '-.']
    marker_list = ['o', 'v', 's', 'D', 'x', '<']
    subfigure_prefix = ['(a) ', '(b) ', '(c) ', '(d) ',
                        '(e) ', '(f) ', '(g) ', '(h) ',
                        '(j) ', '(k) ', '(l) ', '(m) ',
                        '(n) ', '(p) ', '(q) ', '(r) ',
                        '(s) ', '(t) ', '(v) ', '(y) ']

    city_show = [x.title() for x in city_name_list]
    traffic_area_labels = ['Low', 'Medium', 'High']

    # traffic_area_labels = ['Low', 'High']

    def __init__(self, splitting_methods):
        self.rr = RecordReader(splitting_methods)

    def __set_x_axis_for_month(self, ax_list, vision_type='not_blind'):
        x_axis_labels = []
        x_axis_locs = []
        for c in range(0, 12, 2):
            x_axis_labels.append(MONTHS_OF_A_YEAR[c])
            x_axis_locs.append(c)
        ax_list.set_xticks(x_axis_locs)
        ax_list.set_xticklabels(x_axis_labels)
        minor_locator_x = AutoMinorLocator(2)
        ax_list.xaxis.set_minor_locator(minor_locator_x)
        if vision_type != 'blind':
            ax_list.set_xlabel('Months of a Year', fontsize=self.def_font_size)

    def __set_x_axis_for_season(self, ax_list, vision_type='not_blind'):
        seasons = ["Winter", "Spring", "Summer", "Fall"]
        x_axis_labels = []
        x_axis_locs = []
        for c in range(len(seasons)):
            x_axis_labels.append(seasons[c])
            x_axis_locs.append(c + 0.2)
        ax_list.set_xticks(x_axis_locs)
        ax_list.set_xticklabels(x_axis_labels)
        minor_locator_x = AutoMinorLocator(4)
        ax_list.xaxis.set_minor_locator(minor_locator_x)

        if vision_type != 'blind':
            ax_list.set_xlabel('Seasons', fontsize=self.def_font_size)

    def __set_x_axis_for_hour(self, ax_list, vision_type='not_blind'):
        x_axis_labels = []
        x_axis_locs = []
        for c in range(2, 24, 4):
            x_axis_labels.append(str(c).zfill(2) + ":00")
            x_axis_locs.append(c)
        ax_list.set_xticks(x_axis_locs)
        ax_list.set_xticklabels(x_axis_labels)
        minor_locator_x = AutoMinorLocator(4)
        ax_list.xaxis.set_minor_locator(minor_locator_x)

        if vision_type != 'blind':
            ax_list.set_xlabel('Hours of a Day', fontsize=self.def_font_size)

    def __set_x_axis_for_day(self, ax_list, vision_type='not_blind'):
        x_axis_labels = []
        x_axis_locs = []
        for c in range(0, 10, 1):
            x_axis_labels.append(str(c + 1))
            x_axis_locs.append(c)
        ax_list.set_xticks(x_axis_locs)
        ax_list.set_xticklabels(x_axis_labels)
        minor_locator_x = AutoMinorLocator(4)
        ax_list.xaxis.set_minor_locator(minor_locator_x)

        if vision_type != 'blind':
            ax_list.set_xlabel('Days', fontsize=self.def_font_size)

    def plt_vs_day(self, filter):
        div_val = 1
        if False:
            div_val = 24000.0 * 5

        data = self.rr.get_data_per_day(filter)
        fig, ax = plt.subplots(1, 1, figsize=(9, 7))
        filter_index = RecordWriter.filter_list.index(filter)
        ax.set_ylabel(RecordWriter.filter_list_readable[filter_index] + " (MWh)", fontsize=16)
        for method_index in (list(range(len(data)))):
            data[method_index] = [x / div_val for x in data[method_index]]
            label_prefix = RecordReader.get_label_prefix(self.rr.splitting_methods[method_index])
            x_pos = np.arange(4)
            if Monitor.method_show_order[method_index] == 'traffic_aware':
                ax.bar(x_pos + method_index * 0.4, data[method_index], width=0.4,
                       edgecolor=Monitor.method_type_colors[method_index], align='center', alpha=0.4,
                       label=label_prefix, hatch=Monitor.method_type_hatch[method_index], fill=False)
            else:
                ax.bar(x_pos + method_index * 0.4, data[method_index], width=0.4,
                       edgecolor=Monitor.method_type_colors[method_index], align='center', alpha=0.4,
                       label=label_prefix, hatch=Monitor.method_type_hatch[method_index], fill=False)
        size_of_data = len(data[0])
        self.__set_x_axis_for_season(ax)
        ax.grid(b=True, axis='y', which='major', linestyle='--')
        ax.legend(loc=2)
        fig_name = "Seasonal_" + filter[:-1]
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + fig_name + '.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + fig_name + '.eps', format='eps', bbox_inches='tight')

    def _plt_vs_month(self, filter, traffic_scen, data, number_of_legend, compare_cities):
        div_val = 1
        if True:
            div_val = (1000000.0 / 30)
        fig, ax = plt.subplots(1, 1, figsize=(9, 7))

        for i in range(number_of_legend):
            if number_of_legend == 1:
                h = data
            else:
                h = data[i]
            #     filter_list = ["DU:", "Ren:", "Total:", "Fossil:", "Batt:", "Unstored:"]
            filter_index = RecordWriter.filter_list.index(filter)
            ax.set_ylabel(RecordWriter.filter_list_readable[filter_index] + " (MWh)", fontsize=16)
            if compare_cities:
                label_prefix = city_name_list[i].title()
                h[0] = [x / div_val for x in h[0]]
                ax.plot(h[0], label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[i],
                        color=Monitor.method_type_colors[i], marker=Monitor.marker_list[i], markersize='7', lw='2')
            else:
                label_prefix = RecordReader.get_label_prefix(self.rr.splitting_methods[i])
                h = [x / div_val for x in h]
                ax.plot(h, label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[i],
                        color=Monitor.method_type_colors[i], marker=Monitor.marker_list[i], markersize='7', lw='2')

            self.__set_x_axis_for_month(ax)
            ax.grid(b=True, which='both', axis='both')
            # ax.grid(b=True, axis='y', which='major', linestyle='--')
            ax.legend(loc=1, fontsize=self.def_font_size)
        fig_name = "Monthly_" + filter[:-1] + "_ts_" + str(traffic_scen)
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + fig_name + '.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + fig_name + '.eps', format='eps', bbox_inches='tight')
        plt.close(fig)

    def plt_vs_month(self, filter, averaged=True):
        compare_cities = True

        data_filter = self.rr.get_data_per_day(filter)
        if averaged:
            data = []
            data_for_all_city = OrderedDict()
            for i in range(len(city_name_list)):
                new_key_is = RecordReader.get_key(city_name_list[i], 100)
                for traffic_scen in traffic_scenarios:
                    old_key_is = RecordReader.get_key(city_name_list[i], traffic_scen)
                    if new_key_is in data_for_all_city:
                        data_for_all_city[new_key_is] = [[x + y for x, y in zip(data_for_all_city[new_key_is][0], data_filter[old_key_is][0])]]
                    else:
                        data_for_all_city[new_key_is] = data_filter[old_key_is]
            number_of_legend = len(city_name_list)
            for i in range(len(city_name_list)):
                key_is = RecordReader.get_key(city_name_list[i], 100)
                data.append(data_for_all_city[key_is])
            self._plt_vs_month(filter, 100, data, number_of_legend, compare_cities)

        else:
            for traffic_scen in traffic_scenarios:
                data = []
                if compare_cities:
                    number_of_legend = len(city_name_list)
                    for i in range(len(city_name_list)):
                        key_is = RecordReader.get_key(city_name_list[i], traffic_scen)
                        data.append(data_filter[key_is])
                else:
                    number_of_legend = len(self.rr.splitting_methods)
                    key_is = RecordReader.get_key(city_name_list[0], traffic_scen)
                    data = data_filter[key_is]
                self._plt_vs_month(filter, traffic_scen, data, number_of_legend, compare_cities)

    def plt_feasibility(self, data, method_name):
        MAX_YEAR = 0
        methods = ['grid', method_name]
        fig, ax = plt.subplots(4, 3, figsize=(9, 7))
        for traffic_scen in traffic_scenarios:
            city_index = 0
            for city_name in city_name_list:
                ax1 = ax[city_index, traffic_scen - 1]
                ax1.get_yaxis().set_visible(False)
                ax1.grid(b=True, which='both', axis='both')
                if city_name == "stockholm":
                    MAX_YEAR = 51
                else:
                    MAX_YEAR = 11
                ax1.set_xlim(0, MAX_YEAR - 1)
                major_ticks = np.arange(0, MAX_YEAR, (MAX_YEAR - 1) / 5)
                # minor_ticks = np.arange(60, 151, 5)
                ax1.set_xticks(major_ticks)
                ax1.set_title(Monitor.subfigure_prefix[city_index * len(traffic_scenarios) + (traffic_scen - 1)]
                              + city_name.title() + " " + Monitor.traffic_area_labels[traffic_scen - 1])
                method_index = 0
                for method in methods:
                    key_is = city_name + '_' + method + '_ts:' + str(traffic_scen)
                    base_val = data[key_is]
                    plt_sequence = [0 for x in range(MAX_YEAR)]
                    if method == 'grid':
                        for year in range(MAX_YEAR):
                            plt_sequence[year] = base_val * (year)
                            grid_sequence = plt_sequence
                    else:
                        for year in range(MAX_YEAR):
                            plt_sequence[year] = (base_val + MAINTANENCE_COST) * year + CAPITAL_EXPENDITURE
                            ren_sequence = plt_sequence

                    if method == 'grid':
                        label_prefix = "Pure Grid"
                    else:
                        label_prefix = "Renewable"
                    ax1.plot(plt_sequence, label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[method_index],
                             color=Monitor.method_type_colors[method_index], marker=Monitor.marker_list[method_index], markersize='2', lw='1'
                             )
                    method_index += 1
                for year in range(MAX_YEAR):
                    if ren_sequence[year] < grid_sequence[year]:
                        year_of_cross = year
                        break
                ax1.annotate(year_of_cross, xy=(year_of_cross, ren_sequence[year_of_cross]), xycoords='data',
                             xytext=(0.6, 0.95), textcoords='axes fraction',
                             arrowprops=dict(arrowstyle="->", connectionstyle="arc3"),
                             horizontalalignment='right', verticalalignment='top',
                             )
                if city_name == "istanbul" and traffic_scen == 2:
                    ax1.set_xlabel('Years of Lifetime', fontsize=self.def_font_size)
                city_index = city_index + 1

        ax1.grid(b=True, axis='y', which='major', linestyle='--')
        lgd = ax1.legend(loc='upper right', bbox_to_anchor=(0.6, 6.4), ncol=2, fancybox=True, shadow=True,
                         fontsize=Monitor.def_font_size + 2)
        # plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=None)
        plt.subplots_adjust(hspace=0.5)
        fig_name = "Fig13"
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + fig_name + '.pdf', format='pdf')
            plt.show()
        else:
            fig.savefig(FIGURES_PATH + fig_name + '.eps', format='eps', bbox_inches='tight')

    @staticmethod
    def city_name_abbreviation(city_name):
        if city_name == 'stockholm':
            return 'Stc'
        elif city_name == 'cairo':
            return 'Cai'
        elif city_name == 'jakarta':
            return 'Jkrt'
        elif city_name == 'istanbul':
            return 'Ist'
        else:
            print("Aieee!")
            return None

    def plt_feasibility_solar_panel(self, data):
        div_val = 1000.0
        methods = ['grid', self.rr.splitting_methods[0]]
        fig, ax = plt.subplots(4, 5, figsize=(9, 7))
        solar_panel_size_list = [0, 1, 2, 3, 4]
        solar_panel_labels = [str((2 ** x) * 5) for x in solar_panel_size_list]
        for solar_panel_size in solar_panel_size_list:
            city_index = 0
            for city_name in city_name_list:
                ax1 = ax[city_index, solar_panel_size]
                ax1.get_yaxis().set_visible(False)
                if city_name == "stockholm" and solar_panel_size == 0:
                    MAX_YEAR = 51
                else:
                    MAX_YEAR = 16
                ax1.set_xlim(0, MAX_YEAR - 1)
                major_ticks = np.arange(0, MAX_YEAR, (MAX_YEAR - 1) / 5)
                ax1.set_xticks(major_ticks)
                ax1.set_title(Monitor.subfigure_prefix[city_index * len(solar_panel_size_list) + solar_panel_size]
                              + Monitor.city_name_abbreviation(city_name) + " " + solar_panel_labels[solar_panel_size])

                method_index = 0
                for method in methods:
                    key_is = self.rr.get_key_by_method_and_city(city_name, solar_panel_size, method)
                    base_val = data[key_is]
                    plt_sequence = [0 for x in range(MAX_YEAR)]
                    if method == 'grid':
                        for year in range(MAX_YEAR):
                            plt_sequence[year] = base_val * (year)
                            plt_sequence[year] /= div_val
                            grid_sequence = plt_sequence
                    else:
                        for year in range(MAX_YEAR):
                            plt_sequence[year] = (base_val + MAINTANENCE_COST) * year + CAPEX_SOLAR_PANEL[solar_panel_size]
                            plt_sequence[year] /= div_val
                            ren_sequence = plt_sequence

                    if method == 'grid':
                        label_prefix = "Pure Grid"
                    else:
                        label_prefix = "Renewable"
                    ax1.plot(plt_sequence, label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[method_index], markevery=5,
                             color=Monitor.method_type_colors[method_index], marker=Monitor.marker_list[method_index], markersize='5', lw='1'
                             )
                    method_index += 1
                year_of_cross = 0
                for year in range(MAX_YEAR):
                    if ren_sequence[year] < grid_sequence[year]:
                        year_of_cross = year
                        break
                ax1.annotate(year_of_cross, xy=(year_of_cross, ren_sequence[year_of_cross]), xycoords='data',
                             xytext=(0.6, 0.95), textcoords='axes fraction',
                             arrowprops=dict(arrowstyle="->", connectionstyle="arc3"),
                             horizontalalignment='right', verticalalignment='top',
                             )
                if city_name == "istanbul" and solar_panel_size == 2:
                    ax1.set_xlabel('Years of Lifetime', fontsize=self.def_font_size)
                city_index = city_index + 1

        lgd = ax1.legend(loc='upper right', bbox_to_anchor=(-0.5, 6.4), ncol=2, fancybox=True, shadow=True,
                         fontsize=Monitor.def_font_size)
        plt.subplots_adjust(left=0.05, right=0.99, hspace=0.5)
        fig.text(0.03, 0.5, "TCO (1000$)", ha='center', va='center', rotation='vertical', fontsize=Monitor.def_font_size)

        ax1.grid(b=False)
        fig_name = "new"
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + fig_name + '.pdf', format='pdf')
        else:
            fig.savefig(FIGURES_PATH + fig_name + '.eps', format='eps', bbox_inches='tight')


    def _plt_vs_hour_sep(self, filter, city_name, traffic_scen, data_for_all_city):
        fig, axes = plt.subplots(2, 1, figsize=(9, 7))
        ax_ec = axes.flat[0]
        ax_cc = axes.flat[1]
        for method_index in range(len(splitting_methods)):
            h = None
            for site_index in range(self.rr.number_of_site):
                key_is = RecordReader.get_key_by_method(splitting_methods[method_index], site_index)
                data = data_for_all_city[key_is]
                if site_index == self.rr.number_of_site - 1:
                    h_cc = data
                elif h is None:
                    h = data
                else:
                    h = [h[i] + data[i] for i in range(len(h))]

            label_prefix = RecordReader.get_label_prefix(splitting_methods[method_index])
            color_index = RecordReader.get_color_index(splitting_methods[method_index])
            h.append(h[0])
            h_cc.append(h_cc[0])
            ax_ec.plot(h, label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[color_index],
                       color=Monitor.method_type_colors[color_index], marker=Monitor.marker_list[color_index],
                       markersize='7', lw='2')

            type_offset = len(splitting_methods)
            ax_cc.plot(h_cc, label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[color_index],
                       color=Monitor.method_type_colors[color_index], marker=Monitor.marker_list[color_index], markersize='7', lw='2')

        filter_index = RecordWriter.filter_list.index(filter)
        ax_ec.set_ylabel("# of " + RecordWriter.filter_list_readable[filter_index], fontsize=16)
        ax_cc.set_ylabel("# of " + RecordWriter.filter_list_readable[filter_index], fontsize=16)
        subfigure_title = ['Edge Clouds', 'Center Cloud']
        # subfigure_title = [Remote Units', 'Center Unit']
        ax_ec.set_title(Monitor.subfigure_prefix[0] + subfigure_title[0], size=16)
        ax_cc.set_title(Monitor.subfigure_prefix[1] + subfigure_title[1], size=16)
        self.__set_x_axis_for_hour(ax_ec, 'blind')
        self.__set_x_axis_for_hour(ax_cc)
        ax_cc.grid(b=True, which='both', axis='both')
        ax_ec.grid(b=True, which='both', axis='both')

        lgd = ax_ec.legend(loc='upper right', bbox_to_anchor=(0.88, 1.35), ncol=2, fancybox=True, shadow=True, fontsize=Monitor.def_font_size)

        fig_name = "Sep_Hourly_" + filter[:-1] + "_" + city_name + "_" + str(traffic_scen)
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + fig_name + '.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + fig_name + '.eps', format='eps', bbox_inches='tight')
        plt.close(fig)

    def plt_vs_hour_sep(self, filter, averaged=True):
        if averaged:
            data_for_all_city = OrderedDict()
            for traffic_scen in traffic_scenarios:
                for city_name in city_name_list:
                    data = self.rr.get_data_by_time_slot(filter, city_name, traffic_scen)
                    for key, value in data.items():
                        if key in data_for_all_city:
                            data_for_all_city[key] = [x + y for x, y in zip(data_for_all_city[key], value)]
                        else:
                            data_for_all_city[key] = [x for x in value]

            self._plt_vs_hour_sep(filter, "all", 0, data_for_all_city)
        else:
            for traffic_scen in traffic_scenarios:
                for city_name in city_name_list:
                    data_for_all_city = self.rr.get_data_by_time_slot(filter, city_name, traffic_scen)
                    self._plt_vs_hour_sep(filter, city_name, traffic_scen, data_for_all_city)

    def _plt_vs_hour(self, filter, city_name, traffic_scen, data_for_all_city):
        if city_name == "all":
            div_val = 12000.0
        else:
            div_val = 1000.0
        fig, ax = plt.subplots(1, 1, figsize=(9, 7))
        CLOUDS_SEPARATELY = True
        if CLOUDS_SEPARATELY:
            for method_index in range(len(splitting_methods)):
                h = None
                for site_index in range(self.rr.number_of_site):
                    key_is = RecordReader.get_key_by_method(splitting_methods[method_index], site_index)
                    data = data_for_all_city[key_is]
                    if site_index == self.rr.number_of_site - 1:
                        h_cc = data
                    elif h is None:
                        h = data
                    else:
                        h = [h[i] + data[i] for i in range(len(h))]

                label_prefix_1 = RecordReader.get_label_prefix(splitting_methods[method_index])
                color_index = RecordReader.get_color_index(splitting_methods[method_index])

                h = [x / div_val for x in h]
                label_prefix = label_prefix_1 + " ECs"
                # label_prefix = label_prefix_1 + " RUs"
                ax.plot(h, label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[color_index],
                        color=Monitor.method_type_colors[color_index], marker=Monitor.marker_list[color_index],
                        markersize='7', lw='2')

                h_cc = [x / div_val for x in h_cc]
                label_prefix = label_prefix_1 + " CC"
                # label_prefix = label_prefix_1 + " CU"
                type_offset = len(splitting_methods)
                ax.plot(h_cc, label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[type_offset + color_index],
                        color=Monitor.method_type_colors[color_index], marker=Monitor.marker_list[type_offset + color_index], markersize='7', lw='2')
        else:
            for method_index in range(len(splitting_methods)):
                h = None
                for site_index in range(self.rr.number_of_site):
                    key_is = RecordReader.get_key_by_method(splitting_methods[method_index], site_index)
                    data = data_for_all_city[key_is]
                    if h is None:
                        h = data
                    else:
                        h = [h[i] + data[i] for i in range(len(h))]

                label_prefix = RecordReader.get_label_prefix(splitting_methods[method_index])

                h = [x / div_val for x in h]
                ax.plot(h, label="{}".format(label_prefix), linestyle=Monitor.method_type_lines[method_index],
                        color=Monitor.method_type_colors[method_index], marker=Monitor.marker_list[method_index], markersize='7', lw='2')
        filter_index = RecordWriter.filter_list.index(filter)
        ax.set_ylabel(RecordWriter.filter_list_readable[filter_index] + " (kWh)", fontsize=self.def_font_size)
        self.__set_x_axis_for_hour(ax)
        # ax.grid(b=True, axis='y', which='major', linestyle='--')
        ax.grid(b=True, which='both', axis='both')
        ax.legend(loc=2, fontsize=self.def_font_size)
        fig_name = "Hourly_" + filter[:-1] + "_" + city_name + "_" + str(traffic_scen)
        if PDF_FORMAT:
            # plt.show()
            fig.savefig(FIGURES_PATH + fig_name + '.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + fig_name + '.eps', format='eps', bbox_inches='tight')
        plt.close(fig)

    def plt_vs_hour(self, filter, averaged=True):
        if averaged:
            data_for_all_city = OrderedDict()
            for traffic_scen in traffic_scenarios:
                for city_name in city_name_list:
                    data = self.rr.get_data_by_time_slot(filter, city_name, traffic_scen)
                    for key, value in data.items():
                        if key in data_for_all_city:
                            data_for_all_city[key] = [x + y for x, y in zip(data_for_all_city[key], value)]
                        else:
                            data_for_all_city[key] = value
            self._plt_vs_hour(filter, "all", 0, data_for_all_city)
        else:
            for traffic_scen in traffic_scenarios:
                for city_name in city_name_list:
                    data_for_all_city = self.rr.get_data_by_time_slot(filter, city_name, traffic_scen)
                    self._plt_vs_hour(filter, city_name, traffic_scen, data_for_all_city)

    def plt_du_per_hour(self):  # plot function example
        self.du_vs_hour()


    def plt_generic_per_hour(self, filter):  # plot function example
        self.plt_vs_hour(filter)

    def plt_generic_per_day(self, filter):  # plot function example
        self.plt_vs_day(filter)

    def plt_generic_per_month(self, filter):  # plot function example
        self.plt_vs_month(filter)

    def plt_bar_total_expenditure(self, expenditure_values, op_title='Operational Cost (1000$)'):
        div_val = 1
        if True:
            div_val = 1000.0
        if JOURNAL4 and not REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
            NORMALIZED_GRAPH = False
        else:
            NORMALIZED_GRAPH = True
        if RESULTS_WITH_NON_RENEWABLE:
            b_off = 0.2
            wid = 0.2
        else:
            b_off = 0.2
            wid = 0.3
        if REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
            fig, axes = plt.subplots(1, 1, figsize=(9, 7))
        else:
            fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        city_index = 0
        for city in city_name_list:
            if REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
                ax1 = axes
            else:
                ax1 = axes.flat[city_index]
            base_width = []
            for method_index in (list(range(len(Monitor.method_show_order)))):
                only_one_method_vals = []
                if REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
                    second_list = networkScale
                else:
                    second_list = traffic_scenarios
                for ts in second_list:
                    key_is = self.rr.get_key_by_method_and_city(city, ts, Monitor.method_show_order[method_index])
                    print("1. city:{} method_index:{} ts:{} key_is:{}".format(city, method_index, ts, key_is))
                    print(expenditure_values)
                    val = expenditure_values[key_is]
                    print("2. city:{} method_index:{} ts:{} key_is:{} val:{}".format(city, method_index, ts, key_is, val))
                    only_one_method_vals.append(val / div_val)
                x_pos = np.arange(len(only_one_method_vals))
                if NORMALIZED_GRAPH:
                    if Monitor.method_show_order[method_index] == Monitor.method_show_order[0]:
                        base_width = list(only_one_method_vals)
                    else:
                        if JOURNAL4:
                            percentage_vals = [100 + (x - y) * (100.0 / abs(y)) for x, y in zip(only_one_method_vals, base_width)]
                        else:
                            percentage_vals = [(x * 100.0) / y for x, y in zip(only_one_method_vals, base_width)]
                    if Monitor.method_show_order[method_index] == Monitor.method_show_order[0]:
                        ax1.bar(x_pos + (method_index) * wid - b_off, [100 for x in range(len(Monitor.traffic_area_labels))], width=wid,
                                edgecolor=Monitor.method_type_colors[method_index], align='center', alpha=0.4,
                                label=Monitor.method_type_labels[method_index], hatch=Monitor.method_type_hatch[method_index], fill=False,
                                )
                    else:
                        ax1.bar(x_pos + (method_index) * wid - b_off, percentage_vals, width=wid,
                                edgecolor=Monitor.method_type_colors[method_index], align='center', alpha=0.4,
                                label=Monitor.method_type_labels[method_index], hatch=Monitor.method_type_hatch[method_index], fill=False,
                                )
                else:
                    ax1.bar(x_pos + (method_index) * wid - b_off, only_one_method_vals, width=wid,
                            edgecolor=Monitor.method_type_colors[method_index], align='center', alpha=0.4,
                            label=Monitor.method_type_labels[method_index], hatch=Monitor.method_type_hatch[method_index], fill=False,
                            )
            if not REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
                ax1.set_title(Monitor.subfigure_prefix[city_index] + city.title(), fontsize=Monitor.def_font_size - 2)
            city_index += 1

            # ax1.set_ylim(20, 121)
            if NORMALIZED_GRAPH:
                major_ticks = np.arange(20, 161, 20)
                # minor_ticks = np.arange(60, 151, 5)
                ax1.set_yticks(major_ticks)
            else:
                pass
                major_ticks = np.arange(-10, 26, 5)
                # minor_ticks = np.arange(-50, 151, 10)
                # ax1.set_yticks(minor_ticks, minor=True)
                ax1.set_yticks(major_ticks, minor=False)

            # ax1.set_yticks(minor_ticks, minor=True)
            for label in ax1.get_yticklabels():
                label.set_fontsize(Monitor.def_font_size)
            ax1.set_xlim(-0.5, len(Monitor.traffic_area_labels) - 0.2)
            ax1.set_xticks(x_pos + 0.1)
            if not REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
                ax1.set_xticklabels(Monitor.traffic_area_labels, fontsize=Monitor.def_font_size - 4)
            else:
                labels_journal = ["6DUs", "12DUs", "24DUs"]
                labels_thesis = ["6EC", "12EC", "24EC"]
                labels = labels_journal
                ax1.set_xticklabels([labels[0], labels[1], labels[2]], fontsize=Monitor.def_font_size + 2)
            ax1.grid(axis='y', which='major')
            # ax1.grid(which='major', linestyle=':')
            # ax1.grid(which='minor', linestyle=':')
            ax1.set_axisbelow(True)
            if city == 'stockholm':
                lgd = ax1.legend(loc='upper right', bbox_to_anchor=(2.2, 1.37), ncol=4, fancybox=True, shadow=True,
                                 fontsize=Monitor.def_font_size)
        # Set common labels
        data_title = op_title
        if not REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
            fig.text(0.03, 0.5, data_title, ha='center', va='center', rotation='vertical', fontsize=Monitor.def_font_size)
        else:
            fig.text(0.03, 0.5, "Normalized OpEx (%)", ha='center', va='center', rotation='vertical', fontsize=Monitor.def_font_size + 2)
            ax1.legend(fontsize=Monitor.def_font_size)
            ram_size_text = ["50GB", "120GB", "300GB"]
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            text_offset = .3
            for text_index in range(3):
                ax1.text(0.14 + text_offset * text_index, 0.72, ram_size_text[text_index], transform=ax1.transAxes, fontsize=Monitor.def_font_size - 2,
                         verticalalignment='top', bbox=props)

        # fig.savefig(FIGURES_PATH + 'bc.eps', format='eps', bbox_extra_artists=(lgd,), bbox_inches='tight')
        fig_name = "opex"
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + fig_name + '.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + fig_name + '.eps', format='eps', bbox_inches='tight')

    def plt_all_scenarios(self, filter_type):
        if REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER:
            dict_data = OrderedDict()
            city_name = city_name_list[0]
            for network_index in networkScale:
                data = self.rr.get_data_by_iteration(filter_type, network_index)
                for method in self.rr.splitting_methods:
                    key_is = self.rr.get_key_by_method_and_city(city_name, network_index, method)
                    dict_data[key_is] = data[key_is]
            self.plt_bar_total_expenditure(dict_data)
        else:
            data = self.rr.get_data_by_iteration(filter_type, 0)
            if RESULTS_WITH_NON_RENEWABLE:
                GRID_OPEX = [190, 215, 860]
                GRID_TCO = []
                for n in GRID_OPEX:
                    GRID_TCO.append(n - CAP_EFF_PER_DAY)
                for traffic_scen in traffic_scenarios:
                    for city_name in city_name_list:
                        key_is = city_name + '_' + 'grid' + '_ts:' + str(traffic_scen)
                        data[key_is] = GRID_TCO[traffic_scen - 1]
            self.plt_bar_total_expenditure(data)

    def plt_objective_function(self):
        Monitor.plt_all_scenarios(self, "Objective Function")

    def plt_du_iteration(self, filter):  # plot function example
        fig, ax = plt.subplots(1, 1, figsize=(9, 7))
        data = self.rr.get_data_per_day(filter)
        all_val = None
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                key_is = RecordReader.get_key(city_name, traffic_scen)
                value = data[key_is]
                a = np.array(value)
                if all_val is not None:
                    all_val = all_val + np.array(value)
                else:
                    all_val = np.array(value)
                # val = data[key_is]

        for i in range(len(all_val)):
            filter_index = RecordWriter.filter_list.index(filter)
            ax.set_ylabel(RecordWriter.filter_list_readable[filter_index])
            label_prefix = RecordReader.get_label_prefix(self.rr.splitting_methods[i])

            h = all_val[i]
            for h_index in range(len(h)):
                h[h_index] /= 1.0
            ax.plot(h, label=str(label_prefix), markersize='7', lw='2')
            ax.grid(b=True, which='major', linestyle='--')
            # self.__set_x_axis_for_day(ax)
            instance_list = [1, 2, 4, 8]
            label_list = [str(x / 5.0) for x in instance_list]
            x_pos = np.arange(4)
            ax.set_xticks(x_pos)
            ax.set_xticklabels(label_list, fontsize=Monitor.def_font_size)
            ax.legend()
        plt.show()

    def plt_iteration_index(self, filter):  # plot function example
        data = self.rr.get_data_per_day(filter)
        data = [list(map(float, x)) for x in data]
        fig, ax = plt.subplots(1, 1, figsize=(9, 7))
        for i in range(len(data)):
            filter_index = RecordWriter.filter_list.index(filter)
            ax.set_ylabel(RecordWriter.filter_list_readable[filter_index])
            label_prefix = RecordReader.get_label_prefix(self.rr.splitting_methods[i])

            h = data[i]
            for h_index in range(len(h)):
                h[h_index] /= 1.0
            ax.plot(h, label=str(label_prefix), markersize='7', lw='2')
            ax.grid(b=True, which='major', linestyle='--')
            self.__set_x_axis_for_day(ax)
            ax.legend()
        plt.show()

    def show_feasibility_solar_panel(self):
        GRID_OPEX = [197]
        dict_data = OrderedDict()
        filter_type = "Objective Function"
        for solar_panel_size in [0, 1, 2, 3, 4]:
            data = self.rr.get_data_by_iteration(filter_type, solar_panel_size)
            for city_name in city_name_list:
                if city_name == "stockholm" and solar_panel_size == 3:
                    print("pause there")
                key_is = self.rr.get_key_by_method_and_city(city_name, solar_panel_size, 'grid')
                grid_opex = GRID_OPEX[0] * OPEX_PER_YEAR_CONVERTER * DOLLAR_K_CONVERTER
                dict_data[key_is] = grid_opex
                key_is = self.rr.get_key_by_method_and_city(city_name, solar_panel_size, self.rr.splitting_methods[0])
                renewable = data[key_is]
                renewable_opex = renewable * OPEX_PER_YEAR_CONVERTER * DOLLAR_K_CONVERTER
                dict_data[key_is] = renewable_opex

                year_compansation = CAPEX_SOLAR_PANEL[solar_panel_size] / (
                            grid_opex - (renewable_opex + MAINTANENCE_COST))
                print("capex:{} grid_opex:{} ren_opex:{} maintanence:{}".format(
                    CAPEX_SOLAR_PANEL[solar_panel_size], grid_opex, renewable_opex, MAINTANENCE_COST))
                print("solar_panel_size:{} city_name:{} year_compensation:{} renewable_opex:{}".format(solar_panel_size,
                                                                                                       city_name,
                                                                                                       year_compansation,
                                                                                                       renewable_opex))

        self.plt_feasibility_solar_panel(dict_data)


    def show_feasibility(self):
        # method_name = 'Heuristic_Renewable'
        method_name = 'BatteryAware_Renewable_Dynamic'
        # method_name = 'TrafficAware_Renewable_Dynamic'
        GRID_OPEX_4hours = [190, 215, 860]
        GRID_OPEX_12hours = [213, 230, 263]
        # ts1: 196784
        GRID_OPEX = [197]
        dict_data = OrderedDict()
        filter_type = "Objective Function"
        data = self.rr.get_data_by_iteration(filter_type, NUMBER_OF_SIMULATION_DAY)
        for traffic_scen in traffic_scenarios:
            for city_name in city_name_list:
                key_is = self.rr.get_key_by_method_and_city(city_name, traffic_scen, method_name)
                renewable = data[key_is]
                renewable_opex = renewable * OPEX_PER_YEAR_CONVERTER
                dict_data[key_is] = renewable_opex

                key_is = city_name + '_' + 'grid' + '_ts:' + str(traffic_scen)
                grid_opex = GRID_OPEX[traffic_scen - 1] * OPEX_PER_YEAR_CONVERTER * DOLLAR_K_CONVERTER
                dict_data[key_is] = grid_opex

                year_compansation = CAPITAL_EXPENDITURE / (grid_opex - renewable_opex)
                print("traffic_scen:{} city_name:{} year_compensation:{}".format(traffic_scen, city_name, year_compansation))
        self.plt_feasibility(dict_data, method_name)


    def execute_print(self):
        # self.show_feasibility_solar_panel()
        # self.plt_du_per_hour()
        # '''
        #new_filter = ["Unstored:"]
        # new_filter = ["Batt:", "Unstored:"]
        # new_filter = ["DU:"]
        new_filter = ["Sold:"]
        # new_filter = RecordWriter.filter_list
        for op_title in new_filter:
            print(("Filter is:{}".format(op_title)))
            # exception_list = [RecordWriter.filter_list[0], "Transfer:", "Should:", "BSON:", "BSCRF:", "BSAssigned:"]
            exception_list = ["Transfer:", "Should:", "BSON:", "BSCRF:", "BSAssigned:"]
            if op_title not in exception_list:
                pass
                # self.plt_generic_per_hour(op_title)
                # self.plt_vs_hour_sep(op_title)
                # self.plt_generic_per_day(op_title)
                self.plt_generic_per_month(op_title)
                # m.plt_iteration_index(RecordWriter.filter_list[0])
                # m.plt_du_iteration(op_title)
        # '''
        # self.plt_objective_function()
        # m.plt_all_scenarios(op_title)


def converting_12_iteration_to_1_iteration(splitting_methods):
    rr = RecordReader(splitting_methods)
    rr.merge_the_iterations()


def clean_empty_lines():
    with open(RecordReader.csv_file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer = []
        for p in csv_reader:
            if p != []:
                writer.append(p)

        with open(OUTPUT_PATH + "test.csv", 'w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', lineterminator='\n', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerows(writer)


if __name__ == '__main__':
    # splitting_methods = ['TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic', 'Heuristic_Renewable']
    # splitting_methods = ['BatteryAware']
    if JOURNAL3:
        splitting_methods = ['TrafficAware_Renewable_Dynamic', 'BatteryAware_SwitchOn_Dynamic', 'BatteryAware_Renewable_Dynamic']
    else:
        splitting_methods = ['TrafficAware_Renewable_Dynamic']
        # splitting_methods = ['BatteryAware_Renewable_Dynamic_PreRoute', 'BatteryAware_Renewable_Dynamic']
        # splitting_methods = ['BatteryAware_Renewable_Dynamic_PreRoute', 'TrafficAware_Renewable_Dynamic', 'BatteryAware_Renewable_Dynamic']
    # **************************************** MONITORING  ****************************************
    # converting_12_iteration_to_1_iteration(splitting_methods)
    # clean_empty_lines()

    m = Monitor(splitting_methods)
    m.execute_print()
