# coding:utf-8
import random
class A:
    def __init__(self):
        self.qi = 1
        self.yuan = 2

    @staticmethod
    def make():
        print(self.qi)
        print(self.wang)

    def create(self):
        self.wang = 3
        self.make()

current_filename = str(111) + "_" + str("qqqq") + "_" + "1111" + \
                   "_" + str(random.randint(1000000, 9999999)) + ".xls.tmp"

print(current_filename)
