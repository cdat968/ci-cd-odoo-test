# Overview

## Current Behavior

OCA Helpdesk and `qa_bug_management` can install in the same CI database, but
there is no user-facing bridge between `helpdesk.ticket` and `qa.bug.ticket`.

## Target Behavior

A QA manager can create a QA bug from a Helpdesk ticket with a manual button.
The system stores a link in both directions and opens the existing bug instead
of creating duplicates.

## Non-Goals

- Do not auto-create QA bugs for every Helpdesk ticket.
- Do not sync Helpdesk stages with QA bug statuses.
- Do not copy Helpdesk attachments into QA evidence.
- Do not auto-create project tasks.
