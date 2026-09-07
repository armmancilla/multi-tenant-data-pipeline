import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

class DatabaseClient:
    """
    A lightweight wrapper around a psycopg2 connection.
    Accepts a fully-formed configuration dict.
    """
    
    def __init__(self, config: dict):
        """
        config expects:
        {
            'database': str,
            'user': str,
            'password': str,
            'host': str,
            'port': int
        }
        """
        self.config = config
        self.conn = None
        
    def connect(self):
        """Establishes the connection and sets autocommit=False for transaction control."""
        if self.conn and not self.conn.closed:
            return self.conn
            
        self.conn = psycopg2.connect(
            database=self.config['database'],
            user=self.config['user'],
            password=self.config['password'],
            host=self.config['host'],
            port=self.config['port']
        )
        self.conn.autocommit = False  # Explicit transaction control
        return self.conn
        
    def close(self):
        """Closes the connection if open."""
        if self.conn and not self.conn.closed:
            self.conn.close()
            
    def commit(self):
        """Commits the current transaction."""
        if self.conn:
            self.conn.commit()
            
    def rollback(self):
        """Rolls back the current transaction."""
        if self.conn:
            self.conn.rollback()
            
    def cursor(self):
        """Returns a cursor (with DictCursor for column-name access)."""
        if not self.conn or self.conn.closed:
            self.connect()
        return self.conn.cursor(cursor_factory=DictCursor)
    
    def __enter__(self):
        """Enables 'with DatabaseClient(config) as client:' pattern."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Auto-rolls back on exception, otherwise commits. Then closes."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()
        return False
    
    def execute_sql_file(self, filepath: str, params: dict = None, dynamic_tables: dict = None):
        """Executes a raw SQL file with optional parameter substitution."""
        if not self.conn or self.conn.closed:
            self.connect()
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Could not find SQL file at: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        with self.cursor() as cur:
            if dynamic_tables:
                # 1. Convert dictionary keys into safely quoted Postgres Identifiers
                # e.g. {"target_table": "clientes"} becomes Identifier("clientes")
                identifiers = {k: sql.Identifier(v) for k, v in dynamic_tables.items()}
                
                # 2. Format the SQL string using psycopg2.sql
                sql_script = sql.SQL(sql_script).format(**identifiers)
            if params:
                cur.execute(sql_script, params)
            else:
                cur.execute(sql_script)
            self.conn.commit()