# Research: Browser Token and Safe Device Selection

## Decision: Capture token availability at portal startup

**Decision**: Add a frozen setting that records whether an environment token
existed when the portal factory started.

**Rationale**: A browser token is safe only when it is an alternative to a
missing startup credential. A later environment change must not expose a new
sign-in mode in a running process.

**Alternatives considered**:

- Read the environment on every request. This makes the sign-in mode change
  while the portal runs.
- Offer all token modes. This can make two credentials compete in one session.

## Decision: Keep the browser token in the live session registry

**Decision**: Build a Mist session from the submitted token and store only the
session object in the existing in-memory `SessionRegistry`.

**Rationale**: The registry already binds a cloud session to the signed browser
and removes it on sign-out. The signed browser cookie contains only an owner
key. A run record and a lock record do not hold the cloud session.

**Alternatives considered**:

- Store the token in the browser session cookie. This exposes a credential to
  the client.
- Store the token in a run or capture record. This creates durable secret data.

## Decision: Derive a safe browser-token identity with `GetSelf`

**Decision**: Call the Mist `GetSelf` endpoint after the token session logs in.
Accept a nonempty token name only. Build the owner and audit identity from that
name and the browser identifier.

**Rationale**: The operator does not need to enter an email address for this
mode. The safe name identifies the lock holder without disclosing the token.

**Alternatives considered**:

- Reuse a typed email address. This does not meet the token-name requirement.
- Use a token digest. This is opaque to an operator and does not support audit
  review by the credential owner.

## Decision: Filter plans after complete capture

**Decision**: Preserve all capture rows. Add a selected type set to option
state. Use that set when the view lists target rows and when the service builds
the stored targets.

**Rationale**: A capture is an audit record for the full site. The selection
only limits a planned firmware action.

**Alternatives considered**:

- Filter capture data before storage. This removes audit data.
- Filter in the template alone. A crafted request could send omitted types.

## Decision: Calculate safe target by compatible model

**Decision**: Keep the existing per-type override only when every selected
model supports it. Otherwise use the highest compatible version for that model.
Compare that safe target with a known running version for the inventory marker.

**Rationale**: A shared type target can be invalid for a mixed-model site. A
model-level fallback keeps version selection safe and makes the marker honest.

**Alternatives considered**:

- Use the highest type-wide version. This can send an unsupported version.
- Mark unknown running versions as mismatched. This creates a false warning.
