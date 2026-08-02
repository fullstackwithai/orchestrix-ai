# Project Explanation

Orchestrix AI is an enterprise workflow automation and governed AI-agent orchestration platform designed and implemented by **Arsim Shefkiu** through **DesignHubMK**.

The project solves a common enterprise problem: business processes are spread across forms, APIs, email, CRM systems, AI tools, and human approvals, but teams need one place to model, execute, observe, and audit the complete process. Orchestrix brings those steps into a visual, versioned workflow with explicit state transitions and human control.

The application uses FastAPI, SQLAlchemy, Pydantic, SQLite or PostgreSQL-compatible persistence, a browser-based workflow canvas, optional OpenAI integration, Docker, automated tests, and GitHub Actions. Its workflow engine supports triggers, actions, AI agents, conditions, human approvals, delays, webhooks, and end nodes.

I implemented the product architecture, database models, graph validation, execution engine, workflow versioning, approval queue, run resumption, audit evidence, frontend designer, API contracts, testing, Docker setup, and technical documentation.

The main technical challenge was making the system genuinely stateful and auditable rather than presenting a visual mockup. I solved this by persisting workflow versions and runs, pausing execution at human tasks, recording decisions as evidence, and resuming the same run after approval. The result demonstrates full-stack application engineering, workflow design, AI integration, governance, and production-oriented software practices.

Portfolio: https://www.designhubmk.com
