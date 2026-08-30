# Private Capital — Architecture Baseline

## 1. Purpose

This document defines the current architectural baseline of the Private Capital knowledge platform.

The system is designed as an evidence-first structured knowledge system for the Iranian private capital / capital markets domain.

The canonical knowledge layer is based on:

- Entity
- Claim
- Evidence
- Source

Product experiences such as Atlas, Research and Watch are expected to consume this shared knowledge substrate rather than maintain independent parallel data models.

---

## 2. Canonical Principles

### 2.1 Entity identity is separate from relations

An Entity represents the canonical identity of a real-world or conceptual object.

Examples include:

- Person
- Organization
- OrganizationUnit
- Project
- Investment
- Fund
- Sector
- Concept
- InvestorCategory

Relations between entities are represented as Claims.

### 2.2 Claims are first-class knowledge objects

A Claim represents an atomic assertion.

Conceptually:

```text
Claim
├── id
├── subject
├── predicate
├── object XOR value
├── temporal
├── status
└── confidence
```

A Claim must reference evidence before it can be treated as canonical supported knowledge.

### 2.3 Evidence is separate from Source

Source represents the source document or origin.

Evidence represents the specific support extracted from a source for a particular claim.

The conceptual chain is:

```text
Source
  ↓
Evidence
  ↓
Claim
```

### 2.4 Quantitative data belongs to the Claim layer

A reported quantitative fact is represented as a Claim with a structured `value`.

Conceptually:

```text
Claim
├── subject
├── predicate
└── value
```

A Claim must contain exactly one of:

```text
object
```

or:

```text
value
```

Never both.

### 2.5 Derived metrics are not canonical facts

A metric calculated by aggregating canonical claims is a derived result.

It must not be stored as if a source directly reported it.

Conceptually:

```text
Canonical Quantitative Claims
        ↓
    Aggregation
        ↓
    Derived Metric
```

The UI and API must distinguish reported values from derived values.

---

## 3. Source of Truth

The architecture must distinguish between canonical data and generated artifacts.

Canonical data includes:

```text
atlas/entities/**
atlas/claims/**
atlas/evidence/**
atlas/sources/**
atlas/schemas/**
atlas/taxonomies/**
```

Indexes and search structures should eventually be generated from canonical data rather than acting as independent sources of truth.

In particular:

```text
atlas/entities/index.json
```

must not become an independent conflicting copy of canonical entity records.

---

## 4. ID Convention

Canonical IDs follow:

```text
<type>:<canonical-slug>
```

Examples:

```text
person:ali-sanginian
organization:amin-investment-bank
organization:kian-financial-group
project:dadman
```

IDs must be stable and should not depend on UI filenames.

---

## 5. Product Architecture

### Atlas

Atlas is the canonical entity exploration experience.

It consumes:

```text
Entities
Claims
Evidence
Sources
Taxonomies
```

Atlas should eventually support multiple canonical Entity types rather than being limited to Person and Organization.

### Research

Research is the narrative and research experience.

Research content may contain:

```text
Content
Mentions
Candidate Claims
References to canonical Claims
```

Research must not create a second canonical knowledge system.

The intended workflow is:

```text
Mention
   ↓
Candidate Claim
   ↓
Review
   ↓
Canonical Claim
```

### Watch

Watch is the future event and freshness experience.

Watch must consume the canonical substrate and must not create duplicate Entity or Source systems.

---

## 6. Canonical Claim Model

The intended Claim model is:

```text
Claim
├── id
├── subject
├── predicate
├── object XOR value
├── temporal
├── status
├── confidence
└── evidence references
```

For relationship claims:

```text
subject
predicate
object
```

For quantitative claims:

```text
subject
predicate
value
```

The two forms share the same Claim infrastructure.

---

## 7. Quantitative Architecture

Reported quantitative information belongs inside the Claim layer.

Example:

```text
fund:kian-fund-1
        │
        └── HAS_AUM
                │
                └── value
                     ├── amount
                     ├── currency
                     ├── unit
                     ├── raw
                     └── period_type
```

Derived aggregates are calculated from canonical quantitative claims.

They are not independent canonical facts.

---

## 8. Research Workflow

Research introduces a research-stage workflow rather than a second knowledge base.

The intended lifecycle is:

```text
Mention
   ↓
Candidate Claim
   ↓
Review
   ↓
Canonical Claim
```

Once a candidate is promoted, the canonical Atlas Claim becomes the authoritative structured statement.

Research should retain references to canonical knowledge rather than duplicate it.

---

## 9. Development Rule

Before adding major product capabilities, the canonical data contract and validation system must be stabilized.

Priority order:

1. Baseline
2. Canonical schemas
3. Strict validation
4. Data cleanup and migration
5. Generated indexes
6. Atlas renderer
7. Research integration
8. Quantitative layer
9. Watch
10. Graph / intelligence
11. API / AI infrastructure
12. Production hardening

---

## 10. Architectural Constraint

No new product module may introduce a parallel canonical representation of:

- Person
- Organization
- Concept
- Investment
- Fund
- Source
- Claim
- Evidence

The shared canonical substrate remains the system of record.

---

## 11. Current Known Baseline Risks

The repository currently requires architectural cleanup before production-scale expansion.

Known areas requiring work include:

- strict schema enforcement
- cross-file reference validation
- evidence integrity
- source-schema consistency
- entity/index consistency
- claim storage conventions
- research candidate/canonical lifecycle
- broader entity rendering
- taxonomy/rule completeness

These are baseline work items and are not considered resolved by this document.

---

## 12. Baseline Scope

This document records the architecture baseline only.

It does not itself implement:

- schema migrations
- data migrations
- renderer changes
- Research changes
- Watch changes
- Graph changes
- API changes
- AI infrastructure

Those changes belong to later implementation phases.

---

## 13. Baseline Principle

The project should evolve around one canonical evidence-backed knowledge substrate.

Conceptually:

```text
               Canonical Knowledge Substrate

        Entity
           │
        Claim ───── Value
           │
        Evidence
           │
         Source
           │
     Taxonomies / Rules
           │
        Validator
           │
    ┌──────┼─────────┐
    ↓      ↓         ↓
  Atlas  Research   Watch
```

Atlas, Research and Watch are different product experiences over the same underlying knowledge system.
