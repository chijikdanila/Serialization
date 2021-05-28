from json import JsonSerializer
from pickle import PickleSerializer


class Fabric:
    @staticmethod
    def create_serializer(string):
        if string == "Json":
            return JsonSerializer
        elif string == "Pickle":
            return PickleSerializer
        else:
            return None
