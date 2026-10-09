### Late event-stream subscribers keep the run's earlier events

- **Fixed**: A browser that connects while an operation runs receives the events that the run published before the connection. The Execution Log keeps its first lines. Refs #4144.
