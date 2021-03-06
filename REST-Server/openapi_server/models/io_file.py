# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from openapi_server.models.base_model_ import Model
from openapi_server import util


class IOFile(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, name=None, description=None, filetype=None, variables=None):  # noqa: E501
        """IOFile - a model defined in OpenAPI

        :param name: The name of this IOFile.  # noqa: E501
        :type name: str
        :param description: The description of this IOFile.  # noqa: E501
        :type description: str
        :param filetype: The filetype of this IOFile.  # noqa: E501
        :type filetype: str
        :param variables: The variables of this IOFile.  # noqa: E501
        :type variables: List[Variable]
        """
        self.openapi_types = {
            'name': str,
            'description': str,
            'filetype': str,
            'variables': List[Variable]
        }

        self.attribute_map = {
            'name': 'name',
            'description': 'description',
            'filetype': 'filetype',
            'variables': 'variables'
        }

        self._name = name
        self._description = description
        self._filetype = filetype
        self._variables = variables

    @classmethod
    def from_dict(cls, dikt) -> 'IOFile':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The IOFile of this IOFile.  # noqa: E501
        :rtype: IOFile
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this IOFile.

        The name of a given input or output file. This should be general and should not reference a specific file.  # noqa: E501

        :return: The name of this IOFile.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this IOFile.

        The name of a given input or output file. This should be general and should not reference a specific file.  # noqa: E501

        :param name: The name of this IOFile.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    @property
    def description(self):
        """Gets the description of this IOFile.

        Description of the file.  # noqa: E501

        :return: The description of this IOFile.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this IOFile.

        Description of the file.  # noqa: E501

        :param description: The description of this IOFile.
        :type description: str
        """
        if description is None:
            raise ValueError("Invalid value for `description`, must not be `None`")  # noqa: E501

        self._description = description

    @property
    def filetype(self):
        """Gets the filetype of this IOFile.

        The file type (extension) for this file  # noqa: E501

        :return: The filetype of this IOFile.
        :rtype: str
        """
        return self._filetype

    @filetype.setter
    def filetype(self, filetype):
        """Sets the filetype of this IOFile.

        The file type (extension) for this file  # noqa: E501

        :param filetype: The filetype of this IOFile.
        :type filetype: str
        """
        if filetype is None:
            raise ValueError("Invalid value for `filetype`, must not be `None`")  # noqa: E501

        self._filetype = filetype

    @property
    def variables(self):
        """Gets the variables of this IOFile.

        An array of variables associated with a given input or output file  # noqa: E501

        :return: The variables of this IOFile.
        :rtype: List[Variable]
        """
        return self._variables

    @variables.setter
    def variables(self, variables):
        """Sets the variables of this IOFile.

        An array of variables associated with a given input or output file  # noqa: E501

        :param variables: The variables of this IOFile.
        :type variables: List[Variable]
        """

        self._variables = variables
