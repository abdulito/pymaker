import inspect
import json
import re

from bson import json_util, ObjectId
from datetime import datetime, date

####  CONSTANTS

TYPE_FIELD = '_type'

###############################################################################
# Maker Exception class
###############################################################################
class MakerException(Exception):
    def __init__(self, message,cause=None):
        self.message  = message
        self.cause = cause

    def __str__(self):
        return self.message

###############################################################################
def resolve_class(kls):
    try:
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__( module )
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m
    except Exception, e:
        raise MakerException("Cannot resolve class '%s'. Cause: %s" % (kls, e))

###############################################################################

class Maker():
    ###########################################################################
    def __init__(self,
                 type_bindings=None,
                 default_type=None,
                 object_descriptor_resolver=None):

        self.type_bindings = type_bindings
        self.default_type = default_type or GenericDocObject
        self.object_descriptor_resolver = object_descriptor_resolver

        self.ignore_fields = []

    ###########################################################################
    def make(self, datum):

        if datum is None:
            return None

        # primitive types
        if isinstance(datum, (str, unicode, bool,
                              int, long, float, complex,
                              date, datetime, ObjectId)):
            return datum

        if (inspect.isroutine(datum) or
            inspect.isclass(datum) or
            inspect.ismodule(datum)):
            return datum

        # lists
        if isinstance(datum, list):
            return self._make_list(datum)

        return self._make_object(datum)

    ###########################################################################
    def _make_list(self, datum):
        return map(lambda elem: self.make(elem), datum)

    ###########################################################################
    def _make_object(self, datum):

        desc_resolver = self.object_descriptor_resolver
        if desc_resolver and desc_resolver.is_datum_descriptor(datum):
            datum = desc_resolver.resolve_datum_descriptor(datum)

        # instantiate object
        result = self.instantiate(datum)

        # define properties
        for key, value in datum.items():
            if (key not in self.ignore_fields and
                key != TYPE_FIELD):
                prop_name = self.resolve_property_name(key)
                prop_val = self.make(value)

                self._set_object_property(result, prop_name, prop_val)

        return result

    ###########################################################################
    def instantiate(self, datum):

        obj_type = GenericDocObject

        if TYPE_FIELD in datum :
            type_name = datum[TYPE_FIELD]
            if isinstance(type_name, (str, unicode)):
                obj_type = self.resolve_type(type_name)
                if not obj_type:
                    raise Exception("Could not resolve _type %s" % type_name)
            elif inspect.isclass(type_name):
                obj_type = type_name
            else:
                raise Exception("Invalid _type value '%s'. _type can "
                                "be a string or a class" % type_name)

        return obj_type()

    ###########################################################################
    def _set_object_property(self, obj, property, value):
        setattr(obj, property, value)

    ###########################################################################
    def resolve_type(self, type_name):
        if self.type_bindings and type_name in self.type_bindings:
            return resolve_class(self.type_bindings[type_name])
        else:
            return resolve_class(type_name)

    ###########################################################################
    def resolve_property_name(self, datum_prop_name):
        # TODO use a mapping
        return un_camelcase(datum_prop_name)

###############################################################################
def un_camelcase(property_name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', property_name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

###############################################################################
# GenericDocObject
###############################################################################
class GenericDocObject(object):

    ###########################################################################
    def __init__(self, document={}):
        self.__dict__['_document'] = document

    ###########################################################################
    def __getattr__(self, name):
        if self._document.has_key(name):
            return self._document[name]

    ###########################################################################
    def has_key(self, name):
        return self._document.has_key(name)

    ###########################################################################
    def __setattr__(self, name, value):
        if hasattr(getattr(self.__class__, name, None), '__set__'):
            # THANK YOU http://bit.ly/HOTMsT
            return object.__setattr__(self, name, value)
        self._document[name] = value

    ###########################################################################
    def __delattr__(self, name):
        if hasattr(getattr(self.__class__, name, None), '__delete__'):
            # THANKS AGAIN http://bit.ly/HOTMsT
            return object.__delattr__(self, name)
        del self._document[name]

    ###########################################################################
    def __getitem__(self, name):
        return self.__getattr__(name)

    ###########################################################################
    def __setitem__(self, name, value):
        return self.__setattr__(name, value)

    ###########################################################################
    def __delitem__(self, name):
        return self.__delattr__(name)

    ###########################################################################
    def __contains__(self, name):
        return self.has_key(name)

    ###########################################################################
    def __str__(self):
        return document_pretty_string(self._document)

    ###########################################################################
    def __repr__(self):
        return self._document.__repr__()

    ###########################################################################
    def items(self):
       return  dict((key, self[key]) for key in self._document.keys()).items()

###############################################################################
# other helpful utilities... okay, just document_pretty_string()
###############################################################################
def document_pretty_string(document):
    return json.dumps(document, indent=4, default=json_util.default)

###############################################################################
MAKER = Maker()

def o(datum):
    return MAKER.make(datum)