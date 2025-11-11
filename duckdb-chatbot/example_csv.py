"""
Example demonstrating CSV data loading and analysis
"""
import os
from chatbot import DuckDBChatbot


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    print("Initializing DuckDB Chatbot with CSV data...")
    with DuckDBChatbot(api_key=api_key, database_path=":memory:") as bot:

        # Load sample CSV data
        print("\nLoading sample data from CSV...")
        bot.load_csv_data("employees", "sample_data.csv")
        print("Data loaded successfully!")

        # Example queries
        examples = [
            "Show me the first 5 rows of the employees table",
            "What is the average salary by department?",
            "Which city has the highest average salary?",
            """Create a visualization showing the distribution of employees
            by department with a bar chart""",
            """Analyze the relationship between age and salary.
            Create a scatter plot and calculate the correlation.""",
        ]

        for i, query in enumerate(examples, 1):
            print("\n" + "="*60)
            print(f"Example {i}")
            print("="*60)
            print(f"Query: {query}")
            print("-"*60)

            response = bot.chat(query)
            print(f"Bot: {response}")


if __name__ == "__main__":
    main()
