# Design

## Data Links

- `qa.bug.ticket.project_id`
- `qa.bug.ticket.project_task_id`
- `project.task.qa_bug_id`
- `project.project.qa_bug_ids`

## Project Selection

Task creation uses `qa.bug.ticket.project_id` first. If it is empty and the bug
came from Helpdesk, it falls back to `helpdesk_ticket_id.project_id` and stores
that project on the bug.

## Permissions

Only `qa_bug_management.group_qa_manager` can create a Project task from a QA
bug. Developers may open linked tasks/bugs according to existing QA and Project
access rules, but cannot create tasks through the bridge.

## UI

QA Bug form gains `Project`, `Project Task`, `Create Project Task`, and
`Open Project Task`.

Project form gains a Bugs smart button and a Bugs tab. Both are hidden when
`qa_bug_count == 0`.
