# Rasa Solution Engineer - Take Home Test

Rasa Solution Engineer Applicant

![RASA](https://i.imgur.com/EdAsJ5y.png)

## Preparation Instructions

Your task is to work with a client-owned Retail AI Agent designed to support common retail customer service scenarios, such as order status lookups, returns and exchanges, and membership or subscription management.

As part of this technical take-home exercise, you will be given an existing Retail AI Agent that has not been built well, and contains several intentional issues. The agent reflects a realistic customer implementation. Your goal is to identify and resolve these issues, then extend the agent by adding additional skills.

You will have **three business days** to complete the exercise.

This take-home will be reviewed by a Rasa Engineer. Your approach, decisions, and improvements will be discussed during a follow-up technical interview.

## What We Are Evaluating

Approach this exercise as you would a real customer or production scenario. We are evaluating:

- Your understanding of the Rasa platform
- Your technical depth and correctness
- Your ability to diagnose and resolve issues logically
- Your resourcefulness and use of available documentation
- Your ability to clearly explain, present and demo your work creatively

## Getting Started

To prepare, review the **Rasa Pro** documentation:  
https://rasa.com/docs/pro/intro/

You will need:

- A **Rasa Pro Developer Edition** license
- An **OpenAI API key** (GPT-4o)

Request a Rasa Pro Developer Edition license here:  
https://rasa.com/rasa-pro-developer-edition-license-key-request

OpenAI configuration details are available here:  
https://rasa.com/docs/reference/config/components/llm-configuration/#openai

> [!NOTE]
> If you need an OpenAI API key, feel free to reach out and we can provide one.

## Familiarity with Rasa

- **If you are already familiar with Rasa**  
  - Review the files in this repository, starting with this README.

- **If you are new to Rasa, we recommend**:
  - Installing Rasa Pro locally and completing the prerequisite setup steps below
  - Reviewing key concepts, starting with flows:  
    https://rasa.com/docs/reference/primitives/flows/
  - Reviewing the Rasa Command Line Interface:  
    https://rasa.com/docs/reference/api/command-line-interface/
  - Reading this README in full

## Prerequisites

You will need the following tools installed locally to run this project:
- **Homebrew**: Package manager for macOS
- **pyenv**: Python version management
- **uv**: Fast Python package installer and dependency resolver

## Setup

1. Install and set up **Rasa Pro**:  
   https://rasa.com/docs/pro/installation/python
2. Confirm your Rasa version is **3.15.10 or later**.

> **Note**  
> Ensure your Rasa license key and OpenAI API key are set as environment variables within your virtual environment.

## Usage

### Rasa Pro Workflow

A typical local workflow looks like:
1. Clean existing models and logs
2. Train and validate the Rasa model
3. Start the Rasa Inspector

## Project Structure

Below is a brief overview of the directories and files in the project root:

- `README.md`: Instructions and context for the take-home exercise
- `actions/`: Python code defining custom actions for the assistant
- `config.yml`: Configuration files for different language models and runtime settings
- `credentials.yml`: Credentials for external services used by the assistant
- `data/`: Flow definitions and conversational data
- `docs/`: Sample documents used for Enterprise Search scenarios
- `domain/`: Domain definitions for the assistant
- `e2e_tests/`: End-to-end test scenarios, organized by test suite
- `endpoints.yml`: Endpoint configuration for the assistant
- `models`: Trained models are stored here
- `prompts/`: Jinja2 templates used for custom prompt generation
- `requirements.txt`: Python dependencies required for the project


## Your Take Home Tasks

### Introduction

Read this readme carefully and leverage the Rasa docs during your take home exercise.

This GitHub repository includes all the files required to configure, train and debug an AI Agent.

## 1. Train your model

The training should fail. Identify why and apply the appropriate corrections. Once the corrections are applied. Train the model again. The model should successfully train after your fixes.

*Describe the issues. How did you fix it and get the agent to train successfully?*

## 2. Start your agent

Try to have the following conversation with this agent:

```
BOT: Welcome to Rasa Market, my name is Zoey. How may I help you today?
USER: I want to return my order ord123
BOT: Got it. You'd like to return your item, I can help with that.
BOT: Just so you know, if the wrong item or size was sent, we do offer free exchanges in case that works better for you.
BOT: Would you like to exchange your item?
USER: Do I have to pay a fee to exchange an item?
BOT: Please give me a few moments to look into that.
BOT: No, you do not have to pay a fee to exchange an item. Exchanges are free as long as they are completed within the 90-day return window.
BOT: Would you like to exchange your item?
...
```

*Identify the issue(s) and apply the correction. You should be able to complete the conversation happy path as described above.*

**Rephrasing**

In the above conversation, the client does not want the agent to always say:

`Please give me a few moments to look into that.`

*Update the agent so that, when generating this response, the LLM dynamically responds in a pirate-like tone. The response should not be hardcoded; it should be generated by the model and vary naturally across interactions.*

## 3. Create a new flow

Create a new flow `flow_get_store_hours` that returns the store hours. The store hours are stored in `data/store_hours.json`.

**All hours of operation**

You should be able to have a conversation like this:
```
BOT: Welcome to Rasa Market, my name is Zoey. How may I help you today?
USER: What are your store hours?
BOT: Our hours of operation are:
Mon 8am - 8pm
Tue 8am - 8pm
Wed 8am - 8pm
Thu 8am - 8pm
Fri 8am - 9pm
Sat 8am - 9pm
Sun 8am - 5pm
...
```

## 4. Update your flow

Update your `flow_get_store_hours` to also provide a specific day's hours of operation. The user should now be able to ask about a specific day, or see all the hours.

**Specific day's hours of operation**

You should be able to have a conversation like this:
```
BOT: Welcome to Rasa Market, my name is Zoey. How may I help you today?
USER: What are your store hours on Friday?
BOT: Our hours on Friday are:
Fri 8am - 9pm
...
```

*Consider error handling, e.g. What if user makes up a day of the week?*

## 5. Restrict your flow

Update the `flow_get_store_hours` flow to run when the user explicitly asks for store hours through a clearly classified NLU intent with confidence at least `90%`.

**BONUS POINTS**: Trigger the flow with an NLU intent while preventing the flow from being started by the LLM CommandGenerator.

*Explain exactly what was done to implement this.*

## 6. Use the End-to-end (E2E) CLI-based testing tool to test your flows. 

Your task for this step is to leverage the End-to-end (E2E) testing tool that allows you to test conversation scenarios with different pre-configured contexts, execute custom actions, verify response texts or names, and assert when slots are filled or not.

*Create various testing scenarios, execute them and document the results.*

## 7. Connect to an MCP server

Fix issues related to MCP tooling.

The MCP tooling utilizes the following files:
- `data/schedule_appointment.yml`
- `domain/schedule_appointment.yml`
- `sub_agents/*`
- `endpoints.yml`

You should be able to connect to an MCP server to have a conversation like this:

```
BOT: Welcome to Rasa Market, my name is Zoey. How may I help you today?
USER: I want to schedule an appointment with a specialist
BOT: To help you schedule an appointment with a specialist, I need a bit more information. Could you please let me know:
* Your availability (start date, end date, and preferred time range).
* If you have a preferred doctor or specialist.
* Any specific dates you are not available.
BOT: Let me know, and I'll assist you further!
USER: I can do anytime on Friday, or 10am-2pm on Saturday. I don't have a preferred doctor.
BOT: Thank you for providing your availability. Just to confirm:
* You are available anytime on Friday.
* You are available 10:00 AM to 2:00 PM on Saturday.
* You do not have a preferred doctor.
BOT: Are there any specific dates you are not available, or should I proceed with this information?
USER: those are the only 2 days I'm available, the rest of the days I am not available. please proceed.
BOT: Unfortunately, there are no available appointment slots for the specified days and times. Would you like to adjust your availability or explore other options? Let me know how you'd like to proceed!
USER: what days are open?
BOT: Here are the available appointment slots:
18 February 2026 at 09:00
19 February 2026 at 11:30
2 March 2026 at 13:30
3 March 2026 at 16:00
BOT: Would you like to book any of these slots, or should I assist you further?
USER: I'll take the first one
BOT: Are you sure you want to book the 18 February 2026 at 09:00?
Yes
No, cancel
USER: yes
BOT: Okay I have booked the slot '18 February 2026 at 09:00' for you!
BOT: Is there anything else I can help you with before we end our call?
USER: nope
BOT: Thank you for calling and have a wonderful day. Goodbye.
```

*Determine and resolve the issues with the MCP tooling related files.*
