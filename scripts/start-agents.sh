#!/usr/bin/env bash
# QA Platform — tmux agent team session
# Usage: bash scripts/start-agents.sh

SESSION="qa-agents"
PROJECT_DIR="/Users/macos/Desktop/WorkSpace/Odoo_Project/odoo"

tmux kill-session -t "$SESSION" 2>/dev/null

tmux new-session -d -s "$SESSION" -n "orchestrator" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:orchestrator" "echo '[Orchestrator] Ready. Run: claude'" Enter

tmux new-window -t "$SESSION" -n "agent1-planner" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:agent1-planner" "echo '[Agent 1: Planner] Ready. Run: claude'" Enter

tmux new-window -t "$SESSION" -n "agent2-frontend" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:agent2-frontend" "echo '[Agent 2: Frontend] Ready. Run: claude'" Enter

tmux new-window -t "$SESSION" -n "agent3-backend" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:agent3-backend" "echo '[Agent 3: Backend] Ready. Run: claude'" Enter

tmux new-window -t "$SESSION" -n "agent4-pipeline" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:agent4-pipeline" "echo '[Agent 4: Pipeline] Ready. Run: claude'" Enter

tmux new-window -t "$SESSION" -n "agent5-odoo" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:agent5-odoo" "echo '[Agent 5: Odoo Dev] Ready. Run: claude'" Enter

tmux new-window -t "$SESSION" -n "agent6-devops" -c "$PROJECT_DIR"
tmux send-keys -t "$SESSION:agent6-devops" "echo '[Agent 6: DevOps] Ready. Run: claude'" Enter

tmux select-window -t "$SESSION:orchestrator"
tmux attach-session -t "$SESSION"
