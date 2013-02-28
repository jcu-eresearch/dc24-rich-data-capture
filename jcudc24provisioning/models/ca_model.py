from datetime import date
import colander
from sqlalchemy.ext.declarative import DeclarativeMeta
import sys
from colanderalchemy.types import SQLAlchemyMapping

import logging
import deform
from jcudc24provisioning.views.ca_scripts import fix_schema_field_name, convert_schema

logger = logging.getLogger(__name__)

__author__ = 'casey'

class CAModel(object):
    def __init__(self, appstruct=None, schema=None):
#        if not isinstance(self, DeclarativeMeta): TODO: Why does this not work?
#            raise TypeError("CAModel implementations must subclase SQLALchemy DeclarativeMeta (eg. Base=declarative_base(), class YourModel(CAModel, Base): ...)")

        if not hasattr(self, 'id'):
            raise AttributeError("All CAModel's must have an 'id' unique identifier.")

        if appstruct is not None:
            self.update(appstruct)

        self._schema = schema

    @property
    def schema(self):
        if '_schema' not in locals() or self._schema is None:
            self._schema = convert_schema(SQLAlchemyMapping(type(self)))
        return self._schema

    def dictify(self, schema=None, force_not_empty_lists=False):
        if schema is None:
            schema = self.schema
        return self.convert_sqlalchemy_model_to_data(self, schema=schema, force_not_empty_lists=force_not_empty_lists)

    def update(self, appstruct):
        return self.create_sqlalchemy_model(appstruct, model_object=self) is not None
    
    def _get_field_type(self, field_name, model_object):
        class_manager = model_object._sa_class_manager[field_name]
        parent = getattr(class_manager, 'parententity', getattr(class_manager, '_parententity', None)) # Seems to have either or?
        return parent.columns._data[field_name].type.python_type
#        return model_object._sa_class_manager[field_name]._parententity.columns._data[field_name].type.python_type

    def _get_ca_registry(self, field_name, model_class):
        try:
            ca_registry = None
            if field_name in model_class._sa_class_manager:
                if hasattr(model_class._sa_class_manager[field_name].comparator, 'mapper') and field_name in model_class._sa_class_manager[field_name].comparator.mapper.columns._data:
                    ca_registry = model_class._sa_class_manager[field_name].comparator.mapper.columns._data[field_name]._ca_registry
                elif hasattr(model_class._sa_class_manager[field_name], '_parententity') and field_name in model_class._sa_class_manager[field_name]._parententity.columns._data:
                    ca_registry = model_class._sa_class_manager[field_name]._parententity.columns._data[field_name]._ca_registry
                elif hasattr(model_class._sa_class_manager[field_name], '_parententity') and field_name in model_class._sa_class_manager[field_name]._parententity.relationships._data:
                    ca_registry = model_class._sa_class_manager[field_name]._parententity.relationships._data[field_name].ca_registry
                elif hasattr(model_class._sa_class_manager[field_name], 'property') and hasattr(model_class._sa_class_manager[field_name].property, 'ca_registry'):
                    ca_registry = model_class._sa_class_manager[field_name].property.ca_registry
                else:
                    raise NotImplementedError("ca_registry lookup for this object isn't implemented.")
    #                return None
            return ca_registry
        except Exception as e:
            logger.exception("Exception occurred while getting model's ca_registry: %s" % e)

    def fileupload_to_filehandle(self, field_name, value, model_object):
        try:
            ca_registry = self._get_ca_registry(field_name, self.get_model_class(model_object))
    
            # This isn't a form
            if ca_registry is None:
                return value

            # Handle file uploads
            # If this is a file field
            if 'type' in ca_registry and isinstance(ca_registry['type'], deform.FileData):
                # If this is a new file
                if isinstance(value, dict) and 'preview_url' in value:
                    value = str(value['preview_url'])
    
                # If this is an already selected and uploaded file
                elif isinstance(value, dict) and 'fp' in value and hasattr(value['fp'], 'name'):
                    value = str(value['fp'].name)
    
                # File was previously uploaded and the user just removed it
                else:
                    value = None
    
            return value
    
        except Exception as e:
            logger.exception("Exception occurred while converting file upload to filehandle: %s" % e)

    def normalize_form_value(self, field_name, value, model_object):
        try:
            # Normalise values returned from forms
            if not isinstance(value, list) and not isinstance(value, dict):
                if value == 'false' or (isinstance(getattr(model_object, field_name), bool) and not bool(value)):
                    value = False
                elif value == 'true' or (isinstance(getattr(model_object, field_name), bool) and bool(value)):
                    value = True
                elif value == colander.null or value == 'None' or value == 'colander.null' or isinstance(value, str) and value == '':
#                    field_type = self._get_field_type(field_name, model_object)
#                    if field_type in (int, float, long):
#                        value = 0
#                    else:
                    value = None

                # Best attempt, cast all values to their required type
                if value is not None and isinstance(getattr(model_object, field_name), (int, long, float, str)):
                    value = (type(getattr(model_object, field_name)))(value)
    
            elif (isinstance(value, dict) or value is None):
                value = self.fileupload_to_filehandle(field_name, value, model_object)
    
            return value
        except Exception as e:
            logger.exception("Exception occurred while normalizing model value: %s" % e)

    def get_model_class(self, model_object):
        return model_object._sa_instance_state.class_


    def create_sqlalchemy_model(self, data, model_class=None, model_object=None):
        is_data_empty = True
        if model_object is None and model_class is not None:
            model_object = model_class()

        if model_class is None and model_object is not None:
            model_class = self.get_model_class(model_object)

        if model_class is None or model_object is None:
            raise ValueError("Model class or model object could not be found while creating sqlalchemy model.")

        if data is None or not isinstance(data, dict) or len(data) <= 0:
            return None

        prefix = ''.join(str(x + ":") for x in data.items()[0][0].split(":")[:-1])
        new_model = True
        if model_object.id is not None and model_object.id >= 0:
            new_model = False
        elif prefix + 'id' in data and (isinstance(data[prefix + 'id'], (long, int)) or (isinstance(data[prefix + 'id'], basestring) and data[prefix + 'id'].isnumeric())) and long(data[prefix + 'id']) >= 0:
            new_model = False

        for field_name, value in data.items():
            field_name = fix_schema_field_name(field_name)

            # If this is a grouping - add its fields to the current model_object
            if not hasattr(model_object, field_name) and isinstance(value, dict):
                self.create_sqlalchemy_model(value, model_class=model_class, model_object=model_object)
            elif hasattr(model_object, field_name):
                # Fix form values to be the correct class and type and post formatting (eg. fileupload gets file handle from dict, bool is converted from 'false' to False, etc.).
                value = self.normalize_form_value(field_name, value, model_object)

                if isinstance(getattr(model_object, field_name), list) or isinstance(value, list):
                    # If the value hasn't changed
                    if value is None or value == getattr(model_object, field_name):
                        continue
                    # If all items have been removed
                    if value is None:
                        is_data_empty = False
                        setattr(model_object, field_name, [])
                        continue

                    # Otherwise the list has been changed in some other way
                    # Remove all items from the list, so that any items that aren't there are deleted.
                    old_items = []
                    for i in reversed(range(len(getattr(model_object, field_name, [])))):
                        old_items.append(getattr(model_object, field_name)[i])

                    for item in value:
                        if item is None or item is colander.null or not isinstance(item, dict) or len(item) <= 0:
                            continue

                        if 'schema_select' in item and len(item) == 2:  # This is the custom developed select mapping - flatten the select out
                            method = item.pop('schema_select')
                            item = item.values()[0]

                        current_object = None

                        prefix = ''.join(str(x + ":") for x in item.items()[0][0].split(":")[:-1])

                        # If the item has an id and the id==an item in the model_object, update the model object item instead of creating a new one.
                        if prefix + 'id' in item and (isinstance(item[prefix + 'id'], (long, int)) or (isinstance(item[prefix + 'id'], basestring) and item[prefix + 'id'].isnumeric())):
                            for model_item in old_items:
    #                            print "ID's: " + str(getattr(model_item, 'id', None)) + " : " + str(item['id'])
                                current_object_id = getattr(model_item, 'id', None)
    #                            print (isinstance(current_object_id, (int, long)) or (isinstance(current_object_id, basestring) and current_object_id.isnumeric()))
                                if (isinstance(current_object_id, (int, long)) or (isinstance(current_object_id, basestring) and current_object_id.isnumeric())) and int(getattr(model_item, 'id', None)) == int(item[prefix + 'id']):
                                    current_object = model_item
                                    old_items.remove(current_object)
    #                                print "Current Object: " + str(current_object)
                                    break

                        child_table_object = self.create_sqlalchemy_model(item, model_class=model_object._sa_class_manager[field_name].property.mapper.class_, model_object=current_object)
                        # If the child object has changed
                        if child_table_object is not None:
                            is_data_empty = False

                            # If the child object is new
                            if current_object is None:
                                getattr(model_object, field_name).append(child_table_object) # Add the modified object

                        # If the child object was just updated SQLAlchemy keeps track of the changes internally
#                        elif current_object is not None:
#                            getattr(model_object, field_name).append(current_object) # Re-add the un-modified object

                    # Delete items in the list that were missing from the new data
                    for item in old_items:
                        getattr(model_object, field_name).remove(item)
                        del item
                        is_data_empty = False

                elif isinstance(getattr(model_object, field_name), dict) or isinstance(value, dict):
                    # If the value hasn't been changed

                    if value == getattr(model_object, field_name):
                        continue
                    elif value is None:
                        # If the value is now empty and it was set previously
                        is_data_empty = False
                        setattr(model_object, field_name, None)
                        continue

                    current_object = None
                    if getattr(model_object, field_name) is not None:
                        current_object = getattr(model_object, field_name, None)

                    if not hasattr(model_object._sa_class_manager[field_name].property, 'mapper'):
                        raise AttributeError("Model conversion scripts have an error, trying to generate a model with invalid values.")
                    child_table_object = self.create_sqlalchemy_model(value, model_class=model_object._sa_class_manager[field_name].property.mapper.class_, model_object=current_object)

                    if child_table_object is not None:
                        setattr(model_object, field_name, child_table_object)
                        is_data_empty = False

                else:
                    # If the value hasn't been changed
                    field_type = self._get_field_type(field_name, model_object)
                    if value == getattr(model_object, field_name) or\
                       (field_type in (int, float, long) and (value is None or value==0) and (getattr(model_object, field_name) is None or getattr(model_object, field_name) == 0)):
                        continue

                    # If the value is now empty and it was set previously
                    elif value is None:
                        setattr(model_object, field_name, None)
                        is_data_empty = False
                        continue
                    try:

                        # Don't use default values to determine if the data is a new object.
                        ca_registry = self._get_ca_registry(field_name, model_class)
                        if 'default' not in ca_registry or not value == ca_registry['default'] or not new_model:
                            is_data_empty = False
                        setattr(model_object, field_name, value)

                    except Exception as e:
                        logger.exception("Failed to set model attribute: %s" % field_name)
                        continue


        if is_data_empty:
            return None

        return model_object
    
    def convert_sqlalchemy_model_to_data(self, model, schema=None, force_not_empty_lists=False):
        if schema is None:
            # This will not take groupings into account
            schema = convert_schema(SQLAlchemyMapping(type(model)))

        data = {}
    
        if model is None:
            return data
    
        for node in schema:
            name = fix_schema_field_name(node.name)
    
            if hasattr(model, name):
                value = getattr(model, name, None)
    
                if isinstance(value, date):
                    value = str(value)
    
                if isinstance(value, bool)  and hasattr(node.widget, 'true_val'):
                    if value:
                        value = node.widget.true_val
                    elif hasattr(node.widget, 'false_val'):
                        value = node.widget.false_val
    
                if isinstance(value, list):
                    node_list = []
                    for item in value:
                        node_list.append(self.convert_sqlalchemy_model_to_data(item,  node.children[0], force_not_empty_lists))

                    if force_not_empty_lists and len(value) == 0:
                        node_list.append(self.convert_sqlalchemy_model_to_data(node.children[0]._reg.cls(),  node.children[0], force_not_empty_lists))
    
                    data[node.name] = node_list
                elif isinstance(node.typ, deform.FileData) and value is not None:
                    tempstore = node.widget.tmpstore.tempstore
                    data[node.name] = node.default
                    if value is not None:
                        randid = value.split("/")[-1]
                        for file_uid in tempstore:
                            if 'randid' in tempstore[file_uid] and (tempstore[file_uid]['randid']) == str(randid):
                                data[node.name] = tempstore[file_uid]
                                break
    
                elif len(node.children):
                    data[node.name] = self.convert_sqlalchemy_model_to_data(value,  node, force_not_empty_lists)
    
                elif value is None:
                    data[node.name] = node.default
                else:
                    data[node.name] = value
            elif len(node.children) > 0:
                node_data = self.convert_sqlalchemy_model_to_data(model, node.children, force_not_empty_lists)
    
                # Fix data for select mapping schemas
                if not ':' in node.name:
                    data['schema_select'] = str(getattr(model, 'method_id', None))
    
    
                data[node.name] = node_data
    
        return data

    

