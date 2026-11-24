# Mini Project 7 – Practice Hub MCP Server

**INF601 – Advanced Programming in Python**
**Hosia Stokes Jr**

A [FastMCP](https://github.com/modelcontextprotocol/python-sdk) server that wraps the
Practice Hub REST API (`https://practice.fhsucyber.com`) so Claude Code can read,
create, update, and delete posts by calling MCP tools.

## How it works

MCP (Model Context Protocol) is a standard way for an AI assistant to call tools
that a program provides. `server.py` is that program:

1. Claude Code starts `server.py` and talks to it over **stdio** (standard input and
   output).
2. The server tells Claude which tools exist, using each function's name, type hints,
   and docstring.
3. When Claude calls a tool, the server sends the matching HTTP request to Practice Hub
   with your API token and returns the JSON result.

## Tools

| Tool | HTTP request | What it does |
|---|---|---|
| `list_posts(mine=False)` | `GET /api/v1/posts?mine=...` | Lists posts, newest first (the API returns up to 50). `mine=True` shows only your posts. |
| `get_post(post_id)` | `GET /api/v1/posts/{id}` | Gets one post by ID. |
| `create_post(title, body="", tags=None)` | `POST /api/v1/posts` | Creates a post you own. `title` is required; `tags` is a list of strings. |
| `update_post(post_id, title=None, body=None, tags=None)` | `PATCH /api/v1/posts/{id}` | Changes only the fields you pass, on one of **your** posts. |
| `delete_post(post_id)` | `DELETE /api/v1/posts/{id}` | Permanently deletes one of **your** posts. |

Endpoints, methods, and fields follow the Practice Hub API Guide
(`https://practice.fhsucyber.com/docs-guide`). Every request sends
`Authorization: Bearer <token>`.

## Error handling

All requests go through one helper, `_request()`. It turns problems into clear
messages, raised as FastMCP `ToolError`s. Claude sees a readable explanation, and the
server keeps running for the next request.

| Situation | Message Claude receives |
|---|---|
| 401 | Authentication failed: token missing, invalid, or expired |
| 403 | Permission denied: the post belongs to another user |
| 404 | Not found: the post does not exist |
| 422 | Practice Hub rejected the data, plus the API's own reason |
| Other 4xx/5xx | Practice Hub API error with the status code and details |
| Timeout (15 s) or connection failure | Practice Hub could not be reached |
| Empty title, or `update_post` with nothing to change | Rejected before any request is sent |

Error messages never include the API token. If `PRACTICE_API_URL` or
`PRACTICE_API_TOKEN` is missing at startup, the server stops with a message naming the
missing variable.

## Project files

```
mini_project_7/
├── server.py            # The FastMCP server and its five tools
├── agent_lab.py         # Week 14 Agent SDK lab (see "Agent SDK Lab" below)
├── test_server.py       # Offline unit tests (fake API, no token needed)
├── requirements.txt     # mcp==1.30.0, httpx==0.28.1, claude-agent-sdk==0.2.188
├── .claude/skills/post-summarizer/
│   └── SKILL.md         # Week 14 Agent Skill (see "Agent Skill" below)
├── docs/                # Acceptance-test transcript and Week 14 skill and SDK lab test results
├── .gitignore           # Keeps .venv, .env, caches, and secrets out of Git
└── README.md
```

## Installation (macOS)

Requires Python 3.10 or newer (built with Python 3.14).

```bash
cd ~/mini_project_7
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`mcp` is pinned below version 2. In `mcp` 2.x, `FastMCP` was renamed `MCPServer`, and
the starter code's `from mcp.server.fastmcp import FastMCP` no longer works.

## Environment variables

| Variable | Example | Purpose |
|---|---|---|
| `PRACTICE_API_URL` | `https://practice.fhsucyber.com` | Base URL of the API (no trailing slash needed) |
| `PRACTICE_API_TOKEN` | *(your token)* | Your personal Practice Hub API token |

The token is **never** written in the source code or committed to Git. To load it
into your current Terminal without it appearing on screen or in your shell history
(zsh, the macOS default):

```bash
read -s "PRACTICE_API_TOKEN?Paste your Practice Hub API token: "; echo
export PRACTICE_API_TOKEN
export PRACTICE_API_URL=https://practice.fhsucyber.com
```

## Running the tests

The tests replace the real API with a fake one, so they need no token and no internet
connection:

```bash
source .venv/bin/activate
python -m unittest -v
```

They cover the request each tool sends (method, path, and data), the 401, 403, 404,
422, and 500 messages, timeouts, connection failures, and a check that the token never
appears in an error message.

## Registering the server with Claude Code

Run this from the project folder, in a Terminal where `PRACTICE_API_TOKEN` is loaded
(see above):

```bash
cd ~/mini_project_7
claude mcp add --env PRACTICE_API_URL=https://practice.fhsucyber.com \
  --env PRACTICE_API_TOKEN="$PRACTICE_API_TOKEN" \
  --transport stdio practice-hub \
  -- /Users/hosiastokes/mini_project_7/.venv/bin/python /Users/hosiastokes/mini_project_7/server.py
```

- `--transport stdio` sits between the last `--env` and the server name on purpose.
  `--env` accepts several values, so a name placed right after it would be read as
  another variable.
- Everything after `--` is the command Claude Code runs. It uses the virtual
  environment's Python, so `mcp` and `httpx` are available.
- This uses the default **local** scope. The configuration, including the token, is
  saved privately in `~/.claude.json` in your home folder, **not** in this repository.
  Do not use `--scope project`: it would write a `.mcp.json` file into the project
  folder. (`.gitignore` also blocks `.mcp.json` as a safety net.)

Check that it connected:

```bash
claude mcp list          # should show practice-hub ... ✔ Connected
```

Inside Claude Code, `/mcp` shows the server and its five tools. To remove it:
`claude mcp remove practice-hub`.

## Acceptance test

Start Claude Code in the project folder (`cd ~/mini_project_7 && claude`) and ask:

1. **Read posts:** "Use the practice-hub tools to list my Practice Hub posts."
2. **Create a post:** "Create a Practice Hub post titled 'MP7 acceptance test' with
   the body 'Created by Claude Code through my FastMCP server.' and the tags inf601
   and mcp."
3. **Modify its title:** "Change the title of that post to 'MP7 acceptance test –
   edited'."

Claude should call `list_posts`, `create_post`, and `update_post`, in that order.

**Result (November 14, 2026):** all three tool calls succeeded through Claude Code.
`create_post` created post 60, and `update_post` changed its title to
"MP7 acceptance test – edited". The redacted transcript is in
[`docs/acceptance-test-transcript.md`](docs/acceptance-test-transcript.md).

## Agent Skill: `post-summarizer` (Week 14)

`.claude/skills/post-summarizer/SKILL.md` is a Claude Code Agent Skill. It reads your
Practice Hub posts through the `practice-hub` MCP server, summarizes them into a study
note, and publishes the note as a new post **only after you approve it**.

### Requirements

- The `practice-hub` server is registered and connected (see
  [Registering the server with Claude Code](#registering-the-server-with-claude-code)).
- Claude Code is started from this project folder, so it finds the skill in `.claude/skills/`.

### Using it

```bash
cd ~/mini_project_7
claude
```

Then, inside Claude Code:

1. Type `/post-summarizer`. You can also ask in plain words, for example "summarize my
   Practice Hub posts into a study note", and Claude Code loads the skill itself.
2. Claude calls `list_posts` with `mine=true`, then shows the draft study note, the number of
   posts, and the proposed title (`Study Note - Practice Hub Digest`) and tags.
3. Reply with your approval (for example, "Yes, publish it with inf601 and mcp tags") or ask
   for changes. Nothing is posted until you approve.
4. Claude calls `create_post` and then `get_post` to confirm the new post, and shows you its ID.

### Safety rules in the skill

- Only `list_posts` and `get_post` (read-only) are pre-approved in `allowed-tools`.
  Claude Code still asks permission before `create_post` runs.
- The skill never calls `update_post` or `delete_post`, so existing posts are not changed.
- If no posts are found, it says so and does not publish.
- The API token stays in the server's environment and is never shown.

Each approved run creates a **new** post. It does not update an earlier digest, so
delete old digests by hand in Practice Hub if you only want one.

**Result (November 23–24, 2026):** the skill published post 70 and post 71 after
approval, and `get_post` confirmed both. Post 60 was not changed. Full results are in
[`docs/week14-agent-skill-test.md`](docs/week14-agent-skill-test.md).

## Agent SDK Lab (Week 14)

`agent_lab.py` uses the [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk)
(`claude-agent-sdk`) to run an agent on a small task: it names three common network
security risks, recommends a solution for each, and prints the answer.

### How it works

- `asyncio.run()` starts `run_agent()`, which calls the SDK's `query()` with a prompt
  and `ClaudeAgentOptions`, and reads the agent's messages as they stream in.
- The text from each `AssistantMessage` is collected. The final `ResultMessage` reports
  whether the run succeeded, how long it took, and how many turns it used.
- The agent gets **no tools** (`tools=[]`), no project settings or skills
  (`setting_sources=[]`), no MCP servers (`strict_mcp_config=True`), and one turn
  (`max_turns=1`). It can only answer, so it cannot reach Practice Hub or change files.

### Authentication

The Agent SDK runs Claude Code behind the scenes. When `ANTHROPIC_API_KEY` is **not**
set, it uses the account you are logged in to in Claude Code, so no API key is needed.
Run `claude` once and log in first if you haven't already.

### Running it

```bash
cd ~/mini_project_7
source .venv/bin/activate
pip install -r requirements.txt
python agent_lab.py
```

**Result (November 23, 2026):** the program exited with code 0 after 9.6 seconds and
1 turn. It printed three risks with solutions: phishing (security training, email
filtering, MFA), unpatched software (patch management and automatic updates), and weak
or default passwords (strong password policies, password managers, MFA). Sample output:

```
Asking the agent about network security risks...

THREE COMMON NETWORK SECURITY RISKS

1. Phishing Attacks
   Risk: Phishing
   Why it's dangerous: Attackers send fake emails or messages that
   trick users into revealing passwords or installing malware. ...
   Solution: Provide regular security awareness training, enable
   email filtering, and require multi-factor authentication (MFA) ...
...
------------------------------------------------------------
Finished in 9.6 s, 1 turn(s).
```

Full test results, including versions, the sign-in check, the asynchronous generator
error found on the first run and its fix, and a requirements table, are in
[`docs/week14-agent-sdk-test.md`](docs/week14-agent-sdk-test.md).

## AI Usage

This project was built with help from **Claude** (Anthropic) as a coding assistant, in
line with the course AI Use Policy.

**What I did:**
- Supplied the assignment requirements and the professor's starter code.
- Chose to pin `mcp` below version 2 so the FastMCP starter code works as written, and
  installed the packages in my own virtual environment.
- Reviewed the code, made the decisions, and ran the commands that use my real API
  token (tests, registration, and the acceptance test) on my own Mac.

**What Claude helped with:**
- Confirming the endpoints, HTTP methods, and JSON fields from the Practice Hub API
  Guide before writing any tools.
- Writing the shared `_request()` error handling and the `get_post`, `create_post`,
  `update_post`, and `delete_post` tools, while keeping the starter code's structure.
- Writing the offline unit tests, `requirements.txt`, `.gitignore`, and this README.
- Explaining each part of the code in beginner-friendly terms, and preparing the
  Claude Code registration command and acceptance-test steps.
- Week 14: moving `SKILL.md` into `.claude/skills/post-summarizer/`, matching its tool
  parameters to `server.py`, running the skill through Claude Code, and writing
  `docs/week14-agent-skill-test.md`. I approved each post before it was published.
- Week 14 Agent SDK lab: writing `agent_lab.py` against the installed
  `claude-agent-sdk` package, running it with my Claude Code login (no API key), and
  fixing a cleanup warning found on the first run. I reviewed the results before they
  were committed.

My API token was never shared with Claude or written into any file in this repository.
