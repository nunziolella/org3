# Functional Specification

## Dashboard

The dashboard is the command centre of AIProd. It should show daily focus, top weekly priorities, next actions, active projects, unprocessed inbox items, incubated ideas, area status, review reminders, quick capture and a cognitive workload indicator.

## Quick Capture and Inbox

The Inbox receives text, voice notes, tasks, ideas, problems, goals, observations, references, decisions and notes.

For each input, AIProd should propose:

- object type;
- summary;
- related area;
- related project;
- urgency;
- impact;
- strategic alignment;
- mental cost;
- next action;
- destination.

Possible destinations are task, project, note, area, incubated idea, archive or discard.

## Areas

Areas represent ongoing responsibilities without a fixed completion date.

Default areas:

- Stability;
- Education;
- Personal Income;
- Entrepreneurial Assets;
- Wealth and Investments.

## Projects

A project is a temporary effort with a defined outcome.

Required information includes title, description, area, desired outcome, motivation, status, priority, urgency, impact, strategic alignment, mental cost, deadline, weekly time budget, next action, blockers, notes and related ideas.

Statuses: proposed, active, paused, blocked, completed, cancelled and archived.

The system should warn the user when too many projects are active.

## Next Actions

A next action must be immediately executable. Actions should be filterable by date, energy, work context, type and estimated duration.

Task types:

- deep_work;
- light_work;
- quick_admin;
- review.

## Idea Incubator

The incubator stores valid ideas that are not currently active. Each idea may contain category, interest level, economic potential, strategic relevance, exploration cost, status, future review date and relations.

## Weekly Review

The review should cover inbox processing, overdue actions, stalled projects, overloaded areas, conflicting priorities, projects without next actions, ideas eligible for promotion, delegation opportunities and the next week's top outcomes.

## AI Assistant

The assistant operates on structured system context rather than as a generic standalone chat.

Core capabilities:

- semantic classification;
- entity extraction;
- duplicate detection;
- project association;
- task decomposition;
- priority recommendation;
- next-action generation;
- review summaries;
- overload and conflict detection;
- contextual search.

## Search and Relations

Users should be able to search across every object and view links between notes, tasks, projects, areas, ideas and decisions.

## Settings

Settings should support profile details, working hours, review day, active project limit, scoring weights, AI providers, privacy, data export and notifications.
