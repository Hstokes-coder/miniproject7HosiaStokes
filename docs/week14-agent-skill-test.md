# Week 14 – Agent Skill Test Results

**INF601 – Advanced Programming in Python · Hosia Stokes Jr**

- **Skill:** `post-summarizer` (`.claude/skills/post-summarizer/SKILL.md`)
- **Dates:** November 23–24, 2026 (times below are UTC, as returned by the API)
- **Client:** Claude Code v2.1.325, updated to v2.1.331 during testing, started in `~/mini_project_7`
- **MCP server:** `practice-hub` (this repository's `server.py`, stdio transport)
- **API:** `https://practice.fhsucyber.com`

## What the skill does

1. Calls `list_posts` with `mine=true` to read my posts.
2. Groups the posts by topic and drafts a Markdown study note
   (Topics, Key Points, Takeaways, Next Steps).
3. Shows me the draft, the post count, and the proposed title and tags.
4. Waits for my explicit approval.
5. Calls `create_post` with the title "Study Note - Practice Hub Digest".

It never calls `update_post` or `delete_post`.

## Fixes made before testing

| Problem | Fix |
|---|---|
| `SKILL.md` sat at the repository root, so Claude Code did not list it as a skill. | Moved it to `.claude/skills/post-summarizer/SKILL.md`. After the move, Claude Code listed `post-summarizer` as an available skill. |
| Step 1 used `list_posts` with `mine=true` and `limit=25`, but `list_posts` in `server.py` only takes `mine`. | Removed `limit=25` and noted that the server returns up to 50 posts, newest first. |
| Tool names were bare (`list_posts`). | Used the full Claude Code names (`mcp__practice-hub__list_posts`, etc.) so the skill clearly uses this server. |
| The skill gave no guidance for an empty result. | Added: if no posts come back, say so and do not create a post. |

The front matter also gained `allowed-tools`, which lists only the two
read-only tools (`list_posts` and `get_post`). `create_post` is left out on
purpose, so Claude Code still asks permission before it runs.

## Parameter check against `server.py`

| Tool | Parameters in `server.py` | Used by the skill |
|---|---|---|
| `list_posts` | `mine: bool = False` | `mine=true` |
| `get_post` | `post_id: int` | only if full details are needed |
| `create_post` | `title: str`, `body: str = ""`, `tags: list[str] \| None = None` | `title`, `body`, `tags=["inf601", "mcp"]` |

## Test runs

### Run 1 – first digest (post 70)

1. I typed `/post-summarizer`. Claude Code loaded the skill from
   `.claude/skills/post-summarizer`.
2. `list_posts(mine=true)` returned **1 post**: #60, "MP7 acceptance test – edited".
3. Claude showed the draft with the title, the tags `inf601` and `mcp`, and the
   post count, then asked for approval. It published **nothing** until I replied.
4. Running `/post-summarizer` a second time without replying did **not** count as
   approval. Claude asked again.
5. I replied "Yes, publish it with inf601 and mcp tags."
6. `create_post` returned **post 70**, created at 2026-11-24 05:49:41.
7. Verification: `get_post(70)` returned the same title, tags, and body, and
   `list_posts(mine=true)` showed 2 posts (#70, #60).

### Run 2 – after a Claude Code restart (post 71)

1. After `/restart`, I typed `/post-summarizer` again.
2. `list_posts(mine=true)` returned **2 posts** (#70, #60).
3. Before showing the draft, Claude warned that publishing would create a second post
   with the same title as #70.
4. I approved, and `create_post` returned **post 71**, created at
   2026-11-24 05:56:41. Its study note covers posts #60 and #70.
5. Verification: `get_post(71)` matched the approved draft, and
   `list_posts(mine=true)` showed 3 posts (#71, #70, #60).

### Run 3 – repeated approval with no new draft

I sent another "Yes, publish…" message when no new draft was waiting. Claude did
**not** create a duplicate post. It read post 71 back with `get_post` instead and
asked me to confirm before publishing another copy.

## Results

| Requirement | Result |
|---|---|
| Skill is found and runs as `/post-summarizer` | Pass |
| Retrieves my posts through the `practice-hub` MCP server | Pass |
| Summarizes them into a study note with the required sections | Pass |
| Shows the draft and asks for approval before publishing | Pass (it also didn't publish when I re-ran the skill or repeated my approval) |
| Publishes with the correct title and tags | Pass (posts 70 and 71) |
| Verifies the new post with `get_post` | Pass |
| Does not modify or delete existing posts | Pass: post 60's `updated_at` stayed 2026-11-14 15:37:58, and post 70's stayed unchanged |
| No API token in the session, files, or output | Pass: the token is only passed through `PRACTICE_API_TOKEN` and never appeared |

## Notes

- Posts 70 and 71 have the same title, because each run publishes a new post. To keep only
  one digest, delete #70 by hand in Practice Hub. The skill itself never deletes posts.
- Not tested: declining a draft or asking for changes (step 5's revise path), and an
  account with no posts.
