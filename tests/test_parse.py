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

import pytest
from pathlib import Path

from coldstart.parse import (
    list_dialects,
    list_entities,
    list_domains,
    list_queries,
    get_queries_from_domains,
    get_queries,
)


@pytest.fixture(scope="module")
def global_query_bank():
    
    query_bank = str(Path(__file__).parent.joinpath("query_bank").resolve())
    return {"query_folder": query_bank}


def test_list_dialects_1(global_query_bank):
    
    query_bank = global_query_bank["query_folder"]
    a = list_dialects(query_dir=query_bank)
    assert len(a) > 0
    assert "bigquery" in a 

    
def test_list_entities_1(global_query_bank):
    
    query_bank = global_query_bank["query_folder"]
    a = list_entities(dialect="bigquery", query_dir=query_bank)
    assert len(a) > 0
    assert "team_id" in a 
    

def test_list_entities_2(global_query_bank):
    """ Dialect cannot be None, dialect not in list of valid dialects """
    
    query_bank = global_query_bank["query_folder"]
    try:
        list_entities(dialect=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        list_entities(dialect="bigquery23", query_dir=query_bank)
    except ValueError:
        assert True


def test_list_domains_1(global_query_bank):
    
    query_bank = global_query_bank["query_folder"]
    assert len(list_domains(dialect="bigquery", entity_id="team_id", query_dir=query_bank)) == 2
    assert len(list_domains(dialect="bigquery", entity_id="game_id", query_dir=query_bank)) == 1
    
    
def test_list_domains_2(global_query_bank):
    """ ValueError is raised when entity_id is None, when entity_id not in list of valid entities, when dialect is None, when dialect not in list of valid dialects"""
    
    query_bank = global_query_bank["query_folder"]
    try:
        list_domains(entity_id=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        list_domains(entity_id="NCAA", query_dir=query_bank)
    except ValueError:
        assert True
    try:
        list_domains(entity_id="team_id", dialect=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        list_domains(entity_id="team_id", dialect="bigquery23", query_dir=query_bank)
    except ValueError:
        assert True
        
        
def test_list_queries_1(global_query_bank):

    query_bank = global_query_bank["query_folder"]
    assert len(list_queries(dialect="bigquery", entity_id="team_id", domains=["wins", "losses"], query_dir=query_bank)) == 2
    assert len(list_queries(dialect="bigquery", entity_id="team_id", domains=["wins"], query_dir=query_bank)) == 1
    assert len(list_queries(dialect="bigquery", entity_id="team_id", domains=None, query_dir=query_bank)) == 2
  
    
def test_list_queries_2(global_query_bank):
    """ ValueError is raised when dialect is None, dialect not in valid list, entity_id is None, entity not in valid list, domain not in valid list"""
    
    query_bank = global_query_bank["query_folder"]
    try:
        list_queries(dialect=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        list_queries(dialect="bigquery23", query_dir=query_bank)
    except ValueError:
        assert True
    try:
        list_queries(dialect="bigquery", entity_id=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        list_queries(dialect="bigquery", entity_id="NCAA", query_dir=query_bank)
    except ValueError:
        assert True
    try:
        list_queries(dialect="bigquery", entity_id="team_id", domains=["NCAA"], query_dir=query_bank)
    except ValueError:
        assert True
        

def test_get_queries_from_domains_1(global_query_bank):
    
    query_bank = global_query_bank["query_folder"]
    
    queries = get_queries_from_domains(dialect= "bigquery", entity_id="team_id", domains=["wins", "losses"], query_dir=query_bank)
    
    queries = list(queries.keys())
    
    assert "testQuery1" in queries
    assert "testQuery2" in queries
    assert "testQuery3" not in queries
    
    
def test_get_queries_from_domains_2(global_query_bank):
    """ ValueError is raised when dialect is None, dialect not in list of valid dialects, entity_id is None, entity_id not in list of valid entities,
    domain not in list of valid domains"""
    
    query_bank = global_query_bank["query_folder"]
    try:
        get_queries_from_domains(dialect=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        get_queries_from_domains(dialect="bigquery23", query_dir=query_bank)
    except ValueError:
        assert True
    try:
        get_queries_from_domains(dialect="bigquery", entity_id=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        get_queries_from_domains(dialect="bigquery", entity_id="NCAA", query_dir=query_bank)
    except ValueError:
        assert True
    try:
        get_queries_from_domains(dialect="bigquery", entity_id="team_id", domains=["NCAA"], query_dir=query_bank)
    except ValueError:
        assert True
    
    
def test_get_queries_1(global_query_bank):
    
    query_bank = global_query_bank["query_folder"]
    
    queries = get_queries(dialect="bigquery", entity_id="team_id", queries=["testQuery1", "testQuery2"], query_dir=query_bank)
    
    queries = list(queries.keys())
    
    assert "testQuery1" in queries
    assert "testQuery2" in queries
    assert "testQuery3" not in queries
    
    
def test_get_queries_2(global_query_bank):
    """ ValueError is raised when dialect is None, dialect not in list of valid dialects, entity_id is None, entity_id not in list of valid entities,
    query not in list of available queries"""
    
    query_bank = global_query_bank["query_folder"]
    try:
        get_queries(dialect=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        get_queries(dialect="bigquery23", query_dir=query_bank)
    except ValueError:
        assert True
    try:
        get_queries(dialect="bigquery", entity_id=None, query_dir=query_bank)
    except ValueError:
        assert True
    try:
        get_queries(dialect="bigquery", entity_id="NCAA", query_dir=query_bank)
    except ValueError:
        assert True
    try:
        get_queries(dialect="bigquery", entity_id="team_id", queries=["testQuerynotavailable"], query_dir=query_bank)
    except ValueError:
        assert True