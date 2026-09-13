Reduce lock audit history read memory.

The lock audit reader now keeps only the requested page while it infers expiry rows across the full trail. This keeps row order and row shape unchanged.
