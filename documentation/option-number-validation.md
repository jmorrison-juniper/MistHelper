# Upgrade Option Number Validation

The upgrade portal rejects non-ASCII digits and oversized digit strings before
integer conversion. Finite controls use their existing maximum. Unbounded
controls use the active Python representation limit. Refusals name the control
and do not include the typed value.
