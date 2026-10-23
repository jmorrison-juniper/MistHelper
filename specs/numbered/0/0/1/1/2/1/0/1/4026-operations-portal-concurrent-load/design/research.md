# Research

## Decision

Use a module lock with a second application configuration read inside the lock.

## Rationale

The current helper checks and assigns shared configuration without synchronization.
The issue comments reproduce duplicate construction after a 50 millisecond constructor delay.
Current `origin/main` at `9991d30a187e5d215462eefac60a09a57e5f99e5` retains this implementation.
The issue artifacts endpoint returned HTTP 404.
The linked image concerns mixed menu evidence, which remains outside this repair.

## Alternatives considered

Eager initialization changes application construction and expands ownership.
An application-local lock requires additional setup changes.
A lock around every operation would serialize requests and recreate the responsiveness risk.

## Evidence

Use a barrier for simultaneous first access and a controlled constructor release.
An instrumented configuration records every initial executor read before the constructor can finish.
The test fails if any request receives a different executor.
No unknown dependency or design question remains.
