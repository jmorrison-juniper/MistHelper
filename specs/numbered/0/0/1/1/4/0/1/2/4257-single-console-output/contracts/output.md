# Output contract

- Each `echo()` call produces one direct stdout write.
- Each `echo()` call produces one INFO record with the existing template and arguments.
- The application console handler rejects that record because stdout already shows it.
- The file handler retains that record at INFO.
- Unrelated logger records retain their configured console visibility.
- Repeated bootstrap does not accumulate handlers or change the filter result.
- Menu text, numbering, input handling, and dispatch do not change.
