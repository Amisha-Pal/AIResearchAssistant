import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { parseApiError } from '../api/errors'
import { useAuth } from '../auth/useAuth'
import { AuthLayout } from '../components/layout/AuthLayout'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { PasswordField } from '../components/ui/PasswordField'
import { TextField } from '../components/ui/TextField'
import { normalizeUsername, PASSWORD_HINT, validate, validators } from '../utils/validation'

const EMPTY = { username: '', email: '', first_name: '', last_name: '', password: '', password_confirm: '' }

export default function SignupPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const update = (field) => (event) => {
    setForm((f) => ({ ...f, [field]: event.target.value }))
    setErrors((e) => ({ ...e, [field]: '' }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const found = validate({
      username: () => validators.username(form.username),
      email: () => validators.email(form.email),
      password: () => validators.password(form.password),
      password_confirm: () => validators.match(form.password_confirm, form.password),
    })
    setErrors(found)
    setFormError('')
    if (Object.keys(found).length) return
    setSubmitting(true)
    try {
      await register({
        ...form,
        username: normalizeUsername(form.username),
        email: form.email.trim(),
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
      })
      navigate('/dashboard', { replace: true })
    } catch (error) {
      const parsed = parseApiError(error)
      setFormError(parsed.message)
      setErrors(parsed.fields)
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Your papers, chats and experiments stay private to your account."
      footer={
        <>
          Already have an account? <Link to="/login">Log in</Link>
        </>
      }
    >
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert type="error">{formError}</Alert>
        <div className="form-grid">
          <TextField
            label="First name (optional)"
            autoComplete="given-name"
            value={form.first_name}
            onChange={update('first_name')}
            error={errors.first_name}
          />
          <TextField
            label="Last name (optional)"
            autoComplete="family-name"
            value={form.last_name}
            onChange={update('last_name')}
            error={errors.last_name}
          />
        </div>
        <TextField
          label="Username"
          autoComplete="username"
          value={form.username}
          onChange={update('username')}
          error={errors.username}
          autoFocus
        />
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={update('email')}
          error={errors.email}
        />
        <PasswordField
          label="Password"
          autoComplete="new-password"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
          hint={PASSWORD_HINT}
        />
        <PasswordField
          label="Confirm password"
          autoComplete="new-password"
          value={form.password_confirm}
          onChange={update('password_confirm')}
          error={errors.password_confirm}
        />
        <Button type="submit" loading={submitting} className="btn-block">
          Create account
        </Button>
      </form>
    </AuthLayout>
  )
}
