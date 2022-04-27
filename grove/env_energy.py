""" energy module.
Classes in this module are responsible for creating/managing/consuming both the renewable and the fossil energies.

"""
import csv

# from constants import *
from helpers import *
from time_machine import *


class SolarEnergy:
    """ SolarEnergy Class.
    This class represents a solar energy source.
    """
    whole_year_energy = None

    def __init__(self, city_name):
        self.whole_year_energy = self.__create_whole_year_energy(city_name)
        pass

    def get_solar_energy(self, day_of_the_year, hour_of_the_day, panel_size):
        day_of_the_year = day_of_the_year % NUMBER_OF_SIMULATION_DAY
        # day_of_the_year = 50  # fixme: del it
        return self.whole_year_energy[day_of_the_year][hour_of_the_day] * panel_size

    def get_average_regeneration_energy_in_a_day(self, panel_size):
        regenerated_energy_in_a_day = [0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
        for day_no in range(365):
            for hour_of_the_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                regenerated_energy_in_a_day[hour_of_the_day] += self.whole_year_energy[day_no][hour_of_the_day]
        return [(x / 365.0) * panel_size for x in regenerated_energy_in_a_day]

    @staticmethod
    def __create_whole_year_energy(city_name):
        pvwatts_path = "../input/solar_data/pvwatts_hourly_" + city_name + ".csv"
        ac_watt_data = [[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for y in
                        range(NUMBER_OF_SIMULATION_DAY)]
        with open(pvwatts_path, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=' ', quotechar='|')
            hour_of_the_day = 0
            day_of_the_year = 0
            for row in csv_reader:
                if csv_reader.line_num > 19:
                    hour_field = int(row[0].split('","')[2])  # row is a list with one element
                    if hour_of_the_day != int(hour_field):
                        # raise Exception("Houston we have a problem: the hour order in the csv file is not true!!") # csv file is really has error !!
                        print("Houston we have a problem: the hour order in the csv file is not true!! day_of_the_year:{} and hour_of_the_day:{}".format(
                            day_of_the_year, hour_of_the_day))
                    ac_watt_field = float(row[0].split('","')[9].replace('"', ''))  # row is a list with one element
                    # random_val = (np.random.poisson(10)) / 140.0    #fixme: check that why we randomize the data
                    random_val = 0
                    ac_watt_data[day_of_the_year][hour_of_the_day] = ac_watt_field * (1 + random_val)
                    hour_of_the_day += 1
                    if hour_of_the_day == 24:
                        hour_of_the_day = 0
                        day_of_the_year += 1
                    if day_of_the_year == NUMBER_OF_SIMULATION_DAY:
                        break  # simulations that lesser and equal to one year returns at this point
                    if day_of_the_year == 365:
                        number_of_simulation_years = NUMBER_OF_SIMULATION_DAY / 365
                        for year in range(1, number_of_simulation_years):
                            for day_of_the_year in range(0, 365):
                                for hour_of_the_day in range(24):
                                    random_val = (np.random.poisson(10)) / 140.0
                                    ac_watt_data[year * 365 + day_of_the_year][hour_of_the_day] = ac_watt_data[day_of_the_year][hour_of_the_day] * (
                                            1 + random_val)
                        break
            return ac_watt_data


class BatteryFlashMemory:
    """This class represents the battery flash memory.

    * It is automatically created by the initialize step of the Battery Class.
    * the fields in this sub module only used for monitor module
    * Battery class calls log_current_time_slot method at each time slice to log the current status of the battery.

    """
    history = None
    ren_energy_consumption = None
    fossil_energy_consumption = None  # represents the fossil energy consumption
    excessive_energy = None
    unstored_energy = None
    renewable_usage_ratio = None

    def __init__(self):
        """Battery class initial method.
        This function erase the battery flash memory.
        """
        self.history = []  # initializing an empty history
        self.initialization_for_the_next_time_slot()

    def log_current_time_slot(self, day_of_the_year, hour_of_the_day, harvesting_amount, remaining_energy):
        """Battery class initial method.
        This function writes the current time values to the flash.
        """  # we do not need to log the excessive energy
        self.history.append(
            (day_of_the_year,
             hour_of_the_day,
             harvesting_amount,  # outside
             self.fossil_energy_consumption,  # inside
             self.ren_energy_consumption,  # inside
             self.unstored_energy,
             remaining_energy,  # outside
             self.renewable_usage_ratio))  # outside

    def initialization_for_the_next_time_slot(self):
        # initializations for next time slot
        self.renewable_usage_ratio = 0.0
        self.fossil_energy_consumption = 0.0
        self.ren_energy_consumption = 0.0
        self.excessive_energy = 0.0
        self.unstored_energy = 0.0

class Battery:
    """This class represents a battery in a agent_cloud.

    * Created by Environment Class.
    * The Environment_Cloud should call increase_the_time_slot method at each time slice to simulate the Battery.
    * The Environment_Cloud should call consume_power method when it is consume energy.

     """


    consuming_power_per_time_slice_static = None
    consuming_power_per_time_slice_dynamic = None

    remaining_energy = None  # the remaining energy of the battery

    fm = None  # using to log the history of the battery
    solar_energy = None
    battery_size = None
    panel_size = None

    def __init__(self, solar_energy, panel_size, max_battery_energy, cloud_type):
        """Battery class initial method.
        This function initialize a new battery which has an empty log, zero remaining energy at the time slice 0.
        """
        self.battery_size = max_battery_energy

        if cloud_type == CloudType.edge:
            self.consuming_power_per_time_slice_static = PowerCons.P_EC_STA
            self.consuming_power_per_time_slice_dynamic = PowerCons.P_EC_DYN
            self.DU_UTILIZATION = 1.0
        else:
            self.consuming_power_per_time_slice_static = PowerCons.P_CC_STA
            self.consuming_power_per_time_slice_dynamic = PowerCons.P_CC_DYN
            self.DU_UTILIZATION = PowerCons.CENTRALIZATION_FACTOR

        self.solar_energy = solar_energy  # connecting the battery to the solar panel
        self.panel_size = panel_size
        if AVERAGE_GIVEN_DATA:
            self.ge = solar_energy.get_average_regeneration_energy_in_a_day(self.panel_size)
        self.remaining_energy = 0  # batteries are empty at the starting time self.battery_size  # batteries are full at the starting time
        self.fm = BatteryFlashMemory()  # flash memory is erased
        self.time_machine = TimeMachine.get_instance()

    def get_the_fossil_en_cons(self):
        history = self.fm.history[-1]
        hour_of_the_day = history[1]
        return history[3] * self.energy_prices_per_hour[hour_of_the_day]

    def get_the_last_24_hour_consumptions(self):
        total_data_len = REWARD_WINDOW_SIZE
        print_the_history = False
        self.energy_prices_per_hour = PowerCons.ELEC_PRICE
        # self.energy_prices_per_hour = [0] * 19 + [1] * 1 + [0] * 4

        if len(self.fm.history) < total_data_len:
            data_len = len(self.fm.history)
        else:
            data_len = total_data_len
        ren_en = 0
        cost = 0
        unstored_en = 0
        # if self.time_machine.get_day_of_the_year()%20 == 3 and self.time_machine.get_hour() == 0:
        #     print_the_history = True
        #     print("\n--------------------day:{}\thour:{}\n".format(self.time_machine.get_day_of_the_year(), self.time_machine.get_hour()))
        for i in range(1, data_len + 1):
            history = self.fm.history[-i]
            if print_the_history:
                print("history:{}".format(history))
            hour_of_the_day = history[1]
            cost += history[3] * self.energy_prices_per_hour[hour_of_the_day]
            ren_en += history[4]
            unstored_en += history[5]
        cost_avg = cost / data_len
        ren_en_avg = ren_en / data_len
        unstored_en_avg = unstored_en / data_len
        if print_the_history:
            print_the_history = False
            print("\n--------------------fossil_en_total:{}\tren_en_total:{} cost_avg:{}\tren_en_avg:{}\n".format(cost, ren_en, cost_avg, ren_en_avg))

        return cost_avg, unstored_en_avg

    def battery_update(self, process_load, renewable_energy_ratio):
        hour = self.time_machine.get_hour()
        se = self.__harvest_the_solar_energy(hour)
        self.__consume_energy(process_load, renewable_energy_ratio)
        # print("fossil:{}\tren:{}".format(self.fm.fossil_energy_consumption, self.fm.ren_energy_consumption))
        self.__record_the_current_status(self.time_machine.get_day_of_the_year(), hour, se)
        return self.remaining_energy

    def get_battery_utilization(self):
        if self.battery_size == 0:
            return 0
        else:
            return self.remaining_energy / self.battery_size

    def __record_the_current_status(self, day_of_the_year, hour_of_the_day, se):
        self.fm.log_current_time_slot(
            day_of_the_year,
            hour_of_the_day,
            se,
            self.remaining_energy)

        self.fm.initialization_for_the_next_time_slot()

    def __calculate_excessive_energy(self):
        if self.remaining_energy >= self.battery_size:
            # if the battery does not have enough capacity to store new harvested energy
            self.fm.excessive_energy = self.remaining_energy - self.battery_size  # log the wasted en. val.
            self.remaining_energy = self.battery_size  # battery has full capacity
        else:  # if battery has enough cap.
            self.fm.excessive_energy = 0  # log the wasted en. val.

    def __harvest_the_solar_energy(self, hour):
        """bs calls this func. periodically at each time slice which needs for logging and harvesting energy
        """
        if AVERAGE_GIVEN_DATA:
            se = self.ge[hour]
        else:
            se = self.solar_energy.get_solar_energy(self.time_machine.get_day_of_the_year(), hour, self.panel_size)
        self.remaining_energy += se
        # solar panel energy of the current time slice is stored in the battery
        return se

    def __consume_total_energy_cons(self, process_load):

        total_process_gops = process_load * PowerCons.USER_CHUNK_SIZE * PowerCons.GOPS_VALUE_PER_URF
        total_process_energy_cons = total_process_gops / PowerCons.GOPS_2_WATT_CONVERTER
        total_energy_consumption = self.consuming_power_per_time_slice_static \
                                   + total_process_energy_cons * self.consuming_power_per_time_slice_dynamic * self.DU_UTILIZATION
        return total_energy_consumption

    def __consume_energy(self, process_load, renewable_energy_ratio):
        """env
        """
        total_energy_consumption = self.__consume_total_energy_cons(process_load)

        self.__calculate_excessive_energy()
        consume_energy_minus_excessive_en = total_energy_consumption - self.fm.excessive_energy
        if consume_energy_minus_excessive_en <= 0:
            self.fm.ren_energy_consumption = total_energy_consumption
            # we consume energy from excessive part,
            # so battery is full and the system did not consume from grid
            # now we will calculate the unstored_energy
            self.fm.unstored_energy = self.fm.excessive_energy - total_energy_consumption
        else:
            self.fm.unstored_energy = 0
            self.fm.ren_energy_consumption = self.fm.excessive_energy
            ren_energy_consumption_demand = consume_energy_minus_excessive_en * renewable_energy_ratio
            if ren_energy_consumption_demand <= self.remaining_energy:
                self.fm.ren_energy_consumption += ren_energy_consumption_demand
                self.remaining_energy = self.remaining_energy - ren_energy_consumption_demand
            else:
                self.fm.ren_energy_consumption += self.remaining_energy
                self.remaining_energy = 0
        self.fm.renewable_usage_ratio = self.fm.ren_energy_consumption / total_energy_consumption
        self.fm.fossil_energy_consumption = total_energy_consumption - self.fm.ren_energy_consumption
