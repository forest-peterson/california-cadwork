# Agent instructions

The skills for this repository are in `.claude/skills/`. Each skill is a folder with a `SKILL.md` file. Before a task, read the `SKILL.md` of each skill whose description matches the task, and follow it.

## Changing a file in this repository

A change reaches the main branch this way. The user logs the agent in to GitHub through MCP. The agent pushes the change to the user's own copy of this repository on GitHub (a fork) and opens a request for review (a pull request). An admin of this repository reviews the change and accepts it. Do not ask the user for a token.

The `*.ifc` file in this repository is a large text file, and it will change: the file here now is a test file of 76 MB and 1.47 million lines. The login through MCP carries small files only, so a whole `*.ifc` file of that size cannot go up through it. How an edit to the `*.ifc` file goes up is under test. Two facts are measured on the test file: git merges two edits to different single lines of the file by itself, and a save of the file through the software library ifcopenshell, with no edit, changes every line of the file.
