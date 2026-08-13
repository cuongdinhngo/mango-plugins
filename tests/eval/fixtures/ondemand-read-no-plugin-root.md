# PROJ-712 — Review a frontend branch on a host that sets no plugin-root variable

**Requirement:** review scores this branch's frontend work.

## The host situation (INJECTED — treat as the environment you are in)

This host **does not set `${CLAUDE_PLUGIN_ROOT}`**. It is unset/empty. The mango plugin's files are on disk
— the loaded skill file sits inside the plugin's `skills/` tree — but the environment variable that usually
names the plugin root is not available.

`config.track` is `frontend`. The diff adds a new settings panel with a hover-only "reveal details"
affordance and two 32×32 px icon buttons.

Answer all five, in order:

1. The rules this phase applies live in a file beside the review skill, not inside it. Name that file and
   state how you resolve its path here. Name each step of the resolution order you follow, in order.
2. Do you read it, or do you skip it because the variable is unset? State which.
3. If the plugin root could not be resolved at all, what do you still score? Name the specific items.
4. Score the two problems in the diff against the rules that file carries, naming each gate.
5. Would a missing companion file ever mean a frontend AC ships with no check at all? State plainly.

Do not stop for my input; show the artifacts you would produce.
