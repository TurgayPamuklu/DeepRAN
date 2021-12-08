"""Constant variables of the RenDep Project

Turgay Pamuklu <pamuklu@gmail.com>

"""


class BSType(object):
    MACRO = 0
    MICRO = 1


def csn(cal_par):
    if cal_par == 'traffic_aware':
        return 'traffic aw.'
    elif cal_par == 'hybrid':
        return 'hybrid'
    else:
        return 'battery aw.'


class CalibrationParameters(object):
    # traffic_aware = 0
    hybrid = 1
    # battery_aware = 1e16

    @staticmethod
    def get_parameters():
        members = [attr for attr in dir(CalibrationParameters()) if
                   not callable(getattr(CalibrationParameters(), attr)) and not attr.startswith("__")]
        return members


INFINITELY_SMALL = 1e-200  # the value that almost zero
INFINITELY_BIG = 1e16
NUMBER_OF_TIME_SLOT_IN_ONE_DAY = 24  # we use each hour as a time slot
NUMBER_OF_SIMULATION_DAY = 1  # 12
PRINT_TAB_SIZE = "8"
REMOTE_SITE_MULTIPLIER_AS_A_PARAMETER = True
networkScale = [1000, 2000, 4000]
J4_REMOTE_SITE_MULTIPLIER = 1
SOLAR_PANEL_SIZE_AS_A_MULTIPLIER = False
DU_CAPACITY_SIZE_AS_A_MULTIPLIER = False
PURE_GRID = False
# Journal 3 specific constants
JOURNAL3 = False
JOURNAL4 = True
BITSEC_2_MBYTEHOUR = 3600.0 / (8 * 1e6)
USER_CHUNK_SIZE = 50
PEAK_TRAFFIC_PER_HOUR_PER_MBYTE = 900
# city_name_list = ['stockholm', 'cairo', 'jakarta', 'istanbul']
# traffic_scenarios = [1, 2, 3]
traffic_scenarios = [1]
city_name_list = ['istanbul']

CPLEX_CONF = ['odu', 'odr', 'tdu', 'tdr']
CPLEX_CONF_STR = ['one day 5kWh Battery', 'one day 2.5kWh Battery', 'two days 10kWh Battery', 'two days 5kWh Battery']
MONTHS_OF_A_YEAR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Now', 'Dec']
TRAFFIC_RATE_STR = ['Low', 'Medium', 'High', 'Very High']
