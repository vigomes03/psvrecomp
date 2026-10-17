# W22 — Translate a tracked project document to English

## Goal
Translate one project-owned UTF-8 text file from Portuguese to clear technical English.

## Input
The source document is provided as the only context file. Its repository-relative path is stated in the command that dispatches this card.

## Required output
Return the **complete translated replacement file**, not a patch and not an explanation.

## Translation rules
1. Translate all natural-language Portuguese prose, headings, table cells, comments, user-facing messages, and examples into English.
2. Preserve Markdown structure, line-oriented data formats, tables, code fences, JSON syntax, shell commands, paths, environment-variable names, identifiers, numeric values, hashes, `run_id` values, dates, and quoted API/runtime output exactly unless they are human-readable prose.
3. Do not rename files, symbols, command-line flags, environment variables, JSON keys, or protocol values.
4. Do not add facts, delete facts, summarize, or redact information.
5. Keep the document internally consistent and use US technical English.

## Acceptance checks
- The result is a complete UTF-8 file with the same structural role as the input.
- Every `run_id`, hexadecimal address, path, command, environment-variable name, and code identifier from the source remains present.
- No new unverified claim is introduced.
- The reviewer must be able to compare the output with the source without needing external context.
