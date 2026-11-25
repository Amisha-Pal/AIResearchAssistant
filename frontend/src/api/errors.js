function firstMessage(value) {
  if (Array.isArray(value)) return firstMessage(value[0])
  if (value && typeof value === 'object') return firstMessage(Object.values(value)[0])
  return value ? String(value) : ''
}

/**
 * Normalise an Axios error from the backend's `{"error": {...}}` envelope into
 * `{ message, fields }`, where `fields` maps field names to one message each.
 */
/** True when the API could not be reached (network failure, or a gateway/dev proxy with the backend down). */
export function isServerUnreachable(error) {
  if (!error?.response) return true
  return [502, 503, 504].includes(error.response.status) && !error.response.data?.error
}

export function parseApiError(error, fallback = 'Something went wrong. Please try again.') {
  if (isServerUnreachable(error)) {
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
