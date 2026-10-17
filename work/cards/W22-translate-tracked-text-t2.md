# W22 — Attempt 2: translate a tracked project document to English

## Previous attempt rejected
The worker output contained only the final directory-tree code fence from `CLAUDE.md`, omitting the preceding 132 lines. It was not a complete replacement file.

## Goal
Translate the supplied project-owned UTF-8 text file from Portuguese to clear technical English.

## Required output protocol
Return the complete replacement file between these exact sentinel lines, with no Markdown fence anywhere in the response:

`<<<TRANSLATED_FILE>>>`

`<<<END_TRANSLATED_FILE>>>`

The translated document itself may contain its original Markdown code fences; preserve them exactly.

## Translation rules
1. Translate all natural-language Portuguese prose, headings, table cells, comments, user-facing messages, and examples into English.
2. Preserve Markdown structure, line-oriented data formats, tables, code fences, JSON syntax, shell commands, paths, environment-variable names, identifiers, numeric values, hashes, `run_id` values, dates, and quoted API/runtime output exactly unless they are human-readable prose.
3. Do not rename files, symbols, command-line flags, environment variables, JSON keys, or protocol values.
4. Do not add facts, delete facts, summarize, or redact information.
5. Keep the document internally consistent and use US technical English.

## Acceptance checks
- Output contains every source section and table.
- Output preserves every source `run_id`, hexadecimal address, path, command, environment-variable name, and code identifier.
- Output contains no TODO marker or explanation outside the sentinel region.
