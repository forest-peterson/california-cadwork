---
name: long-chats
description: "Use when an agent works with an author in a chat and the chat is getting long: many turns, long tool results (a whole web page, file or spreadsheet), or a notice that the chat will be compressed. Judge length by the amount of text against the context window of the model in use, not by the number of turns or tool calls: we use tools by default. It says when to tell the author that the chat is long and to recommend a new chat, and why. The working-with-a-scientist skill depends on it, so load it when that skill is loaded. When a new chat is recommended, load the prompt-writing skill for the prompt that starts the new chat."
---

# Long chats

v0.5, 20 November 2026

This skill holds the rule for a chat that is getting long.

## What makes a chat long

- A chat's length is the amount of text the chat holds: the author's messages, the agent's replies and tool calls, and the tool results. Compression comes when the chat's text nears the limit of what the agent can hold at once, so the amount of text is also the test of closeness to compression.
- A tool result adds as much text as the result holds. A whole web page, file or spreadsheet adds much text; a folder listing, a status message or a short answer adds little.
- The number of tool calls is not a test of closeness to compression, because we use tools by default. Do not judge a chat's length by counting tool calls.

## How long is long

- The limit is the context window of the model in use, measured in tokens, the units in which a model counts text. The system prompt names the model. Anthropic's Help Center gives the models' windows in chat: on paid plans the newest models have up to 1M tokens (1,000,000), and older models 500K or 200K. Before calling a chat long, look up there the window of the model in use.
- Estimate the chat's text in tokens at one token per 2.5 characters. The estimate is rough, so the test below leaves a wide margin.
- A chat is long when the estimate passes half the window: on a model with a 1M-token window, about 500,000 tokens, or 1,250,000 characters. Half leaves room for the system prompt and the tools, which take part of the window before the chat begins, and leaves time to act before compression. Below half, the chat is not long, however many turns or tool calls it has had.

## The rule

- When a chat is long by the test above, say so and recommend starting a new one, early enough to act on, before the chat is compressed. Give the estimate and the window, for example "about 520,000 tokens of a 1M-token window."
- Call a chat long only by the test above, not on a guess. When the estimate is below half the window, go on with the work and do not mention the chat's length.
- The compressing pop-up comes too late, and another chat will not review a long chat in full, so a long chat is a record that can no longer be read whole.

## The new chat

- The skill prompt-writing, in the same repository, gives the rules for the prompt that starts the new chat. Load that skill when a new chat is recommended.

## Check before sending

Before sending a reply in a chat that has gone long, check that the reply says the chat is long and recommends a new chat. Check too that a judgment that the chat is long rests on the amount of text the chat holds, not on the number of tool calls, and that the reply gives the estimate and the window, with the estimate past half the window. A rule does not check the reply; this step does.

## The sources named above

- Anthropic, Claude Help Center, "How large is the context window on paid Claude plans?": https://support.claude.com/en/articles/8606394-how-large-is-the-context-window-on-paid-claude-plans
- Anthropic, Claude Help Center, "How do usage and length limits work?": https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work
