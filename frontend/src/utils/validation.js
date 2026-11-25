const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
// Mirrors Django's UnicodeUsernameValidator: Unicode letters, digits and @ . + - _
const USERNAME_RE = /^[\p{L}\p{N}_.@+-]+$/u

/** Same normalisation as Django's `AbstractBaseUser.normalize_username`. */
export const normalizeUsername = (value) => String(value ?? '').trim().normalize('NFKC')

export const validators = {
  required: (value, label = 'This field') => (String(value ?? '').trim() ? '' : `${label} is required.`),
  email: (value) => {
    if (!String(value ?? '').trim()) return 'Email is required.'
    return EMAIL_RE.test(value.trim()) ? '' : 'Enter a valid email address.'
  },
  username: (value) => {
    const v = normalizeUsername(value)
    if (!v) return 'Username is required.'
    if (v.length > 150) return 'Username must be at most 150 characters.'
    return USERNAME_RE.test(v) ? '' : 'Use only letters, digits and the characters @ . + - _'
  },
  password: (value) => {
    if (!value) return 'Password is required.'
    if (value.length < 8) return 'Password must be at least 8 characters.'
    if (/^\d+$/.test(value)) return 'Password cannot be entirely numeric.'
    return ''
  },
  match: (value, other, label = 'Passwords') => (value === other ? '' : `${label} do not match.`),
}

/** Run `rules` ({ field: () => message }) and return only the fields that failed. */
export function validate(rules) {
  const errors = {}
  for (const [field, rule] of Object.entries(rules)) {
    const message = rule()
    if (message) errors[field] = message
  }
  return errors
}

export const PASSWORD_HINT =
  'At least 8 characters, not entirely numeric, not a common password and not too similar to your username or email.'
