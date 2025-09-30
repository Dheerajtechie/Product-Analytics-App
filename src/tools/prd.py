def generate_prd_markdown(title: str, problem: str, goals: str, metrics: str, risks: str, executive_summary: str) -> str:
	return f"""
# {title}

## Executive Summary
{executive_summary}

## Problem Statement
{problem}

## Goals & Non-goals
{goals}

## Success Metrics
{metrics}

## Risks & Mitigations
{risks}

## Milestones
- Milestone 1: Discovery & Design
- Milestone 2: MVP rollout (A/B test)
- Milestone 3: Iterations & GA

## Appendices
- Data sources: users.csv, events.csv
- Definitions: activation = first key action; conversion = purchase after activation
"""
