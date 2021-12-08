"""Renewable Energy Module.
Classes in this module are responsible for creating/managing/consuming both the renewable and the fossil energies.

"""
import csv

import numpy as np

from constants import *
from helpers import SaatliMaarifTakvimi, SHC


class SolarEnergy:
    """This class represents a solar energy source.

     * Battery Class creates this class at its initialize step.
     * It has only one method which returns the average energy of a one day for each time slice.

    """
    whole_year_energy = None

    def __init__(self, city_name):
        self.whole_year_energy = self.__create_whole_year_energy(city_name)
        pass

    def get_solar_energy(self, day_of_the_year, hour_of_the_day, panel_size):
        return self.whole_year_energy[day_of_the_year][hour_of_the_day] * panel_size

    def get_average_regeneration_energy_in_a_day(self, panel_size):
        # regenerated_energy_in_a_day = [0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
        # for hour_of_the_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
        #     avg_val = 0.0
        #     for day_no in range(NUMBER_OF_SIMULATION_DAY):
        #         avg_val += self.whole_year_energy[day_no][hour_of_the_day]
        #     regenerated_energy_in_a_day[hour_of_the_day] = avg_val / NUMBER_OF_SIMULATION_DAY
        # return [x * panel_size for x in regenerated_energy_in_a_day]

        regenerated_energy_in_a_day = [0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)]
        for day_no in range(365):
            for hour_of_the_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                regenerated_energy_in_a_day[hour_of_the_day] += self.whole_year_energy[day_no][hour_of_the_day]
        return [(x / 365.0) * panel_size for x in regenerated_energy_in_a_day]

    def get_average_regeneration_energy_in_a_month(self, panel_size):
        smf = SaatliMaarifTakvimi()
        regenerated_energy_in_a_month = [0 for x in range(len(SHC.LIST_OF_MONTHS_IN_A_YEAR))]
        for day_no in range(365):
            for hour_of_the_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                regenerated_energy_in_a_month[smf.month_of_the_year] += self.whole_year_energy[day_no][hour_of_the_day]
                smf.yapragi_kopar()  # increase_the_time_slot
        for month_no in range(12):
            regenerated_energy_in_a_month[month_no] /= SHC.NUMBER_OF_DAYS_IN_MONTHS[month_no]
        return regenerated_energy_in_a_month * panel_size

    def get_average_regeneration_energy_in_a_month_per_hour(self, month, panel_size):
        smf = SaatliMaarifTakvimi()
        regenerated_energy_in_a_month = [[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for y in range(len(SHC.LIST_OF_MONTHS_IN_A_YEAR))]
        for day_no in range(365):
            for hour_of_the_day in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                regenerated_energy_in_a_month[smf.month_of_the_year][hour_of_the_day] += self.whole_year_energy[day_no][hour_of_the_day]
                smf.yapragi_kopar()  # increase_the_time_slot
        for month_no in range(12):
            regenerated_energy_in_a_month[month_no] = [x / SHC.NUMBER_OF_DAYS_IN_MONTHS[month_no] for x in regenerated_energy_in_a_month[month_no]]
        return regenerated_energy_in_a_month[month] * panel_size

    def __create_whole_year_energy(self, city_name):
        pvwatts_path = "../input/solar_data/pvwatts_hourly_" + city_name + ".csv"
        ac_watt_data = [[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for y in
                        range(NUMBER_OF_SIMULATION_DAY)]
        with open(pvwatts_path, 'rb') as csv_file:
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
                    random_val = (np.random.poisson(10)) / 140.0
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
    ren_energy_consumption = None  # represents the renewable energy consumption
    fossil_energy_consumption = None  # represents the fossil energy consumption
    bs_awake_state = {'Sleep', 'Awake'}  # represents the restriction_type of the waste restriction_type
    wasted_energy = None  # represents the amount of the wasted energy
    renewable_usage_ratio = None

    def __init__(self):
        """Battery class initial method.
        This function erase the battery flash memory.
        """
        self.history = []  # initializing an empty history
        self.initialization_for_the_next_time_slot()

    def log_current_time_slot(self, harvesting_amount, remaining_energy, rewlsb, rewssb):
        """Battery class initial method.
        This function writes the current time values to the flash.
        """
        self.history.append(
            (harvesting_amount,  # outside
             self.bs_awake_state,  # inside
             self.fossil_energy_consumption,  # inside
             self.ren_energy_consumption,  # inside
             self.wasted_energy,  # inside
             remaining_energy,  # outside
             self.renewable_usage_ratio,
             rewlsb,
             rewssb))  # outside

    def initialization_for_the_next_time_slot(self):
        # initializations for next time slot
        self.renewable_usage_ratio = 0.0
        self.fossil_energy_consumption = 0.0
        self.ren_energy_consumption = 0.0
        self.bs_awake_state = 'Sleep'
        self.wasted_energy = 0.0


class Battery:
    """This class represents a battery power.

    * It is created by the BaseStation Class.
    * The BaseStation Class should call increase_the_time_slot method at each time slice to simulate the Battery.
    * The BaseStation Class should call consume_power method when it is awake. This method consumes a constant energy.

     """
    # CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO = 754.8  # default consuming energy value is the 754.8 which needs for a 20W Tx Power
    # CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO = 150  # default consuming energy value is the ?? which needs for a 2W Tx Power in a micro bs
    OLD_SKOOL_POWER_CONSUMPTION = False
    if OLD_SKOOL_POWER_CONSUMPTION:
        CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO = 1350  # from Auer et. al.
        CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO = 144.6  # from Auer et. al.
        consuming_power_per_time_slice = None
    else:
        CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_STATIC = 780
        CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_DYNAMIC = 564
        CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO_STATIC = 112
        CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO_DYNAMIC = 32.76
        consuming_power_per_time_slice_static = None
        consuming_power_per_time_slice_dynamic = None


    INCREMENTING_BATTERY_SIZE = 2500
    remaining_energy = None  # the remaining energy of the battery
    rewlsb = None  # the remaining energy of the battery
    rewssb = None  # the remaining energy of the battery
    rewssb_rec = None  # the remaining energy of the battery
    rewlsb_rec = None

    time_slot_of_the_current_day = None  # simulates the current time
    flash_memory = None  # using to log the history of the battery
    solar_energy = None
    day_of_the_year = None
    battery_size = None
    panel_size = None


    def __init__(self, solar_energy, panel_size, max_battery_energy, bs_type):
        """Battery class initial method.
        This function initialize a new battery which has an empty log, zero remaining energy at the time slice 0.
        """
        self.battery_size = max_battery_energy
        if self.OLD_SKOOL_POWER_CONSUMPTION:
            if bs_type == BSType.MICRO:
                self.consuming_power_per_time_slice = self.CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO
            else:
                self.consuming_power_per_time_slice = self.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO
        else:
            if bs_type == BSType.MICRO:
                self.consuming_power_per_time_slice_static = self.CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO_STATIC
                self.consuming_power_per_time_slice_dynamic = self.CONSUMING_POWER_PER_TIME_SLICE_FOR_MICRO_DYNAMIC
            else:
                self.consuming_power_per_time_slice_static = self.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_STATIC
                self.consuming_power_per_time_slice_dynamic = self.CONSUMING_POWER_PER_TIME_SLICE_FOR_MACRO_DYNAMIC


        self.solar_energy = solar_energy  # connecting the battery to the solar panel
        self.panel_size = panel_size
        self.remaining_energy = self.battery_size  # batteries are full at the starting time
        self.rewlsb = self.battery_size + self.INCREMENTING_BATTERY_SIZE
        self.rewssb = self.battery_size - self.INCREMENTING_BATTERY_SIZE
        self.time_slot_of_the_current_day = 0  # batteries are connected to the solar panel at the midnight
        self.flash_memory = BatteryFlashMemory()  # flash memory is erased
        self.day_of_the_year = 0

    def get_battery_utilization(self):
        if self.battery_size == 0:
            return 0
        else:
            return self.remaining_energy / self.battery_size

    def __increase_day(self):
        self.day_of_the_year += 1

    def increase_the_time_slot(self):
        """bs calls this func. periodically at each time slice which needs for logging and harvesting energy
        """
        se = self.solar_energy.harvest_the_solar_energy(self.day_of_the_year, self.time_slot_of_the_current_day, self.panel_size)
        self.remaining_energy += se
        self.rewlsb += se
        self.rewssb += se
        # solar panel energy of the current time slice is stored in the battery
        if self.remaining_energy >= self.battery_size:
            # if the battery does not have enough capacity to store new harvested energy
            self.flash_memory.wasted_energy = self.remaining_energy - self.battery_size  # log the wasted en. val.
            self.remaining_energy = self.battery_size  # battery has full capacity
        else:  # if battery has enough cap.
            self.flash_memory.wasted_energy = 0  # log the wasted en. val.

        if self.rewlsb >= self.battery_size + self.INCREMENTING_BATTERY_SIZE:
            self.rewlsb = self.battery_size + self.INCREMENTING_BATTERY_SIZE
            self.rewlsb_rec = self.INCREMENTING_BATTERY_SIZE
        else:
            self.rewlsb_rec = max(self.rewlsb - self.battery_size, 0)

        if self.rewssb >= self.battery_size - self.INCREMENTING_BATTERY_SIZE:
            self.rewssb_rec = self.rewssb - (self.battery_size - self.INCREMENTING_BATTERY_SIZE)
            self.rewssb = self.battery_size - self.INCREMENTING_BATTERY_SIZE
        else:
            self.rewssb_rec = 0

        self.flash_memory.log_current_time_slot(
            se,
            self.remaining_energy,
            self.rewlsb_rec,
            self.rewssb_rec)
        self.time_slot_of_the_current_day += 1
        if self.time_slot_of_the_current_day == 24:
            self.time_slot_of_the_current_day = 0
            self.__increase_day()
        self.flash_memory.initialization_for_the_next_time_slot()

    def consume_power(self, system_load=1):
        """bs calls this func. if it wants to get the default energy amount
        """
        if self.OLD_SKOOL_POWER_CONSUMPTION:
            self.__consume_power(self.consuming_power_per_time_slice)
        else:
            self.__consume_power(self.consuming_power_per_time_slice_static + system_load * self.consuming_power_per_time_slice_dynamic)

    def __consume_power(self, requested_power):
        """power consumption for operating the bs
        """
        self.flash_memory.bs_awake_state = 'Awake'
        if requested_power > self.remaining_energy:  # if we do not have enough energy in the battery
            self.flash_memory.fossil_energy_consumption = requested_power - self.remaining_energy  # log the amount of the fossil en. cons.
            self.flash_memory.ren_energy_consumption = self.remaining_energy  # log the amount of the ren. en. cons.
            self.flash_memory.renewable_usage_ratio = float(
                self.remaining_energy) / requested_power  # log the current energy consumption restriction_type
            self.remaining_energy = 0.0
        else:
            self.remaining_energy -= requested_power  # give the energy from the battery
            self.flash_memory.ren_energy_consumption = requested_power  # log the amount of the ren. en. cons.
            self.flash_memory.renewable_usage_ratio = 1.0  # log the current energy consumption restriction_type
        self.rewlsb = max(self.rewlsb - requested_power, 0)
        self.rewssb = max(self.rewssb - requested_power, 0)


