import datetime

import six
import typing

import requests
from uuid import UUID

def _deserialize(data, klass):
    """Deserializes dict, list, str into an object.

    :param data: dict, list or str.
    :param klass: class literal, or string of class name.

    :return: object.
    """
    if data is None:
        return None

    if klass in six.integer_types or klass in (float, str, bool):
        return _deserialize_primitive(data, klass)
    elif klass == object:
        return _deserialize_object(data)
    elif klass == datetime.date:
        return deserialize_date(data)
    elif klass == datetime.datetime:
        return deserialize_datetime(data)
    elif type(klass) == typing.GenericMeta:
        if klass.__extra__ == list:
            return _deserialize_list(data, klass.__args__[0])
        if klass.__extra__ == dict:
            return _deserialize_dict(data, klass.__args__[1])
    else:
        return deserialize_model(data, klass)


def _deserialize_primitive(data, klass):
    """Deserializes to primitive type.

    :param data: data to deserialize.
    :param klass: class literal.

    :return: int, long, float, str, bool.
    :rtype: int | long | float | str | bool
    """
    try:
        value = klass(data)
    except UnicodeEncodeError:
        value = six.u(data)
    except TypeError:
        value = data
    return value


def _deserialize_object(value):
    """Return an original value.

    :return: object.
    """
    return value


def deserialize_date(string):
    """Deserializes string to date.

    :param string: str.
    :type string: str
    :return: date.
    :rtype: date
    """
    try:
        from dateutil.parser import parse
        return parse(string).date()
    except ImportError:
        return string


def deserialize_datetime(string):
    """Deserializes string to datetime.

    The string should be in iso8601 datetime format.

    :param string: str.
    :type string: str
    :return: datetime.
    :rtype: datetime
    """
    try:
        from dateutil.parser import parse
        return parse(string)
    except ImportError:
        return string


def deserialize_model(data, klass):
    """Deserializes list or dict to model.

    :param data: dict, list.
    :type data: dict | list
    :param klass: class literal.
    :return: model object.
    """
    instance = klass()

    if not instance.openapi_types:
        return data

    for attr, attr_type in six.iteritems(instance.openapi_types):
        if data is not None \
                and instance.attribute_map[attr] in data \
                and isinstance(data, (list, dict)):
            value = data[instance.attribute_map[attr]]
            setattr(instance, attr, _deserialize(value, attr_type))

    return instance


def _deserialize_list(data, boxed_type):
    """Deserializes a list and its elements.

    :param data: list to deserialize.
    :type data: list
    :param boxed_type: class literal.

    :return: deserialized list.
    :rtype: list
    """
    return [_deserialize(sub_data, boxed_type)
            for sub_data in data]


def _deserialize_dict(data, boxed_type):
    """Deserializes a dict and its elements.

    :param data: dict to deserialize.
    :type data: dict
    :param boxed_type: class literal.

    :return: deserialized dict.
    :rtype: dict
    """
    return {k: _deserialize(v, boxed_type)
            for k, v in six.iteritems(data)}


def is_valid_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

    Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

    Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

    Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """
    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except:
        return False

    return str(uuid_obj) == uuid_to_test


def _get_variables(file):
    """Obtain MINT variables for a given IO file"""
    params = (
        ('io', file),
        ('endpoint', 'https://endpoint.mint.isi.edu/ds/query'),
    )

    response = requests.get('https://query.mint.isi.edu/api/mintproject/MINT-ModelCatalogQueries/getI_OVariablesAndUnits', params=params)
    variables = response.json()['results']['bindings']

    variables_table = []
    for v in variables:
        e = {'name': v.get('label',{}).get('value'),
             'long_name': v.get('longName',{}).get('value'),
             'description': v.get('description',{}).get('value'),
             'standard_name': v.get('sn',{}).get('value'),
             'standard_name_ontology': '',
             'unit': v.get('unit',{}).get('value'),
             'metadata': {}}
        variables_table.append(e)

    output = {'name': file.split('instance/')[1],
              'variables': variables_table,
              'filetype': '',
              'description': ''}
              
    return output

def _parse_io(io, url, request_headers):
    """Parse MINT input/output object into a dictionary"""
    io_ = io.to_dict()

    # only if ID is a valid UUID4 otherwise skip dataset
    if is_valid_uuid(io_['id']):
        io_['name'] = io_.pop('label')
        io_['filetype'] = io_.pop('has_format')
        io_.pop('type')
        io_.pop('has_dimensionality')

        # query DCAT for variable information related to dataset
        q = {
          "dataset_id": io_['id']
        }

        resp = requests.post(f"{url}/datasets/dataset_variables",
                             headers=request_headers,
                             json=q).json()

        variables = resp['dataset']['variables']

        
        io_.pop('has_presentation')
        io_['variables'] = []
        for v in variables:
            v['name'] = v.pop('variable_name')
            v['id'] = v.pop('variable_id')
            v['metadata'] = v.pop('variable_metadata')
            # TODO: obtain standard name information
            v['standard_name'] = 'TODO'
            io_['variables'].append(v)
        return io_    
    else:
        return None