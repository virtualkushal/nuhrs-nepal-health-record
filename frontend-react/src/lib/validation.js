// Shared validation rules, mirrored from the NUHRS backends so the browser
// enforces exactly what the API enforces. Keep these in sync with:
//   national-platform/core/validators.py         (NID_RE, NEPAL_MOBILE_RE, PASSWORD_RE)
//   national-platform/core/password_validation.py
//   the edge services' clinical/lab validators.py

// Nepal NIN (DoNIDCR): exactly 10 non-intelligible digits, no checksum.
export const NIN_PATTERN = "\\d{10}";
export const NIN_TITLE = "National ID must be exactly 10 digits (Nepal NIN)";

// Nepal mobile: optional +977 / 00977 / 0 prefix, then 9[678] + 8 digits.
// Covers NTC, Ncell and Smart Cell ranges. Storage is the bare 10 digits.
export const NEPAL_MOBILE_PATTERN = "(\\+977|00977|0)?9[678]\\d{8}";
export const NEPAL_MOBILE_TITLE =
  "Enter a valid Nepal mobile number, e.g. 9841234567 or +9779841234567";

// Password policy: >=8 chars with upper + lower + digit + special.
export const PASSWORD_PATTERN =
  "(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[^A-Za-z0-9]).{8,}";
export const PASSWORD_TITLE =
  "At least 8 characters with an uppercase letter, a lowercase letter, a digit and a special character";

export function isValidNin(value) {
  return new RegExp(`^${NIN_PATTERN}$`).test(
    String(value || "").replace(/[\s-]/g, "")
  );
}

export function isValidNepalMobile(value) {
  return new RegExp(`^${NEPAL_MOBILE_PATTERN}$`).test(
    String(value || "").replace(/[\s\-()]/g, "")
  );
}

// Strip separators and any +977 / 00977 / 0 prefix -> bare 10 digits.
export function normalizeNepalMobile(value) {
  const cleaned = String(value || "").replace(/[\s\-()]/g, "");
  if (!isValidNepalMobile(cleaned)) return cleaned;
  if (cleaned.startsWith("+977")) return cleaned.slice(4);
  if (cleaned.startsWith("00977")) return cleaned.slice(5);
  if (cleaned.startsWith("0")) return cleaned.slice(1);
  return cleaned;
}

export function isValidPassword(value) {
  return new RegExp(`^${PASSWORD_PATTERN}$`).test(String(value || ""));
}
