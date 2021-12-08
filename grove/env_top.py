"""
The Cloud environment. Everything about the cloud.
"""
import sys

from env_energy import *
from env_traffic import *
from performanceCalculator import *


class CloudEnvironment:
    time_machine = None
    battery = [None for x in range(N_OF_CLOUD)]
    CREATE_INPUT_DATA = False

    def __init__(self, city, traffic_rate):
        # ----- DEBUG
        # self.debug_reward_per_urf = [0 for x in range(4)]
        # self.debug_count_per_urf = [0 for x in range(4)]
        # ----- DEBUG
        self.time_machine = TimeMachine.get_instance()
        self.du_load_in_cc = 0
        self.number_of_ue = NUMBER_OF_UE_PER_EC * N_OF_EC  # Total Number of User
        self.r_ec = range(N_OF_EC)
        self.traffic_load = None  # we will get these given data from folder input/given_data
        self.solar_energy = None
        self.cost_avg = [0 for x in range(N_OF_CLOUD)]
        self.ren_en_avg = [0 for x in range(N_OF_CLOUD)]
        self.unstored_en_avg = [0 for x in range(N_OF_CLOUD)]
        if self.CREATE_INPUT_DATA:
            city_list = ['stockholm', 'cairo', 'jakarta']
            for c in city_list:
                self.create_and_save_solar_energy(c)
            # Traffic.create_and_save_traffic(1)
            sys.exit()

        self.load_data(traffic_rate, city)
        pass

    def close(self):
        Event('print performance results', 'test')
        pass

    def create_and_save_solar_energy(self, city_name):
        snapshot = Snapshot()
        snapshot.set_solar_data_path(city_name)
        solar_energy = SolarEnergy(city_name)  # connecting the battery to the solar panel
        snapshot.save_solar_energy(solar_energy)
        print("solar energy is saved in a file.")


    # Loading Traffic and Solar Energy
    def load_data(self, traffic_rate, city):
        # LOAD TRAFFIC
        snapshot = Snapshot()
        snapshot.set_traffic_data_path(1)  # always 1, we change the traffic rate after loading the generated one
        self.traffic_load = snapshot.load_tr()
        self.traffic_load = self.traffic_load * traffic_rate
        # Traffic.plt_traffic_in_a_year_period(self.traffic_load[0][0])
        snapshot.set_solar_data_path(city)
        self.solar_energy = snapshot.load_solar_energy()
        if AVERAGE_GIVEN_DATA:
            self.traffic_load = Traffic.get_average_traffic(self.traffic_load)

    # @PerformanceCalculator
    def step(self, number_of_active_urf, renewable_energy_ratio, ec_index):
        current_time_slot = self.time_machine.get_hour()
        the_day = self.time_machine.get_day_of_the_year()
        if ec_index == CC_INDEX:
            remaining_en = self.battery[ec_index].battery_update(self.du_load_in_cc, renewable_energy_ratio)
            self.du_load_in_cc_diagnose = self.du_load_in_cc
            self.du_load_in_cc = 0
        else:  # EC
            if AVERAGE_GIVEN_DATA:
                du_urllc_load = self.traffic_load[ec_index][PacketType.URLLC][current_time_slot] * N_OF_URF
                du_embb_load = self.traffic_load[ec_index][PacketType.EMBB][current_time_slot] * number_of_active_urf
                self.du_load_in_cc += self.traffic_load[ec_index][PacketType.EMBB][current_time_slot] * (N_OF_URF - number_of_active_urf)
            else:
                du_urllc_load = self.traffic_load[ec_index][PacketType.URLLC][the_day][current_time_slot] * N_OF_URF
                du_embb_load = self.traffic_load[ec_index][PacketType.EMBB][the_day][current_time_slot] * number_of_active_urf
                self.du_load_in_cc += self.traffic_load[ec_index][PacketType.EMBB][the_day][current_time_slot] * (N_OF_URF - number_of_active_urf)
            du_load = du_urllc_load + du_embb_load
            remaining_en = self.battery[ec_index].battery_update(du_load, renewable_energy_ratio)

        self.cost_avg[ec_index], self.unstored_en_avg[ec_index] = self.battery[ec_index].get_the_last_24_hour_consumptions()
        total_cost = 0
        ren_en_avg = 0
        for i in range(N_OF_CLOUD):
            total_cost += self.cost_avg[i]
            ren_en_avg += self.ren_en_avg[i]
        # reward = -(cost_avg / 1000.0) + (ren_en_avg / 200.0)
        # if self.unstored_en_avg[ec_index] > 0:
        #     print("debuggging")
        # reward = (total_cost / REWARD_NORMALIZER)
        # UNSTORED_EN_WEIGHTING_FACTOR = 5
        # reward = (total_cost + self.unstored_en_avg[ec_index] * UNSTORED_EN_WEIGHTING_FACTOR) / REWARD_NORMALIZER
        reward = total_cost / REWARD_NORMALIZER
        next_time_slot = (current_time_slot + 1) % NUMBER_OF_TIME_SLOT_IN_ONE_DAY
        if AVERAGE_GIVEN_DATA:
            if ec_index == CC_INDEX:
                load = 0
                for i in range(N_OF_EC):
                    load += self.traffic_load[i][PacketType.EMBB][next_time_slot]
                traffic_load = load / N_OF_EC
            else:
                traffic_load = self.traffic_load[ec_index][PacketType.EMBB][next_time_slot]
        else:
            if ec_index == CC_INDEX:
                load = 0
                for i in range(N_OF_EC):
                    load += self.traffic_load[i][PacketType.EMBB][the_day][next_time_slot]
                traffic_load = load / N_OF_EC
            else:
                traffic_load = self.traffic_load[ec_index][PacketType.EMBB][the_day][next_time_slot]
        # ----- DEBUG
        # print("number_of_active_urf:{} ec_index:{} reward:{}".format(number_of_active_urf, ec_index, reward))
        # if number_of_active_urf != None:
        #     self.debug_reward_per_urf[number_of_active_urf] += reward
        #     self.debug_count_per_urf[number_of_active_urf] += 1
        # ----- DEBUG
        return remaining_en, next_time_slot, traffic_load, reward

    def calculate_one_year_obj_func(self):
        total_cost = 0
        for cloud_index in range(N_OF_CLOUD):
            for rec in self.battery[cloud_index].fm.history:
                hour_of_the_day = rec[1]
                fossil_energy_consumption = rec[3]
                total_cost += fossil_energy_consumption * PowerCons.ELEC_PRICE[hour_of_the_day]
        return total_cost

    def reset(self, sp, batt):
        self.time_machine.reset_the_time_machine()
        # solar_energy, panel_size, max_battery_energy, cloud_type):
        for ec_index in self.r_ec:
            self.battery[ec_index] = Battery(self.solar_energy, sp, batt, CloudType.edge)
        self.battery[CC_INDEX] = Battery(self.solar_energy, sp * PowerCons.CC_SIZING_MULTIPLIER, batt * PowerCons.CC_SIZING_MULTIPLIER, CloudType.center)
        remaining_energy = 0
        self.du_load_in_cc = 0
        self.cost_avg = [0 for x in range(N_OF_CLOUD)]
        self.ren_en_avg = [0 for x in range(N_OF_CLOUD)]
        current_time_slot = self.time_machine.get_hour()
        traffic_load = 0
        return remaining_energy, current_time_slot, traffic_load
