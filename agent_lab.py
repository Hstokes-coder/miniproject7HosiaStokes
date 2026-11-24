# INF601 - Advanced Programming in Python
# Hosia Stokes
# Week 14 - Agent SDK Lab

"""Run a Claude agent with the Claude Agent SDK and print its answer.

The agent identifies three common network security risks and recommends a
solution for each one.

Authentication: the Agent SDK runs the Claude Code CLI behind the scenes.
When ANTHROPIC_API_KEY is not set, it uses the account you are already
logged in to in Claude Code (your subscription), so no API key is needed.
"""

import asyncio
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    CLINotFoundError,
    ResultMessage,
    TextBlock,
    query,
)

PROMPT = (
    "Identify three common network security risks. For each one, give:\n"
    "1. The risk's name\n"
    "2. A one- or two-sentence explanation of why it is dangerous\n"
    "3. A recommended solution\n"
    "Format the answer in plain text with a numbered list, suitable for "
    "printing in a terminal. Keep it under 300 words."
)

OPTIONS = ClaudeAgentOptions(
    system_prompt=(
        "You are a network security instructor helping college students. "
        "Give clear, accurate, beginner-friendly answers."
    ),
    tools=[],                # this task needs no file, shell, or web tools
    setting_sources=[],      # don't load project settings, skills, or hooks
    strict_mcp_config=True,  # don't connect to any MCP servers (e.g. Practice Hub)
    max_turns=1,             # a single answer is all this task needs
)


async def run_agent() -> int:
    """Send the prompt to the agent, print its reply, and return an exit code."""
    print("Asking the agent about network security risks...\n")
    answer_parts = []
    result = None

    # Read every message until the stream ends on its own. Leaving the loop
    # early (with return or break) makes the SDK print a cleanup warning.
    async for message in query(prompt=PROMPT, options=OPTIONS):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    answer_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            result = message

    if result is None:
        print("The agent ended without returning a result.")
        return 1
    if result.is_error:
        print(f"The agent reported an error: {result.result or result.subtype}")
        return 1

    print("\n".join(answer_parts).strip())
    print("\n" + "-" * 60)
    print(f"Finished in {result.duration_ms / 1000:.1f} s, {result.num_turns} turn(s).")
    return 0


def main() -> None:
    try:
        exit_code = asyncio.run(run_agent())
    except CLINotFoundError:
        print("Claude Code was not found. Install it and run `claude` once to log in.")
        exit_code = 1
    except ClaudeSDKError as e:
        print(f"Agent SDK error: {e}")
        exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
