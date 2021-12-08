DEBUGGING_ALLOW = False
AVERAGE_GIVEN_DATA = False
REINFORCEMENT_ONLINE = True
NUMBER_OF_EPISODES_CONF = 10000
SHOW_EVERY_CONF = 2000
SOLAR_PANEL_INSTANCE_SIZE_CONF = 1
BATTERY_INSTANCE_SIZE_CONF = 1
LEARNING_RATE_SIZE_CONF = 1
DISCOUNT_SIZE_CONF = 1
city_name_list = ['stockholm', 'cairo', 'jakarta', 'istanbul']
traffic_rate_list = [0.5, 1, 2]
method_list_rl = ["Q", "S"]

REWARD_WINDOW_SIZE = 25
print("CONFIGURATION FILE::{}\t AVG:{}".format(__file__, AVERAGE_GIVEN_DATA), flush=True)
