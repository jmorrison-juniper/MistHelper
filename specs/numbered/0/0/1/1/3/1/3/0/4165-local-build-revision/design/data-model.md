# Image revision data model

The clean build label contains the full hexadecimal commit returned by Git.
The dirty build label contains that commit followed by `-dirty`.
The helper passes this value as `MISTHELPER_BUILD_REVISION` only during the provider build.
The compose build overlay writes `org.opencontainers.image.revision`.

A clean label enters the existing commit and image-input comparison.
A dirty label produces a failed verification result before commit resolution.
An empty or invalid label produces a failed verification result with an explicit cause.

The build captures any previous metadata environment value and restores it after success or failure.
No new runtime setting or persistent operator configuration exists.
