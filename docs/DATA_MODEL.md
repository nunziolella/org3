# Data Model

## User

- id
- name
- email
- timezone
- preferred_review_day
- active_project_limit
- created_at
- updated_at

## Area

- id
- user_id
- name
- description
- icon
- status
- created_at
- updated_at

## InboxItem

- id
- user_id
- raw_content
- source_type
- processing_status
- suggested_type
- suggested_area_id
- suggested_project_id
- ai_summary
- ai_next_action
- confidence_score
- created_at
- processed_at

## Project

- id
- user_id
- area_id
- title
- description
- desired_outcome
- motivation
- status
- urgency_score
- impact_score
- strategic_alignment_score
- mental_cost_score
- priority_score
- weekly_time_budget_minutes
- due_date
- created_at
- updated_at
- completed_at

## Task

- id
- user_id
- project_id
- title
- description
- status
- task_type
- energy_level
- context
- estimated_minutes
- urgency_score
- priority_score
- due_date
- scheduled_at
- created_at
- updated_at
- completed_at

## Idea

- id
- user_id
- area_id
- title
- description
- category
- status
- interest_score
- economic_potential_score
- strategic_relevance_score
- exploration_cost_score
- review_at
- created_at
- updated_at

## Note

- id
- user_id
- area_id
- project_id
- title
- content
- note_type
- created_at
- updated_at

## Review

- id
- user_id
- review_type
- period_start
- period_end
- summary
- blockers
- decisions
- top_outcomes
- ai_recommendations
- created_at
- completed_at

## Relation

- id
- user_id
- source_type
- source_id
- target_type
- target_id
- relation_type
- created_at

## AIProposal

- id
- user_id
- source_type
- source_id
- proposal_type
- payload
- confidence_score
- status
- model_provider
- model_name
- created_at
- reviewed_at

## AuditEvent

- id
- user_id
- entity_type
- entity_id
- action
- actor_type
- before_state
- after_state
- created_at

## Important constraints

- All user-owned objects include `user_id`.
- Every project belongs to one primary area.
- A task may belong to one project.
- Relations support additional many-to-many links.
- AI proposals cannot directly overwrite confirmed data.
- Raw Inbox content remains available after conversion.
- Completed and archived objects remain queryable.
