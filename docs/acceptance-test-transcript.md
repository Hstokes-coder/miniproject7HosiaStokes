# Mini Project 7 – Acceptance Test Transcript

**INF601 – Advanced Programming in Python · Hosia Stokes Jr**

- **Date:** November 14, 2026 (about 7:38 AM Pacific)
- **Client:** Claude Code v2.1.325, started in `~/mini_project_7`
- **MCP server:** `practice-hub` (this repository's `server.py`, stdio transport),
  registered with `claude mcp add` as shown in the README
- **API:** `https://practice.fhsucyber.com`

## Redaction notes

- The API token was never typed into the Claude Code session. It is passed to the
  server only through the `PRACTICE_API_TOKEN` environment variable, so it does not
  appear in the export.
- The exported file contained no tokens, passwords, cookies, or email addresses, so no
  redactions were needed inside the conversation.
- Two Claude Code startup notices (a model promotion and a hidden-notice count) were
  left out because they are unrelated to the test. Everything else is copied exactly
  from the `/export` file.

## Notes on how the test ran

- All three test prompts were sent in a single message, so Claude Code ran the
  `list_posts` call at the same time as `create_post`. That is why the post list came
  back empty: the list was taken just before the new post existed.
- The export collapses the tool-call details ("Called practice-hub 3 times"). The
  results below are Claude Code's summary of what the three tool calls returned.

## Transcript

```text
▗ ▗   ▖ ▖  Claude Code v2.1.325
           Opus 5.5 · Claude Pro
 ▘▘   ▝▝   ~/mini_project_7

❯ Use the practice-hub tools to list my Practice Hub posts.
  Create a Practice Hub post titled "MP7 acceptance test" with the body
  "Created by Claude Code through my FastMCP server." and the tags inf601 and
  mcp.
  Change the title of that post to "MP7 acceptance test – edited".

  Called practice-hub 3 times (ctrl+o to expand)

⏺ All three steps ran through your practice-hub MCP server.

  1. Listed your posts: you had none. I ran the list at the same moment as the
     create, so the empty result is from just before the new post existed.
  2. Created the post: it got id 60, with the title "MP7 acceptance test", the
     body "Created by Claude Code through my FastMCP server." and the tags
     inf601 and mcp.
  3. Changed the title: post 60 is now titled "MP7 acceptance test – edited".
     The body and tags didn't change, and updated_at moved from 15:37:55 to
     15:37:58.

  If you want, I can list your posts again so the edited post shows up in the
  results.

✻ Cooked for 13s · done 7:38 AM
```

## Result

| Acceptance step | Tool | Outcome reported |
|---|---|---|
| 1. Read my posts | `list_posts` | Succeeded; returned an empty list (taken before the new post existed) |
| 2. Create a test post | `create_post` | Succeeded; created post **60** |
| 3. Modify its title | `update_post` | Succeeded; post 60 retitled "MP7 acceptance test – edited" |

## Follow-up verification (read-only)

Run the same day at 10:13 AM Pacific in a new Claude Code session in
`~/mini_project_7`. The prompts asked Claude Code to use only `list_posts`
(`mine=true`) and `get_post`, and not to create, update, or delete anything. The
output below is copied from my Terminal with Claude Code's detailed transcript
view (Ctrl+O) turned on.

```text
⏺ Here is post 60 from get_post. I didn't create, update or delete anything.

  ┌─────────────┬───────────────────────────────────────────────────┐
  │    Field    │                       Value                       │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ id          │ 60                                                │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ title       │ MP7 acceptance test – edited                      │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ body        │ Created by Claude Code through my FastMCP server. │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ tags        │ inf601, mcp                                       │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ author_name │ Hosia Stokes                                      │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ created_at  │ 2026-11-14T15:37:55.719923                        │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ updated_at  │ 2026-11-14T15:37:58.040500                        │
  └─────────────┴───────────────────────────────────────────────────┘

  The values are the same as what list_posts returned.

✻ Crunched for 5s · done 10:13 AM
```

What this confirms:

- Post 60 exists and belongs to me (`author_name`: Hosia Stokes).
- Its title is **"MP7 acceptance test – edited"**, so the `update_post` call worked.
- The body ("Created by Claude Code through my FastMCP server.") and tags
  (`inf601`, `mcp`) match what `create_post` sent, so the update changed only the
  title.
- `created_at` (15:37:55) and `updated_at` (15:37:58 UTC) match the original
  acceptance test, which shows this verification did not modify the post.
- Only the `get_post` result was captured. The `list_posts` response itself was
  scrolled out of view; Claude Code reported that it returned the same values.

## Unit tests on macOS

`python -m unittest -v`, run on my Mac in the project's `.venv` (Python 3.14,
`mcp` 1.30.0, `httpx` 0.28.1). Shortened to the final lines; all 19 tests
showed `ok`:

```text
test_update_post_with_nothing_to_change (test_server.ServerTests.test_update_post_with_nothing_to_change) ... ok

----------------------------------------------------------------------
Ran 19 tests in 0.002s

OK
```

## Server registration check

```text
practice-hub: /Users/hosiastokes/mini_project_7/.venv/bin/python /Users/hosiastokes/mini_project_7/server.py - ✔ Connected
```
