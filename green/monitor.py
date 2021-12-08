"""Monitor Module.
It has one class Monitor which use the matplotlib to show graphics for the results that calculates by the other classes.
(Journal 1)
"""
import csv
import math

import matplotlib.cm as cm
import matplotlib.colors as col
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import AutoMinorLocator

from helpers import CoordinateConverter
from helpers import SHC
from helpers import SaatliMaarifTakvimi
from heuristic import E
from output import Output
from snapshot import *

FIGURES_PATH = "../figures/"
PDF_FORMAT = True


class CplexPlotter:
    new_figure = 0
    line_style = ['-', '--', '-.', ':']

    def __init__(self):
        self.__discrete_cmap(15)

    def __discrete_cmap(self, n=8):
        cpool = ['#bd2309', '#bbb12d', '#1480fa', '#14fa2f', '#000000',
                 '#faf214', '#2edfea', '#ea2ec4', '#ea2e40', '#cdcdcd',
                 '#577a4d', '#2e46c0', '#f59422', '#219774', '#8086d9']
        cmap3 = col.ListedColormap(cpool[0:n], 'indexed')
        cm.register_cmap(cmap=cmap3)

    ##################################################################
    # NEW METHODS FOR CPLEX_OPERATOR
    ##############################################################
    def plot_fossil_vs_bses(self, data, data_labels):
        fig = plt.figure(self.new_figure)
        ax = fig.add_subplot(1, 1, 1)
        x_axis = []
        for c in range(0, len(data[0]), 1):
            x_axis.append(c)
        ax.set_xticks(x_axis)
        ax.set_xticklabels(x_axis)
        ax.set_xlabel('BS ID')
        ax.set_ylabel('Number of Awake Time Slot')
        # ax.set_ylabel('Number of Awake Base Stations')
        for i in range(len(data)):
            ax.plot(data[i], linestyle=self.line_style[i], label=data_labels[i])
        #plt.ylim((18, 28))
        plt.legend(loc=0, prop={'size': 16})
        ax.grid(True)

    def plot_awake_vs_hour(self, data, data_labels):
        fig = plt.figure(self.new_figure)
        ax = fig.add_subplot(1, 1, 1)
        x_axis = []
        for c in range(0, 48, 1):
            x_axis.append(c)
        ax.set_xticks(x_axis)
        ax.set_xticklabels(x_axis)
        ax.set_xlabel('Hours of Two Days')
        ax.set_ylabel('Number of Awake Base Stations')
        for i in range(len(data)):
            ax.plot(data[i], linestyle=self.line_style[i], label=data_labels[i], linewidth=3)
        plt.ylim((18, 28))
        plt.legend()
        ax.grid(True)

    def plot_ren_vs_hour(self, data, data_labels):
        fig = plt.figure(self.new_figure)
        ax = fig.add_subplot(1, 1, 1)
        x_axis = []
        for c in range(0, 48, 1):
            x_axis.append(c)
        ax.set_xticks(x_axis)
        ax.set_xticklabels(x_axis)
        ax.set_xlabel('Hours of Two Days')
        ax.set_ylabel('Renewable Energy Usage Ratio')
        for i in range(len(data)):
            ax.plot(data[i], linestyle=self.line_style[i], label=data_labels[i], linewidth=3)
        # plt.ylim((18,28))
        plt.legend()
        ax.grid(True)

    def show(self):
        plt.show()


class BatteryMemoryPlotter:
    def_font_size = 16
    battery_history = None
    conf = None
    year_data = None
    new_figure = 0

    def __init__(self, number_of_deployed_bs):
        self.conf = Monitor.method_show_order
        self.__discrete_cmap(15)
        self.year_data = self.__get_data_for_sim_duration()
        self.number_of_deployed_bs = number_of_deployed_bs

    def show(self):
        plt.show()

    def __discrete_cmap(self, n=8):
        """create a colormap with n (n<15) discrete colors and register it"""
        # define individual colors as hex values
        cpool = ['#bd2309', '#bbb12d', '#1480fa', '#14fa2f', '#000000',
                 '#faf214', '#2edfea', '#ea2ec4', '#ea2e40', '#cdcdcd',
                 '#577a4d', '#2e46c0', '#f59422', '#219774', '#8086d9']
        cmap3 = col.ListedColormap(cpool[0:n], 'indexed')
        cm.register_cmap(cmap=cmap3)


    ##################################################################
    # OLD METHODS FOR TRADITIONAL OPERATORS
    ##############################################################

    def __set_total_data_vs_hour(self, axis, column_index, show_type='active_wasted'):
        y_axis_data_list = []
        hours = range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)
        for conf_no in range(len(self.conf)):
            d = [0 for x in hours]
            y_axis_data_list.append(d)
        hour_of_the_day = 0
        for data_for_one_time_slot in self.year_data:  # for each time slot data_for_one_time_slot represents [conf][recorded_data_type]
            for conf_no in range(len(self.conf)):
                y_axis_data_list[conf_no][hour_of_the_day] += data_for_one_time_slot[conf_no][column_index]
            # increase_the_time_slot
            hour_of_the_day += 1
            if hour_of_the_day == NUMBER_OF_TIME_SLOT_IN_ONE_DAY:
                hour_of_the_day = 0

        if column_index == 0:
            for conf_no in range(len(self.conf)):
                for h in hours:
                    y_axis_data_list[conf_no][h] /= self.number_of_deployed_bs * NUMBER_OF_SIMULATION_DAY
        else:
            if show_type == 'show_carbon_emission':
                constant_product = E.CARBON_RATE
            else:
                constant_product = 1
            for conf_no in range(len(self.conf)):
                for h in hours:
                    y_axis_data_list[conf_no][h] /= (1e6 * constant_product)

        for conf_no in range(len(self.conf)):
            axis.plot(y_axis_data_list[conf_no], label=Monitor.method_type_labels[conf_no], linestyle=Monitor.method_type_lines[conf_no],
                      color=Monitor.method_type_colors[conf_no], marker=Monitor.marker_list[conf_no],
                      markersize='7', lw='2')

    def __set_total_data_vs_month(self, axis, column_index, show_type='active_wasted'):  # column index informs the recorded data restriction_type
        y_axis_data_list = []
        for conf_no in range(len(self.conf)):
            d = [0 for x in range(len(SHC.LIST_OF_MONTHS_IN_A_YEAR))]
            y_axis_data_list.append(d)
        smf = SaatliMaarifTakvimi()
        for data_for_one_time_slot in self.year_data:  # for each time slot data_for_one_time_slot represents [conf][recorded_data_type]
            for conf_no in range(len(self.conf)):
                y_axis_data_list[conf_no][smf.month_of_the_year] += data_for_one_time_slot[conf_no][column_index]
            smf.yapragi_kopar()  # increase_the_time_slot

        if column_index == 0:  # abc in BATTERY_RECORDS_FOR_EACH_CONF = ['abc', 'fec', 'rec', 'we']
            for conf_no in range(len(self.conf)):
                for m in range(len(SHC.LIST_OF_MONTHS_IN_A_YEAR)):
                    y_axis_data_list[conf_no][m] /= self.number_of_deployed_bs * 0.01
                    y_axis_data_list[conf_no][m] /= (NUMBER_OF_TIME_SLOT_IN_ONE_DAY * SHC.NUMBER_OF_DAYS_IN_MONTHS[m])
        else:
            if show_type == 'show_carbon_emission':
                constant_product = E.CARBON_RATE
            else:
                constant_product = 1
            for conf_no in range(len(self.conf)):
                for m in range(len(SHC.LIST_OF_MONTHS_IN_A_YEAR)):
                    y_axis_data_list[conf_no][m] /= (1e6 * constant_product)

        for conf_no in range(len(self.conf)):
            axis.plot(y_axis_data_list[conf_no], label=Monitor.method_type_labels[conf_no], linestyle=Monitor.method_type_lines[conf_no],
                      color=Monitor.method_type_colors[conf_no], marker=Monitor.marker_list[conf_no],
                      markersize='7', lw='2')

        # Ratio of Switched On Base Stations and Amount of Unstored Ren. En. per Hour
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

    def plot_every_vs_month_two_figures(self, show_type='active_wasted'):
        fig = plt.figure(self.new_figure)
        for i in range(2):
            ax_list = fig.add_subplot(2, 1, i + 1)
            if i == 0:
                if show_type == 'show_carbon_emission':
                    plotted_type = 1  # grid energy figure
                else:
                    plotted_type = 0  # active bs figure
                self.__set_x_axis_for_month(ax_list, 'blind')
                ax_list.set_title('(a) Ratio of Switched on Base Stations')
            else:
                if show_type == 'show_carbon_emission':
                    plotted_type = 2  # ren. energy figure
                else:
                    plotted_type = 3  # wasted energy figure
                self.__set_x_axis_for_month(ax_list)
                ax_list.set_title('(b) Amount of Unstored Renewable Energy')
            self.__set_total_data_vs_month(ax_list, plotted_type, show_type)
            self.__plot_y_label(ax_list, plotted_type)
        plt.legend(loc='upper right', bbox_to_anchor=(0.99, 2.6), ncol=3, fancybox=True, shadow=True,
                   fontsize=Monitor.def_font_size)
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + 'active_unstored_monthly.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + 'active_unstored_monthly.eps', format='eps', bbox_inches='tight')

    def plot_every_vs_month(self, plotted_type):
        fig = plt.figure(self.new_figure)
        ax_list = fig.add_subplot(1, 1, 1)
        self.__set_x_axis_for_month(ax_list)
        self.__set_total_data_vs_month(ax_list, plotted_type)
        self.__plot_y_label(ax_list, plotted_type)
        plt.legend(loc='upper right', bbox_to_anchor=(0.95, 1.1), ncol=3, fancybox=True, shadow=True,
                   fontsize=Monitor.def_font_size)

    def __set_x_axis_for_hour(self, ax_list, vision_type='not_blind'):
        x_axis_labels = []
        x_axis_locs = []
        for c in range(2, NUMBER_OF_TIME_SLOT_IN_ONE_DAY, 4):
            x_axis_labels.append(str(c).zfill(2) + ":00")
            x_axis_locs.append(c)
        ax_list.set_xticks(x_axis_locs)
        ax_list.set_xticklabels(x_axis_labels)
        minor_locator_x = AutoMinorLocator(4)
        ax_list.xaxis.set_minor_locator(minor_locator_x)

        if vision_type != 'blind':
            ax_list.set_xlabel('Hours of a Day', fontsize=self.def_font_size)

    def plot_every_vs_hour_two_figures(self, show_type='active_wasted'):
        fig = plt.figure(self.new_figure)
        for i in range(2):
            ax_list = fig.add_subplot(2, 1, i + 1)
            if i == 0:
                if show_type == 'show_carbon_emission':
                    plotted_type = 1  # grid energy figure
                else:
                    plotted_type = 0  # active bs figure
                self.__set_x_axis_for_hour(ax_list, 'blind')
                ax_list.set_title('(a) Ratio of Switched on Base Stations')
            else:
                if show_type == 'show_carbon_emission':
                    plotted_type = 2  # ren. energy figure
                else:
                    plotted_type = 3  # wasted energy figure
                self.__set_x_axis_for_hour(ax_list)
                ax_list.set_title('(b) Amount of Unstored Renewable Energy')
            self.__set_total_data_vs_hour(ax_list, plotted_type, 'show_carbon_emission')
            self.__plot_y_label(ax_list, plotted_type)
        plt.legend(loc='upper right', bbox_to_anchor=(0.99, 2.6), ncol=3, fancybox=True, shadow=True,
                   fontsize=Monitor.def_font_size)
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + 'active_unstored_hourly.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + 'active_unstored_hourly.eps', format='eps', bbox_inches='tight')

    def plot_every_vs_hour(self, plotted_type):
        fig = plt.figure(self.new_figure)
        ax_list = fig.add_subplot(1, 1, 1)
        self.__set_x_axis_for_hour(ax_list)
        self.__set_total_data_vs_hour(ax_list, plotted_type)
        self.__plot_y_label(ax_list, plotted_type)
        plt.legend(loc='upper right', bbox_to_anchor=(0.95, 1.1), ncol=3, fancybox=True, shadow=True,
                   fontsize=Monitor.def_font_size)

    def __plot_y_label(self, axis, plotted_type):
        if plotted_type == 0:
            axis.set_ylabel('Switched On (%)', fontsize=self.def_font_size)
        if plotted_type == 1:
            axis.set_ylabel('Carbon (Ton)', fontsize=self.def_font_size)
        if plotted_type == 2:
            axis.set_ylabel('Renewable En. (MW)', fontsize=self.def_font_size)
        if plotted_type == 3:
            axis.set_ylabel('Unstored En. (MW)', fontsize=self.def_font_size)

        axis.grid(b=True, which='both', axis='both')

    def __get_data_for_sim_duration(self):
        year_data = []
        with open(Output.output_file_name(), 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=' ', quotechar='|')
            for row in csv_reader:
                if csv_reader.line_num > 1:
                    daily_data = [[0 for x in range(len(SHC.BATTERY_RECORDS_FOR_EACH_CONF))] for y in range(len(self.conf))]
                    all_operation_methods = CalibrationParameters.get_parameters()
                    for i in range(len(self.conf)):
                        c = all_operation_methods.index(self.conf[i])
                        column_no = len(SHC.COMMON_BATTERY_RECORDS) + c * len(SHC.BATTERY_RECORDS_FOR_EACH_CONF)
                        for f in range(len(SHC.BATTERY_RECORDS_FOR_EACH_CONF)):
                            daily_data[i][f] = float(row[0].split(',')[column_no])
                            column_no += 1
                    year_data.append(daily_data)
        return year_data


class Monitor:
    """Monitor Class.
    This class use the matplotlib to show graphics for the results that calculates by the other classes.

    """
    new_figure = 0
    def_font_size = 14

    method_type_colors = ['red', 'blue', 'green']
    method_type_labels = ['Traffic Aware', 'Battery Aware', 'Hybrid']
    method_show_order = ['traffic_aware', 'battery_aware', 'hybrid']
    method_type_lines = ['-', '--', '-.', '-', '--', '-.']
    method_type_hatch = ['XXX', '\\\\', '\///']
    marker_list = ['o', 'v', 's', 'D', 'x', '<']
    subfigure_prefix = ['(a) ', '(b) ', '(c) ', '(d) ']

    city_show = [x.title() for x in city_name_list]
    traffic_area_labels = ['Sparse', 'Normal', 'Dense', 'High D.']

    method_type_colors_gurobi = ['red', 'blue']
    method_type_labels_gurobi = ['Gurobi', 'Our Heuristic']
    method_show_order_gurobi = ['gurobi', 'heuristic']

    def __init__(self):
        self.__discrete_cmap(15)

    @staticmethod
    def __discrete_cmap(n=8):
        """create a colormap with n (n<15) discrete colors and register it"""
        # define individual colors as hex values
        cpool = ['#bd2309', '#bbb12d', '#1480fa', '#14fa2f', '#000000',
                 '#faf214', '#2edfea', '#ea2ec4', '#ea2e40', '#cdcdcd',
                 '#577a4d', '#2e46c0', '#f59422', '#219774', '#8086d9']
        cmap3 = col.ListedColormap(cpool[0:n], 'indexed')
        cm.register_cmap(cmap=cmap3)

    @staticmethod
    def plt_cost_vs_traffic_rate(expenditure_values, avg_traffic):
        fig, axes = plt.subplots(1, 2, figsize=(9, 7))
        city_order_inc_radiation = ['stockholm', 'istanbul', 'jakarta', 'cairo']
        solar_radiation_data = []
        for method_name in Monitor.method_show_order:
            the_average_cost_of_each_harvested = [0 for x in range(len(city_name_list))]
            for city in city_name_list:
                total_val = 0
                for ts in traffic_scenarios:
                    key_is = city + '_' + method_name + '_ts:' + str(ts)
                    total_val += expenditure_values[key_is]
                total_val /= len(traffic_scenarios) * 1000.0
                city_show_order_index = city_order_inc_radiation.index(city)
                the_average_cost_of_each_harvested[city_show_order_index] = total_val
            solar_radiation_data.append(the_average_cost_of_each_harvested)

        traffic_density_data = []
        for method_name in Monitor.method_show_order:
            the_average_cost_of_each_traffic_rate_per_bs = []
            for ts in traffic_scenarios:
                total_val = 0
                for city in city_name_list:
                    key_is = city + '_' + method_name + '_ts:' + str(ts)
                    total_val += expenditure_values[key_is]
                total_val /= len(city_name_list) * E.YEARS_OF_LIFE_CYCLE
                total_val_per_bs = total_val / avg_traffic[ts - 1]
                the_average_cost_of_each_traffic_rate_per_bs.append(total_val_per_bs)
            traffic_density_data.append(the_average_cost_of_each_traffic_rate_per_bs)

        for plot_no in range(2):
            ax1 = axes.flat[plot_no]
            if plot_no == 0:
                for method_no in range(len(solar_radiation_data)):
                    ax1.plot(solar_radiation_data[method_no], label=Monitor.method_type_labels[method_no], linestyle=Monitor.method_type_lines[method_no],
                             color=Monitor.method_type_colors[method_no], marker=Monitor.marker_list[method_no],
                             markersize=7, lw=2)
                city_show = [x.title() for x in city_order_inc_radiation]
                ax1.set_xticks(list(range(len(city_show))))
                ax1.set_xticklabels(city_show, fontsize=Monitor.def_font_size)
                ax1.set_ylabel('Total Cost of Ownership (1000\$)', fontsize=Monitor.def_font_size + 2)
                ax1.set_title(Monitor.subfigure_prefix[plot_no] + 'Solar Radiation Level', size=16)
                lgd = ax1.legend(loc='upper right', bbox_to_anchor=(2.25, 1.15), ncol=4, fancybox=True, shadow=True,
                           fontsize=Monitor.def_font_size)
            else:
                for method_no in range(len(traffic_density_data)):
                    ax1.plot(traffic_density_data[method_no], label=Monitor.method_type_labels[method_no], linestyle=Monitor.method_type_lines[method_no],
                             color=Monitor.method_type_colors[method_no], marker=Monitor.marker_list[method_no],
                             markersize=7, lw=2)
                ax1.set_xticks(list(range(len(Monitor.traffic_area_labels))))
                ax1.set_xticklabels(Monitor.traffic_area_labels, fontsize=Monitor.def_font_size)
                ax1.set_ylabel('Cost Density (\$/km$^2$/Mbits)', fontsize=Monitor.def_font_size + 2)
                ax1.set_ylim(0.6, 2.6)
                ax1.set_yticks(np.arange(0.6, 2.7, 0.2))
                ax1.set_title(Monitor.subfigure_prefix[plot_no] + 'Traffic Rate', size=16)
            ax1.grid(b=True, which='both', axis='both')
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + 'bc_cumulative.pdf', format='pdf', bbox_extra_artists=(lgd,), bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + 'bc_cumulative.eps', format='eps', bbox_extra_artists=(lgd,), bbox_inches='tight')

    @staticmethod
    def plt_bar_gurobi(expenditure_values):
        fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        city_index = 0
        for city in city_name_list:
            max_val = 0
            min_val = 1000000000
            ax1 = axes.flat[city_index]
            ax1.set_title(Monitor.subfigure_prefix[city_index] + city.title())
            for method_index in (list(range(len(Monitor.method_show_order_gurobi)))):
                only_one_method_vals = []
                for ts in traffic_scenarios:
                    key_is = city + '_' + Monitor.method_show_order_gurobi[method_index] + '_ts:' + str(ts)
                    val = expenditure_values[key_is] / 1000
                    if max_val < val:
                        max_val = val
                    if min_val > val:
                        min_val = val
                    only_one_method_vals.append(val)
                x_pos = np.arange(len(only_one_method_vals))
                if Monitor.method_show_order_gurobi[method_index] == 'gurobi':
                    ax1.bar(x_pos + method_index * 0.4, only_one_method_vals, width=0.4,
                            edgecolor=Monitor.method_type_colors_gurobi[method_index], align='center', alpha=0.4,
                            label=Monitor.method_type_labels_gurobi[method_index], hatch=Monitor.method_type_hatch[0], fill=False)
                else:
                    ax1.bar(x_pos + method_index * 0.42, only_one_method_vals, width=0.4,
                            edgecolor=Monitor.method_type_colors_gurobi[method_index], align='center', alpha=0.4,
                            label=Monitor.method_type_labels_gurobi[method_index], hatch=Monitor.method_type_hatch[1], fill=False)
            city_index += 1
            ax1.set_ylim(min_val - 50, max_val + 50)
            for label in ax1.get_yticklabels():
                label.set_fontsize(16)

            for label in ax1.get_yticklabels():
                label.set_fontsize(Monitor.def_font_size)
            ax1.set_xlim(-0.5, 3.8)
            ax1.set_xticks(x_pos + 0.2)
            ax1.set_xticklabels(Monitor.traffic_area_labels, fontsize=Monitor.def_font_size)
            ax1.grid(b=True, which='both', axis='y')
            if city == 'stockholm':
                lgd = ax1.legend(loc='upper right', bbox_to_anchor=(1.75, 1.4), ncol=3, fancybox=True, shadow=True,
                                 fontsize=Monitor.def_font_size + 2)

        # Set common labels
        fig.text(0.06, 0.5, 'Total Cost of Ownership (1000$)', ha='center', va='center', rotation='vertical', fontsize=20)
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + 'gurobi_compare.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + 'gurobi_compare.eps', format='eps', bbox_inches='tight')

    @staticmethod
    def plt_bar_gurobi_normalized(expenditure_values):
        fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        city_index = 0
        for city in city_name_list:
            ax1 = axes.flat[city_index]
            base_width = []
            ax1.set_title(city.title())
            for method_index in (list(range(len(Monitor.method_show_order_gurobi)))):
                only_one_method_vals = []
                for ts in traffic_scenarios:
                    key_is = city + '_' + Monitor.method_show_order_gurobi[method_index] + '_ts:' + str(ts)
                    val = expenditure_values[key_is]
                    only_one_method_vals.append(val)
                if Monitor.method_show_order_gurobi[method_index] == 'gurobi':
                    base_width = list(only_one_method_vals)
                x_pos = np.arange(len(only_one_method_vals))
                if Monitor.method_show_order_gurobi[method_index] == 'gurobi':
                    ax1.bar(x_pos + (method_index) * 0.4, [100 for x in range(4)], width=0.4,
                            color=Monitor.method_type_colors_gurobi[method_index], align='center', alpha=0.4,
                            label=Monitor.method_type_labels_gurobi[method_index])
                else:
                    percentage_vals = [(x * 100.0) / y for x, y in zip(only_one_method_vals, base_width)]
                    ax1.bar(x_pos + (method_index) * 0.4, percentage_vals, width=0.4,
                            color=Monitor.method_type_colors_gurobi[method_index], align='center', alpha=0.4,
                            label=Monitor.method_type_labels_gurobi[method_index])
            city_index += 1

            ax1.set_ylim(0, 110)
            major_ticks = np.arange(0, 111, 10)
            minor_ticks = np.arange(0, 111, 5)
            ax1.set_yticks(major_ticks)
            ax1.set_yticks(minor_ticks, minor=True)
            for label in ax1.get_yticklabels():
                label.set_fontsize(Monitor.def_font_size)
            ax1.set_xlim(-0.5, 3.8)
            ax1.set_xticks(x_pos + 0.2)
            ax1.set_xticklabels(Monitor.traffic_area_labels, fontsize=Monitor.def_font_size)
            ax1.grid(b=True, which='both', axis='y')
            if city == 'stockholm':
                lgd = ax1.legend(loc='upper right', bbox_to_anchor=(1.85, 1.3), ncol=6, fancybox=True, shadow=True,
                                 fontsize=Monitor.def_font_size)
        # Set common labels
        fig.text(0.06, 0.5, 'Nominal Expenditure', ha='center', va='center', rotation='vertical', fontsize=16)

        fig.savefig(FIGURES_PATH + 'gurobi_compare.eps', format='eps', bbox_inches='tight')
        plt.show()

    @staticmethod
    def plt_bar_total_expenditure(expenditure_values):
        fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        city_index = 0
        for city in city_name_list:
            ax1 = axes.flat[city_index]
            base_width = []
            for method_index in (list(range(len(Monitor.method_show_order)))):
                only_one_method_vals = []
                for ts in traffic_scenarios:
                    key_is = city + '_' + Monitor.method_show_order[method_index] + '_ts:' + str(ts)
                    val = expenditure_values[key_is]
                    only_one_method_vals.append(val)
                if Monitor.method_show_order[method_index] == 'traffic_aware':
                    base_width = list(only_one_method_vals)
                else:
                    percentage_vals = [(x * 100.0) / y for x, y in zip(only_one_method_vals, base_width)]
                x_pos = np.arange(len(only_one_method_vals))
                if Monitor.method_show_order[method_index] == 'traffic_aware':
                    ax1.bar(x_pos + (method_index) * 0.3 - 0.1, [100 for x in range(4)], width=0.3,
                            edgecolor=Monitor.method_type_colors[method_index], align='center', alpha=0.4,
                            label=Monitor.method_type_labels[method_index], hatch=Monitor.method_type_hatch[method_index], fill=False,
                            )
                else:
                    ax1.bar(x_pos + (method_index) * 0.3 - 0.1, percentage_vals, width=0.3,
                            edgecolor=Monitor.method_type_colors[method_index], align='center', alpha=0.4,
                            label=Monitor.method_type_labels[method_index], hatch=Monitor.method_type_hatch[method_index], fill=False,
                            )

            ax1.set_title(Monitor.subfigure_prefix[city_index] + city.title())
            city_index += 1

            ax1.set_ylim(60, 200)
            major_ticks = np.arange(60, 201, 20)
            ax1.set_yticks(major_ticks)
            for label in ax1.get_yticklabels():
                label.set_fontsize(Monitor.def_font_size)
            ax1.set_xlim(-0.5, 3.8)
            ax1.set_xticks(x_pos + 0.2)
            ax1.set_xticklabels(Monitor.traffic_area_labels, fontsize=Monitor.def_font_size)
            ax1.grid(axis='y')
            ax1.set_axisbelow(True)
            if city == 'stockholm':
                lgd = ax1.legend(loc='upper right', bbox_to_anchor=(2.2, 1.37), ncol=3, fancybox=True, shadow=True,
                                 fontsize=Monitor.def_font_size+2)

        # Set common labels
        fig.text(0.06, 0.5, 'Total Cost of Ownership (Normalized)', ha='center', va='center', rotation='vertical', fontsize=20)

        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + 'bc.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + 'bc.eps', format='eps', bbox_inches='tight')

    @staticmethod
    def annotate_group(name, xspan, ax=None):
        """Annotates a span of the x-axis"""

        def annotate(ax, name, left, right, y, pad):
            arrow = ax.annotate(name,
                                xy=(left, y), xycoords='data', size=22,
                                xytext=(right, y - pad), textcoords='data',
                                annotation_clip=False, verticalalignment='top',
                                horizontalalignment='center', linespacing=2.0,
                                arrowprops=dict(arrowstyle='-', shrinkA=0, shrinkB=0,
                                                connectionstyle='angle,angleB=90,angleA=0,rad=5')
                                )
            return arrow

        if ax is None:
            ax = plt.gca()
        ymin = ax.get_ylim()[0] - 100000
        ypad = 0.01 * np.ptp(ax.get_ylim())
        xcenter = np.mean(xspan)
        left_arrow = annotate(ax, name, xspan[0], xcenter, ymin, ypad)
        right_arrow = annotate(ax, name, xspan[1], xcenter, ymin, ypad)
        return left_arrow, right_arrow

    @staticmethod
    def make_second_bottom_spine(ax=None, label=None, offset=0, labeloffset=20):
        """Makes a second bottom spine"""
        if ax is None:
            ax = plt.gca()
        # second_bottom = spi.Spine(ax, 'bottom', ax.spines['bottom']._path)
        # second_bottom.set_position(('outward', offset))
        # ax.spines['second_bottom'] = second_bottom

        if label is not None:
            # Make a new xlabel
            ax.annotate(label,
                        xy=(0.5, 0), xycoords='axes fraction',
                        xytext=(0, -labeloffset), textcoords='offset points',
                        verticalalignment='top', horizontalalignment='center', size=22)

    def plt_iterations_heuristic_prev_data(self, h_all):  # plot function example
        fig, axes = plt.subplots(2, 4, figsize=(9, 7))
        marker_list = ['D', 'x', 'v', 'o', 's', '<', 'D', 'x', 'v', 'o', 's', '<']
        for i in range(len(h_all)):
            ax = axes.flat[i]
            h = h_all[i]
            city_name_list_with_prev = []
            for c in city_name_list:
                city_name_list_with_prev.append(c + ' c')
                city_name_list_with_prev.append(c + ' p')
            city_show = [x.title() for x in city_name_list_with_prev]
            for h_index in range(len(h)):
                h[h_index] /= 1000
            ax.plot(h, label=str(city_show[i]), marker=marker_list[i], markersize='7', lw='2')
            ax.grid(b=True, which='major', linestyle='--')
            ax.legend()

    def plt_iterations_heuristic(self, h_all, show_type='total_expenditure'):  # plot function example
        fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        for i in range(len(h_all)):
            ax = axes.flat[i]
            h = h_all[i]
            for h_index in range(len(h)):
                h[h_index] /= 1000
            ax.plot(h, label=str(Monitor.city_show[i]), marker=Monitor.marker_list[i], markersize='7', lw='2')
            ax.grid(b=True, which='major', linestyle='--')
            ax.legend()

    @staticmethod
    def plt_confidence_intervals(confidence_data, comparison_type="OPERATIONAL_METHODS"):  # plot function example
        fig, axes = plt.subplots(4, 1, figsize=(9, 7))
        x_pos = np.arange(0.5, 10.5, 1)
        traffic_scen = 3
        for city_index in range(len(city_name_list)):
            city_name = city_name_list[city_index]
            ax = axes.flat[city_index]
            if comparison_type is "OPERATIONAL_METHODS":
                for method_no in (list(range(len(Monitor.method_show_order)))):
                    if Monitor.method_show_order[method_no] != "battery_aware":
                        key_is = city_name + '_' + Monitor.method_show_order[method_no] + '_ts:' + str(traffic_scen)
                        list_data = [instance_data / 1000 for instance_data in confidence_data[key_is]]
                        min_val = int(min(list_data))
                        max_val = int(max(list_data))
                        ax.plot(x_pos, list_data, label=Monitor.method_type_labels[method_no], linestyle="None",
                                color=Monitor.method_type_colors[method_no], marker=Monitor.marker_list[method_no],
                                markersize=7, lw=2)
            else:
                for method_no in (list(range(len(Monitor.method_show_order_gurobi)))):
                    key_is = city_name + '_' + Monitor.method_show_order_gurobi[method_no] + '_ts:' + str(traffic_scen)
                    list_data = [instance_data / 1000 for instance_data in confidence_data[key_is]]
                    min_val = int(min(list_data))
                    max_val = int(max(list_data))
                    ax.plot(x_pos, list_data, label=Monitor.method_type_labels_gurobi[method_no], linestyle="None",
                            color=Monitor.method_type_colors_gurobi[method_no], marker=Monitor.marker_list[method_no],
                            markersize=7, lw=2)

            ax.set_title(Monitor.subfigure_prefix[city_index] + Monitor.city_show[city_index])

            axis_labels = []
            for c in range(10, 10, 2):
                axis_labels.append(c)
            ax.set_xticks(list(range(0, 11, 1)))
            ax.set_xticklabels(axis_labels, fontsize=16)
            ax.grid(b=True, which='major')
            for label in ax.get_yticklabels():
                label.set_fontsize(14)

            if comparison_type is "OPERATIONAL_METHODS":
                if traffic_scen is 1:
                    min_val = int(math.ceil((min_val - 10) / 20) * 20)
                    major_ticks = np.arange(min_val, min_val + 50, 20)
                elif traffic_scen is 2:
                    min_val = int(math.ceil((min_val - 10) / 50) * 50)
                    major_ticks = np.arange(min_val, min_val + 160, 50)
                elif traffic_scen is 3:
                    min_val = int(math.ceil((min_val - 10) / 50) * 50)
                    major_ticks = np.arange(min_val, min_val + 160, 50)
                elif traffic_scen is 4:
                    min_val = int(math.ceil((min_val - 10) / 50) * 50)
                    major_ticks = np.arange(min_val, min_val + 160, 50)
            else:
                if traffic_scen is 1:
                    min_val = int(math.ceil((min_val - 10) / 50) * 50)
                    major_ticks = np.arange(min_val, min_val + 150, 50)
                elif traffic_scen is 2:
                    min_val = int(math.ceil((min_val - 10) / 50) * 50)
                    major_ticks = np.arange(min_val, min_val + 160, 50)
                elif traffic_scen is 3:
                    min_val = int(math.ceil((min_val - 10) / 50) * 50)
                    major_ticks = np.arange(min_val, min_val + 220, 50)
                elif traffic_scen is 4:
                    min_val = int(math.ceil((min_val - 10) / 50) * 50)
                    major_ticks = np.arange(min_val, min_val + 350, 100)

            ax.set_yticks(major_ticks)

            if city_index == 1:
                lgd = ax.legend(loc='upper right', bbox_to_anchor=(0.75, 2.9), ncol=2, fancybox=True, shadow=True, fontsize=14, numpoints=1)
                lgd.get_title().set_fontsize('16')

        if comparison_type is "OPERATIONAL_METHODS":
            if PDF_FORMAT:
                file_name = "confidence_interval.pdf"
            else:
                file_name = "confidence_interval.eps"
        else:
            if PDF_FORMAT:
                file_name = "confidence_interval_gurobi.pdf"
            else:
                file_name = "confidence_interval_gurobi.eps"
        # Set common labels
        fig.text(0.06, 0.5, 'Total Cost of Ownership (1000\$)', ha='center', va='center', rotation='vertical', fontsize=20)

        fig.text(0.5, 0.04, 'Instances', ha='center', va='center', fontsize=16)
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + file_name, format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + file_name, format='eps', bbox_inches='tight')

    @staticmethod
    def plt_iterations_same_size(h_all, best_heuristic_all=None,
                                 show_type='total_expenditure', configuration="city"):  # plot function example
        fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        number_of_batt_2_draw = E.MAX_BATTERY_SIZE - 4
        number_of_panel_2_draw = E.MAX_PANEL_SIZE - 2
        same_size_type_lines = [':', '--', '-.', ':', '--', '-.']
        for i in range(len(h_all)):
            min_val = 100000000
            max_val = 0
            ax = axes.flat[i]
            h = h_all[i]
            if best_heuristic_all is not None:
                best_heuristic_value = best_heuristic_all[i]
                best_heuristic_value_for_draw = [best_heuristic_value / 1000 for x in range(number_of_batt_2_draw)]
                min_val = best_heuristic_value_for_draw[0]
                ax.plot(best_heuristic_value_for_draw, label='H', linestyle='-', markersize='7', lw='2')
            for solar_panel_no in range(number_of_panel_2_draw):
                x = []
                for batt_no in range(number_of_batt_2_draw):
                    x.append(h[solar_panel_no * E.MAX_BATTERY_SIZE + batt_no] / 1000)
                ax.plot(x, label='' + str(solar_panel_no + 1), marker=Monitor.marker_list[solar_panel_no], linestyle=same_size_type_lines[solar_panel_no], markersize=7, lw=2)
                if min_val > min(x):
                    min_val = min(x)
                if max_val < max(x):
                    max_val = max(x)
            if configuration == "city":
                ax.set_title(Monitor.subfigure_prefix[i] + Monitor.city_show[i])
            else:
                ax.set_title(Monitor.subfigure_prefix[i] + Monitor.traffic_area_labels[i])
            axis_labels = []
            for c in range(2, number_of_batt_2_draw + 1, 2):
                axis_labels.append(int(c * 2.5))
            ax.set_xticks(list(range(1, number_of_batt_2_draw, 2)))
            ax.set_xticklabels(axis_labels, fontsize=16)
            ax.set_xlim((0, number_of_batt_2_draw - 1))
            ax.grid(b=True, which='major')
            ax.set_ylim(min_val - 20, max_val+20)
            for label in ax.get_yticklabels():
                label.set_fontsize(16)

            major_ticks = np.arange(int(math.ceil((min_val - 20) / 30) * 30), max_val + 20, 30)
            ax.set_yticks(major_ticks)

            if i == 1:
                lgd = ax.legend(loc='upper right', bbox_to_anchor=(1.05, 1.45), ncol=7, fancybox=True, shadow=True, fontsize=14, title="Solar Panel Size")
                lgd.get_title().set_fontsize('16')
        if PDF_FORMAT:
            if configuration == "city":
                file_name = "combination_per_city.pdf"
            else:
                file_name = "combination_per_traffic.pdf"
        else:
            if configuration == "city":
                file_name = "combination_per_city.eps"
            else:
                file_name = "combination_per_traffic.eps"
        # Set common labels
        if show_type == 'carbon_emission':
            fig.text(0.06, 0.5, '$CO_2 (Tonne)$', ha='center', va='center', rotation='vertical', fontsize=16)
        else:
            fig.text(0.06, 0.5, 'Total Cost of Ownership (1000\$)', ha='center', va='center', rotation='vertical', fontsize=20)

        fig.text(0.5, 0.04, 'Battery Size (kW/h)', ha='center', va='center', fontsize=16)
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + file_name, format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + file_name, format='eps', bbox_inches='tight')

    def plt_iterations_all_type(self, h):  # plot function example
        # (total_expenditure, capital_expenditure, operational_expenditure)
        NUMBER_OF_SOLAR_PANEL = 8
        NUMBER_OF_BATT_TYPE = 12
        fig = plt.figure(self.new_figure)
        it_count = min(list(map(len, h)))
        # min(h, key = len)
        ax = fig.add_subplot(1, 1, 1)
        self.new_figure += 1

        operation_index = 0
        for operational_method in CalibrationParameters.get_parameters():
            x = []
            y = []
            z = []
            for i in range(it_count):
                x.append(h[operation_index][i][0])
                y.append(h[operation_index][i][1])
                z.append(h[operation_index][i][2])
            if operation_index == 0:
                ls = '--'
            elif operation_index == 1:
                ls = '-.'
            else:
                ls = '-'

            ax.plot(x, label=csn(operational_method) + ' total exp.', marker='o', lw='2', linestyle=ls)
            ax.plot(y, label=csn(operational_method) + ' capital exp.', marker='v', lw='2', linestyle=ls)
            ax.plot(z, label=csn(operational_method) + ' operational exp.', marker='s', lw='2', linestyle=ls)
            operation_index += 1
        # ax.spines['bottom'].set_position(('outward', 40))
        self.make_second_bottom_spine(ax=ax, offset=80, labeloffset=100, label='Solar Panel Size (KW)')

        # Annotate the groups
        for sol_index in range(NUMBER_OF_SOLAR_PANEL):
            # self.annotate_group(str(sol_index+1), (x[sol_index*NUMBER_OF_BATT_TYPE], x[(sol_index+1)*NUMBER_OF_BATT_TYPE]))
            self.annotate_group(str(sol_index + 1), (sol_index * NUMBER_OF_BATT_TYPE, (sol_index + 1) * NUMBER_OF_BATT_TYPE - 1), ax=ax)

        axis_labels = []
        for sol_index in range(NUMBER_OF_SOLAR_PANEL):
            for batt_index in range(4, NUMBER_OF_BATT_TYPE + 1, 4):
                axis_labels.append(int(batt_index * 2.5))
        plt.xticks(range(3, it_count, 4), axis_labels, fontsize=22)
        plt.xlabel('Battery Size (KW)', fontsize=24)
        plt.subplots_adjust(bottom=0.2)
        plt.legend(loc=1, ncol=3, fontsize=16)
        ax.set_xlim((0, it_count - 1))

        plt.yticks(fontsize=16)
        minor_locator_y = AutoMinorLocator(4)
        ax.yaxis.set_minor_locator(minor_locator_y)
        plt.ylabel('Expenditure (1000$)', fontsize=16)
        # plt.title("City: " + city_name + " Traffic Scenario: " + str(traffic_scen), fontsize=32)
        plt.grid(b=True, which='major', linestyle='--')
        plt.grid(b=True, which='minor', linestyle=':')

    def __plt_energy_usage_at_a_specific_hour(self, bs_index, energy_usage_type):
        HOUR_OF_THE_DAY = 19
        recording_hours = 24 * 365
        recording_days = recording_hours / 24
        _type = [0 for x in range(recording_days)]
        converter = ['Sleep', 'Awake']
        for i in range(recording_days):
            for k in range(3):
                if energy_usage_type[HOUR_OF_THE_DAY + i * 24] == converter[k]:
                    _type[i] = k
                    break
        #plt.plot(_type[i], 'r:s', label='energy_type')
        fig = plt.figure(self.new_figure)
        ax_energy_type = fig.add_subplot(1, 1, 1)
        ax_energy_type.set_yticks(list(range(len(converter))))
        ax_energy_type.set_yticklabels(converter)
        ax_energy_type.set_ylim((-1, 4))
        ax_energy_type.set_xticks(list(range(recording_days)))
        ax_energy_type.grid(True)

        ax_energy_type.plot(_type, 'r:s', label='energy restriction_type')
        for tl in ax_energy_type.get_yticklabels():
            tl.set_color('r')
        plt.title("BS: {}".format(bs_index))
        plt.grid(True)

        plt.legend()
        plt.show()

    @staticmethod
    def __plt_remaining_energy(bs_index, x):  # plot function example
        plt.plot(x, label='Remaining Energy')
        plt.title("BS: {}".format(bs_index))
        plt.grid(True)

        # plt.legend()
        plt.show()

    @staticmethod
    def __plt_power_consumption(bs_index, x, y, z):  # plot function example
        plt.plot(x, label='renewable')
        plt.plot(y, label='fossil')
        plt.plot(z, label='total')
        plt.title("BS: {}".format(bs_index))
        plt.grid(True)

        plt.legend()
        plt.show()

    def __plt_for_each_day(self, bs_index, p, a, b, c, energy_usage_type, harvesting_amount, energy_waste_type,
                           wasted_energy):
        fig = plt.figure(self.new_figure)
        ax_rit_ratio = fig.add_subplot(2, 1, 1)
        ax_bs_power = fig.add_subplot(2, 1, 2)
        l = 365
        d = 24

        converter2 = ['None', 'Waste']
        _type = [[0 for x in range(24)] for x in range(30)]
        _type2 = [[0 for x in range(24)] for x in range(30)]
        _p = [[0 for x in range(24)] for x in range(30)]
        _h = [[0 for x in range(24)] for x in range(30)]
        _w = [[0 for x in range(24)] for x in range(30)]
        ax_rit_ratio.set_xticks(list(range(d)))
        ax_rit_ratio.grid(True)

        ax_waste_type = ax_rit_ratio.twinx()
        ax_waste_type.set_yticks(list(range(len(converter2))))
        ax_waste_type.set_yticklabels(converter2)
        ax_waste_type.set_ylim((-1, 4))

        # ax_bs_power.set_ylim((0, 700))
        ax_bs_power.set_xticks(list(range(d)))
        ax_bs_power.grid(True)

        #ax_harvest_power = ax_bs_power.twinx()
        ax_wasted_energy = ax_bs_power.twinx()

        for i in range(5, 6):  # fifth and sixth day
            _p[i] = p[i * d:i * d + d]
            _h[i] = harvesting_amount[i * d:i * d + d]
            _w[i] = wasted_energy[i * d:i * d + d]
            for j in range(d):
                data_index = i * d + j
                _type[i][j] = energy_usage_type[data_index]
                for k in range(2):
                    if energy_waste_type[data_index] == converter2[k]:
                        _type2[i][j] = k
                        break

            ax_rit_ratio.plot(_type[i], 'r:s', label='rit_ratio')
            for tl in ax_rit_ratio.get_yticklabels():
                tl.set_color('r')

            ax_waste_type.plot(_type2[i], 'b-.D', label='waste_type')
            for tl in ax_waste_type.get_yticklabels():
                tl.set_color('b')

            ax_bs_power.plot(_p[i], 'r:s', label='bs_power')
            for tl in ax_bs_power.get_yticklabels():
                tl.set_color('r')

            ax_wasted_energy.plot(_w[i], 'm-.<', label='wasted_power')
            for tl in ax_wasted_energy.get_yticklabels():
                tl.set_color('m')

        plt.title("BS: {}".format(bs_index))

        ax_rit_ratio.legend()
        ax_bs_power.legend()
        ax_wasted_energy.legend()
        plt.show()

    @staticmethod
    def __plt_dist_power_consumption_per_hour(bs_index, x, y, z, type):  # plot function example
        l = 24
        _x = [0 for aa in range(l)]
        _y = [0 for aa in range(l)]
        _z = [0 for aa in range(l)]
        _type = [0 for aa in range(l)]
        for i in range(l):
            hour_of_the_day = i % 24
            _x[hour_of_the_day] += x[hour_of_the_day]
            _y[hour_of_the_day] += y[hour_of_the_day]
            _z[hour_of_the_day] += z[hour_of_the_day]
            _type[hour_of_the_day] += type[hour_of_the_day]

        # plt.plot(_x, label='renewable')
        #plt.plot(_y, label='fossil')
        plt.plot(_type, label='total')
        plt.title("BS: {}".format(bs_index))
        plt.grid(True)

        plt.legend()
        plt.show()

    def show_harvesting_energy_all(self, harvesting_power):
        number_of_city = len(harvesting_power)
        fig, ax1 = plt.subplots(figsize=(9, 7))

        city_colors = ['red', 'blue', 'green', 'yellow', 'purple']

        for i in range(number_of_city):
            vals = harvesting_power[i][1]
            x_pos = np.arange(len(vals))
            ax1.bar(x_pos - i * 0.2, vals, width=0.2, color=city_colors[i], align='center', alpha=0.4, label=harvesting_power[i][0])

        ax1.legend(loc=4)
        # ax1.legend()
        plt.xlabel('Months', fontsize=24)
        # plt.xlabel('Type of Algorithm')
        plt.title('Harvested Energy per Month', fontsize=32)
        plt.xticks(np.arange(12) + 0.4, list(range(12)))

        plt.ylabel('Average Harvested Renewable Energy (Watts)', fontsize=24)
        plt.grid(True)
        plt.show()

    def show_harvesting_energy_month(self, harvesting_power):
        fig = plt.figure(self.new_figure)
        number_of_city = len(harvesting_power)
        x_axis_labels = []
        x_axis_locs = []
        for c in range(0, 12, 3):
            x_axis_labels.append(MONTHS_OF_A_YEAR[c])
            x_axis_locs.append(c + 0.4)
        for i in range(number_of_city):
            ax = fig.add_subplot(1, 1, 1)
            # ax = fig.add_subplot(2, 2, i + 1)
            harvesting_power[i][1][:] = [x / 1000.0 for x in harvesting_power[i][1]]
            ax.bar(range(len(harvesting_power[i][1])), harvesting_power[i][1])
            # ax.set_title(harvesting_power[i][0].title(), fontsize=16)
            ax.set_xticks(x_axis_locs)
            ax.set_xticklabels(x_axis_labels, fontsize=12)
            ax.set_ylim((0, 7))
            # ax.grid(True)

        # Set common labels
        # fig.text(0.5, 0.04, 'Months of a Year', ha='center', va='center', fontsize=16)
        # fig.text(0.06, 0.5, 'Avg. Energy in One Day (KWatts)', ha='center', va='center', rotation='vertical', fontsize=16)

        # plt.show()
        fig.savefig(FIGURES_PATH + 'harvested_daily.pdf', format='pdf', bbox_inches='tight')

    def show_harvesting_energy_hour(self, harvesting_power):
        fig = plt.figure(self.new_figure)
        number_of_city = len(harvesting_power)
        x_axis_labels = []
        x_axis_locs = []
        for c in range(0, 24, 4):
            x_axis_labels.append(c)
            x_axis_locs.append(c + 0.4)

        for i in range(number_of_city):
            ax = fig.add_subplot(2, 2, i + 1)
            harvesting_power[i][1][:] = [x / 1000.0 for x in harvesting_power[i][1]]
            ax.bar(range(len(harvesting_power[i][1])), harvesting_power[i][1])
            ax.set_title(harvesting_power[i][0].title(), fontsize=16)
            ax.set_xticks(x_axis_locs)
            ax.set_xticklabels(x_axis_labels, fontsize=12)
            ax.set_xlim((0, 24))
            ax.set_ylim((0, 0.7))
            ax.grid(True)

        # Set common labels
        fig.text(0.5, 0.04, 'Hours of a Day', ha='center', va='center', fontsize=16)
        fig.text(0.06, 0.5, 'Avg. Energy per Hour (KWatts)', ha='center', va='center', rotation='vertical', fontsize=16)

        fig.savefig(FIGURES_PATH + 'harvested_hourly.eps', format='eps', bbox_inches='tight')

    def show_battery_history(self, bh):
        bs_count = len(bh)
        recording_hours = len(bh[0])
        #for bs_index in xrange(bs_count):
        for bs_index in range(6, 10):
            harvesting_amount = []
            awake_state = []
            fossil_energy_consumption = []
            ren_energy_consumption = []
            wasted_energy = []
            remaining_energy = []
            renewable_usage_ratio = []
            for hour_index in range(recording_hours):
                # for hour_index in xrange(24 * 30, 24 * 30 * 2):
                harvesting_amount.append(bh[bs_index][hour_index][0])
                awake_state.append(bh[bs_index][hour_index][1])
                fossil_energy_consumption.append(bh[bs_index][hour_index][2])
                ren_energy_consumption.append(bh[bs_index][hour_index][3])
                wasted_energy.append(bh[bs_index][hour_index][4])
                remaining_energy.append(bh[bs_index][hour_index][5])
                renewable_usage_ratio.append(bh[bs_index][hour_index][6])
            total_en_cons = [ren_energy_consumption[i] + fossil_energy_consumption[i] for i in range(len(ren_energy_consumption))]
            self.__plt_remaining_energy(bs_index, remaining_energy)
            self.__plt_power_consumption(bs_index, ren_energy_consumption, fossil_energy_consumption, total_en_cons)
            # self.__plt_energy_usage_at_a_specific_hour(bs_index, renewable_usage_ratio)
            # self.__plt_dist_power_consumption_per_hour(bs_index, ren_energy_consumption, fossil_energy_consumption, total_en_cons, renewable_usage_ratio)
            # self.__plt_for_each_day(bs_index, remaining_energy, ren_energy_consumption, fossil_energy_consumption, total_en_cons,
            # renewable_usage_ratio, harvesting_amount, renewable_usage_ratio, wasted_energy)

    @staticmethod
    def plot_energy_consumption(battery_history):
        bs_deployed_count = len(battery_history)
        time_interval_start = NUMBER_OF_TIME_SLOT_IN_ONE_DAY * 144
        time_interval_end = NUMBER_OF_TIME_SLOT_IN_ONE_DAY * 145
        bs_count_list = [bs_deployed_count]
        bs_count_total = 0
        for i in range(time_interval_start, time_interval_end):
            bs_count_in_time_interval = 0
            for bs_data in battery_history:
                if bs_data[i][1] == 'Awake':
                    bs_count_in_time_interval += 1
            bs_count_list.append(bs_count_in_time_interval)
            bs_count_total += bs_count_in_time_interval

        plt.bar(range(len(bs_count_list)), bs_count_list)
        bs_count_per_time = float(bs_count_total) / len(bs_count_list)
        energy_consumption_rate = (bs_count_per_time / bs_deployed_count) * 100
        plt.xticks(np.arange(len(bs_count_list)) + 0.4, ['P'] + list(range(len(bs_count_list) - 1)))
        plt.xlabel('Hours of The Day')
        plt.ylabel('Number of Awake Base Station')
        plt.title('New Energy Consumption %{}'.format(energy_consumption_rate))

    def show_bs_range_table(self, range_table, index):
        fig = plt.figure(self.new_figure)
        ax = fig.add_subplot(10, 10, index + 1)
        # ax = fig.add_subplot(1, 1, 1)
        ax.pcolormesh(range_table, cmap=plt.cm.Blues)
        ax.set_title("{0:d}".format(index))

    @staticmethod
    def show():
        plt.show()


class MonitorAssignment(Monitor):
    def show_bs_locations(self):
        snapshot = Snapshot()
        fig, axes = plt.subplots(nrows=2, ncols=2)
        self.new_figure += 1
        location_size = CoordinateConverter.GRID_COUNT_IN_ONE_EDGE
        for i in traffic_scenarios:
            array_index = i - 1
            snapshot.set_traffic_scen_folder(i)
            c = snapshot.load_city_after_deployment()
            number_of_bs = len(c.bs_locations)
            ax = axes.flat[array_index]
            ax.set_title(Monitor.subfigure_prefix[array_index] + Monitor.traffic_area_labels[array_index], fontsize=16)
            # a = [[0 for x in xrange(location_size)] for x in xrange(location_size)]

            x1 = []
            y1 = []
            x2 = []
            y2 = []
            color1 = []
            color2 = []
            area1 = []
            area2 = []

            for bs_no in range(number_of_bs):
                bs_coor = c.bs_locations[bs_no]
                bs_type = c.bs_types[bs_no]

                if bs_type == BSType.MACRO:
                    x1.append(bs_coor[0])
                    y1.append(bs_coor[1])
                    color1.append('b')
                    area1.append(50)
                else:
                    x2.append(bs_coor[0])
                    y2.append(bs_coor[1])
                    color2.append('r')
                    area2.append(20)

            ax.scatter(x1, y1, s=area1, c=color1, marker="<", alpha=0.5)
            ax.scatter(x2, y2, s=area2, c=color2, marker="o", alpha=0.5)
            ax.grid()
            ax.tick_params(axis='both', which='both', bottom='off', top='off', left='off', right='off', labelleft='off', labelbottom='off')
        plt.subplots_adjust(left=0.1, bottom=0.05, right=0.9, top=0.9, wspace=0.15, hspace=0.15)
        # Set common labels
        fig.text(0.5, 0.0, "Distance (Km)", ha='center', va='center', fontsize=16)
        fig.text(0.06, 0.5, "Distance (Km)", ha='center', va='center', rotation='vertical', fontsize=16)
        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + 'bs_locations.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + 'bs_locations.eps', format='eps', bbox_inches='tight')

    def __get_only_deployed_bs_locations(self, deployed, loc, type):
        only_deployed = []
        only_deployed_bs_type = []
        for i in deployed:
            only_deployed.append(loc[i])
            only_deployed_bs_type.append(type[i])
        return only_deployed, only_deployed_bs_type

    def show_assignment_all(self, operator, co=None):
        HOURS_OF_A_DAY = [12, 18, 22, 4]
        fig, axes = plt.subplots(nrows=2, ncols=2)
        self.new_figure += 1

        time_interval_start = NUMBER_OF_TIME_SLOT_IN_ONE_DAY * 81

        for i in range(len(HOURS_OF_A_DAY)):
            ax = axes.flat[i]
            configuration = operator.city_configuration_list[time_interval_start + HOURS_OF_A_DAY[i]]
            ax.set_title(Monitor.subfigure_prefix[i] + "{:0>2d}:00".format(HOURS_OF_A_DAY[i]), fontsize=16)
            # (only_deployed, deployed_bs_types) = self.__get_only_deployed_bs_locations(f.bs_deployed_and_active, co.bs_locations, co.bs_types)
            location_size = len(configuration.assigning)
            a = [[0 for x in range(location_size)] for x in range(location_size)]
            for x_i in range(location_size):
                for y_i in range(location_size):
                    a[x_i][y_i] = configuration.assigning[x_i][y_i] % 14
            '''
            for i in xrange(len(only_deployed)):
                bs_coor = only_deployed[i]
                bs_type = deployed_bs_types[i]
                if bs_type == 0:
                    a[bs_coor[0]][bs_coor[1]] = 14
                else:
                    a[bs_coor[0]][bs_coor[1]] = 15
            '''
            im = ax.imshow(a, cmap=cm.get_cmap("jet"), interpolation='none', alpha=0.65)
            # ax.imshow(a, cmap=cm.get_cmap("jet"), interpolation='none')
            ax.grid()

            ax.tick_params(axis='both', which='both', bottom='off', top='off', left='off', right='off', labelleft='off', labelbottom='off')
            # plt.subplots_adjust(left=-0.3, bottom=0.05, right=1.25, top=0.9, wspace=-0.75, hspace=0.2)
            plt.subplots_adjust(left=0.0, bottom=0.05, right=0.9, top=0.9, wspace=-0.35, hspace=0.15)
            # Set common labels
            fig.text(0.5, 0.0, "Distance (Km)", ha='center', va='center', fontsize=16)
            fig.text(0.09, 0.5, "Distance (Km)", ha='center', va='center', rotation='vertical', fontsize=16)

        if PDF_FORMAT:
            fig.savefig(FIGURES_PATH + 'assignments.pdf', format='pdf', bbox_inches='tight')
        else:
            fig.savefig(FIGURES_PATH + 'assignments.eps', format='eps', bbox_inches='tight')


class MonitorTraffic(Monitor):
    def plt_traffic_in_a_day_period(self, user_traffic_demand_in_one_day):
        NORMALIZED_VALUE = 10
        ZONE_COUNT = len(user_traffic_demand_in_one_day)
        '''
        zone = [[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(ZONE_COUNT)]
        # for j in range(ZONE_COUNT):
        #    for i in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
        #        zone[j][i] =  user_traffic_demand_in_one_day[i][j][j]
        for i in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
            zone[0][i] = user_traffic_demand_in_one_day[i][3][3] / NORMALIZED_VALUE
            zone[1][i] = user_traffic_demand_in_one_day[i][11][11] / NORMALIZED_VALUE
            zone[2][i] = user_traffic_demand_in_one_day[i][16][16] / NORMALIZED_VALUE
            zone[3][i] = user_traffic_demand_in_one_day[i][19][19] / NORMALIZED_VALUE
            zone[4][i] = user_traffic_demand_in_one_day[i][20][20] / NORMALIZED_VALUE
        '''
        fig = plt.figure(self.new_figure)
        ax = fig.add_subplot(1, 1, 1)
        for j in range(ZONE_COUNT):
            ax.plot(user_traffic_demand_in_one_day[j], label="Zone:{}".format(j + 1))
        axis_labels = []
        for c in range(0, 24, 2):
            str_ax_labels = "{:0>2d}".format(c)
            axis_labels.append(str_ax_labels)
        ax.set_xticks(list(range(0, 24, 2)))
        ax.set_xticklabels(axis_labels)
        ax.set_xlim(0, 23)
        minor_locator_x = AutoMinorLocator(2)
        ax.xaxis.set_minor_locator(minor_locator_x)
        plt.xlabel('Hours of a Day', fontsize=16)

        '''
        axis_labels = []
        for c in range(0, NORMALIZED_VALUE, NORMALIZED_VALUE / 10):
            axis_labels.append(c / NORMALIZED_VALUE)
        ax.set_yticks(axis_labels, axis_labels)
        ax.set_ylim(0, 0.8)
        minor_locator_y = AutoMinorLocator(2)
        ax.yaxis.set_minor_locator(minor_locator_y)
        plt.ylabel('Normalized User Data Traffic', fontsize=16)
        '''

        # ax.grid(b=True, which='major', linestyle='--')
        # ax.grid(b=True, which='minor', linestyle=':')
        # ax.legend(loc=2)
        # plt.show()
        fig.savefig(FIGURES_PATH + 'traffic_day.eps', format='eps', bbox_inches='tight')

    def simple_show_city_map(self, map_data, type_of_draw):
        fig, axes = plt.subplots(nrows=2, ncols=2)
        self.new_figure += 1
        number_of_map = len(map_data)
        max_val = np.max(map_data)
        min_val = np.min(map_data)
        map_data = map_data - min_val
        max_val = np.max(map_data)
        min_val = np.min(map_data)
        # fig.suptitle(main_title, fontsize=32)
        for i in range(number_of_map):
            ax = axes.flat[i]
            # ax.set_xlabel("Distance (3 km)")
            # ax.set_ylabel("Distance (3 km)")
            if type_of_draw == "day_period":
                if i == 0:
                    ax.set_title("04:00", fontsize=18)
                if i == 1:
                    ax.set_title("11:00", fontsize=18)
                if i == 2:
                    ax.set_title("16:00", fontsize=18)
                if i == 3:
                    ax.set_title("20:00", fontsize=18)
            else:
                if i == 0:
                    ax.set_title("Monday", fontsize=18)
                if i == 1:
                    ax.set_title("Wednesday", fontsize=18)
                if i == 2:
                    ax.set_title("Saturday", fontsize=18)
                if i == 3:
                    ax.set_title("Sunday", fontsize=18)

            # im = ax.imshow(map_data[i]/float(max_val), cmap=cm.get_cmap("gray_r"), interpolation='nearest', vmin=0, vmax=1)
            im = ax.imshow(map_data[i] / float(max_val), cmap=cm.get_cmap("Blues"), interpolation='nearest', vmin=0, vmax=1)
            ax.tick_params(axis='both', which='both', bottom='off', top='off', left='off', right='off', labelleft='off', labelbottom='off')
            ax.grid(True)

        # plt.subplots_adjust(left=-0.3, bottom=0.05, right=1.25, top=0.9, wspace=-0.65, hspace=0.2)
        plt.subplots_adjust(left=-0.3, bottom=0.05, right=1.25, top=0.9, wspace=-0.75, hspace=0.2)
        cbar_ax = fig.add_axes([0.80, 0.1, 0.03, 0.7])
        # ticks=[0,0.5,1]
        cbar = fig.colorbar(im, cax=cbar_ax)
        cbar.set_label('Normalized Traffic Rate', fontsize=16)

        # Set common labels
        fig.text(0.5, 0.0, "Distance (Km)", ha='center', va='center', fontsize=16)
        fig.text(0.14, 0.5, "Distance (Km)", ha='center', va='center', rotation='vertical', fontsize=16)
        if PDF_FORMAT:
            if type_of_draw == "day_period":
                fig.savefig(FIGURES_PATH + 'traffic_hours_of_the_day.pdf', format='pdf', bbox_inches='tight')
            else:
                fig.savefig(FIGURES_PATH + 'traffic_days_of_the_week.pdf', format='pdf', bbox_inches='tight')
        else:
            if type_of_draw == "day_period":
                fig.savefig(FIGURES_PATH + 'traffic_hours_of_the_day.eps', format='eps', bbox_inches='tight')
            else:
                fig.savefig(FIGURES_PATH + 'traffic_days_of_the_week.eps', format='eps', bbox_inches='tight')
        # cbar.set_ticks(range(0,3,1))
        # cbar.set_ticklabels(['Low\nTraffic', 'Medium\nTraffic', 'High\nTraffic'])
