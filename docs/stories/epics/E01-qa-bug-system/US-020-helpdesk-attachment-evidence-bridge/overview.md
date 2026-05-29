# Overview

## Current Behavior

Helpdesk ticket attachments stay on `helpdesk.ticket` as `ir.attachment`
records. Creating a QA bug from Helpdesk does not populate QA Bug evidence.

## Target Behavior

When QA creates a QA bug from a Helpdesk ticket, image attachments from the
Helpdesk ticket are linked into `qa.bug.evidence` as attachment-backed
screenshots. The images render in the existing QA Bug evidence gallery.

## Non-Goals

- Do not upload Helpdesk attachments to Cloudinary.
- Do not copy non-image attachments into evidence.
- Do not add Project evidence thumbnails/lightbox in this story.
