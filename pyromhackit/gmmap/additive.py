from abc import ABCMeta, abstractmethod


class Additive(metaclass=ABCMeta):
    @abstractmethod
    def __add__(self, operand):
        return NotImplementedError()

    @abstractmethod
    def __radd__(self, operand):
        return NotImplementedError()
