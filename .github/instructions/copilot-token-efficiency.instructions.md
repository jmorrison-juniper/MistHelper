---
description: "Use when: any AI agent interaction. Copilot token efficiency guidelines for minimizing waste under token-based billing."
applyTo: "**"
---

# Copilot Token Efficiency (Effective June 2026)

GitHub Copilot uses token-based billing. Usage is measured by AI
compute consumed (model complexity, prompt size, response size,
context size, agent/tool usage).

Enterprise plans include pooled AI Credits (3900 Enterprise /
1900 Business). Users are blocked at 100% of their assigned budget
($200/month cap). Contact gh-copilot-support@juniper.net for
business-justified increases.

## Model Selection

- Use **Auto** mode by default.
- Reserve advanced reasoning models for complex tasks (architecture,
  multi-file refactors, root cause analysis).
- Never send throwaway prompts ("hi", "test", "you there?") to
  advanced models.

## Context Control

- Share only relevant files, functions, and snippets -- not entire
  repositories.
- Do not paste massive logs, full stack traces, or large JSON payloads.
  Trim to the relevant section.
- Start MCP servers only when needed. Each server's tool definitions
  consume tokens on every request (~10K input tokens before any user
  prompt is processed).
- Compact long chat sessions periodically.

## Prompt Discipline

- Keep prompts focused: "Review auth_service.py for retry logic issues"
  NOT "Analyze everything and improve it."
- Ask for a plan first before large changes.
- Combine related changes into one well-scoped prompt instead of 10
  separate prompts.
- Request constrained outputs -- output tokens cost more than input.

## Agent Mode Usage

- Use agent mode for multi-step tasks requiring file reads, tool calls,
  and iterative reasoning.
- Use standard chat for quick questions, syntax help, small fixes.
- Never use agent mode for trivial tasks.

## Debugging Efficiency

- Start with the smallest failing component and expand only if needed.
- Share only the failing test, function, or log snippet.

## Non-Coding Tasks

For email drafting, meeting summaries, presentations, and general
business writing, use Microsoft Copilot instead.

## Monitoring

Track usage from GitHub settings (https://github.com/settings/copilot/features)
or VS Code's Copilot icon tooltip (hover for AI credits consumed;
divide by 100 for USD cost this month).

## Quick Reference

| Want To... | Recommended | Avoid |
| - | - | - |
| Ask a quick question | Standard chat or Auto | Agent Mode |
| Fix a small bug | Share only the relevant file/function | Entire repository analysis |
| Review code | Limit scope to affected files | Large workspace reviews |
| Debug an issue | Start with the failing component | Loading unrelated modules |
| Generate code | Request only what is needed | Full repository rewrites |
| Analyze architecture | Use advanced models when needed | Repeated retries with vague prompts |
| Use MCP tools | Start only required MCPs | Loading every MCP server |
| Work efficiently | Ask for a plan first | "Fix everything" prompts |
