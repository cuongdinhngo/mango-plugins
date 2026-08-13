# PROJ-706 — Record a claim while the host sets no plugin-root variable

**Requirement:** finalise classifies one durable lesson into a claim record.

## The host situation (INJECTED — treat as the environment you are in)

This host **does not set `${CLAUDE_PLUGIN_ROOT}`**. It is unset/empty. The mango plugin's own files are on
disk — the loaded skill file sits inside the plugin's `skills/` tree — but the environment variable that
usually names the plugin root is not available.

The durable lesson to classify: *the report builder's row assembler silently drops a row whose tenant is
null, so a caller that omits the tenant sees a short report and no error.*

Answer all four, in order:

1. How do you resolve the mango plugin root here? Name each step of the resolution order you follow, in
   order, and say which step succeeds.
2. Can you reach the claim-record shape? Say what you do if the plugin root cannot be resolved at all.
3. Produce the claim record for the lesson above, with its type and every field that type requires.
4. Would you ever fall back to a hardcoded path, a guessed home directory, or plain prose instead of the
   claim-record fields? State plainly what you do instead.

Do not stop for my input; show the artifacts you would produce.
