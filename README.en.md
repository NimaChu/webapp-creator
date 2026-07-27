# HTML Design

[简体中文](README.md) | [English](README.en.md)

Describe an idea in plain language and turn it into a lightweight web app that runs on its own.

HTML Design is a skill for AI coding agents. By default, it creates a single `index.html`
with no frontend framework, build step, or required publishing platform. The finished app
can run in a browser, travel on a USB drive, be shared as a file, or live on any static server.

AI is optional. Calculators, dashboards, and small games can run entirely in the browser,
while model-powered apps can connect to a local or OpenAI-compatible model selected by you.

## Why a single HTML file

- Open it directly in a browser and move or back it up like any other file
- Avoid React, Tailwind, npm, and build-server dependencies
- Keep the HTML, styles, and behavior visible and easy to change
- Work across local, offline, LAN, and ordinary static-server environments
- Keep local model configuration and credentials separate from the app

Large media, complex game logic, workers, or WASM can still use additional local files.
The project remains static and portable.

## What it can build

- Tools: calculators, converters, generators, forms, and file utilities
- Dashboards: metrics, trends, filters, comparisons, and exception lists
- Guided flows: setup wizards, diagnostics, reviews, and step-by-step tasks
- Knowledge apps: guides, FAQs, notes, summaries, and searchable references
- Web games: lightweight games for mouse, keyboard, and touch
- HTML presentations: fullscreen stories with keyboard navigation and print output
- AI tools: text generation, image understanding, image generation, and code assistance

Every app favors native HTML, CSS, and JavaScript so it stays lightweight, transparent,
and easy to adapt.

## Install the skill

The easiest option is to give the repository URL to an Agent that supports custom skills.
For example, start a new Codex conversation and send:

> Install and enable the HTML Design skill from https://github.com/NimaChu/html-design.
> Before installing it, inspect its SKILL.md and scripts. Place it in my user-level skills
> directory without modifying my other skills. Run the included check after installation,
> then tell me whether I need to restart or open a new conversation and how to invoke it.

The Agent may ask for permission to access GitHub and write to your user skills directory.
Approve it after confirming the repository and the `html-design` skill name.

If you have already downloaded the repository, tell the Agent:

> Install my downloaded html-design repository as a user-level skill, verify the installation,
> and tell me how to invoke it.

## Start using it

You do not need to choose a technical approach first. Describe the result you want:

> Use html-design to build a travel expense splitter for groups and multiple currencies.
> Make the result easy to copy and comfortable to use on a phone.

Or:

> Use html-design to build a word-matching game with a saved high score and support for
> touch and keyboard input. Deliver it as an index.html.

For a local AI app:

> Use html-design to build a local article rewriting tool connected to an OpenAI-compatible
> model, with streaming output and a cancel button.

The Agent will choose the appropriate app type and handle the interface, behavior,
validation, and local preview.
