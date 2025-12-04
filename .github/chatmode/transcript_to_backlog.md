# Transcript_to_Backlog
This project was created to support Technical Program Managers (TPMs), Product Owners, and Engineers in accelerating the gap between customer feedback and actionable engineering work.

## Table of Contents

- [Overview](#overview)  
- [Prerequisites](#prerequisites)  
- [Features](#features) 
- [Use Cases](#use-cases)
- [Usage](#usage)

## Overview
**Transcript_to_Backlog** is a developer productivity tool that extracts structured Agile work items — including user stories and spikes — directly from meeting transcripts or project notes.

Powered by **GitHub Copilot Chat (GHC)**, this tool supports two usage modes:

- **Custom Agent Mode** (for VS Code Insiders with agent support)

## Prerequisites
- Visual Studio Code (VSC) GitHub Copilot extension:
    - Make sure you have a GitHub Copilot license or subscription.
    - Install and enable the GitHub Copilot extension from the VS Code Marketplace.
    - GitHub Copilot Chat enabled in **VS Code**
- A transcript or note file inside`./transcripts` folder


## Features

- Automatically generates a complete backlog: epics, user stories, and spikes
- Parses raw meeting transcripts and structures conversations into actionable Agile work items
- Supports metadata tagging (e.g., UX, DevX, AI, Reporting, etc.) for easy categorization
- Flags vague or incomplete input as refinement and marks fully formed items as ready
- Outputs well-organized Markdown files suitable for direct use in Agile planning


## Use Cases

- Turn customer calls, discovery sessions, or brainstorming meetings into a fully fleshed-out backlog
- Rapidly generate epics, user stories, acceptance criteria, and technical spikes from raw notes
- Standardize backlog creation to improve clarity and accelerate handoff to product and engineering teams


## Usage

### Run with Custom Agent (VS Code Insiders Preview)
If you're using VS Code Insiders and have access to GitHub Copilot Custom Agents, follow these steps:

1. Add your raw transcript file into ./transcripts folder.

1. Open the transcript or notes file
Open the `.txt` file you'd like to extract user stories from (e.g., ./contoso_chatbot_transcript.txt)

1. Open Copilot Chat
Open the Copilot Chat pane from the sidebar (or press Cmd+I / Ctrl+I if you have the shortcut enabled).

1. Choose Your Custom Agent

    Click the dropdown in the upper-right of the Copilot Chat window (next to the "Send" button).

    Select the `transcript_to_backlog` Agent from the list of available agents.

1. Choose models (e.g., GPT-4.1, Claude Sonnet 3.5, etc)

    Ask it:

    `Please generate backlog items from this transcript file.`

    OR

    `Generate user stories and spikes from this transcript`

1. Output

    The agent will:

    - Parse the content

    - Generate structured user stories and spikes

    - Include full metadata, tags, status (ready or refinement)

    - Output the results as a markdown document you can save

1. Save
If you like the changes the GitHub Copilot made, you can click on 'Keep' button to save the changes.
