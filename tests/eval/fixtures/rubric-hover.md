# PROJ-302 — Row actions on the records table

**Requirement:** Each table row exposes an "edit" action and a draggable reorder handle.

**Acceptance Criteria:**
- Every row offers an edit action.
- Rows can be reordered by dragging the handle.

---

## Diff under review

```diff
--- a/web/records-table.css
+++ b/web/records-table.css
@@ -40,6 +40,12 @@ .records-row {
   align-items: center;
 }
+
+/* edit action is revealed only when the pointer is over the row */
+.records-row .edit-action { display: none; }
+.records-row:hover .edit-action { display: inline-flex; }
--- a/web/records-table.js
+++ b/web/records-table.js
@@ -12,6 +12,14 @@ function wireRow(row) {
   const handle = row.querySelector(".reorder-handle");
+  // reorder via dragging the handle
+  handle.addEventListener("mousedown", (e) => {
+    startDrag(row, e.clientX, e.clientY);
+  });
+  document.addEventListener("mousemove", (e) => {
+    if (dragging) moveDrag(e.clientX, e.clientY);
+  });
 }
```
