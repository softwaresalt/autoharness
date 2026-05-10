# How best to compact context window

Is there a way to perform context window compaction such that it effectively truncates old context no longer relevant in the current session when the session is effectively one long running session?

The Three-Layer Pipeline Strategy
Frameworks handling highly autonomous agents generally use a tiered approach to keep the context window lean without losing the plot:

- Layer 1: Tool Result Offloading (Disk I/O): A single tool call (e.g., reading a massive log file or querying a database) can eat thousands of tokens. Harnesses will automatically write any tool response over a certain threshold (e.g., 2,000 tokens) to the local disk. The context window just keeps a file path and a 10-line preview. If the agent needs the deep details again, it can explicitly call a tool to read that offloaded file.

- Layer 2: Tool Input Eviction: The harness actively looks for and deletes the raw inputs of old "write" commands. If an agent spent 5 turns executing edit_file commands, the harness will drop the massive code diffs from the history once those changes are successfully committed, keeping only the knowledge that the file was edited.

- Layer 3: Head Summarization & Tail Preservation: Triggered automatically when the context hits a threshold (e.g., 85% capacity). The harness uses a cheaper LLM call to summarize the "head" (oldest messages) of the conversation, preserves the "tail" (the most recent 10-15% of the back-and-forth), and archives the raw original messages to disk just in case.

By combining manual commands, agent-driven triggers, and silent I/O offloading, modern CLI agents can effectively maintain a single, perpetual session that "forgets" the noise but remembers the overarching architectural decisions.
