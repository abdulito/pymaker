__author__ = 'abdul'

from pymaker.maker import resolve_class, GenericDocObject, Maker
from bson import DBRef

###############################################################################
# ObjectCollection
###############################################################################
class ObjectCollection:

    ###########################################################################
    def __init__(self, collection, clazz=None, type_bindings=None):
        self.collection = collection
        self.maker =  Maker(type_bindings=type_bindings,
            default_type=clazz,
            object_descriptor_resolver=self)
        self.database = collection.database
        self.name = collection.name

    ###########################################################################
    # Object descriptor Resolver implementations
    ###########################################################################


    ###########################################################################
    def is_datum_descriptor(self, value):
        return type(value) is DBRef

    ###########################################################################
    def resolve_datum_descriptor(self, desc):
        db_ref = desc
        ref_collection_name = db_ref.collection
        ref_collection = self.database[ref_collection_name]
        return ref_collection.find_one({"_id": db_ref.id})

    ###########################################################################
    # queries
    ###########################################################################
    def find(self, query=None, sort=None, limit=None):
        if query is None or (query.__class__ == dict):
            result = self.find_iter( query, sort, limit )
            # TODO: this is bad for large result sets potentially
            return [ d for d in result ]
        else:
            return self.find_one({ "_id" : query }, sort=sort)

    ###########################################################################
    def find_iter(self, query=None, sort=None, limit=None):
        if query is None or (query.__class__ == dict):
            if limit is None:
                documents = self.collection.find(query, sort=sort)
            else:
                documents = self.collection.find(query, sort=sort, limit=limit)

            for doc in documents:
                yield self.make_obj( doc )
        else:
            # assume query is _id and do _id lookup
            yield self.find_one({ "_id" : query }, sort=sort)

    ###########################################################################
    def find_one(self, query=None, sort=None):
        result = self.collection.find_one(query, sort=sort)
        return self.make_obj( result )

    ###########################################################################
    def find_and_modify(self, query=None, update=None):
        result = self.collection.find_and_modify(query=query, update=update)
        return self.make_obj(result)

    ###########################################################################
    def save_document(self, document):
        self.collection.save(document)

    ###########################################################################
    def make_obj( self, doc ):
        return self.maker.make(doc)

    ###########################################################################
    def insert(self, object):
        pass

    ###########################################################################
    def save(self, object):
        pass

    ###########################################################################
    def remove(self, object):
        pass