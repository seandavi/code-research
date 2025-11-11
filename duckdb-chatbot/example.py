"""
Example usage of the DuckDB Chatbot
"""
import os
from chatbot import DuckDBChatbot


def main():
    # Get API key from environment variable
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    # Create chatbot with in-memory database
    print("Initializing DuckDB Chatbot...")
    with DuckDBChatbot(api_key=api_key, database_path=":memory:") as bot:

        # Example 1: Create sample data
        print("\n" + "="*60)
        print("Example 1: Creating sample data")
        print("="*60)

        response = bot.chat("""
        Create a sample sales dataset with the following Python code:

        import pandas as pd
        data = {
            'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'product': ['A', 'B', 'A', 'C', 'B'],
            'sales': [100, 150, 120, 200, 180],
            'profit': [20, 35, 25, 50, 40]
        }
        df = pd.DataFrame(data)
        db.create_table_from_dataframe('sales', df)
        print("Sample data created successfully!")
        """)
        print(f"\nBot: {response}")

        # Example 2: Query the data
        print("\n" + "="*60)
        print("Example 2: Querying the database")
        print("="*60)

        response = bot.chat("Show me all the sales data ordered by date")
        print(f"\nBot: {response}")

        # Example 3: Perform aggregation
        print("\n" + "="*60)
        print("Example 3: Data aggregation")
        print("="*60)

        response = bot.chat("What is the total sales and profit by product?")
        print(f"\nBot: {response}")

        # Example 4: Create a visualization
        print("\n" + "="*60)
        print("Example 4: Creating a plot")
        print("="*60)

        response = bot.chat("""
        Create a bar chart showing total sales by product.
        Use matplotlib and make it look professional with labels and title.
        """)
        print(f"\nBot: {response}")

        # Example 5: Complex analysis
        print("\n" + "="*60)
        print("Example 5: Complex analysis with Python")
        print("="*60)

        response = bot.chat("""
        Calculate the profit margin (profit/sales) for each product and
        create a visualization comparing profit margins. Also tell me which
        product has the highest margin.
        """)
        print(f"\nBot: {response}")


def interactive_mode():
    """Run the chatbot in interactive mode."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return

    print("="*60)
    print("DuckDB Chatbot - Interactive Mode")
    print("="*60)
    print("Type 'exit' or 'quit' to end the conversation")
    print("Type 'reset' to clear conversation history")
    print("Type 'tables' to list all tables")
    print("="*60 + "\n")

    with DuckDBChatbot(api_key=api_key, database_path=":memory:") as bot:
        while True:
            try:
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break

                if user_input.lower() == 'reset':
                    bot.reset_conversation()
                    print("Conversation history cleared.")
                    continue

                if user_input.lower() == 'tables':
                    tables = bot.db_manager.list_tables()
                    print(f"Tables: {tables}")
                    continue

                response = bot.chat(user_input)
                print(f"\nBot: {response}")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_mode()
    else:
        main()
