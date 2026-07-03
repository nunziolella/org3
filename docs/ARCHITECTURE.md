# System Architecture

## Status

This document describes the target architecture and must be reconciled with the actual Emergent-generated source code when the complete application is available in the repository.

## Recommended stack

### Frontend

- Next.js;
- React;
- TypeScript;
- Tailwind CSS;
- shadcn/ui;
- Lucide icons;
- Framer Motion.

### Backend

- Supabase or equivalent managed PostgreSQL platform;
- server-side API routes or edge functions;
- authentication and row-level security;
- background processing for AI classification.

### State management

Use local component state where possible. Introduce a lightweight shared store only when server state and component state are insufficient.

## Logical architecture

### Presentation layer

Dashboard, forms, cards, filters, reviews, relationship views and AI proposal panels.

### Application layer

Capture workflow, inbox processing, project lifecycle, task lifecycle, review generation, scoring, active project limits, permissions and validation.

### Domain layer

Core entities:

- User;
- Area;
- InboxItem;
- Project;
- Task;
- Idea;
- Note;
- Review;
- Relation;
- AIProposal.

### Infrastructure layer

Persistence, authentication, AI integration, vector search, transcription, notifications, analytics and audit logs.

## AI processing pipeline

1. Receive captured input.
2. Persist raw input.
3. Create a processing job.
4. Analyse intent and entities.
5. Retrieve related context.
6. Generate classification and recommendations.
7. Validate output against a strict schema.
8. Store the AI proposal separately.
9. Present the proposal to the user.
10. Apply only approved changes.

## AI governance

- Raw input must never be overwritten.
- AI output must remain separate from confirmed user data.
- Every automated change must be traceable.
- Low-confidence proposals should require confirmation.
- Provider failures must not prevent manual use.

## Priority scoring

Initial formula:

`priority_score = urgency × impact × strategic_alignment ÷ mental_cost`

Implementation should normalise values, avoid division by zero, allow configurable weights and keep every score explainable.

## Non-functional requirements

### Performance

- dashboard interactive within two seconds under normal conditions;
- quick capture persisted immediately;
- AI processing asynchronous;
- optimistic UI only where rollback is safe.

### Reliability

- captured inputs must not be lost;
- failed AI jobs must be retryable;
- conversions should be idempotent where possible.

### Security

- authenticated access;
- row-level data isolation;
- encrypted transport;
- server-side secrets;
- audit logs for important changes.

### Accessibility

- keyboard navigation;
- sufficient contrast despite glassmorphism;
- visible focus states;
- semantic labels;
- reduced-motion support.

## Design system

The visual direction combines bento grids, glassmorphism, dark mode, modern sans-serif typography, soft gradients, rounded cards, restrained animation and strong hierarchy. Glass effects must never reduce readability.
