---
name: post-summarizer
description: Summarize my recent Practice Hub posts into a Markdown study note using the practice-hub MCP server, then publish it as a new post only after I approve. Use when I ask to summarize, digest, or make a study note from my Practice Hub posts.
allowed-tools: mcp__practice-hub__list_posts, mcp__practice-hub__get_post
---

# Practice Hub Post Summarizer

## Purpose

Retrieve my recent posts from Practice Hub through the existing
`practice-hub` MCP server (`server.py`) and organize them into a study note.

## Steps

1. Call `mcp__practice-hub__list_posts` with `mine=true`.
   - `mine` is the only supported parameter. There is no `limit`;
     the server returns up to 50 posts, newest first.
   - Use `mcp__practice-hub__get_post` only if a post's full details are needed.
2. Review the posts and identify common topics (use each post's `tags`,
   `title`, and `body`).
3. Organize the information into a Markdown study note with these sections:
   Topics, Key Points (cite post IDs), Takeaways, and Next Steps.
4. Display the full draft to me, including the post count and the
   proposed title and tags.
5. Ask for my explicit approval before creating a new post. If I ask for
   changes, revise the draft and show it again.
6. Only after I approve, call `mcp__practice-hub__create_post` with:
   - `title`: `Study Note - Practice Hub Digest`
   - `body`: the approved Markdown study note
   - `tags`: optional list of strings (for example `["inf601", "mcp"]`)

## Restrictions

- Do not modify or delete existing posts: never call
  `mcp__practice-hub__update_post` or `mcp__practice-hub__delete_post`.
- Do not expose API tokens or environment variable values.
- Only publish after receiving my explicit approval.
- If no posts are returned, tell me and do not create a post.
