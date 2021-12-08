"""Using for tests.

"""
from helpers import *

energy_prices_per_hour = [0.29] * 6 + [0.46] * 11 + [0.70] * 5 + [0.29] * 2

if __name__ == '__main__':
    print("Qlearning starts...")
    DAY = 18
    snapshot = Snapshot()
    battery_history = [None for x in range(N_OF_CLOUD)]
    battery_history_filtered = [[None for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(N_OF_CLOUD)]
    cost_each_slot = [[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(N_OF_CLOUD)]
    cost_each_cloud = [0 for x in range(N_OF_CLOUD)]
    for i in range(N_OF_CLOUD):
        battery_history[i] = snapshot.load_battery_history("ec_index_{}".format(i))
    for i in range(N_OF_CLOUD):
        for j in range(24):
            history_index = j + DAY * NUMBER_OF_TIME_SLOT_IN_ONE_DAY
            battery_history_filtered[i][j] = battery_history[i][history_index]
            cost_each_slot[i][j] = battery_history[i][history_index][3] * energy_prices_per_hour[j]
    for i in range(N_OF_CLOUD):
        for j in range(24):
            cost_each_cloud[i] += cost_each_slot[i][j]
    for i in range(N_OF_CLOUD):
        print("EC:{} Cost:{}".format(i, cost_each_cloud[i]))
    print("Total Cost:{}".format(sum(cost_each_cloud)))
