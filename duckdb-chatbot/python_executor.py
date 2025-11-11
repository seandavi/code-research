"""
Python Executor - Safely executes Python code with access to data and plotting
"""
import io
import sys
import traceback
from typing import Dict, Any, Optional
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import base64
from io import BytesIO


class PythonExecutor:
    """Executes Python code with access to data analysis and plotting libraries."""

    def __init__(self, duckdb_manager=None):
        """
        Initialize Python executor.

        Args:
            duckdb_manager: Optional DuckDBManager instance for database access
        """
        self.duckdb_manager = duckdb_manager
        self.last_figure = None

    def execute(self, code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute Python code and return results.

        Args:
            code: Python code to execute
            context: Optional dictionary of variables to make available in execution

        Returns:
            Dictionary with execution results including:
            - success: bool
            - output: stdout output
            - error: error message if failed
            - figure: base64 encoded plot if created
            - result: any returned value
        """
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        # Prepare execution context
        exec_globals = {
            'pd': pd,
            'np': np,
            'plt': plt,
            'matplotlib': matplotlib,
        }

        # Add DuckDB connection if available
        if self.duckdb_manager:
            exec_globals['db'] = self.duckdb_manager
            exec_globals['execute_query'] = self.duckdb_manager.execute_query

        # Add user-provided context
        if context:
            exec_globals.update(context)

        exec_locals = {}
        result = {
            'success': False,
            'output': '',
            'error': None,
            'figure': None,
            'result': None
        }

        try:
            # Execute the code
            exec(code, exec_globals, exec_locals)

            # Capture any matplotlib figures
            if plt.get_fignums():
                result['figure'] = self._encode_figure()
                plt.close('all')

            # Get the output
            result['output'] = captured_output.getvalue()
            result['success'] = True

            # If there's a variable named 'result', include it
            if 'result' in exec_locals:
                result['result'] = exec_locals['result']

        except Exception as e:
            result['error'] = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            result['success'] = False

        finally:
            # Restore stdout
            sys.stdout = old_stdout

        return result

    def _encode_figure(self) -> str:
        """
        Encode the current matplotlib figure as base64 PNG.

        Returns:
            Base64 encoded PNG image
        """
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        buffer.close()
        return image_base64

    def save_figure(self, filepath: str) -> bool:
        """
        Save the current matplotlib figure to a file.

        Args:
            filepath: Path where to save the figure

        Returns:
            True if successful, False otherwise
        """
        try:
            if plt.get_fignums():
                plt.savefig(filepath, bbox_inches='tight', dpi=100)
                plt.close('all')
                return True
            return False
        except Exception as e:
            print(f"Error saving figure: {e}")
            return False
