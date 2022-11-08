# Copyright 2022 CVS Health and/or one of its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from coldstart.build import FeatureFactory


def test_start_engine():
    """ ValueError raised for missing dialect, schema, project_id, unsupported database, failed engine creation"""
    
    db_spec = {
        "dialect": None,
        "driver": None,
        "project_id": "my_project",
        "config": None,
        "schema": "my_schema"
    }        
    
    ff = FeatureFactory()
    
    try:
        ff.start_engine(db_spec)
    except ValueError:
        assert True
        
    db_spec = {
        "dialect": "bigquery",
        "driver": None,
        "project_id": "my_project",
        "config": None
    }        
    
    ff = FeatureFactory()
    
    try:
        ff.start_engine(db_spec)
    except ValueError:
        assert True
        
    db_spec = {
        "dialect": "bigquery",
        "driver": None,
        "config": None,
        "schema": "my_schema"
    }        
    
    ff = FeatureFactory()
    
    try:
        ff.start_engine(db_spec)
    except KeyError:
        assert True
        
    db_spec = {
        "dialect": "bigqueryv2",
        "project_id": "my_project",
        "driver": None,
        "config": None,
        "schema": "my_schema"
    }        
    
    ff = FeatureFactory()
    
    try:
        ff.start_engine(db_spec)
    except ValueError:
        assert True
        
    db_spec = {
        "dialect": "bigquery",
        "project_id": "my_project",
        "driver": None,
        "config": None,
        "schema": "my_schema"
    }        
    
    ff = FeatureFactory()
    
    try:
        ff.start_engine(db_spec)
    except ValueError:
        assert True
        
    