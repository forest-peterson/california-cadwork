---
name: prompt-writing
description: "Use when writing a prompt for an AI agent: the prompt that starts a new chat to carry on work from a long chat, a task for another agent, or instructions an agent will follow. It names Anthropic's prompting guidance as the standard and states what a prompt holds and what it leaves out. The long-chats skill recommends a new chat when a chat goes long, so load this skill when a new chat is recommended."
---

# Prompt writing

v0.5, 21 November 2026

This skill names the standard for a prompt to an AI agent and the rules that follow from it. It cites the standard and does not repeat it.

## What a prompt holds

- The minimal set of information that fully outlines the behavior expected of the agent. Minimal does not mean short: the agent needs enough up front to act. Effective context engineering for AI agents.
- Notes for the agent to read. A prompt from one agent to another is not text for a human to interpret.
- The goal, and the reasons for the instructions, so the agent can act on cases the prompt does not name. Prompting best practices, "Add context to improve performance."
- An instruction as an action to take. An instruction that names only what to avoid leaves the agent to guess what to do. Prompting best practices.
- Steps in a numbered order when the order matters. Prompting best practices.
- A kind of content in its own section, marked with a descriptive XML tag, such as context, instructions, sources, open items and data. Prompting best practices.
- Pointers in place of content the agent can read for itself: the skills to load, the document, which holds its own decisions, and the sources. Effective context engineering for AI agents, on loading context just in time.
- For an open item: what is open, what has been proposed and by whom, and whether the author approved it. A term taken from a source is given in plain words.
- A placeholder for a secret, such as an access token, for the author to fill in.

## What a prompt leaves out

- What the agent can read in the skills, the document or the sources: rules already written, decisions already made, facts already in a source. A copy spends the agent's attention and can drift from the original.
- Dates, history and work already done, unless the agent needs one of them to act.
- A part copied from an earlier prompt that has not been tested against what the agent now needs. A prompt written in a long or compressed chat is the least reliable, because that chat can no longer be read whole (skill long-chats).

## Check before sending

Read the prompt as a colleague without knowledge of the task would, and fix the places where that colleague would be confused or would not know what to do first: the key test in Prompting best practices. Then read the prompt against the rules in this skill and fix faults. A list of rules does not check the prompt; this step does.

## The standard named above

- Anthropic. Prompting best practices. Claude Platform Docs. https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Anthropic. Effective context engineering for AI agents. Anthropic Engineering, 29 September 2025. https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
