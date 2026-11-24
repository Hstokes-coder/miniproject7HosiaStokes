# Week 14 – Agent SDK Lab Test Results

**INF601 – Advanced Programming in Python · Hosia Stokes**

- **Date:** November 23, 2026 (Pacific time)
- **Program:** `agent_lab.py`
- **Commit with the lab:** `a55a584` "Add Week 14 Agent SDK lab"

## Assignment objective

Write a short Python program that uses the Claude Agent SDK to run an agent on a small
task and print its result. The program must:

- use `asyncio` and the official Claude Agent SDK,
- run an agent that identifies three common network security risks and recommends a
  solution for each,
- print the agent's response in the terminal,
- sign in with my existing Claude Code subscription, without creating an API key.

## Versions

| Component | Version |
|---|---|
| macOS | Darwin 25.6.0 |
| Python (project `.venv`) | 3.14.7 |
| `claude-agent-sdk` | 0.2.188 |
| Claude Code CLI | 2.1.331 |

## Installation

From the project folder, using the existing virtual environment:

```bash
cd ~/mini_project_7
source .venv/bin/activate
pip install -r requirements.txt     # includes claude-agent-sdk==0.2.188
```

The SDK runs the Claude Code CLI behind the scenes, so Claude Code must be installed
and logged in (`claude`, then log in once).

After installing, `pip check` reported `No broken requirements found.`, so the SDK
works alongside the project's pinned `mcp==1.30.0` and `httpx==0.28.1`.

## How `agent_lab.py` works

1. **The task.** `PROMPT` asks for three common network security risks. For each one it
   wants the name, why it is dangerous, and a recommended solution, as a numbered plain-text
   list of under 300 words.
2. **Agent options.** `ClaudeAgentOptions` sets:
   - `system_prompt`: the agent acts as a network security instructor for college students.
   - `tools=[]`: no built-in tools (files, shell, web). The task only needs an answer.
   - `setting_sources=[]`: no project settings, skills, or hooks are loaded.
   - `strict_mcp_config=True`: no MCP servers are connected, so the agent cannot reach
     Practice Hub.
   - `max_turns=1`: the agent answers once.
3. **Running the agent.** `main()` calls `asyncio.run(run_agent())`. `run_agent()` loops
   over `query(prompt=PROMPT, options=OPTIONS)` with `async for`. It collects the
   `TextBlock` text from each `AssistantMessage` and keeps the final `ResultMessage`.
4. **Printing the result.** After the stream ends, the program checks the
   `ResultMessage`. If the run succeeded, it prints the answer and then the time taken and
   number of turns, and exits with code 0. If there was no result or the result was an
   error, it prints a message and exits with code 1.
5. **Errors.** `CLINotFoundError` (Claude Code not installed) and other `ClaudeSDKError`s
   are caught and printed as readable messages instead of a traceback.

## Subscription authentication (no API key)

The Agent SDK uses `ANTHROPIC_API_KEY` if it is set. Otherwise it uses the account
logged in to Claude Code. Checks made before and during testing:

| Check | Result |
|---|---|
| `ANTHROPIC_*` environment variables in the shell | None set (`env \| grep -c '^ANTHROPIC_'` printed `0`) |
| How the program was run | `env -u ANTHROPIC_API_KEY .venv/bin/python agent_lab.py`, which guarantees no API key |
| `claude auth status --json` (sign-in fields only) | `loggedIn: true`, `authMethod: claude.ai`, `apiProvider: firstParty`, `subscriptionType: pro` |
| API key in `agent_lab.py` or the repository | None. The program never reads or sets a key. |

No API key was created. The agent ran on my Claude Pro subscription through my Claude
Code login.

## Test runs

All runs used the same command from the project folder:

```bash
env -u ANTHROPIC_API_KEY .venv/bin/python agent_lab.py
```

### Run 1 – first version: worked, but printed an asynchronous generator error

The answer printed correctly and the exit code was 0, but this appeared before the output:

```
An error occurred during closing of asynchronous generator <async_generator object InternalClient._process_query_inner at 0x107f1e840>
asyncgen: <async_generator object InternalClient._process_query_inner at 0x107f1e840>
RuntimeError: aclose(): asynchronous generator is already running
Asking the agent about network security risks...

1. Phishing Attacks
   ...
------------------------------------------------------------
Finished in 6.1 s, 1 turn(s).
exit code: 0
```

**Cause.** The first version printed the answer and called `return` from **inside** the
`async for message in query(...)` loop as soon as the `ResultMessage` arrived. Leaving
the loop early stopped `query()`'s asynchronous generator before it had finished. Python
then tried to close the generator while the SDK's own inner generator was still running,
which raised `RuntimeError: aclose(): asynchronous generator is already running` during
cleanup.

**Fix.** The loop no longer returns early. It saves the `ResultMessage` in a variable
(`result = message`) and keeps reading until the stream ends on its own. The answer is
checked and printed **after** the loop:

```python
async for message in query(prompt=PROMPT, options=OPTIONS):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                answer_parts.append(block.text)
    elif isinstance(message, ResultMessage):
        result = message

if result is None:
    ...
```

### Run 2 – after the fix

stderr was saved to a separate file to check for warnings.

- Exit code: **0**
- `Finished in 9.6 s, 1 turn(s).`
- stderr: **empty**, so the error was gone
- Risks returned: phishing, unpatched software and systems, weak or default passwords,
  each with a solution

### Run 3 – final run, after `requirements.txt` and the README were updated

stdout and stderr were captured together. This is the full output:

```
Asking the agent about network security risks...

Three Common Network Security Risks

1. Phishing Attacks
   Why it's dangerous: Attackers send fake emails or messages that trick users into revealing passwords or installing malware. One click can give an attacker a foothold inside the entire network.
   Solution: Train users regularly to recognize suspicious messages, enable email filtering, and require multi-factor authentication (MFA) so stolen passwords alone are not enough.

2. Unpatched Software and Systems
   Why it's dangerous: Outdated operating systems, applications, and firmware often contain publicly known vulnerabilities. Attackers use automated tools to scan for and exploit these weaknesses quickly.
   Solution: Set up a patch management process. Enable automatic updates where possible, keep an inventory of all devices, and apply critical security patches promptly.

3. Weak or Default Passwords
   Why it's dangerous: Simple, reused, or factory-default passwords are easily guessed or cracked through brute-force and credential-stuffing attacks. A single compromised account can lead to wider network access.
   Solution: Enforce strong password policies (long passphrases), change all default credentials on routers and devices, use a password manager, and enable MFA on all important accounts.

Key takeaway: Most breaches exploit human error or basic hygiene gaps. User training, timely updates, and strong authentication prevent a large share of attacks.

------------------------------------------------------------
Finished in 8.1 s, 1 turn(s).
```

Exit code: **0**. No warnings or errors appeared in the captured output.

The agent's wording changes a little between runs, as expected from a language model.
All three runs returned the same three risks.

## Existing unit tests

`agent_lab.py` does not change `server.py`, so the Mini Project 7 tests were rerun to
confirm nothing broke:

```
$ .venv/bin/python -m unittest -v
...
Ran 19 tests in 0.002s

OK
```

19 of 19 tests passed, both before and after `requirements.txt` was updated.

## Results against the requirements

| Requirement | Result | Evidence |
|---|---|---|
| Uses the official Claude Agent SDK | **Pass** | `from claude_agent_sdk import query, ClaudeAgentOptions, ...` (`claude-agent-sdk` 0.2.188) |
| Uses `asyncio` | **Pass** | `asyncio.run(run_agent())`, with `async for` over `query()` |
| Runs an agent from code on a small task | **Pass** | `query()` with `ClaudeAgentOptions`, 1 turn per run |
| Identifies three network security risks, each with a solution | **Pass** | Runs 1–3: phishing, unpatched software, weak or default passwords |
| Prints the agent's response in the terminal | **Pass** | Run 3 output above |
| Signs in with the Claude Code subscription, no API key | **Pass** | No `ANTHROPIC_*` variables, run with `env -u ANTHROPIC_API_KEY`, `authMethod: claude.ai`, `subscriptionType: pro` |
| Program runs without errors | **Pass** after the fix | Run 1 had the `aclose()` error; runs 2 and 3 exited 0 with no errors |
| Required header at the top of `agent_lab.py` | **Pass** | Lines 1–3 of `agent_lab.py` |
| Existing unit tests still pass | **Pass** | 19 of 19 OK |
| `server.py`, the `post-summarizer` skill, and Practice Hub posts unchanged | **Pass** | Not in the lab's commits, and the agent had no MCP access |
| No credentials exposed | **Pass** | Staged changes scanned for tokens before each commit; none found |

## Not tested

- Running without Claude Code installed or logged in, so the `CLINotFoundError` and
  `ClaudeSDKError` messages were not seen in practice.
- Running on a computer other than this Mac.
