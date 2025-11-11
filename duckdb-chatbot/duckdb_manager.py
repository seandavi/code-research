"""
DuckDB Manager - Handles database connections and query execution
"""
import duckdb
from typing import Optional, Dict, Any, List
import pandas as pd


class DuckDBManager:
    """Manages DuckDB database connections and query execution."""

    def __init__(self, database_path: str = ":memory:"):
        """
        Initialize DuckDB connection.

        Args:
            database_path: Path to database file or ":memory:" for in-memory DB
        """
        self.database_path = database_path
        self.connection = None
        self.connect()

    def connect(self) -> None:
        """Establish connection to DuckDB database."""
        try:
            self.connection = duckdb.connect(self.database_path)
            print(f"Connected to DuckDB: {self.database_path}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to DuckDB: {e}")

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.

        Args:
            query: SQL query string

        Returns:
            pandas DataFrame with query results
        """
        try:
            result = self.connection.execute(query).fetchdf()
            return result
        except Exception as e:
            raise Exception(f"Query execution failed: {e}")

    def execute_query_dict(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries.

        Args:
            query: SQL query string

        Returns:
            List of dictionaries with query results
        """
        df = self.execute_query(query)
        return df.to_dict('records')

    def create_table_from_csv(self, table_name: str, csv_path: str) -> None:
        """
        Create a table from a CSV file.

        Args:
            table_name: Name for the new table
            csv_path: Path to CSV file
        """
        query = f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{csv_path}')"
        self.connection.execute(query)
        print(f"Created table '{table_name}' from {csv_path}")

    def create_table_from_dataframe(self, table_name: str, df: pd.DataFrame) -> None:
        """
        Create a table from a pandas DataFrame.

        Args:
            table_name: Name for the new table
            df: pandas DataFrame
        """
        self.connection.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
        print(f"Created table '{table_name}' from DataFrame")

    def list_tables(self) -> List[str]:
        """
        List all tables in the database.

        Returns:
            List of table names
        """
        result = self.connection.execute("SHOW TABLES").fetchall()
        return [row[0] for row in result]

    def get_table_schema(self, table_name: str) -> pd.DataFrame:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            DataFrame with column information
        """
        query = f"DESCRIBE {table_name}"
        return self.execute_query(query)

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("DuckDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
