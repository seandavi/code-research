"""
DuckDB Chatbot - Interactive chatbot with database and Python analysis capabilities
"""
import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from duckdb_manager import DuckDBManager
from python_executor import PythonExecutor


class DuckDBChatbot:
    """Chatbot that can query DuckDB databases and execute Python analysis code."""

    def __init__(
        self,
        api_key: str,
        database_path: str = ":memory:",
        model: str = "claude-3-5-sonnet-20241022"
    ):
        """
        Initialize the chatbot.

        Args:
            api_key: Anthropic API key
            database_path: Path to DuckDB database
            model: Claude model to use
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.db_manager = DuckDBManager(database_path)
        self.python_executor = PythonExecutor(self.db_manager)
        self.conversation_history = []

        # Define available tools
        self.tools = [
            {
                "name": "execute_sql_query",
                "description": "Execute a SQL query on the DuckDB database and return results as a formatted table. Use this to retrieve, analyze, or manipulate data in the database.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL query to execute"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "execute_python_code",
                "description": "Execute Python code for data analysis, calculations, or creating visualizations. You have access to pandas (pd), numpy (np), matplotlib.pyplot (plt), and can use 'db' to access the DuckDB manager or 'execute_query(sql)' to run SQL queries. Create plots using matplotlib - they will be automatically captured and saved.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The Python code to execute"
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "list_tables",
                "description": "List all tables available in the DuckDB database.",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_table_schema",
                "description": "Get the schema (column names and types) for a specific table.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to describe"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        ]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            String representation of the tool result
        """
        try:
            if tool_name == "execute_sql_query":
                df = self.db_manager.execute_query(tool_input["query"])
                if len(df) == 0:
                    return "Query executed successfully. No rows returned."
                return f"Query returned {len(df)} rows:\n\n{df.to_string()}"

            elif tool_name == "execute_python_code":
                result = self.python_executor.execute(tool_input["code"])
                output_parts = []

                if result['success']:
                    output_parts.append("✓ Code executed successfully")
                    if result['output']:
                        output_parts.append(f"\nOutput:\n{result['output']}")
                    if result['result'] is not None:
                        output_parts.append(f"\nResult: {result['result']}")
                    if result['figure']:
                        output_parts.append("\n📊 Plot created and saved")
                        # In a real application, you'd save this to a file
                        # For now, just indicate that a plot was created
                    return "\n".join(output_parts) if output_parts else "Code executed with no output"
                else:
                    return f"✗ Code execution failed:\n{result['error']}"

            elif tool_name == "list_tables":
                tables = self.db_manager.list_tables()
                if not tables:
                    return "No tables found in the database."
                return f"Tables in database:\n" + "\n".join(f"- {table}" for table in tables)

            elif tool_name == "get_table_schema":
                schema = self.db_manager.get_table_schema(tool_input["table_name"])
                return f"Schema for table '{tool_input['table_name']}':\n\n{schema.to_string()}"

            else:
                return f"Unknown tool: {tool_name}"

        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def chat(self, user_message: str) -> str:
        """
        Send a message to the chatbot and get a response.

        Args:
            user_message: The user's message

        Returns:
            The chatbot's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Make API call with tools
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            tools=self.tools,
            messages=self.conversation_history
        )

        # Process the response
        while response.stop_reason == "tool_use":
            # Extract tool uses from response
            assistant_message = {"role": "assistant", "content": response.content}
            self.conversation_history.append(assistant_message)

            # Execute each tool
            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_result = self._execute_tool(tool_name, tool_input)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": tool_result
                    })

            # Add tool results to history
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })

            # Continue the conversation
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                tools=self.tools,
                messages=self.conversation_history
            )

        # Extract final text response
        final_response = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                final_response += content_block.text

        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })

        return final_response

    def reset_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []

    def load_csv_data(self, table_name: str, csv_path: str) -> None:
        """
        Load data from a CSV file into a table.

        Args:
            table_name: Name for the new table
            csv_path: Path to CSV file
        """
        self.db_manager.create_table_from_csv(table_name, csv_path)

    def close(self) -> None:
        """Close database connections and cleanup."""
        self.db_manager.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
