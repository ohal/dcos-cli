import collections
import json

import pkg_resources
from dcos import util
from dcoscli.marathon import main

import pytest

ResourceData = collections.namedtuple(
    'ResourceData',
    ['properties', 'expected'])

clean_response = json.loads(
    pkg_resources.resource_string(
        'tests',
        'data/marathon/apps/cleaned_response.json').decode('utf-8'))


@pytest.fixture(params=[
    ResourceData(
        properties=json.loads(
            pkg_resources.resource_string(
                'tests',
                'data/marathon/apps/response.json').decode('utf-8')),
        expected=clean_response
        )])
def resource_data(request):
    return request.param


def test_clean_up_resource_definition(resource_data):
    result = main._clean_up_resource_definition(resource_data.properties)
    assert result == resource_data.expected


schema = main._data_schema()


ValidationCheck = collections.namedtuple(
    'ValidationCheck',
    ['properties', 'expected'])


@pytest.fixture(params=[
    ValidationCheck(
        properties=clean_response,
        expected=None),
    ValidationCheck(
        properties=json.loads(
            pkg_resources.resource_string(
                'tests',
                'data/marathon/groups/complicated.json').decode('utf-8')),
        expected=None)
    ])
def validation_check(request):
    return request.param


def test_validation(validation_check):
    result = util.validate_json(validation_check.properties, schema)
    assert result == []
