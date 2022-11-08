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

import re
from pathlib import Path


def list_dialects(query_dir=None):
    """Return list of available dialects

    Args:
        query_dir (str): Target directory containing feature queries.
            If None, coldstart/query_bank is used. Defaults to None.

    Returns:
        list: List of available dialects
    """    

    # Set query directory
    if query_dir is None:
        query_dir = Path(__file__).parent.joinpath("query_bank")
    else:
        query_dir = Path(query_dir)

    # Collect dialects
    valid_dialects = []
    for path in query_dir.rglob("*.sql"):
        query_sql = path.read_text()
        query_dialect = re.search("\-\- DIALECT: (.*?)\\n", query_sql).group(1)
        if query_dialect not in valid_dialects:
            valid_dialects.append(query_dialect)          

    # Return databases
    return valid_dialects


def list_entities(dialect=None, query_dir=None):
    """Return list of available entities

    Args:
        dialect (str): Dialect of interest. Defaults to None.
        query_dir (str): Target directory containing feature queries.
            If None, coldstart/query_bank is used. Defaults to None.

    Raises:
        ValueError: Error for missing dialect
        ValueError: Error for involid dialect

    Returns:
        list: List of available entities
    """    

    # Set query directory
    if query_dir is None:
        query_dir = Path(__file__).parent.joinpath("query_bank")
    else:
        query_dir = Path(query_dir)

    # Check dialect
    if dialect is None:
        raise ValueError("dialect cannot be None.")
    all_dialects = list_dialects(query_dir=query_dir)
    if dialect not in all_dialects:
        raise ValueError("You have submitted an invalid dialect.")

    # Collect entities
    valid_entities = []
    for path in query_dir.rglob("*.sql"):
        query_sql = path.read_text()
        query_dialect = re.search("\-\- DIALECT: (.*?)\\n", query_sql).group(1)
        query_entity = re.search("\-\- ENTITY: (.*?)\\n", query_sql).group(1)
        if query_dialect == dialect and query_entity not in valid_entities:
            valid_entities.append(query_entity)          

    # Return entities
    return valid_entities


def list_domains(dialect=None, entity_id=None, query_dir=None):
    """Return list of available domains

    Args:
        dialect (str): Dialect of interest. Defaults to None.
        entity_id (str): Entity of interest. Defaults to None.
        query_dir (str): Target directory containing feature queries.
            If None, coldstart/query_bank is used. Defaults to None.

    Raises:
        ValueError: Error for missing dialect
        ValueError: Error for invalid dialect
        ValueError: Error for missing entity_id
        ValueError: Error for invalid entity_id

    Returns:
        list: List of available domains
    """    

    # Set query directory
    if query_dir is None:
        query_dir = Path(__file__).parent.joinpath("query_bank")
    else:
        query_dir = Path(query_dir)

    # Check dialect
    if dialect is None:
        raise ValueError("dialect cannot be None.")
    all_dialects = list_dialects(query_dir=query_dir)
    if dialect not in all_dialects:
        raise ValueError("You have submitted an invalid dialect.")

    # Check entity_id
    if entity_id is None:
        raise ValueError("entity_id cannot be None.")
    all_entities = list_entities(dialect=dialect, query_dir=query_dir)
    if entity_id not in all_entities:
        raise ValueError("You have submitted an invalid entity_id.")

    # Collect domains
    valid_domains = []
    for path in query_dir.rglob("*.sql"):
        query_sql = path.read_text()
        query_dialect = re.search("\-\- DIALECT: (.*?)\\n", query_sql).group(1)
        query_entity = re.search("\-\- ENTITY: (.*?)\\n", query_sql).group(1)
        query_domain = re.search("\-\- DOMAIN: (.*?)\\n", query_sql).group(1)
        if query_dialect == dialect and query_entity == entity_id and query_domain not in valid_domains:
            valid_domains.append(query_domain)          

    # Return domains
    return valid_domains


def list_queries(
    dialect=None,
    entity_id=None,
    domains=None,
    query_dir=None
):
    """Return list of available queries 

    Args:
        dialect (str): Dialect of interest. Defaults to None.
        entity_id (str): Entity of interest. Defaults to None.
        domains (list): Domains of interest. Defaults to None.
        query_dir (str): Target directory containing feature queries.
            If None, coldstart/query_bank is used. Defaults to None.

    Raises:
        ValueError: Error for missing dialect
        ValueError: Error for invalid dialect
        ValueError: Error for missing entity_id
        ValueError: Error for invalid entity_id
        ValueError: Error for invalid domain

    Returns:
        list: List of available queries
    """    

    # Set query directory
    if query_dir is None:
        query_dir = Path(__file__).parent.joinpath("query_bank")
    else:
        query_dir = Path(query_dir)

    # Check dialect
    if dialect is None:
        raise ValueError("dialect cannot be None.")
    all_dialects = list_dialects(query_dir=query_dir)
    if dialect not in all_dialects:
        raise ValueError("You have submitted an invalid dialect.")

    # Check entity_id
    if entity_id is None:
        raise ValueError("entity_id cannot be None.")
    all_entities = list_entities(dialect=dialect, query_dir=query_dir)
    if entity_id not in all_entities:
        raise ValueError("You have submitted an invalid entity_id.")

    # Check domains
    if domains is not None:
        all_domains = list_domains(dialect=dialect, entity_id=entity_id, query_dir=query_dir)
        for d in domains:
            if d not in all_domains:
                raise ValueError("You have submitted an invalid domain.")

    # Collect queries
    valid_queries = []
    for path in query_dir.rglob("*.sql"):
        query_name = path.stem
        query_sql = path.read_text()
        query_dialect = re.search("\-\- DIALECT: (.*?)\\n", query_sql).group(1)
        query_entity = re.search("\-\- ENTITY: (.*?)\\n", query_sql).group(1)
        query_domain = re.search("\-\- DOMAIN: (.*?)\\n", query_sql).group(1)
        if query_dialect == dialect and query_entity == entity_id and domains is None:
            valid_queries.append(query_name)
        elif query_dialect == dialect and query_entity == entity_id and query_domain in domains and query_name not in valid_queries: 
            valid_queries.append(query_name)

    # Return queries
    return valid_queries


def get_queries_from_domains(
    dialect=None,
    entity_id=None,
    domains=None,
    query_dir=None
):
    """Prepares dictionary of queries to template for given domains

    Args:
        dialect (str): Dialect of interest. Defaults to None.
        entity_id (str): Entity of interest. Defaults to None.
        domains (list): Domains of interest. Defaults to None.
        query_dir (str): Target directory containing feature queries.
            If None, coldstart/query_bank is used. Defaults to None.

    Raises:
        ValueError: Error for missing dialect
        ValueError: Error for invalid dialect
        ValueError: Error for missing entity_id
        ValueError: Error for invalid entity_id
        ValueError: Error for invalid domain

    Returns:
        dict: Dictionary of queries to template
    """    

    # Set query directory
    if query_dir is None:
        query_dir = Path(__file__).parent.joinpath("query_bank")
    else:
        query_dir = Path(query_dir)

    # Check dialect
    if dialect is None:
        raise ValueError("dialect cannot be None.")
    all_dialects = list_dialects(query_dir=query_dir)
    if dialect not in all_dialects:
        raise ValueError("You have submitted an invalid dialect.")

    # Check entity_id
    if entity_id is None:
        raise ValueError("entity_id cannot be None.")
    all_entities = list_entities(dialect=dialect, query_dir=query_dir)
    if entity_id not in all_entities:
        raise ValueError("You have submitted an invalid entity_id.")

    # Check domains
    all_domains = list_domains(dialect=dialect, entity_id=entity_id, query_dir=query_dir)
    for d in domains:
        if d not in all_domains:
            raise ValueError("You have submitted an invalid domain.")

    # Collect applicable domains and queries
    queries_2_run = {}
    for path in query_dir.rglob('*.sql'):
        query_name = path.stem
        query_sql = path.read_text()
        query_dialect = re.search("\-\- DIALECT: (.*?)\\n", query_sql).group(1)
        query_domain = re.search("\-\- DOMAIN: (.*?)\\n", query_sql).group(1)
        query_entity = re.search("\-\- ENTITY: (.*?)\\n", query_sql).group(1)
        if query_dialect == dialect and query_entity == entity_id and query_domain in domains:
            queries_2_run[query_name] = {
                'SQL': query_sql,
                'DIALECT': query_dialect,
                'ENTITY': query_entity,
                'DOMAIN': query_domain,
            }

    # Return query dict
    return queries_2_run


def get_queries(dialect=None, entity_id=None, queries=None, query_dir=None):
    """Prepares dictionary of queries to template for given queries

    Args:
        dialect (str): Dialect of interest. Defaults to None.
        entity_id (str): Entity of interest. Defaults to None.
        queries (list): Queries of interest. Defaults to None.
        query_dir (str): Target directory containing feature queries.
            If None, coldstart/query_bank is used. Defaults to None.

    Raises:
        ValueError: Error for missing dialect
        ValueError: Error for invalid dialect
        ValueError: Error for missing entity_id
        ValueError: Error for invalid entity_id
        ValueError: Error for invalid query

    Returns:
        dict: Dictionary of queries to template
    """    

    # Set query directory
    if query_dir is None:
        query_dir = Path(__file__).parent.joinpath("query_bank")
    else:
        query_dir = Path(query_dir)

    # Check dialect
    if dialect is None:
        raise ValueError("dialect cannot be None.")
    all_dialects = list_dialects(query_dir=query_dir)
    if dialect not in all_dialects:
        raise ValueError("You have submitted an invalid dialect.")

    # Check entity_id
    if entity_id is None:
        raise ValueError("entity_id cannot be None.")
    all_entities = list_entities(dialect=dialect, query_dir=query_dir)
    if entity_id not in all_entities:
        raise ValueError("You have submitted an invalid entity_id.")

    # Check queries
    all_queries = list_queries(dialect=dialect, entity_id=entity_id, query_dir=query_dir)
    for q in queries:
        if q not in all_queries:
            raise ValueError("You have submitted an invalid query.")

    # Collect queries
    queries_2_run = {}
    for path in query_dir.rglob('*.sql'):
        query_name = path.stem
        query_sql = path.read_text()
        query_dialect = re.search("\-\- DIALECT: (.*?)\\n", query_sql).group(1)
        query_domain = re.search("\-\- DOMAIN: (.*?)\\n", query_sql).group(1)
        query_entity = re.search("\-\- ENTITY: (.*?)\\n", query_sql).group(1)
        if query_dialect == dialect and query_entity == entity_id and query_name in queries:
            queries_2_run[query_name] = {
                'SQL': query_sql,
                'DIALECT': query_dialect,
                'ENTITY': query_entity,
                'DOMAIN': query_domain,
            }

    # Return query dict
    return queries_2_run
