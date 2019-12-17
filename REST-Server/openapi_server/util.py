import datetime

import six
import typing

import requests
import json
from uuid import UUID

from collections import OrderedDict

import mint_client
from mint_client.rest import ApiException

from shapely.geometry import Point
import geopandas as gpd
import numpy as np
from osgeo import gdal
from osgeo import gdalconst
import logging

logging.basicConfig(level=logging.INFO)   

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

def format_stringed_array(str_arr):
    return str_arr.replace("['",'').replace("']",'')

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

def _get_model(ModelName, MINTconfiguration, MINTusername):
    configuration = MINTconfiguration
    username = MINTusername

    try:
        api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
        api_response = api_instance.get_model(ModelName, username=username)
        model = {
                'name': api_response.id,
                'label': api_response.label,
                'description': api_response.description,
                'maintainer': '',
                'category': api_response.has_model_category,
                'versions': [v['id'] for v in api_response.has_software_version]
        }
        return model
    except ApiException as e:
        return "Exception when calling ModelApi->get_model: %s\n" % e


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
    io_ = io
    
    # only if ID is a valid UUID4 otherwise skip dataset
    if is_valid_uuid(io_['id']):
        io_['name'] = io_.pop('label')
        io_['filetype'] = format_stringed_array(io_.pop('hasFormat'))
        io_.pop('type')
        io_.pop('hasDimensionality')

        # query DCAT for variable information related to dataset
        q = {
          "dataset_id": io_['id']
        }

        resp = requests.post(f"{url}/datasets/dataset_variables",
                             headers=request_headers,
                             json=q).json()

        variables = resp['dataset']['variables']
        # query DCAT for standard variables related to dataset
        resp = requests.post(f"{url}/datasets/dataset_standard_variables",
                             headers=request_headers,
                             json=q).json()
        std_vars = resp['dataset']['standard_variables']
        std_vars_dict = {}
        for var in std_vars:
            std_vars_dict[var['standard_variable_id']] = var
        
        io_.pop('hasPresentation')
        io_['variables'] = []
        for v in variables:
            v['name'] = v.pop('variable_name')
            v['id'] = v.pop('variable_id')
            v['metadata'] = v.pop('variable_metadata')

            # Obtain standard name information for the variable  
            q = {
              "variable_ids__in": [v['id']]
            }

            resp = requests.post(f"{url}/variables/variables_standard_variables",
                                 headers=request_headers,
                                 json=q).json()
            print(resp)
            v_ = resp['variables'][0]
            v['standard_names'] = []
            for std in v_['standard_variables']:
                std_var = std_vars_dict[std['standard_variable_id']]
                v['standard_names'].append(std_var)

            io_['variables'].append(v)
        return io_    
    else:
        return None

def _execute_text_query(TextQuery, url, request_headers, MINTconfiguration, MINTusername):

    ###### STANDARD NAME QUERY #######
    if TextQuery.type == 'standard name':
        q = {
            "standard_variable_names__in": [TextQuery.term]
        }
        print(q)
        resp = requests.post(f"{url}/datasets/find", 
                                                headers=request_headers,
                                                json=q).json()
        if resp['result'] == 'success':
            found_resources = resp['resources']
            print(f"Found {len(found_resources)} resources")
        else:
            found_resources = []

        if TextQuery.result_type == 'datasets':
            return found_resources

        elif TextQuery.result_type == 'models':
            # We add the JSON string representation of the model to a set
            # so that we can avoid returning to the user duplicate models
            models = set()
            for d in found_resources:
                found_models = _find_model_by_dataset_id(d["dataset_id"],
                                    MINTconfiguration,
                                    MINTusername)
                for model in found_models:
                    models.add(json.dumps(model))
                
            models_output = []
            for m in list(models):
                models_output.append(json.loads(m))

            return models_output

    ###### KEYWORD QUERY #######
    elif TextQuery.type == 'keyword':
        if TextQuery.result_type == 'datasets':

            payload = {
              "provenance_id": "3831a57f-a372-424a-b310-525b5441581b",
              "search_query": [TextQuery.term] 
            }

            response = requests.post('http://api.mint-data-catalog.org/datasets/jataware_search', data=json.dumps(payload))
            return response.json()['datasets']

        elif TextQuery.result_type == 'models':
            params = (
                ('text', TextQuery.term),
                ('endpoint', 'https://endpoint.mint.isi.edu/ds/query'),
            )

            response = requests.get('https://query.mint.isi.edu/api/dgarijo/jatawareAPI/searchModels', params=params)
            # obtain model labels from result set
            models_ = response.json()['results']['bindings']
            models = [res['w']['value'].split('instance/')[1] for res in models_]
            api_instance = mint_client.ModelApi()
            models_output = []
            for model_id in models:
                try:
                    # Get a Model
                    api_response = api_instance.get_model(model_id, username=MINTusername)
                except ApiException as e:
                    print("Exception when calling ModelApi->get_model: %s\n" % e)
                models_output.append(api_response.to_dict())
            return models_output

        elif TextQuery.result_type == 'variables':

            params = (
                ('text', TextQuery.term),
                ('endpoint', 'https://endpoint.mint.isi.edu/ds/query'),
            )

            response = requests.get('https://query.mint.isi.edu/api/dgarijo/jatawareAPI/searchVariables', params=params)
            results = response.json()['results']['bindings']
            variables = []
            for res in results:
                var = {}
                var['name'] = res['desc']['value']
                var['id'] = res['w']['value'].split('instance/')[1]
                variables.append(var)

            # Get standard variable information from DCAT
            # This is clunky to have to use both catalogs
            # But it seems that the standard variable information is 
            # Not readily available in MCAT so we got to DCAT
            # TODO: ensure that the standard variables are actually compliant
            # TODO: right now standard variables do not have URIs returned by DCAT
            for var in variables:
                q = {
                  "variable_ids__in": [var['id']]
                }

                resp = requests.post(f"{url}/variables/variables_standard_variables",
                                     headers=request_headers,
                                     json=q).json()
                
                dcat_var = resp['variables'][0]
                var['metadata'] = dcat_var['metadata']
                for std in dcat_var['standard_variables']:
                    # TODO: address these blanks
                    if 'standard_variable_uri' not in std:
                        std['standard_variable_uri'] = ''
                var['standard_variables'] = dcat_var['standard_variables']

            return variables       


def _execute_geo_query(GeoQuery, url, request_headers, MINTconfiguration, MINTusername):

    bounding_box = [
        GeoQuery.xmin, 
        GeoQuery.ymin, 
        GeoQuery.xmax,
        GeoQuery.ymax
    ]

    q = {
        "spatial_coverage__within": bounding_box
    }

    resp = requests.post(f"{url}/datasets/find", 
                                            headers=request_headers,
                                            json=q).json()
    if resp['result'] == 'success':
        found_resources = resp['resources']
        print(f"Found {len(found_resources)} resources")
    else:
        found_resources = []

    if GeoQuery.result_type == 'datasets':
        return found_resources

    elif GeoQuery.result_type == 'models':
        # We add the JSON string representation of the model to a set
        # so that we can avoid returning to the user duplicate models
        models = set()
        for d in found_resources:
            found_models = _find_model_by_dataset_id(d["dataset_id"],
                                MINTconfiguration,
                                MINTusername)
            for model in found_models:
                models.add(json.dumps(model))
            
        models_output = []
        for m in list(models):
            models_output.append(json.loads(m))

        return models_output         

def _execute_time_query(TimeQuery, url, request_headers, MINTconfiguration, MINTusername):

    start_time = TimeQuery.start_time
    end_time = TimeQuery.end_time

    q = {
        "start_time__gte": start_time,
        "end_time__lte": end_time
    }

    resp = requests.post(f"{url}/datasets/find", 
                                            headers=request_headers,
                                            json=q).json()

    if resp['result'] == 'success':
        found_resources = resp['resources']
        print(f"Found {len(found_resources)} resources")
    else:
        found_resources = []

    if TimeQuery.result_type == 'datasets':
        return found_resources

    elif TimeQuery.result_type == 'models':
        # We add the JSON string representation of the model to a set
        # so that we can avoid returning to the user duplicate models
        models = set()
        for d in found_resources:
            found_models = _find_model_by_dataset_id(d["dataset_id"],
                                MINTconfiguration,
                                MINTusername)
            for model in found_models:
                models.add(json.dumps(model))
            
        models_output = []
        for m in list(models):
            models_output.append(json.loads(m))

        return models_output              

def _find_model_by_dataset_id(dataset_id, MINTconfiguration, MINTuser):
    print(f"Searching for models associated with the dataset {dataset_id}")
    configuration = MINTconfiguration
    username = MINTuser

    # Step 1: Obtain all MINT Model configurations
    # from these configurations, extract the input/output dataset IDs
    # Step 1 output: a set of Configuration IDs associated with the dataset_id
    api_instance = mint_client.ModelconfigurationApi(mint_client.ApiClient(configuration))
    try:
        # List modelconfiguration
        api_response = api_instance.get_model_configurations(username=username)
        dataset_configs = set()
        for config in api_response:
            for io in config.has_input:
                _id = io.id
                if _id == dataset_id:
                    dataset_configs.add(config.id)
            for io in config.has_output:
                _id = io.id
                if _id == dataset_id:
                    dataset_configs.add(config.id)
        print(f"Found {len(dataset_configs)} Model Configuration associated with {dataset_id}")
    except ApiException as e:
        print("Exception when calling ModelconfigurationApi->get_model_configurations: %s\n" % e)

    # Step 2: Obtain all Model Versions and their associated Model Configuration IDs
    # Step 2 output: a set of Model Version IDs associated with the dataset_id
    api_instance = mint_client.ModelversionApi(mint_client.ApiClient(configuration))
    try:
        # List All ModelVersions
        version_ids = set()
        api_response = api_instance.get_model_versions(username=username)

        for v in api_response:
            c_ = v.has_configuration
            for conf in c_:
                if conf.id in dataset_configs:
                    # this is a config associated with the dataset_id
                    # so add the version to version_ids
                    version_ids.add(v.id)
        print(f"Found {len(version_ids)} Model Version associated with {dataset_id}")
    except ApiException as e:
        print("Exception when calling ModelversionApi->get_model_versions: %s\n" % e)

    # Step 3: Obtain all Models and check if their versions match the Version IDs of interest
    # Step 3 output:
    api_instance = mint_client.ModelApi(mint_client.ApiClient(configuration))
    try:
        # List All models
        api_response = api_instance.get_models(username=username)
        models = set()
        for m in api_response:
            for v in m.has_software_version:
                if v['id'] in version_ids:
                    # this is a model associated with the dataset_id
                    # obtain its name
                    models.add(m.label)
        print(f"Found {len(models)} Models associated with {dataset_id}")
    except ApiException as e:
        print("Exception when calling ModelApi->get_models: %s\n" % e)
    
    try:
        models_output = []
        for m in list(models):
            m_ = _get_model(m, configuration, username)
            models_output.append(m_)
        return models_output
    except Exception as e:
        print(f"Exception when processing model info: {e}")

def format_model(m):
    """
    Takes a model metadata JSON from Redis and formats it for the MaaS API
    """
    model = {'name': m['id'], 
             'description': m['description'].replace('\n',''), 
             'label': m['label'],
             'category': m['category'],
             'maintainer': f"{m['maintainer']['name']}, {m['maintainer']['email']}",
             'version': m['versions']}
    return model

def format_parameters(m):
    """
    Takes in  a model metadata JSON from Redis and formats the parameters for the MaaS API.
    This just pops the `metadata` key and adds all its sub keys as top-level
    keys to the parameter object.
    """
    p = m.get('parameters',[])
    out_p = []
    for p in p:
        o_p = {'name': p['name'],
               'description': p['description'].replace('\n','')}
        for kk, vv in p['metadata'].items():
            o_p[kk] = vv
        out_p.append(o_p)
    return out_p

def format_outputs(m):
    """
    Takes in  a model metadata JSON from Redis and formats the outputs for the MaaS API.
    """
    outputs = m.get('outputs',[])
    out_o = []
    for o in outputs:
        o_ = {'name': o['name'],
              'description': o['description'].replace('\n','')}
        if 'units' in o:
            o_['units'] = o.get('units','')
        if 'metadata' in o:
            o_['metadata'] = o.get('units','')            
        out_o.append(o_)
    return out_o

def format_config(m):
    """
    Takes in  a model metadata JSON from Redis and formats the config the MaaS API.
    """
    c = m.get('configuration',[])
    out_c = {'name': m.get('id'), 'config': {}}
    if len(c) > 0:
        out_c['config'] = c[0]
    return out_c

def sortOD(od):
    res = OrderedDict()
    for k, v in sorted(od.items()):
        if isinstance(v, dict):
            res[k] = sortOD(v)
        else:
            res[k] = v
    return res    

def raster2gpd(InRaster,feature_name,band=1,nodataval=-9999):
    '''
    Description: 
        Takes the path of a raster (.tiff) file and produces a Geopandas Data Frame.
    Params:
        - InRaster: the path of the input raster file
        - feature_name: the name of the feature represented by the pixel values 
    '''

    # open the raster and get some properties
    ds       = gdal.OpenShared(InRaster,gdalconst.GA_ReadOnly)
    GeoTrans = ds.GetGeoTransform()
    ColRange = range(ds.RasterXSize)
    RowRange = range(ds.RasterYSize)
    rBand    = ds.GetRasterBand(band) # first band
    nData    = rBand.GetNoDataValue()
    if nData == None:
        logging.info(f"No nodataval found, setting to {nodataval}")
        nData = nodataval # set it to something if not set
    else:
        logging.info(f"Nodataval is: {nData}")

    # specify the center offset (takes the point in middle of pixel)
    HalfX    = GeoTrans[1] / 2
    HalfY    = GeoTrans[5] / 2

    points = []
    for ThisRow in RowRange:
        RowData = rBand.ReadAsArray(0,ThisRow,ds.RasterXSize,1)[0]
        for ThisCol in ColRange:
            # need to exclude NaN values since there is no nodataval
            if (RowData[ThisCol] != nData) and not (np.isnan(RowData[ThisCol])):
                
                # TODO: implement filters on valid pixels
                # for example, the below would ensure pixel values are between -100 and 100
                #if (RowData[ThisCol] <= 100) and (RowData[ThisCol] >= -100):

                X = GeoTrans[0] + ( ThisCol * GeoTrans[1] )
                Y = GeoTrans[3] + ( ThisRow * GeoTrans[5] ) # Y is negative so it's a minus
                # this gives the upper left of the cell, offset by half a cell to get centre
                X += HalfX
                Y += HalfY

                points.append([Point(X, Y),X,Y,RowData[ThisCol],feature_name])

    return gpd.GeoDataFrame(points, columns=['geometry','longitude','latitude','feature_value','feature_name'])