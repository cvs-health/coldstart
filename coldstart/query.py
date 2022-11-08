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

# References
# https://cloud.google.com/bigquery/docs/best-practices-performance-compute
# https://cloud.google.com/bigquery/docs/best-practices-performance-patterns
# https://cloud.google.com/bigquery/docs/sessions-intro

import re
import shutil
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from tqdm.contrib.concurrent import thread_map


def name_table(schema, query_name):
    """Names tables according to pattern

    Args:
        schema (str): Name of schema
        query_name (str): Name of query

    Returns:
        str: Table name
    """    
    NOW = datetime.now().strftime("%Y%m%d%H%M%S%f")
    table_name = f"{schema}.coldstart_{query_name}_{NOW}_tmp"
    return table_name


def run_query(engine, sql, return_df=True):
    """For running queries

    Args:
        engine (object): Engine object
        sql (str): SQL query
        return_df (bool): Will return dataframe. Defaults to True.

    Returns:
        DataFrame: Query results
    """    
    # TODO: Add retrying with tenacity
    with engine.connect() as connection:
        if return_df is False:
            connection.execute(sql)
        else:
            result = connection.execute(sql)
            df = pd.DataFrame(result.fetchall(), columns=result._metadata.keys)
            return df


def run_threaded_query(query_tuple):
    """Wrapper function for running concurrent queries via threading

    Args:
        query_tuple (tuple): query_name, engine, sql, return_df

    Returns:
        tuple: Results: query_name, status, run_time
    """    

    # Unpack tuple
    query_name, engine, sql, return_df = query_tuple

    # Start timing
    time_start = datetime.now()

    # Execute query
    try:
        run_query(engine=engine, sql=sql, return_df=return_df)
        status = 'SUCCESS'
        time_stop = datetime.now()
        run_time = (time_stop - time_start).seconds
        return (query_name, status, run_time)

    except Exception as e:
        status = 'FAILURE'
        run_time = 0
        print(f'{query_name} FAILED: ', e)
        return (query_name, status, run_time)


def multi_query(query_tuples):
    """For running concurrent queries via threading

    Args:
        query_tuples (list): List of tuples: query_name, engine, sql, return_df

    Returns:
        list: Results: query_name, status, run_time 
    """    
    results = thread_map(run_threaded_query,
                         query_tuples,
                         miniters=1,
                         total=len(query_tuples),
                         desc='Query Progress')
    return results


def stage_leftmost_table(engine, schema, leftmost_table, entity_id, dt1, dt2):
    """Stages leftmost table to include idx while performing data validation

    Args:

        engine (object): Engine object
        schema (str): schema of interest
        leftmost_table (str): User defined leftmost table
        entity_id (str): entity_id of interst
        dt1 (str): min_date
        dt2 (str): max_date

    Raises:
        ValueError: Error for invalid entity_id column
        ValueError: Error for missing y column
        ValueError: Error for missing min_date column
        ValueError: Error for missing max_date column
        ValueError: Error for invalid date format

    Returns:
        str, tuple: Staged table name, Results: query_name, status, run_time
    """

    # Start timing
    time_start = datetime.now()

    # Inspect leftmost table
    sql = f"""
    SELECT *
    FROM {leftmost_table}
    """
    
    # Execute query
    try:
        df = run_query(engine=engine, sql=sql, return_df=True)
    except Exception as e:
        print(e)
        
    # Check that entity_id is present
    if entity_id not in df.columns.tolist():
        raise ValueError("entity_id did not match column in leftmost_table.")
    
    # Check that y is present
    if 'y' not in df.columns.tolist():
        raise ValueError("y column was not found in leftmost_table.")

    # Check if min_date and max_date are present
    if dt1 is not None and dt2 is not None:
        date_flag = 1
    else:
        if 'min_date' not in df.columns.tolist():
            raise ValueError("min_date column was not found in leftmost_table.")
        if 'max_date' not in df.columns.tolist():
            raise ValueError("max_date column was not found in leftmost_table.")
        # TODO: confirm that regex is robust to date and string types
        r = re.compile(r'^\d{4}\-(0?[1-9]|1[012])\-(0?[1-9]|[12][0-9]|3[01])$')
        dt1_sum = df['min_date'].apply(lambda x: bool(r.match(x))).sum()
        dt2_sum = df['max_date'].apply(lambda x: bool(r.match(x))).sum()
        if dt1_sum != len(df) or dt2_sum != len(df):
            raise ValueError("Invalid yyyy-mm-dd format in leftmost_table.")
        else:
            date_flag = 2

    # Create idx table
    query_name = "leftMostTable"
    staged_table = name_table(schema=schema, query_name=query_name)
    if date_flag == 1:
        sql = f"""
        CREATE TABLE {staged_table}
        AS
        SELECT
            CONCAT(
                CAST(LT.{entity_id} AS STRING),
                '_',
                CAST('{dt1}' AS STRING),
                '_',
                CAST('{dt2}' AS STRING)
            ) AS idx,
            LT.{entity_id},
            LT.y,
            CAST('{dt1}' AS DATE) AS min_date,
            CAST('{dt2}' AS DATE) AS max_date
        FROM
            {leftmost_table} AS LT
        """
    elif date_flag ==2:
        sql = f"""
        CREATE TABLE {staged_table}
        AS
        SELECT
            CONCAT(
                CAST(LT.{entity_id} AS STRING),
                '_',
                CAST(LT.{dt1} AS STRING),
                '_',
                CAST(LT.{dt2} AS STRING)
            ) AS idx,
            LT.{entity_id},
            LT.y,
            CAST(LT.{dt1} AS DATE) AS min_date,
            CAST(LT.{dt2} AS DATE) AS max_date
        FROM
            {leftmost_table} AS LT
        """
    
    # Execute query
    try:
        df = run_query(engine=engine, sql=sql, return_df=False)
        status = 'SUCCESS'
    except Exception as e:
        print(e)

    # Stop timing
    time_stop = datetime.now()
    run_time = (time_stop - time_start).seconds

    # Return results
    return staged_table, (query_name, status, run_time)


def freeze_queries(query_dir, export_dir, query_dict):
    """Instruction to save queries to specified directory

    Args:
        query_dir (str): Directory to copy feature queries from
        export_dir (str): Directory to export feature queries to
        query_dict (dict): Untemplated feature queries to freeze
    """

    # Check if directory exists
    if Path(export_dir).is_dir() is False:
        to_path = Path(export_dir)
        try:
            to_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(e)
            
    # Set query directory
    if query_dir is None:
        query_dir = Path(__file__).parent.joinpath("query_bank")
    else:
        query_dir = Path(query_dir)
    
    # Copy queries to directory
    queries_to_copy = list(query_dict.keys())
    for path in query_dir.rglob('*.sql'):
        query_name = path.stem
        if query_name in queries_to_copy:
            shutil.copy(path, f"{export_dir}/{query_name}.sql")


def template_queries(engine, schema, staged_table, query_dict):
    """Templates queries with LEFTMOST_TABLE

    Args:
        engine (object): Engine object
        schema (str): schema of interest
        staged_table (str): Name of staged leftmost tables
        query_dict (dict): Queries to template 

    Returns:
        dict, list: Dictionary of query_name: table_name, list of tamplated
            queries
    """    

    # Iterate over queries
    query_list = []
    table_dict = {}
    for k in query_dict.keys():

        # Parse dictionary and name tables
        query_name = k
        table_name = name_table(schema=schema, query_name=query_name)
        raw_sql = query_dict[k]['SQL']

        # Base templating
        base_sql = f'CREATE TABLE {table_name} AS '
        full_sql = base_sql + raw_sql

        # Parameterized templating
        templated_sql = full_sql.format(LEFTMOST_TABLE=staged_table)

        # Append query list and table dictionary
        # HINT: name, sql, return_df
        query_tuple = (
            query_name,
            engine,
            templated_sql,
            True,
        )
        query_list.append(query_tuple)
        table_dict[query_name] = table_name

    return table_dict, query_list


def collect_metadata(engine, schema, table_list):
    """For collecting successful feature query metadata

    Args:
        engine (object): Engine object
        schema (str): schema of interest
        table_list (list): Table names of successful feature queries

    Returns:
        DataFrame: table_name and column_name
    """    
    
    # Split tables
    to_insert = ["'"+t.split(".")[1]+"'" for t in table_list]
    to_insert_str = ", ".join(str(x) for x in to_insert)
    
    # Format query
    sql = f"""
    SELECT
        CONCAT(table_schema, '.', table_name) AS table_name,
        column_name
    FROM
        {schema}.INFORMATION_SCHEMA.COLUMN_FIELD_PATHS
    WHERE
        table_name IN ({to_insert_str})
    """
    
    # Execute query
    try:
        df = run_query(engine=engine, sql=sql, return_df=True)
    except Exception as e:
        print(e)

    # return dataframe
    return df


def prep_join_query(schema, table_df, feature_table=None):
    """For preparing final join query

    Args:
        schema (str): schema of interest
        table_df (DataFrame): Containing table_name and column_name
        feature_table (str): Specified name of final table. Defaults to None.

    Returns:
        str, str: Join SQL, Name of final table
    """    

    # Base query templating
    if feature_table is None:
        join_table = name_table(schema=schema, query_name="final")
    else:
        join_table = feature_table
    base_sql = f"CREATE OR REPLACE TABLE {join_table} AS "

    # Leftmost templating
    left_df = table_df[table_df['table_name'].str.contains('left')]
    left_table_name = left_df['table_name'].values[0]
    left_y_col = left_df[left_df['column_name'].str.lower() == 'y']['column_name'].values[0]
    select_sql = f'SELECT LMOST.idx, LMOST.{left_y_col}'
    from_sql = f' FROM {left_table_name} AS LMOST'

    # Feature templating
    right_df = table_df[~table_df['table_name'].str.contains('left')]
    join_dict = {}
    for idx, row in right_df.iterrows():
        table_name = row['table_name']
        query_name = table_name.split('_')[-3]
        old_col_name = row['column_name']
        new_col_name = f'{query_name}_{old_col_name}'
        if table_name not in join_dict:
            join_dict[table_name] = query_name
        if old_col_name != 'idx':
            select_sql += f', {query_name}.{old_col_name} AS {new_col_name}'

    for table, alias in join_dict.items():
        from_sql += f' LEFT JOIN {table} AS {alias} ON LMOST.idx = {alias}.idx'

    # Concatenate full query
    full_sql = base_sql + select_sql + from_sql

    # Return sql and table
    return full_sql, join_table


def drop_tables(engine, table_list):
    """For dropping intermediate tables

    Args:
        engine (object): Engine object
        table_list (list): Tables to drop

    Returns:
        list: Results: query_name, status, run_time 
    """

    # Drop intermediate tables
    query_list = []
    for table in table_list:
        sql = f'DROP TABLE IF EXISTS {table}'
        query_tuple = (
            table,
            engine,
            sql,
            False,
        )
        query_list.append(query_tuple)

    # Execute queries
    results = multi_query(query_list)
    return results


def convert_categorical(s):
    """For attempting categorical conversion

    Args:
        s (Series): To attempt categorical conversion on

    Returns:
        Series: Converted to categorical data type
    """
    
    # Convert strings/objects to categoricals if criteria is met
    string_types = [np.dtype('object'), np.dtype('O')]
    dt_col_names = ['date', 'time', 'dt', 'period']
    dt_check = any(x in s.name for x in dt_col_names)
    if (s.dtype in string_types or pd.api.types.is_string_dtype(s)) \
        and (s.nunique() / len(s)) < 0.5 and dt_check is False:
        s = s.astype('category')
    return s


def attempt_downcast(df):
    """For attempting data type downcasting

    Args:
        df (DataFrame): To attempt downcasting on

    Returns:
        DataFrame: Downcasted dataframe
    """
    
    # Calculate reduction in MB
    a = df.memory_usage().sum()

    try:
        # Convert columns to best possible dtypes using dtypes supporting pd.NA
        df = df.copy(deep=True).convert_dtypes()

        # Convert strings/objects to categoricals if criteria is met
        df = df.copy(deep=True).apply(convert_categorical)

        # Calculate reduction in MB
        b = df.memory_usage().sum()
        pct_reduction = np.abs(np.round(((a - b) / a) * 100, 2))
        print(f'DataFrame memory reduction: {pct_reduction}%')

    except Exception as e:
        print(e)

    return df
