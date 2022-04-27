"""Main Module for Q Learning Solution in RLDFS ICC Paper.

"""
from collections import defaultdict
from datetime import datetime
from multiprocessing import Process

from ag_cloud import *
from env_top import *


class Logger:
    """
    Snapshot for the reward, q_table and battery information per episodes according to "configuration -> SHOW_EVERY_CONF"
    """

    def __init__(self, learning_method, learning_rate, discount, sp, batt, city, traffic_rate):
        self.conf_name = "{}_{}_{}_{}_{}_{}_{}".format(learning_method, learning_rate, discount, sp, batt, city, traffic_rate)
        self.ep_rewards_list = [[] for x in range(N_OF_CLOUD)]
        self.total_reward_in_an_episode = [0 for x in range(N_OF_CLOUD)]
        self.aggr_ep_rewards = [{'ep': [], 'avg': [], 'min': [], 'max': []} for x in range(N_OF_CLOUD)]
        # self.highest_q_table = (-1, VERY_BIG_NEGATIVE_VALUE, [None for x in range(N_OF_CLOUD)])
        # self.q_table_history = [(-1, VERY_BIG_NEGATIVE_VALUE, [None for x in range(N_OF_CLOUD)])]
        # self.battery_history = [(-1, VERY_BIG_NEGATIVE_VALUE, [None for x in range(N_OF_CLOUD)])]
        self.q_table_history = []
        self.battery_history = []
        # --------- DEBUG ------------
        if SIM_DEBUG:
            self.ret_record = np.array([[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(N_OF_CLOUD)])
            self.urf_record = np.array([[0 for x in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY)] for x in range(N_OF_EC)])
        # --------- DEBUG ------------

    def log_the_episode_table_and_battery(self, episode_record_number, ag_cloud, env):
        end_of_ep_q_tables = []
        end_of_ep_battery_history = []
        print("episode_record_number:{}".format(episode_record_number))
        for ec_index in range(N_OF_CLOUD):
            end_of_ep_q_tables.append(ag_cloud[ec_index].q_table)
            end_of_ep_battery_history.append(env.battery[ec_index].fm.history)
        # --------- DEBUG ------------
        # count_urf1 = 0
        # urf_1 = []
        # for t in range(24):
        #     if ag_cloud[0].q_table[t][0] < ag_cloud[0].q_table[t][1]:
        #         count_urf1 += 1
        #         urf_1.append(t)
        # print("count_urf1:{} t:{}".format(count_urf1, urf_1))
        # print(ag_cloud[0].q_table)
        # --------- DEBUG ------------
        obj_func = env.calculate_one_year_obj_func()
        self.q_table_history.append((episode_record_number, obj_func, end_of_ep_q_tables))
        self.battery_history.append((episode_record_number, obj_func, end_of_ep_battery_history))


    def add_the_episode_reward(self, episode, ag_cloud, env):
        for ec_index in range(N_OF_CLOUD):
            self.ep_rewards_list[ec_index].append(self.total_reward_in_an_episode[ec_index])
            self.total_reward_in_an_episode[ec_index] = 0
            episode_record_number = episode + 1
            if episode_record_number % LearningParameters.SHOW_EVERY == 0:
                self.get_snapshot_of_rewards(episode_record_number, self.ep_rewards_list[ec_index], ec_index)
                if ec_index == CC_INDEX:
                    self.log_the_episode_table_and_battery(episode_record_number, ag_cloud, env)
                    self.save_log()

    def get_snapshot_of_rewards(self, episode, ep_rewards, ec_index):
        average_reward = sum(ep_rewards[-LearningParameters.SHOW_EVERY:]) / len(ep_rewards[-LearningParameters.SHOW_EVERY:])
        min_reward = min(ep_rewards[-LearningParameters.SHOW_EVERY:])
        max_reward = max(ep_rewards[-LearningParameters.SHOW_EVERY:])
        self.aggr_ep_rewards[ec_index]['ep'].append(episode)
        self.aggr_ep_rewards[ec_index]['avg'].append(average_reward)
        self.aggr_ep_rewards[ec_index]['min'].append(min_reward)
        self.aggr_ep_rewards[ec_index]['max'].append(max_reward)
        if ec_index == CC_INDEX:
            print("Episode: {} Date:{} :: Conf: {} ".format(episode, datetime.now(), self.conf_name))
            print(f"Avg:{average_reward} Min:{min_reward} Max:{max_reward}", flush=True)
            if SIM_DEBUG:
                # --------- DEBUG ------------
                ret1 = np.copy(self.ret_record)
                urf1 = np.copy(self.urf_record)
                print("episode:{} ret1:{} urf1:{}".format(episode, sum(ret1), sum(urf1)))
                self.urf_record = np.zeros_like(self.urf_record)
                # --------- DEBUG ------------

    def save_log(self):
        snapshot = Snapshot()
        file_name = "conf_{}".format(self.conf_name)
        snapshot.save_rewards(self.aggr_ep_rewards[0], file_name)
        snapshot.save_battery_history(self.battery_history, file_name)
        snapshot.save_qtables(self.q_table_history, file_name)

    def get_q_tables(self, type, file_name):
        snapshot = Snapshot()
        if file_name == None:
            file_name = "conf_{}".format(self.conf_name)
        q_table_list = snapshot.load_qtables("{}".format(file_name))
        if type == "last":
            ep, rew, q_tables = q_table_list[-1]
        else:
            ep, rew, q_tables = max(q_table_list, key=lambda item: item[1])
        print("Q_END :: CONF:{} EP:{} REW:{} ".format(self.conf_name, ep, rew))
        return q_tables


class QLearning:
    """
    A top class responsible to implement ML algorithms

    Attributes
    ----------
    logger = logging the rewards/battery/q_table
    env_cloud = environment object
    agent_cloud[ec_index]  = ec/cc agent objects
    learning parameters = testing q-learning parameters with different learning parameters
    """
    agent_cloud = [None for x in range(N_OF_CLOUD)]

    def __init__(self, learning_method, learning_rate, discount, conf, city, traffic_rate):
        print("Learning_Method:{} Learning Rate:{} Discount:{} City:{} Traffic Rate:{}".format(learning_method,
                                                                                               learning_rate, discount, city, traffic_rate))
        print("Sizing:{}".format(conf))
        self.sp = conf[0][0]
        self.batt = conf[0][1]
        self.city = city
        self.traffic_rate = traffic_rate
        self.logger = Logger(learning_method, learning_rate, discount, self.sp, self.batt, self.city, self.traffic_rate)
        self.learning_method = learning_method
        self.learning_rate = learning_rate
        self.discount = discount
        self.env_cloud = CloudEnvironment(self.city, self.traffic_rate)
        for ec_index in range(N_OF_CLOUD):
            if ec_index == CC_INDEX:
                self.agent_cloud[ec_index] = CloudCC(conf[CC_INDEX][1], learning_method)
            else:
                self.agent_cloud[ec_index] = CloudEC(self.batt, learning_method)

    def update_q_tables(self, type, file_name=None):
        # using a previously created q_table to initialize the q table
        q_tables = self.logger.get_q_tables(type, file_name)
        print("Q_Tables are updated from file:{}".format(file_name))
        for ec_index in range(N_OF_CLOUD):
            self.agent_cloud[ec_index].q_table = q_tables[ec_index]

    def update_the_actions_for_milp(self, renewable_energy_ratio, number_of_active_urf):
        # getting the actions from milp solution
        self.renewable_energy_ratio = renewable_energy_ratio
        self.number_of_active_urf = number_of_active_urf

    # @PerformanceCalculator
    def __new_q_calculation(self, ec_index, new_state, current_state, action, reward, action_2, epsilon):
        # value iteration for different q learning methods
        if self.learning_method == "E":  # expected sarsa
            act_size = self.agent_cloud[ec_index].actions.size
            expected_q = 0
            q_max = np.max(self.agent_cloud[ec_index].q_table[new_state, :])
            greedy_actions = 0
            for i in range(act_size):
                if self.agent_cloud[ec_index].q_table[new_state][i] == q_max:
                    greedy_actions += 1

            non_greedy_action_probability = epsilon / act_size
            greedy_action_probability = ((1 - epsilon) / greedy_actions) + non_greedy_action_probability

            for i in range(act_size):
                if self.agent_cloud[ec_index].q_table[new_state][i] == q_max:
                    expected_q += self.agent_cloud[ec_index].q_table[new_state][i] * greedy_action_probability
                else:
                    expected_q += self.agent_cloud[ec_index].q_table[new_state][i] * non_greedy_action_probability
        elif self.learning_method == "S":  # sarsa
            expected_q = self.agent_cloud[ec_index].q_table[new_state][action_2]
        else:  # classic q_learning
            expected_q = np.max(self.agent_cloud[ec_index].q_table[new_state])
        current_q = self.agent_cloud[ec_index].q_table[current_state[ec_index]][action]
        new_q = (1 - self.learning_rate) * current_q + self.learning_rate * (reward + self.discount * expected_q)
        self.agent_cloud[ec_index].q_table[current_state[ec_index]][action] = new_q

    # @PerformanceCalculator
    def __choose_the_action(self, ec_index, current_state, epsilon):
        if np.random.random() > epsilon:
            action = np.argmax(self.agent_cloud[ec_index].q_table[current_state])
            # action = np.argmin(self.agent_cloud[ec_index].q_table[current_state])
            # action = np.random.randint(0, self.agent_cloud.actions.size)
        else:
            action = np.random.randint(0, self.agent_cloud[ec_index].actions.size)
        return action

    # @PerformanceCalculator
    def __step_for_each_agent(self, ec_index, current_state, epsilon):
        # get the action
        action = self.__choose_the_action(ec_index, current_state[ec_index], epsilon)
        # disaggregate the action
        renewable_energy_ratio, number_of_active_urf = self.agent_cloud[ec_index].disaggr_action(action)
        if self.learning_method in method_list_milp:
            # for milp solution we are getting the actions from the previously recorded file
            t = self.env_cloud.time_machine.get_hour()
            number_of_active_urf = self.number_of_active_urf[ec_index][t]
            renewable_energy_ratio = self.renewable_energy_ratio[ec_index][t]
        # --------- DEBUG ------------
        if SIM_DEBUG:
            renewable_energy_ratio = 1.0
            t = self.env_cloud.time_machine.get_hour()
            if ec_index != CC_INDEX:
                self.logger.urf_record[ec_index][t] += number_of_active_urf
            self.logger.ret_record[ec_index][t] += renewable_energy_ratio
        # --------- DEBUG ------------
        # one step in environment due to the action, then get the new states and reward as return values
        remaining_energy, time_slot, traffic_load, reward = self.env_cloud.step(number_of_active_urf, renewable_energy_ratio, ec_index)
        # aggregate the states
        new_state = self.agent_cloud[ec_index].get_discrete_state(remaining_energy, time_slot, traffic_load)
        # choose another action for SARSA method
        action_2 = self.__choose_the_action(ec_index, new_state, epsilon)
        # value iteration
        self.__new_q_calculation(ec_index, new_state, current_state, action, reward, action_2, epsilon)
        current_state[ec_index] = new_state
        return reward

    def run_one_year(self, epsilon, episode):
        # an episode equals to one year run in our problem
        # initializing the environment in the beginning of the episode
        current_state = [-1 for x in range(N_OF_CLOUD)]
        remaining_energy, time_slot, traffic_load = self.env_cloud.reset(self.sp, self.batt)
        for ec_index in range(N_OF_CLOUD):
            current_state[ec_index] = self.agent_cloud[ec_index].get_discrete_state(remaining_energy, time_slot,
                                                                                    traffic_load)
        day = 0
        while day < NUMBER_OF_SIMULATION_DAY:
            # each step equals to one hour in our problem
            for ec_index in range(N_OF_CLOUD):
                # each cloud has their own agent to make a decision (multi-agent solution)
                reward = self.__step_for_each_agent(ec_index, current_state, epsilon)
                self.logger.total_reward_in_an_episode[ec_index] += reward
            # increase the hour
            self.env_cloud.time_machine.next_hour()
            day = self.env_cloud.time_machine.get_day_of_the_year()

    def run_one_year_dqn(self, epsilon, episode):
        remaining_energy, traffic_load, time_slot = self.env_cloud.reset(self.sp, self.batt)
        current_state = self.agent_dqn.get_discrete_state(remaining_energy, traffic_load, time_slot)
        done = False
        day = 0
        while day < NUMBER_OF_SIMULATION_DAY:

            action = self.agent_dqn.act(current_state)
            renewable_energy_ratio, number_of_active_urf = self.env_cloud.disaggr_action(action)
            remaining_energy, traffic_load, time_slot, reward = self.env_cloud.step_dqn(number_of_active_urf,
                                                                                        renewable_energy_ratio)
            new_state = self.agent_dqn.get_discrete_state(remaining_energy, traffic_load, time_slot)

            # add to experience memory
            self.agent_dqn.remember(current_state, action, reward, new_state, done)

            current_state = new_state
            self.logger.total_reward_in_an_episode[0] += reward
            if done:
                # update target model if goal is found
                self.agent_dqn.update_target_model()
                # print("episode: {}/{}, score: {}, e: {:.2}"
                #       .format(e, EPISODES, time, self.agent_dqn.epsilon))
                # break

            self.env_cloud.time_machine.next_hour()
            day = self.env_cloud.time_machine.get_day_of_the_year()

    def main_loop(self):
        # Running each episode with epsilon greedy policy
        epsilon = LearningParameters.initial_epsilon()
        if "DQN" in method_list_rl:
            self.agent_dqn = DQNAgent(self.env_cloud.state_space_size, self.env_cloud.action_space_size)
        for episode in range(LearningParameters.NUMBER_OF_EPISODES):
            self.run_one_year_dqn(epsilon, episode)
            epsilon = LearningParameters.decrement_epsilon(epsilon)
            self.logger.add_the_episode_reward(episode, self.agent_cloud, self.env_cloud)
        self.logger.save_log()
        self.env_cloud.close()


def q_learning_runner(learning_method, learning_rate, discount, conf, city, traffic_rate):
    # Generating QLearning and updating the q table if we use a pregenerated table
    ql = QLearning(learning_method, learning_rate, discount, conf, city, traffic_rate)
    if SECOND_PHASE_UPDATE:
        # ql.update_q_tables("last", "conf_pre_phase")
        ql.update_q_tables("last")
    ql.main_loop()


class DiagnoseBattery():
    # Parsing Battery Logs
    def __init__(self):
        default_val = {}
        self.snapshot = Snapshot()
        self.unstored_en = defaultdict(lambda: 0, default_val)
        self.fossil_cons = defaultdict(lambda: 0, default_val)
        self.ren_en = defaultdict(lambda: 0, default_val)
        self.obj_func = defaultdict(lambda: 0, default_val)
        self.learning_method_list = method_list_rl + method_list_static + method_list_milp
        # self.learning_method_list = method_list_static
        # self.learning_method_list = method_list_rl + method_list_static
        self.DAILY_TS = False
        self.TS = False
        if self.DAILY_TS:
            self.file_name_ext = "daily_ts"
        elif self.TS:
            self.file_name_ext = "ts"
        else:
            self.file_name_ext = "sizing"

    def _get_data_for_daily_dist(self, file_name, log_name):
        print("battery history log_name:{}".format(log_name))
        his = self.snapshot.load_battery_history(file_name)
        bh = his[0][2]
        for cloud_index in range(N_OF_CLOUD):
            for day in range(NUMBER_OF_SIMULATION_DAY):
                for time_slot in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    # if cloud_index == CC_INDEX:
                    #     log_name_2 = log_name + "_CU"
                    # else:
                    #     log_name_2 = log_name + "_DU"
                    log_name_2 = log_name + "_{}".format(time_slot)
                    time_index = day * NUMBER_OF_TIME_SLOT_IN_ONE_DAY + time_slot
                    self.fossil_cons[log_name_2] += bh[cloud_index][time_index][3]  # fossil
                    self.ren_en[log_name_2] += bh[cloud_index][time_index][4]  # ren_en
                    self.unstored_en[log_name_2] += bh[cloud_index][time_index][5]  # unstored_en
                    self.obj_func[log_name_2] += bh[cloud_index][time_index][3] * PowerCons.ELEC_PRICE[time_slot]

    def _get_data_for_each_conf(self, file_name, log_name):
        print("battery history log_name:{}".format(log_name))
        his = self.snapshot.load_battery_history(file_name)
        bh = his[0][2]
        for cloud_index in range(N_OF_CLOUD):
            for day in range(NUMBER_OF_SIMULATION_DAY):
                for time_slot in range(NUMBER_OF_TIME_SLOT_IN_ONE_DAY):
                    # log_name_2 = log_name + "_{}_{}".format(cloud_index, time_slot)
                    if cloud_index == CC_INDEX:
                        log_name_2 = log_name + " CC".format(cloud_index)
                    else:
                        log_name_2 = log_name + " EC".format(cloud_index)
                    log_name_2 = log_name
                    time_index = day * NUMBER_OF_TIME_SLOT_IN_ONE_DAY + time_slot
                    self.fossil_cons[log_name_2] += bh[cloud_index][time_index][3]  # fossil
                    self.ren_en[log_name_2] += bh[cloud_index][time_index][4]  # ren_en
                    self.unstored_en[log_name_2] += bh[cloud_index][time_index][5]  # unstored_en
                    self.obj_func[log_name_2] += bh[cloud_index][time_index][3] * PowerCons.ELEC_PRICE[time_slot]

    def start(self):
        learning_rate = LearningParameters.LEARNING_RATE_BASE
        discount = LearningParameters.DISCOUNT_BASE
        for conf in PowerCons.get_solar_panel_and_battery_for_each_cloud():
            sp = conf[0][0]
            batt = conf[0][1]
            for city in city_name_list:
                for traffic_rate in traffic_rate_list:
                    for learning_method in self.learning_method_list:
                        conf_name = "{}_{}_{}_{}_{}_{}_{}".format(learning_method, learning_rate, discount,
                                                                  sp, batt, city, traffic_rate)
                        log_name = "{}_{}_{}_{}_{}".format(sp, batt, learning_method, city, traffic_rate)
                        file_name = "conf_{}".format(conf_name)
                        if self.DAILY_TS:
                            self._get_data_for_daily_dist(file_name, log_name)
                        else:
                            self._get_data_for_each_conf(file_name, log_name)

    def record_to_file(self):
        self.snapshot.save_rewards(dict(self.obj_func), "obj_func_{}".format(self.file_name_ext))
        self.snapshot.save_rewards(dict(self.fossil_cons), "fossil_cons_{}".format(self.file_name_ext))
        self.snapshot.save_rewards(dict(self.ren_en), "ren_en_{}".format(self.file_name_ext))
        self.snapshot.save_rewards(dict(self.unstored_en), "unstored_en_{}".format(self.file_name_ext))

    def print(self):
        print("{:30}{:10}{:10}{:10}{:10}".format("METHOD", "FOSSIL", "RENEWABLE", "WASTED", "OBJ_FUNC"))
        counter = 0
        for key, val in self.fossil_cons.items():
            if counter % len(self.learning_method_list) == 0:
                print("------------------------------------------")
            counter += 1
            print("{:30}{:<10.0f}{:<10.0f}{:<10.0f}{:<10.0f}".format(key,
                                                                     self.fossil_cons[key],
                                                                     self.ren_en[key],
                                                                     self.unstored_en[key],
                                                                     self.obj_func[key]))


def reinforcement_online():
    # Testing the q learning and milp solutions by running them for one year
    record_reward = dict()
    epsilon = 0  # always choose the argmax
    episode = 0
    q_table_type = "last"
    # q_table_type = "max"
    snapshot = Snapshot()
    learning_method_list = method_list_rl + method_list_milp + method_list_static
    # learning_method_list = method_list_rl
    # learning_method_list = method_list_rl + method_list_static
    learning_rate = LearningParameters.LEARNING_RATE_BASE
    discount = LearningParameters.DISCOUNT_BASE
    for learning_method in learning_method_list:
        for city in city_name_list:
            for traffic_rate in traffic_rate_list:
                for conf in PowerCons.get_solar_panel_and_battery_for_each_cloud():
                    ql = QLearning(learning_method, learning_rate, discount, conf, city, traffic_rate)
                    if learning_method in method_list_rl:
                        ql.update_q_tables(q_table_type)
                    if learning_method in method_list_milp:
                        actions = snapshot.load_actions("milp")
                        act_conf_index = "{}_{}_{}_{}_{}".format(conf[0][0], conf[0][1], learning_method,
                                                                 traffic_rate, city)
                        renewable_energy_ratio, number_of_active_urf = actions[act_conf_index]
                        ql.update_the_actions_for_milp(renewable_energy_ratio, number_of_active_urf)
                    ql.run_one_year(epsilon, episode)
                    episode_record_number = 0
                    if SIM_DEBUG:
                        # --------- DEBUG ------------
                        ret1 = np.copy(ql.logger.ret_record)
                        urf1 = np.copy(ql.logger.urf_record)
                        print("ret1:{}\n urf1:{}".format(ret1, urf1))
                        # --------- DEBUG ------------
                    ql.logger.log_the_episode_table_and_battery(episode_record_number, ql.agent_cloud, ql.env_cloud)
                    ql.logger.save_log()
                    sp = conf[0][0]
                    batt = conf[0][1]
                    dict_key_prefix = "sp:{}_batt:{}_ts:{}_city:{}".format(sp, batt, traffic_rate, city)
                    dict_key = dict_key_prefix
                    record_reward[dict_key] = ql.env_cloud.calculate_one_year_obj_func()
        file_name = "one_year_sim_{}".format(learning_method)
        if AVERAGE_GIVEN_DATA:
            file_name = "{}_avg".format(file_name)
        snapshot.save_rewards(record_reward, file_name)


if __name__ == '__main__':
    random.seed(8)  # same seed:: battery and solar panel sizing
    if REINFORCEMENT_ONLINE:
        # Testing the q learning and milp solutions by running them for one year
        reinforcement_online()
        db = DiagnoseBattery()
        db.start()
        db.print()
        db.record_to_file()
        sys.exit()
    print("Reinforcement starts:{}".format(datetime.now()))
    # **************************************** RL RUN  ****************************************
    multi_process = False
    if multi_process:
        processes = []
        for city in city_name_list:
            for traffic_rate in traffic_rate_list:
                for conf in PowerCons.get_solar_panel_and_battery_for_each_cloud():
                    for learning_rate, discount in LearningParameters.get_rate_and_discount():
                        for lm in method_list_rl:
                            processes.append(Process(target=q_learning_runner, args=(lm, learning_rate, discount, conf,
                                                                                     city,
                                                                                     traffic_rate)))
        for p in processes:
            p.start()
        for p in processes:
            p.join()
    else:
        learning_rate = LearningParameters.LEARNING_RATE_BASE
        discount = LearningParameters.DISCOUNT_BASE
        for city in city_name_list:
            for traffic_rate in traffic_rate_list:
                for conf in PowerCons.get_solar_panel_and_battery_for_each_cloud():
                    for learning_rate, discount in LearningParameters.get_rate_and_discount():
                        for lm in method_list_rl:
                            q_learning_runner(lm, learning_rate, discount, conf, city, traffic_rate)

    print("Running is completed:{}".format(datetime.now()))
    sys.exit()
