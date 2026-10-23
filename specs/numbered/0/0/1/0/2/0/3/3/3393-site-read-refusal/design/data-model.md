# Data model: Site read refusal

The repair changes no model or schema.

The active selection holds the organization and ordered site identifiers.
The signed session holds validated options, the organization binding, and the submission nonce.
The run store holds a complete aggregate plan only after all required reads succeed.

A transport failure changes none of these values.
A replacement save must preserve an earlier plan and its signed options.
A confirmation read failure must preserve the existing plan.
No failure can advance a plan into a submitted state.
