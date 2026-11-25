import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { parseApiError } from '../api/errors'
import { useAuth } from '../auth/useAuth'
import { AuthLayout } from '../components/layout/AuthLayout'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { PasswordField } from '../components/ui/PasswordField'
import { TextField } from '../components/ui/TextField'
import { validate, validators } from '../utils/validation'

export default function LoginPage() {
  const { login, notice, clearNotice } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [form, setForm] = useState({ identifier: '', password: '' })
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
      identifier: () => validators.required(form.identifier, 'Username or email'),
      password: () => validators.required(form.password, 'Password'),
    })
    setErrors(found)
    setFormError('')
    if (Object.keys(found).length) return
    setSubmitting(true)
    try {
      await login(form.identifier.trim(), form.password)
      clearNotice()
      navigate(location.state?.from?.pathname || '/dashboard', { replace: true })
    } catch (error) {
      const parsed = parseApiError(error)
      setFormError(error.response?.status === 401 ? 'Incorrect username/email or password.' : parsed.message)
      setErrors(parsed.fields)
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to continue your research."
      footer={
        <>
          New here? <Link to="/signup">Create an account</Link>
        </>
      }
    >
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert type="info">{notice}</Alert>
        <Alert type="error">{formError}</Alert>
        <TextField
          label="Username or email"
          name="username"
          autoComplete="username"
          value={form.identifier}
          onChange={update('identifier')}
          error={errors.identifier || errors.username}
          autoFocus
        />
        <PasswordField
          label="Password"
          name="password"
          autoComplete="current-password"
          value={form.password}
          onChange={update('password')}
          error={errors.password}
        />
        <div className="form-row-end">
          <Link to="/forgot-password">Forgot password?</Link>
        </div>
        <Button type="submit" loading={submitting} className="btn-block">
          Log in
        </Button>
      </form>
    </AuthLayout>
  )
}
