# Solution Space Configuration
NUMBER_OF_SIMULATION_DAY = 365
N_OF_EC = 20
# Battery Panel Sizing Configuration
SOLAR_PANEL_BASE_CONF = 0.2
BATTERY_BASE_CONF = 200
SOLAR_PANEL_INSTANCE_SIZE_CONF = 1
BATTERY_INSTANCE_SIZE_CONF = 1
CC_SIZING_MULTIPLIER_CONF = 2
# Given Data Configuration
city_name_list = ['istanbul']
traffic_rate_list = [2]
# Methods Configuration
method_list_rl = ["Q", "E", "S"]
method_list_static = ["CRAN", "URF1", "URF2", "DRAN"]
method_list_milp = ["TA", "BA"]
#Learning Method Parameters
NUMBER_OF_EPISODES_CONF = 2000
SHOW_EVERY_CONF = 200
LEARNING_RATE_SIZE_CONF = 1
DISCOUNT_SIZE_CONF = 1
# Others
SIM_DEBUG = False
DEBUGGING_ALLOW = False
SECOND_PHASE_UPDATE = False
REWARD_WINDOW_SIZE = 24
