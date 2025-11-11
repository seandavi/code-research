# DuckDB Chatbot with Python Analysis

A conversational AI chatbot that can query DuckDB databases and perform data analysis using Python code, powered by Claude's tool calling capabilities.

## Overview

This project implements an intelligent chatbot that combines:
- **DuckDB Database Queries**: Execute SQL queries on DuckDB databases
- **Python Data Analysis**: Run Python code with pandas, numpy, and matplotlib
- **Interactive Visualizations**: Create plots and charts automatically
- **Natural Language Interface**: Ask questions in plain English

The chatbot uses Claude's tool calling API to intelligently decide when to use SQL queries versus Python code, and can seamlessly combine both approaches for complex analyses.

## Architecture

The system consists of three main components:

### 1. DuckDB Manager (`duckdb_manager.py`)
Handles all database operations:
- Connection management (in-memory or file-based databases)
- SQL query execution with pandas DataFrame results
- Table creation from CSV files or DataFrames
- Schema inspection and metadata queries

### 2. Python Executor (`python_executor.py`)
Executes Python code safely with:
- Isolated execution environment
- Pre-loaded libraries (pandas, numpy, matplotlib, seaborn)
- Automatic plot capture and encoding
- Access to the DuckDB connection
- Comprehensive error handling

### 3. Chatbot Interface (`chatbot.py`)
Main conversational interface featuring:
- Claude API integration with tool calling
- Four specialized tools:
  - `execute_sql_query`: Run SQL queries
  - `execute_python_code`: Execute Python analysis code
  - `list_tables`: List available database tables
  - `get_table_schema`: Inspect table structure
- Conversation history management
- Automatic tool orchestration

## Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **SQL Execution**: Run complex SQL queries on DuckDB
- **Python Analysis**: Perform statistical analysis and data transformations
- **Automatic Visualization**: Create plots that are captured and saved
- **CSV Import**: Load data from CSV files easily
- **Interactive Mode**: REPL-style interface for exploratory analysis
- **Conversation Context**: The bot remembers previous queries and builds on them

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable dependency management.

1. Install uv (if not already installed):

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

2. Install project dependencies:

```bash
# Install all dependencies
uv pip install -e .

# Or install in a virtual environment (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

3. Set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Alternative: Using pip

If you prefer using pip, you can install directly from pyproject.toml:

```bash
pip install -e .
```

## Usage

### Basic Example

```python
from chatbot import DuckDBChatbot
import os

api_key = os.getenv("ANTHROPIC_API_KEY")

with DuckDBChatbot(api_key=api_key) as bot:
    # Load data from CSV
    bot.load_csv_data("employees", "sample_data.csv")

    # Ask questions in natural language
    response = bot.chat("What is the average salary by department?")
    print(response)

    # Request visualizations
    response = bot.chat("Create a bar chart showing employee count by city")
    print(response)
```

### Running Examples

The project includes several example scripts:

1. **Basic functionality demo**:
```bash
python example.py
```

2. **CSV data analysis**:
```bash
python example_csv.py
```

3. **Interactive mode**:
```bash
python example.py interactive
```

### Interactive Mode

In interactive mode, you can have a conversation with the bot:

```
You: Load the sample_data.csv file into a table called employees

Bot: I've loaded the data successfully. The table has 10 rows.

You: What's the average age by department?

Bot: Here are the average ages by department:
- Engineering: 33.7 years
- Management: 43.5 years
- Marketing: 29.0 years
- Sales: 34.5 years

You: Create a visualization showing salary distribution

Bot: I've created a histogram showing the salary distribution...
```

## Tool Calling Flow

The chatbot uses Claude's tool calling API in a loop:

1. **User Input**: User asks a question or requests an analysis
2. **Claude Decision**: Claude decides which tools to use based on the query
3. **Tool Execution**: Tools execute (SQL query, Python code, etc.)
4. **Result Processing**: Tool results are sent back to Claude
5. **Response Generation**: Claude synthesizes a natural language response
6. **Iteration**: Process repeats if more tools are needed

This allows the bot to break down complex queries into multiple steps automatically.

## Example Queries

The chatbot can handle a wide variety of queries:

### Data Exploration
- "Show me the first 10 rows of the table"
- "What columns are in the employees table?"
- "How many records are in the database?"

### SQL Queries
- "What is the total sales by product?"
- "Find all employees with salary greater than 80000"
- "Calculate average, min, and max salary by department"

### Python Analysis
- "Calculate the correlation between age and salary"
- "Perform a linear regression on the data"
- "Create a pivot table showing sales by month and product"

### Visualizations
- "Create a scatter plot of age vs salary"
- "Make a bar chart of employee count by city"
- "Plot a histogram of the salary distribution"
- "Create a box plot comparing salaries across departments"

### Combined Analysis
- "Which department has the highest average salary? Show it in a chart"
- "Analyze the relationship between age and salary, including a visualization"
- "Calculate profit margin by product and create a comparison plot"

## Code Structure

```
duckdb-chatbot/
├── chatbot.py              # Main chatbot interface
├── duckdb_manager.py       # Database connection and query management
├── python_executor.py      # Python code execution environment
├── example.py              # Basic usage examples
├── example_csv.py          # CSV data loading example
├── test_basic.py           # Component tests
├── sample_data.csv         # Sample dataset for testing
├── pyproject.toml          # Project metadata and dependencies (uv/pip)
├── notes.md               # Development notes and learnings
└── README.md              # This file
```

## How It Works

### SQL Query Execution

When you ask a database question, the bot:
1. Translates your question to SQL
2. Uses `execute_sql_query` tool
3. Returns results as a formatted table

Example:
```
User: "What is the average salary?"
→ Tool: execute_sql_query("SELECT AVG(salary) FROM employees")
→ Result: "Average salary: $80,000"
```

### Python Code Execution

For complex analysis or visualizations:
1. Bot generates appropriate Python code
2. Uses `execute_python_code` tool
3. Captures output and any plots created

Example:
```
User: "Create a histogram of salaries"
→ Tool: execute_python_code("
    df = execute_query('SELECT salary FROM employees')
    plt.hist(df['salary'])
    plt.title('Salary Distribution')
    plt.show()
")
→ Result: Plot captured and saved
```

### Database Access in Python

Python code has access to the database through:
- `db`: The DuckDBManager instance
- `execute_query(sql)`: Helper function to run SQL queries

Example Python code:
```python
# Query the database
df = execute_query("SELECT * FROM employees WHERE age > 30")

# Process with pandas
avg_salary = df['salary'].mean()

# Create visualization
plt.bar(df['city'], df['salary'])
plt.title(f'Salaries by City (avg: ${avg_salary:,.0f})')
plt.show()
```

## Security Considerations

This implementation uses Python's `exec()` for code execution, which has security implications:

- **Current Implementation**: Suitable for trusted environments and demonstrations
- **Production Use**: Should implement sandboxing:
  - Use RestrictedPython for safe execution
  - Run in Docker containers with limited resources
  - Implement timeout mechanisms
  - Validate and sanitize all inputs

## MCP Integration (Future Enhancement)

The architecture is designed to be compatible with Model Context Protocol (MCP):
- Tools are already structured with clear schemas
- DuckDB operations could be exposed as MCP servers
- Python execution could be an MCP tool endpoint
- Would enable standardized integration with other AI applications

## Limitations

1. **Code Execution**: Python code runs with full privileges (not sandboxed)
2. **Plot Storage**: Figures are base64 encoded but not automatically saved to files
3. **Database Size**: In-memory databases are limited by available RAM
4. **API Costs**: Each interaction uses Claude API tokens
5. **Synchronous**: Operations are blocking (no async support yet)

## Future Enhancements

1. **Security**: Implement proper sandboxing for Python execution
2. **Persistence**: Save conversation history and analysis sessions
3. **Export**: Automatically save plots and results to files
4. **Async**: Add asynchronous operation support
5. **Multi-DB**: Support multiple database connections
6. **Streaming**: Stream responses for long-running operations
7. **MCP**: Full Model Context Protocol integration
8. **Web Interface**: Add a web-based UI for easier interaction

## Key Learnings

### Tool Design
Clear, detailed tool descriptions are crucial for Claude to use them effectively. Including information about available variables and expected behavior improves tool usage accuracy.

### Context Sharing
Sharing the DuckDB connection between SQL queries and Python code enables seamless integration. Python code can query the database directly, making complex analyses straightforward.

### Figure Handling
Using matplotlib's non-interactive backend ('Agg') allows figure generation in headless environments. Base64 encoding enables figure transport without file system operations.

### Conversation Flow
Maintaining conversation history allows the bot to:
- Reference previous queries
- Build on prior analysis
- Maintain context across multiple tool uses

### Error Handling
Comprehensive error handling at each layer (database, Python execution, API calls) provides clear feedback when operations fail, making debugging easier.

## Dependencies

- **duckdb** (≥0.9.0): Fast analytical database engine
- **anthropic** (≥0.18.0): Claude API client
- **matplotlib** (≥3.7.0): Plotting and visualization
- **pandas** (≥2.0.0): Data manipulation and analysis
- **numpy** (≥1.24.0): Numerical computing
- **seaborn** (≥0.12.0): Statistical data visualization

## License

This is a demonstration project created for research purposes.

## Conclusion

This chatbot demonstrates the power of combining:
- Large language models (Claude)
- Fast analytical databases (DuckDB)
- Python's data science ecosystem
- Tool calling for intelligent task orchestration

The result is a natural language interface for data analysis that can handle everything from simple queries to complex statistical analysis with visualizations, all through conversational interaction.
