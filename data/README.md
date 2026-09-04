# Data Directory

## Structure

```
data/
├── README.md              # This file
├── scheme_schema.json     # JSON Schema for scheme records
├── rules_schema.json      # JSON Schema for eligibility rules
├── documents_schema.json  # JSON Schema for document requirements
├── tutorials_schema.json  # JSON Schema for tutorial steps
├── canonical_values.json  # Provisional MVP enumerated values
└── schemes/               # Individual scheme JSON files
```

## Pipeline

```
data/schemes/*.json → validate_data.py → generate_seed.py → supabase/seed.sql
```

## Rules

- **No real government data.** Files in `data/schemes/` must be clearly marked structural test fixtures or remain empty.
- **No fabricated facts.** Do not invent eligibility requirements, benefits, documents, URLs, or tutorials for real schemes.
- **canonical_values.json** contains only provisional MVP values. It is NOT exhaustive.

## scheme_code Convention

- Lowercase snake_case
- Pattern: `^[a-z0-9_]+$`
- Examples: `test_scheme_alpha`, `fixture_basic`
- Must be unique across all scheme files
