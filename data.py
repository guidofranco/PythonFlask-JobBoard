import os
import sqlite3
from urllib.parse import urlparse

import psycopg2
from sqlalchemy import create_engine

import pandas as pd


def create_tables():
    commands = (
        '''
        BEGIN;
        DROP TABLE IF EXISTS review;
        DROP TABLE IF EXISTS job;
        DROP TABLE IF EXISTS employer;
        CREATE TABLE employer (
            id SERIAL,
            name character varying,
            description text,
            address character varying,
            city character varying,
            state character varying,
            zip integer,
            CONSTRAINT employer_pkey PRIMARY KEY (id)
        );
        CREATE TABLE job (
            id SERIAL,
            title character varying,
            description text,
            salary integer,
            employer_id integer,
            CONSTRAINT job_pkey PRIMARY KEY (id),
            CONSTRAINT fk_employer_id FOREIGN KEY (employer_id)
                REFERENCES public.employer (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
        );
        CREATE TABLE review
        (
            id SERIAL,
            review text,
            rating integer,
            title character varying,
            date date,
            status character varying,
            employer_id integer,
            CONSTRAINT review_pkey PRIMARY KEY (id),
            CONSTRAINT fk_employer_id FOREIGN KEY (employer_id)
                REFERENCES public.employer (id) MATCH SIMPLE
                ON UPDATE NO ACTION
                ON DELETE NO ACTION
        );
        '''
    )


    conn = None
    try:
        uri = os.environ['HEROKU_DB_URI']
        uri = urlparse(uri)
        db = f'dbname={uri.path[1:]} user={uri.username} password={uri.password} host={uri.hostname}'
        conn = psycopg2.connect(db)
        cur = conn.cursor()
        cur.execute(commands)
        cur.close()
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def insert_data():
    con = sqlite3.connect('db/jobs.sqlite')
    tables = ['employer', 'job', 'review']
    #uri = os.environ['HEROKU_DB_URI']
    uri = 'postgres://cgmmupxrjlnuan:8dc73c9cdd9fdff80dbbabbe9688cd3f6978c0e6122cc506be3f251e835af66d@ec2-54-197-48-79.compute-1.amazonaws.com:5432/d3pqa056b627vd'
    for table in tables:
        # Import table in a DataFrame
        query = f"SELECT * FROM {table}"
        df = pd.read_sql(query, con)
        
        # Discard id column of each table
        df = df.iloc[:, 1:]
    
        # Export DataFrame to table in postgresql database
        engine = create_engine(uri)
        df.to_sql(table, engine, index=False, if_exists='append')

    con.close()

if __name__ == '__main__':
    create_tables()
    insert_data()
