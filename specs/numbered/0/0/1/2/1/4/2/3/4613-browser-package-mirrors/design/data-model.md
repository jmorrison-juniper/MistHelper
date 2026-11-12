# Runner configuration model

The input is `/etc/apt/apt-mirrors.txt`.
The known Azure entry occurs exactly once.
The official HTTPS archive and security entries must both exist.
All other bytes remain unchanged.

The backup uses the suffix `.txt.issue-4613.bak`.
Exclusive creation prevents a repeat from replacing earlier recovery content.
A failed validation or backup prevents the configuration write.
A successful write must match the expected filtered content when read again.

No persistent product data, public interface, or dependency schema changes.
