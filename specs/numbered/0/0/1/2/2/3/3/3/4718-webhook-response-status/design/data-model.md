# Response contract

The repair adds no data field, key strategy, table, or endpoint.
An initial response enters pagination only after an integer HTTP status proves success.
A missing or malformed status produces an error without pagination.
The valid empty and successful response shapes remain unchanged.
The #4715 writer result still determines whether persistence and completion messages can appear.
