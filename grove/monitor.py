"""
This file plots the results of the project.
"""

import sys

import cv2
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib import style
from matplotlib.ticker import AutoMinorLocator

from ag_cloud import StatesEC, ActionsEC, ActionsCC
from helpers import *


class MonitorQTable:
    def __init__(self):
        self.snapshot = Snapshot()
        style.use('ggplot')
        self.s = StatesEC()
        x1, x2 = self.s.get_state_shape()
        self.a = ActionsEC()
        x3, x4 = self.a.get_action_shape()
        self.qtable_shape = (x1, x2, x3, x4)
        self.a = ActionsCC()
        x3 = self.a.get_action_shape()
        self.qtable_shape_cc = (x1, x2, x3)
        self.SAVE_FIGURE = True
        self.ANALYZE_URF_NUMBER = True
        self.qtable_charts_folder = "../output/results/qtable_charts/"

    def get_q_color(self, value, vals):
        if all(elem == vals[0] for elem in vals):
            return "black", 0.1
        elif value == max(vals):
            return "green", 1.0
        else:
            return "red", 0.3

    def __set_x_axis_for_hour(self, ax_list, vision_type='not_blind'):
        x_axis_labels = []
        x_axis_locs = []
        for c in range(0, 24, 2):
            x_axis_labels.append(str(c).zfill(2) + ":00")
            x_axis_locs.append(c)
        ax_list.set_xticks(x_axis_locs)
        ax_list.set_xticklabels(x_axis_labels)
        minor_locator_x = AutoMinorLocator(4)
        ax_list.xaxis.set_minor_locator(minor_locator_x)

        if vision_type != 'blind':
            ax_list.set_xlabel('Hours of a Day')

    def __set_y_axis_for_remaining_energy(self, ax_list, vision_type='blind'):
        axis_labels = []
        axis_locs = []
        ren_en = self.s.get_remaining_en_level_list()
        for index in range(0, len(ren_en), 2):
            axis_labels.append("{}k".format(int(ren_en[index] / 1000)))
            axis_locs.append(index)
        ax_list.set_yticks(axis_locs)
        ax_list.set_yticklabels(axis_labels)
        # minor_locator = AutoMinorLocator(4)
        # ax_list.yaxis.set_minor_locator(minor_locator)

        if vision_type != 'blind':
            ax_list.set_ylabel('Remaining Energy')

    def plot_actions(self):
        for learning_rate, discount in LearningParameters.get_rate_and_discount():
            for ec_index in range(N_OF_EC):
                # for ec_index in [3]:
                file_name = "lr_{}_dis_{}_multi_ec_{}".format(learning_rate, discount, ec_index)
                self.single_plot(file_name)

    def check_different_ec_q_tables(self):
        for learning_rate, discount in LearningParameters.get_rate_and_discount():
            self.__check_different_ec_q_tables(learning_rate, discount)

    def __check_different_ec_q_tables(self, learning_rate, discount):
        q_table_full = [None for x in range(N_OF_CLOUD)]
        for ec_index in range(N_OF_CLOUD):
            file_name = "lr_{}_dis_{}_multi_ec_{}".format(learning_rate, discount, ec_index)
            q_table_list = self.snapshot.load_qtables(file_name)
            q_table = q_table_list[-1]
            if ec_index == CC_INDEX:
                q_table_full[ec_index] = np.reshape(q_table, self.qtable_shape_cc)
            else:
                q_table_full[ec_index] = np.reshape(q_table, self.qtable_shape)

    def single_plot(self, file_name):
        q_table_list = self.snapshot.load_qtables(file_name)
        if self.ANALYZE_URF_NUMBER:
            action_size = self.qtable_shape[2]
        else:
            action_size = self.qtable_shape[3]

        # number_of_snapshots = int(np.floor(self.NUMBER_OF_EPISODES/self.SHOW_EVERY))
        # for episode in range(0, self.NUMBER_OF_EPISODES, self.SHOW_EVERY):
        for episode in [0, 1800]:
            print("Episode:{}".format(episode))
            self.fig = plt.figure(figsize=(12, 9))
            ax = []
            for i in range(action_size):
                ax.append(self.fig.add_subplot(action_size, 1, i + 1))
            q_table = q_table_list[int(episode / LearningParameters.SHOW_EVERY)]
            q_table_full = np.reshape(q_table, self.qtable_shape)
            if self.ANALYZE_URF_NUMBER:
                q_table_separated = q_table_full[:, :, :, 3]
            else:
                q_table_separated = q_table_full[:, :, 0, :]

            for x, x_vals in enumerate(q_table_separated):
                for y, y_vals in enumerate(x_vals):
                    for i in range(action_size):
                        ax[i].scatter(y, x, c=self.get_q_color(y_vals[i], y_vals)[0], marker="o", alpha=self.get_q_color(y_vals[i], y_vals)[1])
                        if self.ANALYZE_URF_NUMBER:
                            ax[i].set_ylabel("# of URF:{}\nBattery Energy".format(self.a.ACTION_NUMBER_OF_URF_LIST[i]))
                        else:
                            ax[i].set_ylabel("Rem.En.:{}\nBattery Energy".format(self.a.ACTION_REN_EN_RATIO_LIST[i]))
                        if i == action_size - 1:
                            x_axis_blind_type = 'not_blind'
                        else:
                            x_axis_blind_type = 'blind'
                        self.__set_x_axis_for_hour(ax[i], x_axis_blind_type)
                        self.__set_y_axis_for_remaining_energy(ax[i])
            ax[0].set_title("ACTION_REN_EN_RATIO: 1.0  Episode:{}".format(episode))
            if self.SAVE_FIGURE:
                plt.savefig(f"{self.qtable_charts_folder}_ep_{episode}.png")
                plt.clf()
                plt.close()
            else:
                plt.show()

        print("End of plot method")

    def make_video(self):
        # windows:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # Linux:
        # fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
        # for ec_index in range(N_OF_EC):
        for ec_index in [3]:
            out_path = f"{self.qtable_charts_folder}qlearn_ec_{ec_index}.avi"
            out = cv2.VideoWriter(out_path, fourcc, 5.0, (1200, 900))
            for episode in range(0, self.NUMBER_OF_EPISODES, self.SHOW_EVERY):
                img_path = f"{self.qtable_charts_folder}_ep_{episode}.png"
                print(img_path)
                frame = cv2.imread(img_path)
                out.write(frame)
            out.release()


class MonitorRewards:
    subfigure_prefix = ['(a) ', '(b) ', '(c) ', '(d) ',
                        '(e) ', '(f) ', '(g) ', '(h) ',
                        '(j) ', '(k) ', '(l) ', '(m) ',
                        '(n) ', '(p) ', '(q) ', '(r) ',
                        '(s) ', '(t) ', '(v) ', '(y) ']
    def_font_size = 16
    methods = ["DRAN", "CRAN", "Q", "S"]
    method_type_colors = ['red', 'green', 'blue', 'magenta']
    method_type_labels = ['D-RAN', 'C-RAN', 'RLDFS-QL', 'RLDFS-Sarsa']
    method_type_hatch = ['..', 'XXX', '\\\\', '\///']
    method_type_lines = ['-', '--', '-.', '-', '--', '-.']
    marker_list = ['o', 'v', 's', 'D', 'x', '<']
    city_show = [x.title() for x in city_name_list]
    traffic_area_labels = ['Low', 'Medium', 'High']

    def __init__(self):
        self.snapshot = Snapshot()
        self.rewards_folder = "../figures/"
        self.SAVE_FIGURE = True

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
        ax_list.grid(axis='y', which='major')
        ax_list.set_axisbelow(True)
        ax_list.autoscale(enable=True, axis='x', tight=True)

        if vision_type != 'blind':
            ax_list.set_xlabel('Hours of a Day', fontsize=self.def_font_size - 2)

    def __set_total_data_vs_hour(self, axis, data):
        y_axis_data_list = []
        hours = range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)
        for conf_no in range(len(self.methods)):
            d = [0 for x in hours]
            y_axis_data_list.append(d)
        hour_of_the_day = 0
        print(data)
        for conf in PowerCons.get_solar_panel_and_battery_for_each_cloud():
            sp = conf[0][0]
            batt = conf[0][1]
        city = 'istanbul'
        traffic_rate = 1
        for method_index in range(len(self.methods)):
            learning_method = self.methods[method_index]
            for time_slot in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                log_name = "{}_{}_{}_{}_{}_{}".format(sp, batt, learning_method, city, traffic_rate, time_slot)
                y_axis_data_list[method_index][time_slot] = data[log_name]
                y_axis_data_list[method_index][time_slot] /= (365)

        for i in range(len(self.methods)):
            axis.plot(y_axis_data_list[i], label=self.method_type_labels[i], linestyle=self.method_type_lines[i],
                      color=self.method_type_colors[i], marker=self.marker_list[i],
                      markersize='7', lw='2')

    def plot_every_vs_hour_two_figures(self):
        fig = plt.figure()
        figure_prefix = "daily"
        file_name_ext = "daily_ts"
        for i in range(2):
            ax_list = fig.add_subplot(2, 1, i + 1)
            if i == 0:
                data = self.snapshot.load_rewards("ren_en_{}".format(file_name_ext))
                # "fossil_cons" "ren_en" "unstored_en"
                self.__set_x_axis_for_hour(ax_list, 'blind')
                # ax_list.set_title('(a) On-Grid Energy Consumption')
                # ax_list.set_ylabel('On-Grid En. (kW)', fontsize=self.def_font_size)
                ax_list.set_title('(a) Renewable Energy Consumption')
                ax_list.set_ylabel('Energy (kWh)', fontsize=self.def_font_size - 4)
                major_ticks = np.arange(0, 1001, 200)
                # minor_ticks = np.arange(60, 151, 5)
                ax_list.set_yticks(major_ticks)
            else:
                data = self.snapshot.load_rewards("unstored_en_{}".format(file_name_ext))
                self.__set_x_axis_for_hour(ax_list)
                ax_list.set_title('(b) Amount of Unstored Energy')
                ax_list.set_ylabel('Energy (kWh)', fontsize=self.def_font_size - 4)
                major_ticks = np.arange(0, 701, 100)
                # minor_ticks = np.arange(60, 151, 5)
                ax_list.set_yticks(major_ticks)
            self.__set_total_data_vs_hour(ax_list, data)

        plt.legend()
        fig.tight_layout(pad=1.0)
        if self.SAVE_FIGURE:
            plt.savefig("{}{}.pdf".format(self.rewards_folder, figure_prefix), format='pdf', bbox_inches='tight')
        else:
            plt.show()
        plt.clf()

    def compare_the_sizes(self, comp_type):
        div_val = 1000.0
        fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        file_name_ext = "sizing"
        data = self.snapshot.load_rewards("{}_{}".format(comp_type, file_name_ext))
        city = city_name_list[0]
        traffic_rate = traffic_rate_list[0]
        sp_show_name = ["50k", "100k", "150k", "200k"]
        batt_name = ["50k", "100k", "150k", "200k"]
        sp_index = 0
        for sp in PowerCons.get_solar_panel_instances():
            ax1 = axes.flat[sp_index]
            for method_no in range(len(self.methods)):
                learning_method = self.methods[method_no]
                only_one_method_vals = []
                for batt in PowerCons.get_battery_instances():
                    log_name = "{}_{}_{}_{}_{}".format(sp, batt, learning_method, city, traffic_rate)
                    val = data[log_name]
                    only_one_method_vals.append(val / div_val)

                ax1.plot(only_one_method_vals, label=self.method_type_labels[method_no],
                         linestyle=self.method_type_lines[method_no],
                         color=self.method_type_colors[method_no], marker=self.marker_list[method_no],
                         markersize=7, lw=2)
            ax1.set_title(MonitorRewards.subfigure_prefix[sp_index] + "Solar Panel:" + sp_show_name[sp_index], fontsize=MonitorRewards.def_font_size - 2)
            sp_index += 1

            # min_val = min(only_one_method_vals)
            # min_val = int(math.ceil((min_val - 10) / 10) * 10)
            # max_val = max(only_one_method_vals)
            # max_val = int(math.ceil((max_val + 10) / 10) * 10)
            # major_ticks = np.arange(min_val, max_val, 10)
            # # minor_ticks = np.arange(60, 151, 5)
            # ax1.set_yticks(major_ticks)

            # for label in ax1.get_yticklabels():
            #     label.set_fontsize(MonitorRewards.def_font_size)
            x_axis_labels = []
            x_axis_locs = []
            for c in range(0, 4, 1):
                x_axis_labels.append(batt_name[c])
                x_axis_locs.append(c)
            ax1.set_xticks(x_axis_locs)
            ax1.set_xticklabels(x_axis_labels)
            ax1.grid(axis='y', which='major')
            ax1.set_xlabel('Battery Size')
            # ax1.set_axisbelow(True)
            # ax1.autoscale(enable=True, axis='x', tight=True)

        ax_left_side = fig.add_subplot(111, frame_on=False)
        plt.tick_params(labelcolor="none", bottom=False, left=False)
        op_title = 'OpEx (k$)'
        plt.ylabel(op_title, fontsize=MonitorRewards.def_font_size, labelpad=15)

        # Set common labels
        handles, labels = ax1.get_legend_handles_labels()
        ax_left_side.legend(handles, labels, loc='center left', bbox_to_anchor=(-0.1, 1.1), ncol=4,
                            framealpha=1, fancybox=True, shadow=True,
                            fontsize=MonitorRewards.def_font_size)

        plt.tight_layout()
        if self.SAVE_FIGURE:
            figure_prefix = "sizing"
            plt.savefig("{}{}.pdf".format(self.rewards_folder, figure_prefix), format='pdf', bbox_inches='tight')
        else:
            plt.show()
        plt.clf()

    def compare_the_methods(self, comp_type):
        div_val = 1
        fig, axes = plt.subplots(2, 2, figsize=(9, 7))
        b_off = 0.3
        wid = 0.2
        file_name_ext = "ts"
        data = self.snapshot.load_rewards("{}_{}".format(comp_type, file_name_ext))
        if comp_type == "obj_func":
            op_title = 'Nominal OpEx'
            figure_prefix = "obj"

        for conf in PowerCons.get_solar_panel_and_battery_for_each_cloud():
            sp = conf[0][0]
            batt = conf[0][1]

        city_index = 0
        for city in city_name_list:
            ax1 = axes.flat[city_index]
            base_width = []
            method_index = 0
            for learning_method in MonitorRewards.methods:
                only_one_method_vals = []
                for traffic_rate in traffic_rate_list:
                    log_name = "{}_{}_{}_{}_{}".format(sp, batt, learning_method, city, traffic_rate)
                    val = data[log_name]
                    only_one_method_vals.append(val / div_val)
                x_pos = np.arange(len(only_one_method_vals))
                if learning_method == MonitorRewards.methods[0]:
                    base_width = list(only_one_method_vals)
                else:
                    JOURNAL4 = False
                    if JOURNAL4:
                        percentage_vals = [100 + (x - y) * (100.0 / abs(y)) for x, y in zip(only_one_method_vals, base_width)]
                    else:
                        percentage_vals = [(x * 100.0) / y for x, y in zip(only_one_method_vals, base_width)]
                if learning_method == MonitorRewards.methods[0]:
                    ax1.bar(x_pos + (method_index) * wid - b_off, [100 for x in range(len(MonitorRewards.traffic_area_labels))], width=wid,
                            edgecolor=MonitorRewards.method_type_colors[method_index], align='center', alpha=0.4,
                            label=MonitorRewards.method_type_labels[method_index], hatch=MonitorRewards.method_type_hatch[method_index], fill=False,
                            )
                else:
                    ax1.bar(x_pos + (method_index) * wid - b_off, percentage_vals, width=wid,
                            edgecolor=MonitorRewards.method_type_colors[method_index], align='center', alpha=0.4,
                            label=MonitorRewards.method_type_labels[method_index], hatch=MonitorRewards.method_type_hatch[method_index], fill=False,
                            )
                method_index += 1
            ax1.set_title(MonitorRewards.subfigure_prefix[city_index] + city.title(), fontsize=MonitorRewards.def_font_size - 2)
            city_index += 1

            ax1.set_ylim(60, 105)
            major_ticks = np.arange(60, 105, 10)
            # minor_ticks = np.arange(60, 151, 5)
            ax1.set_yticks(major_ticks)

            for label in ax1.get_yticklabels():
                label.set_fontsize(MonitorRewards.def_font_size)
            ax1.set_xlim(-0.5, len(MonitorRewards.traffic_area_labels) - 0.2)
            ax1.set_xticks(x_pos + 0.00)
            ax1.set_xticklabels(MonitorRewards.traffic_area_labels, fontsize=MonitorRewards.def_font_size - 4)

            ax1.grid(axis='y', which='major')
            ax1.set_axisbelow(True)
            ax1.autoscale(enable=True, axis='x', tight=True)

        ax_left_side = fig.add_subplot(111, frame_on=False)
        plt.tick_params(labelcolor="none", bottom=False, left=False)

        plt.ylabel(op_title, fontsize=MonitorRewards.def_font_size, labelpad=15)

        # Set common labels
        handles, labels = ax1.get_legend_handles_labels()
        ax_left_side.legend(handles, labels, loc='center left', bbox_to_anchor=(-0.1, 1.1), ncol=4,
                            framealpha=1, fancybox=True, shadow=True,
                            fontsize=MonitorRewards.def_font_size)

        # fig.text(0.00, 0.5, op_title, ha='center', va='center', rotation='vertical', fontsize=MonitorRewards.def_font_size)
        plt.tight_layout()
        if self.SAVE_FIGURE:
            plt.savefig("{}{}.pdf".format(self.rewards_folder, figure_prefix), format='pdf', bbox_inches='tight')
        else:
            plt.show()
        plt.clf()

    def plot_obj(self, instance="Solar"):
        methods = method_list_milp
        number_of_legend = len(methods)
        reward_legend = [0 for x in range(number_of_legend)]
        for index in range(number_of_legend):
            method = methods[index]
            if method in method_list_milp:
                reward_legend[index] = self.snapshot.load_rewards("simulation_{}_avg".format(method))
            else:
                reward_legend[index] = self.snapshot.load_rewards("reinforcement_{}".format(method))
        if instance == "Solar":
            instance_size = PowerCons.SOLAR_PANEL_INSTANCE_SIZE
            instance_list = PowerCons.get_solar_panel_instances()
            average_size = PowerCons.BATTERY_INSTANCE_SIZE
            substring_prefix = "sp:"
            plt.xlabel("Solar Panel Size")
            plot_name = "solar_panel"
        else:
            instance_size = PowerCons.BATTERY_INSTANCE_SIZE
            instance_list = PowerCons.get_battery_instances()
            average_size = PowerCons.SOLAR_PANEL_INSTANCE_SIZE
            substring_prefix = "batt:"
            plt.xlabel("Battery Size")
            plot_name = "battery"

        obj_val = [[0 for x in range(instance_size)] for x in range(number_of_legend)]

        for legend_index in range(number_of_legend):
            rewards = reward_legend[legend_index]
            index = 0
            for ins in instance_list:
                substring = "{}{}".format(substring_prefix, ins)
                res = [val for key, val in rewards.items() if substring in key]
                obj_val[legend_index][index] = sum(res) / average_size
                obj_val[legend_index][index] = obj_val[legend_index][index] * REWARD_NORMALIZER / 1000.0
                index += 1
            method = methods[legend_index]
            if method in method_list_milp:
                plot_label = 'MILP {}'.format(method)
            else:
                plot_label = 'RL {}'.format(method)
            plt.plot(instance_list, obj_val[legend_index], label=plot_label)
        plt.ylabel("Electricity Cost in a Year Period (k$)")
        figure_prefix = "obj"
        plt.legend(loc='upper right', ncol=1, fancybox=True, shadow=True, fontsize=10)
        plt.grid(True)

        if self.SAVE_FIGURE:
            plt.savefig("{}{}_{}.pdf".format(self.rewards_folder, figure_prefix, plot_name), format='pdf', bbox_inches='tight')
        else:
            plt.show()
        plt.clf()

    def plot_rewards(self):
        for learning_rate, discount in LearningParameters.get_rate_and_discount():
            # for ec_index in range(N_OF_EC):
            methods = ["Q", "S"]
            for learning_method in methods:
                conf_name = "{}_{}_{}".format(learning_method, learning_rate, discount)
                for ec_index in [3]:
                    file_name = "conf_{}_{}_{}_ec_{}".format(conf_name, PowerCons.SOLAR_PANEL_BASE, PowerCons.BATTERY_BASE, ec_index)
                    self.single_plot(file_name)

    def single_plot(self, plot_name):
        WITH_BASELINE = False
        SHOW_OBJ_FUNC = True
        self.aggr_ep_rewards = self.snapshot.load_rewards(plot_name)
        x_axis_len = len(self.aggr_ep_rewards['ep'])
        if SHOW_OBJ_FUNC:
            plot_avg = [x * REWARD_NORMALIZER / NUMBER_OF_SIMULATION_DAY for x in self.aggr_ep_rewards['avg']]
            plot_max = [x * REWARD_NORMALIZER / NUMBER_OF_SIMULATION_DAY for x in self.aggr_ep_rewards['max']]
            plt.ylabel("Electricity Cost in a Day Period ($)")
            figure_prefix = "obj"
        else:
            plot_avg = [x for x in self.aggr_ep_rewards['avg']]
            plot_max = [x for x in self.aggr_ep_rewards['max']]
            plt.ylabel("Rewards Values in Each Episode")
            figure_prefix = "rwd"

        if WITH_BASELINE:
            baselines = [-124, -105, -97, -123]
            baseline_plot = [[y for x in range(x_axis_len)] for y in baselines]
        plt.plot(self.aggr_ep_rewards['ep'], plot_avg, label='avg rewards')
        # plt.plot(self.aggr_ep_rewards['ep'], self.aggr_ep_rewards['min'], label='min rewards')
        plt.plot(self.aggr_ep_rewards['ep'], plot_max, label='max rewards')
        if WITH_BASELINE:
            plt.plot(self.aggr_ep_rewards['ep'], baseline_plot[0], label='C-RAN')
            plt.plot(self.aggr_ep_rewards['ep'], baseline_plot[1], label='Static:1')
            plt.plot(self.aggr_ep_rewards['ep'], baseline_plot[2], label='Static:2')
            plt.plot(self.aggr_ep_rewards['ep'], baseline_plot[3], label='D-RAN')
        # bbox_to_anchor=(2.25, 1.15)
        plt.legend(loc='lower center', ncol=3, fancybox=True, shadow=True, fontsize=10)
        plt.grid(True)
        plt.xlabel("Episodes")
        if self.SAVE_FIGURE:
            plt.savefig("{}{}_{}.pdf".format(self.rewards_folder, figure_prefix, plot_name), format='pdf', bbox_inches='tight')
        else:
            plt.show()
        plt.clf()


class MonitorInput:
    def __init__(self):
        self.snapshot = Snapshot()
        self.given_folder = "../output/results/"
        self.SAVE_FIGURE = True

    def get_daily_average_harvested_energy(self):
        avg = []
        for cn in city_name_list:
            self.snapshot.set_solar_data_path(cn)
            s = self.snapshot.load_solar_energy()
            avg.append((cn, s.get_average_regeneration_energy_in_a_day(40)))  # 4 is the panel size
        return avg

    def show_harvesting_energy_hour(self, harvesting_power):
        fig = plt.figure()
        x_axis_labels = []
        x_axis_locs = []
        for c in range(0, 24, 4):
            x_axis_labels.append(c)
            x_axis_locs.append(c)

        ax = fig.add_subplot(1, 1, 1)
        harvesting_power[0][1][:] = [x / 1000 for x in harvesting_power[0][1]]
        ax.bar(range(len(harvesting_power[0][1])), harvesting_power[0][1])
        ax.set_title(harvesting_power[0][0].title(), fontsize=16)
        ax.set_xticks(x_axis_locs)
        ax.set_xticklabels(x_axis_labels, fontsize=12)
        ax.set_xlim((0, 24))
        ax.grid(True)

        # Set common labels
        fig.text(0.5, 0.04, 'Hours of a Day', ha='center', va='center', fontsize=16)
        fig.text(0.03, 0.5, 'Avg. Energy per Hour (KWatts)', ha='center', va='center', rotation='vertical', fontsize=16)

        if self.SAVE_FIGURE:
            plt.savefig(f"{self.given_folder}_harvested_hourly.pdf", format='pdf', bbox_inches='tight')
        else:
            plt.show()

    def plot_daily_average_energy(self):
        avg = self.get_daily_average_harvested_energy()
        self.show_harvesting_energy_hour(avg)


mr = MonitorRewards()
rcParams['pdf.fonttype'] = 42
rcParams['ps.fonttype'] = 42
comp_type = ["obj_func", "fossil_cons", "ren_en", "unstored_en"]
DAILY_TS = False
TS = True
if DAILY_TS:
    mr.plot_every_vs_hour_two_figures()
elif TS:
    mr.compare_the_methods(comp_type[0])
else:
    mr.compare_the_sizes(comp_type[0])

# mr.plot_rewards()
# mr.plot_obj("Solar")
# mr.plot_obj("Battery")
# mq = MonitorQTable()
# mq.plot_actions()
# mq.check_different_ec_q_tables()
# mq.make_video()

# mi = MonitorInput()
# mi.plot_daily_average_energy()
sys.exit()
