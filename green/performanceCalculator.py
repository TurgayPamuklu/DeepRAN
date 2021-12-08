"""performanceCalculator Module.
An Observer to monitoring the performance of algorithms for Journal 1.

"""

import functools
import time

__author__ = 'turgay.pamuklu'


class Observer():
    _observers = []

    def __init__(self):
        self._observers.append(self)
        self._observables = {}

    def observe(self, event_name, callback):
        self._observables[event_name] = callback


class Event():
    def __init__(self, name, data, autofire=True):
        self.name = name
        self.data = data
        if autofire:
            self.fire()

    def fire(self):
        for observer in Observer._observers:
            if self.name in observer._observables:
                observer._observables[self.name](self.data)


class _PerformanceCalculator(Observer):
    class_name = None

    def __init__(self, func):
        self.func = func
        self.delta = 0
        Observer.__init__(self)
        self.observe('print performance results', self.print_delta)
        self.number_of_calling = 0

    def __call__(self, *args):
        self.increase_number_of_calling()
        return self.function_time_calculator(*args)

    def increase_number_of_calling(self):
        self.number_of_calling += 1

    def function_time_calculator(self, *args):
        start_time = time.clock()
        res = self.func(*args)
        self.delta += time.clock() - start_time
        self.class_name = args[0]
        return res

    def __bs_capacity_checker(self, fossil_object):
        for r in fossil_object.remaining_bs_capacity:
            if r > 0.8:
                raise Exception("Aieee SW BUG!");

    def bs_capacity_checker(self, *args):
        res = self.func(*args)
        self.__bs_capacity_checker(args[0])
        return res

    def print_delta(self, data):
        print("class_name::{} func::{} delta:{} number_of_calling:{}").format(self.class_name, self.func, self.delta, self.number_of_calling)


def PerformanceCalculator(func):
    o = _PerformanceCalculator(func)

    @functools.wraps(func)
    def wrapper(*args):
        return o(*args)

    return wrapper


class Singleton:
    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


@Singleton
class GlobalVariablesForPerformanceCalculator:
    def __init__(self):
        self.enable_print = False

    def is_enable_print(self):
        return self.enable_print

    def set_enable_print(self):
        self.enable_print = True

    def clean_enable_print(self):
        self.enable_print = True
