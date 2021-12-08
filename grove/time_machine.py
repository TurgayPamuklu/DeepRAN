"""
This file creates a time machine.
"""

from helpers import NUMBER_OF_TIME_SLOT_IN_ONE_DAY


class TimeMachine:
    __instance = None
    NUMBER_OF_DAYS_IN_MONTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_of_the_year = 0
    day_of_the_month = 1
    day_of_the_year = 0
    hour_of_the_day = -1
    season = 0

    @staticmethod
    def get_instance():
        """ Static access method. """
        if TimeMachine.__instance is None:
            TimeMachine()
        return TimeMachine.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if TimeMachine.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            TimeMachine.__instance = self

        self.reset_the_time_machine()

    def reset_the_time_machine(self):
        self.month_of_the_year = 0
        self.day_of_the_month = 1
        self.hour_of_the_day = 0
        self.day_of_the_year = 0
        self.season = 0

    def next_hour(self):
        self.hour_of_the_day += 1
        if self.hour_of_the_day == NUMBER_OF_TIME_SLOT_IN_ONE_DAY:
            self.hour_of_the_day = 0
            self.day_of_the_month += 1
            self.day_of_the_year += 1
        if self.day_of_the_month > self.NUMBER_OF_DAYS_IN_MONTHS[self.month_of_the_year]:
            self.day_of_the_month = 1
            self.month_of_the_year += 1
            if self.month_of_the_year % 3 == 0:
                self.season += 1
            if self.month_of_the_year == 12:
                self.month_of_the_year = 0
                self.season = 0

    def get_hour(self):
        return self.hour_of_the_day

    def get_day_of_the_month(self):
        return self.day_of_the_month

    def get_day_of_the_year(self):
        return self.day_of_the_year

    def get_month(self):
        return self.month_of_the_year

    def get_season(self):
        return self.season
