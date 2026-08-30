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

Examples:

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
