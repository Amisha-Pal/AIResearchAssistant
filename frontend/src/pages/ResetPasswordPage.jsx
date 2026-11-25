import { useState } from 'react'
import { Link } from 'react-router-dom'

import { authApi } from '../api/auth'
import { parseApiError } from '../api/errors'
import { AuthLayout } from '../components/layout/AuthLayout'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { PasswordField } from '../components/ui/PasswordField'
import { PASSWORD_HINT, validate, validators } from '../utils/validation'

/** Read uid/token from the URL fragment once, then strip them from the address bar and history. */
function readResetParams() {
  const params = new URLSearchParams(window.location.hash.slice(1))
  const result = { uid: params.get('uid') || '', token: params.get('token') || '' }
  if (window.location.hash) {
    window.history.replaceState(null, '', window.location.pathname + window.location.search)
  }
  return result
}

export default function ResetPasswordPage() {
  const [{ uid, token }] = useState(readResetParams)
  const [form, setForm] = useState({ new_password: '', new_password_confirm: '' })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [done, setDone] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const linkIsMissing = !uid || !token

  const update = (field) => (event) => {
    setForm((f) => ({ ...f, [field]: event.target.value }))
    setErrors((e) => ({ ...e, [field]: '' }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const found = validate({
      new_password: () => validators.password(form.new_password),
      new_password_confirm: () => validators.match(form.new_password_confirm, form.new_password),
    })
    setErrors(found)
    setFormError('')
    if (Object.keys(found).length) return
    setSubmitting(true)
    try {
      const data = await authApi.confirmPasswordReset({ uid, token, ...form })
      setDone(data.detail)
    } catch (error) {
      const parsed = parseApiError(error)
      setFormError(parsed.fields.token || parsed.fields.uid || parsed.message)
      setErrors(parsed.fields)
    } finally {
      setSubmitting(false)
    }
  }

  const footer = (
    <>
      Need a new link? <Link to="/forgot-password">Request another reset</Link>
    </>
  )

  if (linkIsMissing) {
    return (
      <AuthLayout title="Invalid reset link" footer={footer}>
        <Alert type="error">This password reset link is incomplete. Open the link from your email again.</Alert>
      </AuthLayout>
    )
  }

  if (done) {
    return (
      <AuthLayout title="Password updated">
        <div className="form">
          <Alert type="success">{done}</Alert>
          <Link to="/login" className="btn btn-primary btn-block">
            Go to login
          </Link>
        </div>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Choose a new password" subtitle="All your other sessions will be signed out." footer={footer}>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert type="error">{formError}</Alert>
        <PasswordField
          label="New password"
          autoComplete="new-password"
          value={form.new_password}
          onChange={update('new_password')}
          error={errors.new_password}
          hint={PASSWORD_HINT}
          autoFocus
        />
        <PasswordField
          label="Confirm new password"
          autoComplete="new-password"
          value={form.new_password_confirm}
          onChange={update('new_password_confirm')}
          error={errors.new_password_confirm}
        />
        <Button type="submit" loading={submitting} className="btn-block">
          Reset password
        </Button>
      </form>
    </AuthLayout>
  )
}
