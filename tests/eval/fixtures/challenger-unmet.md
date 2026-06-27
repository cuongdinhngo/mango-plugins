# PROJ-202 — Add email format validation to the contact form

**Acceptance Criteria:**
1. Submitting an address without an "@" shows the error "Enter a valid email".
2. Entering a valid address clears any previously shown error.
3. The submit button is disabled while the email field is invalid.

---

## Diff under review

```diff
--- a/src/contact_form.js
+++ b/src/contact_form.js
@@ -8,6 +8,18 @@ function initContactForm(root) {
   const input = root.querySelector("#email");
+  const errorEl = root.querySelector(".err");
+
+  function validate(value) {
+    if (!value.includes("@")) {
+      errorEl.textContent = "Enter a valid email";
+      return false;
+    }
+    errorEl.textContent = "";
+    return true;
+  }
+
+  input.addEventListener("input", (e) => {
+    validate(e.target.value);
+  });
 }
```
