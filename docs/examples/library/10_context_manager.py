"""
Example 10: Context Manager — Share context across agents with token budgeting.

The ContextManager maintains a sliding window of context entries,
automatically pruning old entries when the token budget is exceeded.
"""
from nixclaw import ContextManager


def main():
    # Create a context manager with a 1000-token budget
    ctx = ContextManager(max_tokens=1000)

    # Add context from different sources
    ctx.add("user", "I need to build a REST API for a todo app")
    ctx.add("orchestrator", "Breaking down into subtasks: models, routes, tests")
    ctx.add("code_generator", "Created Todo model with id, title, completed fields")
    ctx.add("code_generator", "Created GET/POST/PUT/DELETE endpoints")
    ctx.add("analyzer", "Code review: missing input validation on POST endpoint")
    ctx.add("debugger", "Fixed: added Pydantic schema validation")

    # Get full context
    print("=== Full Context ===")
    print(ctx.get_context())
    print(f"\nEntries: {ctx.entry_count}")
    print(f"Token usage: {ctx.token_usage}")

    # Get context for a specific agent (excludes their own messages)
    print("\n=== Context for Analyzer (excludes own messages) ===")
    print(ctx.get_context_for_agent("analyzer"))

    # Get only the last 3 entries
    print("\n=== Last 3 Entries ===")
    print(ctx.get_context(max_entries=3))

    # Add a large entry to trigger pruning
    ctx.add("researcher", "Detailed analysis: " + "x" * 4000)
    print(f"\nAfter large entry - Entries: {ctx.entry_count}, Tokens: {ctx.token_usage}")

    # Clear
    ctx.clear()
    print(f"After clear - Entries: {ctx.entry_count}, Tokens: {ctx.token_usage}")


if __name__ == "__main__":
    main()
