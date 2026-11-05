# Diagnostic packaging revised before first submission

The read-only pre-pull check found that Mac-only HANDOFF.md was absent on LS6.
This was a diagnostic path assumption, not a runtime hash mismatch. No job was
submitted. The new audit is corrected to verify the original active 764-file
remote seal on compute and the 20-file Mac document/source seal locally. All
frozen files remain unchanged. Original scientific protocol is copied verbatim
into the new diagnostic namespace for reference. Costs and scope are unchanged:
one development node, 15-minute limit, 0.25-SU ceiling, no scientific tasks.
The user has confirmed current BatchMode access. No normal submission is allowed.
