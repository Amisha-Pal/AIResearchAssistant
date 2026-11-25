import { useState } from 'react'
import { Link } from 'react-router-dom'

import { authApi } from '../api/auth'
import { parseApiError } from '../api/errors'
import { AuthLayout } from '../components/layout/AuthLayout'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { TextField } from '../components/ui/TextField'
import { validators } from '../utils/validation'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [formError, setFormError] = useState('')
  const [sentMessage, setSentMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const message = validators.email(email)
    setError(message)
    setFormError('')
    if (message) return
    setSubmitting(true)
    try {
      const data = await authApi.requestPasswordReset(email.trim())
      setSentMessage(data.detail)
    } catch (err) {
      const parsed = parseApiError(err)
      setFormError(parsed.message)
      setError(parsed.fields.email || '')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter your account email and we'll send you a link to choose a new password."
      footer={
        <>
          Remembered it? <Link to="/login">Back to login</Link>
        </>
      }
    >
      {sentMessage ? (
        <div className="form">
          <Alert type="success">
            {sentMessage} The link works once and expires after a limited time. Check your spam folder if it doesn't arrive.
          </Alert>
          <Button variant="ghost" className="btn-block" onClick={() => setSentMessage('')}>
            Send to a different email
          </Button>
        </div>
      ) : (
        <form className="form" onSubmit={handleSubmit} noValidate>
          <Alert type="error">{formError}</Alert>
          <TextField
            label="Email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              setError('')
            }}
            error={error}
            autoFocus
          />
          <Button type="submit" loading={submitting} className="btn-block">
            Send reset link
          </Button>
        </form>
      )}
    </AuthLayout>
  )
}
