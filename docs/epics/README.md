# User Stories and Engineering Tasks

This directory contains the user stories and engineering tasks for the Documentation Recreation Agent Swarm project.

## Structure

```
epics/
├── index.md                              # Overview of all epics
├── 01-repository-analysis/               # Epic 1
│   ├── epic.md                           # Epic description
│   ├── 01-file-type-detection.md         # User story
│   │   └── tasks/                        # Engineering tasks for this story
│   ├── 02-language-support-primary.md    # User story
│   │   └── tasks/                        # Engineering tasks for this story
│   └── ...
└── 02-documentation-generation/          # Epic 2
    ├── epic.md                           # Epic description
    ├── 01-file-metadata-documentation.md # User story
    │   └── tasks/                        # Engineering tasks for this story
    └── ...
```

## User Stories

User stories are written from the perspective of a user and describe a feature that provides value to the user. Each user story includes:

- Story ID
- User story statement
- Acceptance criteria
- Technical notes
- Dependencies
- Effort estimate
- Priority
- Status

## Engineering Tasks

Engineering tasks break down user stories into specific technical implementation details. Each task includes:

- Task ID (derived from the parent story ID)
- Description
- Acceptance criteria
- Technical notes
- Dependencies
- Estimated effort
- Priority
- Status
- Assignee

## Templates

For creating new tasks, refer to the template at:
- [Task Template](/docs/templates/task_template.md)

## Status Tracking

For overall project status, see:
- [Project Status Tracking](/docs/project/status_tracking.md)