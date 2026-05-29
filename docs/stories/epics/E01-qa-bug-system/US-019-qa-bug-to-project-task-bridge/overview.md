# Overview

## Current Behavior

Helpdesk tickets can manually create QA bugs. QA bugs do not yet create linked
Project tasks, and Project forms do not show project-specific QA bugs.

## Target Behavior

QA Managers can manually create one Project task from a QA bug. The link is
stored both ways. Project forms show a Bugs smart button and a Bugs tab only
when the project has QA bugs.

## Non-Goals

- Do not auto-create Project tasks.
- Do not sync Helpdesk stages, QA bug statuses, or Project task stages.
- Do not copy Helpdesk attachments into QA evidence.
- Do not add Project evidence thumbnails/lightbox in this phase.
