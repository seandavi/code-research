"""
Basic functionality tests for DuckDB Chatbot components
These tests verify the core functionality without requiring an API key
"""
import sys
from duckdb_manager import DuckDBManager
from python_executor import PythonExecutor
import pandas as pd


def test_duckdb_manager():
    """Test DuckDB manager functionality."""
    print("Testing DuckDB Manager...")

    with DuckDBManager(":memory:") as db:
        # Test table creation from DataFrame
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'value': [100, 200, 300]
        })
        db.create_table_from_dataframe('test_table', df)

        # Test listing tables
        tables = db.list_tables()
        assert 'test_table' in tables, "Table not created"
        print(f"✓ Table created successfully: {tables}")

        # Test query execution
        result = db.execute_query("SELECT * FROM test_table ORDER BY id")
        assert len(result) == 3, "Query returned wrong number of rows"
        print(f"✓ Query execution successful: {len(result)} rows")

        # Test aggregation
        result = db.execute_query("SELECT SUM(value) as total FROM test_table")
        assert result['total'][0] == 600, "Aggregation failed"
        print(f"✓ Aggregation successful: total = {result['total'][0]}")

        # Test schema
        schema = db.get_table_schema('test_table')
        assert len(schema) == 3, "Schema has wrong number of columns"
        print(f"✓ Schema inspection successful: {len(schema)} columns")

    print("✓ All DuckDB Manager tests passed!\n")


def test_python_executor():
    """Test Python executor functionality."""
    print("Testing Python Executor...")

    # Test basic code execution
    executor = PythonExecutor()

    # Test simple calculation
    result = executor.execute("result = 2 + 2")
    assert result['success'], "Execution failed"
    assert result['result'] == 4, "Calculation incorrect"
    print("✓ Basic execution successful")

    # Test with output
    result = executor.execute("print('Hello, World!')")
    assert result['success'], "Execution failed"
    assert 'Hello, World!' in result['output'], "Output not captured"
    print("✓ Output capture successful")

    # Test with pandas
    code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
result = df['a'].sum()
"""
    result = executor.execute(code)
    assert result['success'], "Pandas execution failed"
    assert result['result'] == 6, "Pandas calculation incorrect"
    print("✓ Pandas integration successful")

    # Test error handling
    result = executor.execute("x = 1 / 0")
    assert not result['success'], "Should have failed"
    assert 'ZeroDivisionError' in result['error'], "Error not captured"
    print("✓ Error handling successful")

    print("✓ All Python Executor tests passed!\n")


def test_integration():
    """Test integration between DuckDB and Python executor."""
    print("Testing Integration...")

    with DuckDBManager(":memory:") as db:
        # Create test data
        df = pd.DataFrame({
            'product': ['A', 'B', 'C'],
            'sales': [100, 200, 150]
        })
        db.create_table_from_dataframe('sales', df)

        # Create executor with database access
        executor = PythonExecutor(db)

        # Test querying from Python
        code = """
df = execute_query("SELECT * FROM sales WHERE sales > 100")
result = len(df)
"""
        result = executor.execute(code)
        assert result['success'], "Integration query failed"
        assert result['result'] == 2, "Integration query returned wrong results"
        print("✓ Database query from Python successful")

        # Test aggregation from Python
        code = """
df = execute_query("SELECT SUM(sales) as total FROM sales")
result = df['total'][0]
"""
        result = executor.execute(code)
        assert result['success'], "Aggregation failed"
        assert result['result'] == 450, "Aggregation returned wrong result"
        print("✓ Database aggregation from Python successful")

    print("✓ All Integration tests passed!\n")


def main():
    """Run all tests."""
    print("="*60)
    print("DuckDB Chatbot - Component Tests")
    print("="*60 + "\n")

    try:
        test_duckdb_manager()
        test_python_executor()
        test_integration()

        print("="*60)
        print("All Tests Passed Successfully!")
        print("="*60)
        return 0

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
