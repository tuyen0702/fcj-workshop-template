# AI Workflow Source and Configuration Files

This folder stores the code and configuration files used by the AI Workflow section of the AI AWS Architecture Reviewer project.

## Folder structure

```text
README/
└── ai-workflow/
    ├── eventbridge/
    │   ├── eventbridge-rule-pattern.json
    │   ├── input-transformer-paths.json
    │   └── input-transformer-template.json
    ├── step-functions/
    │   └── architecture-review-workflow.asl.json
    ├── lambdas/
    │   ├── ai-analyzer/
    │   │   ├── lambda_function.py
    │   │   └── environment.txt
    │   ├── cost-tool/
    │   │   ├── lambda_function.py
    │   │   └── environment.txt
    │   └── pdf-generator/
    │       ├── lambda_function.py
    │       └── environment.txt
    ├── layers/
    │   └── reportlab-layer-structure.txt
    ├── dynamodb/
    │   └── completed-review-example.json
    └── testing/
        └── test-upload-command.md
```

## Notes

- The workshop page explains the flow and implementation steps.
- The full code/configuration files are stored here to keep the workshop page clean and easier to read.
- Replace placeholder Lambda files with the actual deployed Lambda code used in the project.
