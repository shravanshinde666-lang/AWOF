# Analysis Configuration

## Purpose

This phase joins a generated dataset profile with a user-selected business
objective and optional target column. It prepares context for a future ACSA
phase; it does not calculate capability scores or train models.

## Objectives

| Objective | Target requirement | Typical problem |
|---|---|---|
| Predict Behavior | Required | Classification or regression |
| Segment Customers | None | Clustering |
| Identify Risk | Required | Classification or regression |
| Analyze Retention | Required | Classification |
| Optimize Revenue | Optional | Regression or business analysis |

## Target heuristics

Candidates use Dataset Intelligence signals: detected type, cardinality, missing
percentage, constant-column detection, and identifier-candidate detection.
Binary/nominal/ordinal features suggest classification. Continuous numeric
features, and sufficiently variable numeric integers, suggest regression.
Identifiers, constants, and all-null columns are unsuitable.

High cardinality, substantial missingness, text fields, and objective/task
mismatches produce warnings rather than silently choosing a target.

## Problem inference

Segmentation always maps to clustering. Revenue optimization without a target
maps to business analysis. Other configurations infer classification or
regression from the user-selected target. Unknown or ambiguous types are
surfaced as warnings.

## Limitations

Target recommendations use heuristics and assist the user. AWOF does not claim
perfect semantic understanding of column meaning. Configurations are in-memory
only and disappear when the server restarts.
