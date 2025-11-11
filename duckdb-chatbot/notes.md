# Development Notes - DuckDB Chatbot

## Project Goal
Develop a chatbot that can:
- Connect to a DuckDB database
- Perform SQL analyses
- Execute Python code for data analysis
- Create plots and visualizations

## Progress Log

### Initial Setup
- Created project folder structure
- Defined project requirements

### Architecture Design
Designed a modular architecture with three main components:
1. **DuckDBManager** - Handles database connections and queries
2. **PythonExecutor** - Safe Python code execution with plotting support
3. **DuckDBChatbot** - Main interface using Claude's tool calling API

### Implementation Details

#### DuckDB Manager (duckdb_manager.py)
- Connection management for DuckDB databases (in-memory or file-based)
- SQL query execution with results returned as pandas DataFrames
- Table creation from CSV files or DataFrames
- Schema inspection and table listing
- Context manager support for proper resource cleanup

Key features:
- Simple API: `execute_query()`, `create_table_from_csv()`, `list_tables()`
- Error handling for connection and query failures
- Support for both in-memory and persistent databases

#### Python Executor (python_executor.py)
- Safe execution of Python code with captured stdout
- Pre-configured environment with pandas, numpy, matplotlib
- Automatic figure capture and base64 encoding
- Access to DuckDB connection within executed code
- Comprehensive error reporting with tracebacks

Key features:
- Isolated execution context
- Matplotlib figure capture (non-interactive backend)
- Access to database via `db` variable or `execute_query()` function
- Returns structured results (success, output, errors, figures)

#### Chatbot Interface (chatbot.py)
- Claude API integration with tool calling
- Four available tools:
  1. `execute_sql_query` - Run SQL queries
  2. `execute_python_code` - Execute Python analysis code
  3. `list_tables` - Show available tables
  4. `get_table_schema` - Inspect table structure
- Conversation history management
- Automatic tool execution loop

Tool calling flow:
1. User sends message
2. Claude decides which tools to use
3. Tools execute and return results
4. Claude synthesizes response
5. Loop continues if more tools needed

### Learnings

1. **Tool Design**: The tools need clear descriptions for Claude to use them effectively. The `execute_python_code` tool description explicitly mentions available variables and libraries.

2. **Context Sharing**: The Python executor shares the DuckDB connection, allowing seamless integration between SQL queries and Python analysis.

3. **Figure Handling**: Using matplotlib's non-interactive backend ('Agg') allows figure generation without display, with base64 encoding for transport.

4. **Error Handling**: Each component includes comprehensive error handling to provide useful feedback when operations fail.

5. **Conversation Management**: Maintaining conversation history allows the chatbot to reference previous queries and build on prior context.

### Example Use Cases Created

1. **example.py** - Demonstrates basic functionality:
   - Creating sample data with Python
   - SQL queries
   - Aggregations
   - Visualizations
   - Complex analysis combining SQL and Python

2. **example_csv.py** - Shows CSV data loading:
   - Loading external data
   - Exploratory queries
   - Statistical analysis
   - Correlation analysis with visualization

3. **Interactive Mode** - REPL-style interface for ad-hoc analysis

### Testing Approach

Since this requires an API key and is a demonstration project:
- Created comprehensive examples that showcase all features
- Examples can be run with: `python example.py`
- Interactive mode available with: `python example.py interactive`
- CSV example with: `python example_csv.py`

### Potential Enhancements

1. **MCP Integration**: Could integrate with Model Context Protocol for standardized tool interfaces
2. **Persistence**: Add session saving/loading for long-running analyses
3. **Security**: Implement sandboxing for Python code execution (RestrictedPython, Docker)
4. **Streaming**: Add streaming responses for long-running operations
5. **Multi-database**: Support multiple database connections simultaneously
6. **Export**: Add functionality to export results and plots to files
7. **Async**: Implement async operations for better performance

### Dependencies

All dependencies specified in pyproject.toml:
- duckdb: Database engine
- anthropic: Claude API client
- matplotlib: Plotting library
- pandas: Data manipulation
- numpy: Numerical operations
- seaborn: Statistical visualizations

### Dependency Management with uv

Converted project to use `uv` for dependency management:
- Created pyproject.toml with project metadata and dependencies
- Removed requirements.txt in favor of modern Python packaging standards
- Benefits of uv:
  - Much faster dependency resolution and installation (10-100x faster than pip)
  - Written in Rust for performance
  - Compatible with pip and standard Python packaging
  - Better caching and conflict resolution
  - Supports both pip-style and Poetry-style workflows

Installation options:
1. `uv pip install -e .` - Install in current environment
2. `uv venv && uv pip install -e .` - Create virtual environment and install
3. `pip install -e .` - Still works with standard pip

The pyproject.toml also includes optional dev dependencies and tool configurations for code formatting (black) and linting (ruff).

