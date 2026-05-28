# Design

## Module

`qa_helpdesk_bridge` is a production Odoo addon.

## Data Links

- `helpdesk.ticket.qa_bug_id`
- `qa.bug.ticket.helpdesk_ticket_id`

The first slice uses button logic to keep a soft 1-to-1 relationship. A SQL
constraint can be added later if the workflow needs stricter enforcement.

## User Flow

1. QA opens a Helpdesk ticket.
2. If no QA bug exists, QA clicks `Create QA Bug`.
3. The bridge creates a `qa.bug.ticket` from Helpdesk title/description.
4. The Helpdesk ticket changes to `Open QA Bug`.
5. QA can open the source Helpdesk ticket from the QA bug form.

## Scope Boundaries

Project task execution and evidence attachment mapping are future phases.
