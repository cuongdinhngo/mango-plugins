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
@@ -8,6 +8,16 @@ import { useState } from "react";
 function ContactForm() {
   const [email, setEmail] = useState("");
+  const [error, setError] = useState("");
+
+  function validate(value) {
+    if (!value.includes("@")) {
+      setError("Enter a valid email");
+      return false;
+    }
+    setError("");
+    return true;
+  }
 
   return (
     <form>
@@ -16,7 +26,8 @@ function ContactForm() {
       <label>Email</label>
-      <input value={email} onChange={(e) => setEmail(e.target.value)} />
+      <input value={email} onChange={(e) => { setEmail(e.target.value); validate(e.target.value); }} />
+      {error && <span className="err">{error}</span>}
       <button type="submit">Send</button>
     </form>
   );
 }
```
