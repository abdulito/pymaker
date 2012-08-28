__author__ = 'abdul'


from pymaker.maker import o
####################################
class Person():
    first_name = None
    last_name = None
####################################


obj =  o({"_type":"maker_examples.Person",
                   "first_name" : "Abdul",
                   "last_name": "",
                   "kosss": 1})

print obj
