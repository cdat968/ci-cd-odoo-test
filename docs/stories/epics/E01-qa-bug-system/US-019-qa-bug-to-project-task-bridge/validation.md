# Validation

## Proof Strategy

Extend the existing `qa_helpdesk_bridge` tests and CI bridge service. Phase 4
must prove business behavior and permission boundaries.

## Test Cases

- QA Manager creates a Project task from a QA bug with a manual project.
- QA Manager creates a Project task using the Helpdesk ticket project fallback.
- Creating a Project task is idempotent.
- Creating a Project task without any project raises `UserError`.
- Developer without QA Manager permission gets `AccessError`.
- Portal customer cannot read QA bugs.
- Project bug counts and Project Bugs action reflect linked QA bugs.

## Commands

```text
python3 -m py_compile qa_helpdesk_bridge/models/helpdesk_ticket.py qa_helpdesk_bridge/models/qa_bug_ticket.py qa_helpdesk_bridge/models/project_project.py qa_helpdesk_bridge/models/project_task.py qa_helpdesk_bridge/tests/test_helpdesk_bridge.py
python3 - <<'PY' ... XML parse checks ... PY
docker compose -f docker-compose.test.yml config
bash scripts/run_qa_helpdesk_bridge_tests.sh
```

## Acceptance Evidence

- Manifest parse passed and includes Project/Task views.
- XML parse passed for Helpdesk, QA Bug, Project, and Project Task bridge views.
- Python compile passed for Phase 4 models and tests.
- XPath check found no `@string` selectors in bridge views.
- Docker validation is expected on GitHub Actions because local `docker` is not
  available in this shell environment.
