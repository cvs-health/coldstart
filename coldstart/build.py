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

import sys
import warnings
import pandas as pd
from random import shuffle
from tqdm.auto import tqdm
from sqlalchemy import create_engine

from coldstart.parse import (
    list_dialects,
    list_entities,
    list_domains,
    list_queries,
    get_queries_from_domains,
    get_queries
)
from coldstart.query import (
    run_query,
    multi_query,
    stage_leftmost_table,
    freeze_queries,
    template_queries,
    collect_metadata,
    prep_join_query,
    drop_tables,
    attempt_downcast
)


class FeatureFactory(object):
    
    """Coldstart's main class"""
    
    def __init__(self):
        
        self.list_dialects = list_dialects
        self.list_entities = list_entities
        self.list_domains = list_domains
        self.list_queries = list_queries


    def start_engine(self, db_spec):
        """Starts SQLAlchemy engine

        Args:
            db_spec (dict): Used as the config for create_engine

        Raises:
            ValueError: Error for missing dialect
            ValueError: Error for missing schema
            ValueError: Error for missing project_id
            ValueError: Error for unsupported database
            ValueError: Error for failed engine creation
        """    
        
        # Primary value checks
        if "dialect" not in db_spec or db_spec["dialect"] is None:
            raise ValueError("dialect needs to be specified in the db_spec.")
        if "schema" not in db_spec or db_spec["schema"] is None:
            raise ValueError("schema needs to be specified in the db_spec.")
        
        # Secondary value checks
        if db_spec["dialect"] == 'bigquery' and db_spec["project_id"] is None:
            raise ValueError("project_id needs to be specified in the db_spec.")
        
        # Set attributes
        self.dialect = db_spec["dialect"]
        self.schema = db_spec["schema"]
        if "driver" in db_spec:
            self.driver = db_spec["driver"]
        if "config" in db_spec:
            self.config = db_spec["config"]
        if "project_id" in db_spec:
            self.project_id = db_spec["project_id"]
        
        # Create url
        # TODO: Add more databases
        if self.dialect == "bigquery":
            db_url = f"{self.dialect}:///?ProjectId='{self.project_id}'"
        else:
            raise ValueError("This database is not currently supported")
        
        # Create engine
        try:
            self.engine = create_engine(db_url)
        except:
            raise ValueError("Engine not created. Check values in db_spec")


    def run(
        self,
        leftmost_table=None,
        feature_table=None,
        entity_id=None,
        domains=None,
        queries=None,
        date_range=None,
        query_dir=None,
        export_dir=None,
        drop_intermedieate_tables=True,
        return_df=True,
        compute_df=True,
        stop_on_error=False,
        downcast=False,
        batching=False,
        batch_size=None,
    ):
        """Used for running FeatureFactory

        Args:
            leftmost_table (str): Left-most table used for constraining feature
                queries. Should include entity_id and y. Can also include
                min_date and max_date. Defaults to None.
            feature_table (str): Destination for final table. Defaults to None.
            entity_id (str): Entity of interest for feature queries. 
                Defaults to None.
            domains (list): Domains of interest for feature queries.
                Defaults to None.
            queries (list): Queries of interest for feature queries.
                Defaults to None.
            date_range (list): min_date and max_date used for constraining
                feature queries. Defaults to None.
            query_dir (str): Target directory containing feature queries.
                If None, coldstart/query_bank is used. Defaults to None.
            export_dir (str): Destination directory for frozen queries.
                Defaults to None.
            drop_intermedieate_tables (bool): Used for removing intermediate
                query results. Defaults to True.
            return_df (bool): Used for returning a dataframe. Defaults to True.
            compute_df (bool): Used for computing a dataframe. If False,
                a Dask dataframe will be returned as opposed to Pandas.
                Defaults to True.
            stop_on_error (bool): Will halt FeatureFactory if any one query
                fails. Defaults to False.
            downcast (bool): Will attempt dataframe dtype downcasting.
                Defaults to False.
            batching (bool): Used for dividing feature queries into batches.
                Defaults to False.
            batch_size (int): Corresponding batch size if batching is True.
                Defaults to None.

        Raises:
            ValueError: Error for missing engine
            ValueError: Error for errored queries
        """        
        
        # Check for engine
        if hasattr(self, "engine") == False:
            raise ValueError("`start_engine` needs to be called before `run`.")
        
        # Start progress bar
        # TODO: Check tqdm arguments
        pbar = tqdm(
            total=100,
            file=sys.stdout,
            miniters=1,
            initial=10,
            desc="Overall Progress"
        )
        pbar.update(10)
        
        # Stage leftmost table
        if date_range is not None:
            dt1, dt2 = date_range[0], date_range[1]
        else:
            dt1, dt2 = None, None
        staged_table, staged_tuple = stage_leftmost_table(
            engine=self.engine,
            schema=self.schema,
            leftmost_table=leftmost_table,
            entity_id=entity_id,
            dt1=dt1,
            dt2=dt2
        )
        pbar.update(10)
        print("STAGING: Complete")
        
        # Check domains and queries
        if domains is not None and queries is not None:
            warnings.warn("domains will be ignored since queries were specified")
        
        # Collect queries to run
        if queries is not None:
            query_dict = get_queries(
                db=self.dialect, 
                entity_id=entity_id, 
                queries=queries, 
                query_dir=query_dir
            )
        elif domains is not None:
            query_dict = get_queries_from_domains(
                dialect=self.dialect,
                entity_id=entity_id,
                domains=domains,
                query_dir=query_dir
            )
        pbar.update(10)
        print("PARSING: Complete")
        
        # Freeze queries
        if export_dir is not None:
            freeze_queries(query_dir, export_dir, query_dict)
            
        # TODO: Create switch for parquet external tables
        
        # Template queries
        table_dict, query_tuples = template_queries(
            engine=self.engine,
            schema=self.schema,
            staged_table=staged_table,
            query_dict=query_dict,
        )
        pbar.update(10)
        print("TEMPLATING: Complete")
        
        # Execute queries
        if batching is True:
            shuffle(query_tuples)
            c = batch_size
            t = len(query_tuples)
            batches = [query_tuples[x:x+c] for x in range(0, t, c)]
            temp_results = []
            for batch in batches:
                temp_results.append(multi_query(batch))
            results = [item for sublist in temp_results for item in sublist]
        else:
            results = multi_query(query_tuples)
        pbar.update(20)
        print("QUERYING: Complete")
        
        # Append leftmost table info
        results.append(staged_tuple)
        table_dict["leftMostTable"] = staged_table

        # Create query results dataframe
        cols = ["query_name", "query_status", "query_seconds"]
        results_df = pd.DataFrame(results, columns=cols)
        results_df["table_name"] = results_df["query_name"].replace(table_dict)
        print(results_df[cols])

        # Check for failures
        if stop_on_error is True:
            dirty = results_df[results_df["query_status"] == "FAILURE"]
            if len(dirty) > 0:
                raise ValueError("One or many queries errord.")
        clean = results_df[results_df["query_status"] == "SUCCESS"]

        # Collect data types
        clean_tables = clean["table_name"].unique().tolist()
        table_df = collect_metadata(
            engine=self.engine,
            schema=self.schema,
            table_list=clean_tables
        )
        pbar.update(10)
        print("METADATA COLLECTING: Complete")
        
        # Prep join query
        join_sql, final_table = prep_join_query(
            schema=self.schema,
            table_df=table_df, 
            feature_table=feature_table
        )
        
        # Execute query
        try:
            if return_df is True and compute_df is True:
                df = run_query(engine=self.engine, sql=join_sql, return_df=True)
                # Attempt downcasting
                if downcast is True:
                    df = attempt_downcast(df)
                self.df = df
            elif return_df is False:
                run_query(engine=self.engine, sql=join_sql, return_df=True)
            elif return_df is True and compute_df is False:
                # TODO: Implement dask dataframe option
                df = run_query(engine=self.engine, sql=join_sql, return_df=True)
                self.df = df
                warnings.warn("Dask dataframes not yet supported")
        except Exception as e:
            print(e)
        
        # Set final table name
        self.table = final_table 
        pbar.update(10)
        print("MERGING: Complete")
        
        # Drop tables
        if drop_intermedieate_tables == True:
            drop_tables(engine=self.engine, table_list=clean_tables)
        pbar.update(10)
        print("DROPPING: Complete")
        
        # Print for testing
        # print("~~~~~~~~~~~~~~~~~~~~~~~~STAGING~~~~~~~~~~~~~~~~~~~~~~~~")
        # print(staged_table, staged_tuple)
        # print("~~~~~~~~~~~~~~~~~~~~~~~~PARSING~~~~~~~~~~~~~~~~~~~~~~~~")
        # print(query_dict)
        # print("~~~~~~~~~~~~~~~~~~~~~~~~TEMPLATING~~~~~~~~~~~~~~~~~~~~~~~~")
        # print(table_dict, query_tuples)
        # print("~~~~~~~~~~~~~~~~~~~~~~~~QUERYING~~~~~~~~~~~~~~~~~~~~~~~~")
        # print(results)
        # print("~~~~~~~~~~~~~~~~~~~~~~~~METADATA~~~~~~~~~~~~~~~~~~~~~~~~")
        # print(table_df)
        # print("~~~~~~~~~~~~~~~~~~~~~~~~MERGING~~~~~~~~~~~~~~~~~~~~~~~~")
        # print(join_sql, final_table)

    def get_dataframe(self):
        """For returning a dataframe object

        Returns:
            DataFrame: Training data
        """        
        return self.df

    def get_table(self):
        """For returning final feature table name

        Returns:
            str: Table name containing training data
        """        
        return self.table
    
    def stop_engine(self):
        """Stops SQLAlchemy engine"""        
        self.engine.dispose()
