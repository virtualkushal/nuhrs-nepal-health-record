// Turn an error thrown by lib/api.js `request()` into structured form errors.
//
// `request()` attaches the full DRF error body as `err.data` and the HTTP status
// as `err.status`. The DRF shapes we normalize:
//   { field: ["msg", …], … }          → per-field errors
//   { non_field_errors: ["msg"] }      → form-level
//   { detail: "msg" }                  → form-level (403 / 404 / throttle / auth)
//   { field: { sub: ["msg"] } }        → flattened to "sub: msg" under `field`
//   a bare string                      → form-level
//
// Returns { fieldErrors: { name: message }, formError: string }.
//   - fieldErrors — keyed by serializer field name, rendered under each input.
//   - formError   — a single summary line for the banner (empty when every
//     error is field-scoped, so the banner stays hidden and we don't repeat
//     ourselves).

// Keys DRF uses for errors that aren't tied to one field.
const FORM_LEVEL_KEYS = new Set(["non_field_errors", "detail", "__all__"]);

// Recursively collapse a DRF error value (string | array | nested object) into
// one human-readable line.
function flattenMessage(value) {
  if (value == null) return "";
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map(flattenMessage).filter(Boolean).join(" ");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, val]) => {
        const msg = flattenMessage(val);
        if (!msg) return "";
        return FORM_LEVEL_KEYS.has(key) ? msg : `${key}: ${msg}`;
      })
      .filter(Boolean)
      .join(" ");
  }
  return String(value);
}

/**
 * @param err   the Error thrown by lib/api.js request()
 * @param opts.aliases  optional { serializerField: localFieldName } map, for
 *   forms whose input state keys differ from the API's field names.
 */
export function parseApiError(err, { aliases = {} } = {}) {
  const data = err?.data;
  const fieldErrors = {};
  const formParts = [];

  if (data && typeof data === "object" && !Array.isArray(data)) {
    for (const [key, value] of Object.entries(data)) {
      const msg = flattenMessage(value);
      if (!msg) continue;
      if (FORM_LEVEL_KEYS.has(key)) {
        formParts.push(msg);
      } else {
        fieldErrors[aliases[key] || key] = msg;
      }
    }
  } else if (typeof data === "string" && data.trim()) {
    formParts.push(data.trim());
  }

  let formError = formParts.join(" ");
  // Only fall back to the thrown message when the body yielded nothing at all —
  // otherwise field errors carry the detail and the banner stays quiet.
  if (!formError && Object.keys(fieldErrors).length === 0) {
    formError = err?.message || "Something went wrong. Please try again.";
  }

  return { fieldErrors, formError };
}
