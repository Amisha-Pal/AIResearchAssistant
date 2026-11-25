function firstMessage(value) {
  if (Array.isArray(value)) return firstMessage(value[0])
  if (value && typeof value === 'object') return firstMessage(Object.values(value)[0])
  return value ? String(value) : ''
}

/**
 * Normalise an Axios error from the backend's `{"error": {...}}` envelope into
 * `{ message, fields }`, where `fields` maps field names to one message each.
 */
export function parseApiError(error, fallback = 'Something went wrong. Please try again.') {
  if (!error?.response) {
    return {
      message: 'Cannot reach the server. Check that the backend is running and try again.',
      fields: {},
    }
  }
  const envelope = error.response.data?.error
  if (!envelope) {
    return { message: fallback, fields: {} }
  }
  const fields = {}
  for (const [name, value] of Object.entries(envelope.fields || {})) {
    if (name !== 'non_field_errors') fields[name] = firstMessage(value)
  }
  const nonField = firstMessage(envelope.fields?.non_field_errors)
  const hasFieldErrors = Object.keys(fields).length > 0
  let message = nonField || envelope.message || fallback
  if (hasFieldErrors && !nonField) message = 'Please fix the highlighted fields.'
  return { message, fields }
}
