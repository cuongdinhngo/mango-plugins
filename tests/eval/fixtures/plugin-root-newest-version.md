# Host check — resolving `<mango>` where the plugin-root variable is unset and several copies exist

This is not a ticket. It is a host-resolution question about the mango path-resolution order.

## The host state (INJECTED)

- `${CLAUDE_PLUGIN_ROOT}` is **not set**.
- The skill file currently loaded was read from a cache directory that carries **no** `PRINCIPLES.md` and
  **no** `.claude-plugin/plugin.json` alongside it, so step 2 of the order does not settle it.
- A read-only search under the host's plugin roots returns **three** directories that each carry both
  `PRINCIPLES.md` and `.claude-plugin/plugin.json`, in this order:

```
1.  ~/.host/plugins/cache/mango-a/          .claude-plugin/plugin.json → {"name":"mango","version":"1.8.0"}
2.  ~/.host/plugins/cache/mango-b/          .claude-plugin/plugin.json → {"name":"mango","version":"1.9.1"}
3.  ~/.host/plugins/cache/mango-c/          .claude-plugin/plugin.json → {"name":"mango","version":"1.10.1"}
```

The search returned them in the order shown. A plain string sort of the three version values would order
them `1.10.1`, `1.8.0`, `1.9.1`.

Answer all of the following, in order, as a mango skill would when it needs to read
`<mango>/templates/claim-record.md` on this host:

1. Which step of the resolution order are you on, and why did steps 1 and 2 not settle it?
2. Which of the three directories do you use? Give the path and the version.
3. What do you report to the operator about the search itself before you read anything?
4. Would taking the first result the search returned have given the same answer? What would it have loaded?
5. Would ordering the candidates as plain strings have given the same answer? Show the comparison you use
   instead.

Do not stop for my input; show the artifacts you would produce.
