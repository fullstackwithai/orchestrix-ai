# Orchestrix AI Architecture

## Control plane

FastAPI exposes workflow, version, execution, approval, and audit APIs. SQLAlchemy stores all process state.

## Execution plane

The internal graph executor processes typed nodes, updates shared workflow state, records evidence, and selects outgoing edges. Human approval nodes create durable tasks and stop the run until a decision is recorded.

## AI adapter

AI nodes execute through a bounded adapter. With an OpenAI API key, the adapter calls the Responses API. Without a key, the platform uses deterministic offline output so the workflow remains demonstrable and testable.

## BPMN-inspired semantics

Orchestrix uses explicit triggers, actions, conditions, human tasks, timers, and end events. It does not claim full BPMN 2.0 compliance.

## LangGraph integration path

The workflow definition, state model, and node adapter boundaries are designed so the internal executor can later be replaced or supplemented by LangGraph for advanced multi-agent cycles, checkpointing, and graph persistence.
