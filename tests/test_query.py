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
import os, shutil
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine 

from coldstart.query import (
    stage_leftmost_table, 
    run_query,
    run_threaded_query,
    name_table, 
    stage_leftmost_table,
    freeze_queries,
    prep_join_query
)


@pytest.fixture(scope="module")
def global_db():
    
    engine = create_engine("sqlite://")
    
    engine.execute("ATTACH DATABASE ':memory:' AS test_db")
    
    sql = """
    CREATE TABLE test_db.left_table (
        team_id STRING NOT NULL, 
        y INTEGER
    )
    """
    engine.execute(sql)
    
    with engine.connect() as conn:
        conn.execute("INSERT INTO test_db.left_table VALUES (\'a111\', 1)")
        conn.execute("INSERT INTO test_db.left_table VALUES (\'a112\', 0)")
        conn.execute("INSERT INTO test_db.left_table VALUES (\'a113\', 1)")
        conn.execute("INSERT INTO test_db.left_table VALUES (\'a114\', 0)")
        conn.execute("INSERT INTO test_db.left_table VALUES (\'a115\', 1)")
        conn.execute("INSERT INTO test_db.left_table VALUES (\'a116\', 1)")
        
    return {"engine": engine}


def test_run_query(global_db):
    
    engine = global_db["engine"]
    
    sql = """
    SELECT *
    FROM test_db.left_table
    """
    
    assert len (run_query(engine, sql, return_df=True)) == 6
    

def test_run_threaded_query(global_db):
    
    engine = global_db["engine"]
    
    sql = """
    SELECT *
    FROM test_db.left_table
    LIMIT 3
    """
    
    test_query_tuple = ("testQuery0", engine, sql, True)
    
    result = run_threaded_query(test_query_tuple)
    
    assert result[1] == "SUCCESS" 
    

def test_stage_leftmost_table(global_db):
    """ ValueError is raised when entity_id is invalid, min_date is not found in leftmost_table """
    
    engine = global_db["engine"]
    
    try:
        stage_leftmost_table(
            engine=engine,
            schema="test_db",
            leftmost_table="left_table",
            entity_id="NCAA",
            dt1="2022-01-01",
            dt2="2022-09-01"
        )
    except ValueError:
        assert True
    
    try:
        stage_leftmost_table(
            engine=engine,
            schema="test_db",
            leftmost_table="left_table",
            entity_id="team_id",
            dt1=None,
            dt2=None
        )
    except ValueError:
        assert True

        
def test_name_table():
    
    name = name_table("test_schema", "testQuery1")
    assert "test_schema" in name and "coldstart" in name and "testQuery1" in name
    

def test_freeze_queries():
    
    query_dir = Path(__file__).parent/"query_bank"
    export_dir = Path(__file__).parent/"test_export"
    query_dir = str(query_dir)
    query_dict = {}
    query_dict["testQuery1"] = "Select query"
    
    freeze_queries(query_dir, export_dir, query_dict)
    
    assert len(os.listdir(export_dir)) == 1
    
    shutil.rmtree(export_dir)

    
def test_prep_join_query():
    
    data = {}
    data[0] = ["my_schema.coldstart_leftMostTable_2022", "idx"]
    data[1] = ["my_schema.coldstart_leftMostTable_2022", "team_id"]
    data[2] = ["my_schema.coldstart_leftMostTable_2022", "y"]
    data[3] = ["my_schema.coldstart_leftMostTable_2022", "min_date"]
    data[4] = ["my_schema.coldstart_leftMostTable_2022", "max_date"]
    data[5] = ["my_schema.coldstart_testQuery2_2022", "idx"]
    data[6] = ["my_schema.coldstart_testQuery2_2022", "loss_count"]
    data[7] = ["my_schema.coldstart_testQuery1_2022", "idx"]
    data[8] = ["my_schema.coldstart_testQuery1_2022", "win_count"]
    
    table_df = pd.DataFrame.from_dict(
        data,
        orient="index",
        columns=["table_name", "column_name"]
    )
    res = prep_join_query("my_schema", table_df, "my_schema.final_table")
    
    assert "CREATE OR REPLACE TABLE my_schema.final_table AS SELECT LMOST.idx, LMOST.y" in res[0]
