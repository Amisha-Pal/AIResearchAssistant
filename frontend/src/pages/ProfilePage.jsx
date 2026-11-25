import { KeyRound, Save, UserRound } from 'lucide-react'
import { useState } from 'react'

import { authApi } from '../api/auth'
import { parseApiError } from '../api/errors'
import { useAuth } from '../auth/useAuth'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { PasswordField } from '../components/ui/PasswordField'
import { TextField } from '../components/ui/TextField'
import { interestsOf } from '../utils/profile'
import { PASSWORD_HINT, validate, validators } from '../utils/validation'

const toForm = (user) => ({
  first_name: user.first_name || '',
  last_name: user.last_name || '',
  email: user.email || '',
  affiliation: user.affiliation || '',
  bio: user.bio || '',
  research_interests: interestsOf(user).join(', '),
})

const parseInterests = (text) =>
  text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

const formatDate = (value) => (value ? new Date(value).toLocaleString() : 'Never')

function ProfileForm() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState(() => toForm(user))
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState({ type: '', text: '' })
  const [saving, setSaving] = useState(false)
  const initial = toForm(user)
  const dirty = Object.keys(form).some((key) => form[key] !== initial[key])

  const update = (field) => (event) => {
    setForm((f) => ({ ...f, [field]: event.target.value }))
    setErrors((e) => ({ ...e, [field]: '' }))
    setMessage({ type: '', text: '' })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const found = validate({ email: () => validators.email(form.email) })
    setErrors(found)
    if (Object.keys(found).length) return
    const changes = {}
    for (const key of Object.keys(form)) {
      if (form[key] !== initial[key]) {
        changes[key] = key === 'research_interests' ? parseInterests(form[key]) : form[key].trim()
      }
    }
    setSaving(true)
    try {
      const updated = await authApi.updateProfile(changes)
      setUser(updated)
      setForm(toForm(updated))
      setMessage({ type: 'success', text: 'Profile saved.' })
    } catch (error) {
      const parsed = parseApiError(error)
      setErrors(parsed.fields)
      setMessage({ type: 'error', text: parsed.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="card" aria-labelledby="profile-heading">
      <header className="card-header">
        <UserRound size={20} aria-hidden="true" />
        <h2 id="profile-heading">Profile details</h2>
      </header>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert type={message.type || 'info'}>{message.text}</Alert>
        <TextField label="Username" value={user.username} disabled hint="Usernames cannot be changed." />
        <div className="form-grid">
          <TextField
            label="First name"
            autoComplete="given-name"
            value={form.first_name}
            onChange={update('first_name')}
            error={errors.first_name}
          />
          <TextField
            label="Last name"
            autoComplete="family-name"
            value={form.last_name}
            onChange={update('last_name')}
            error={errors.last_name}
          />
        </div>
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={update('email')}
          error={errors.email}
        />
        <TextField
          label="Affiliation"
          placeholder="University, lab or company"
          value={form.affiliation}
          onChange={update('affiliation')}
          error={errors.affiliation}
          maxLength={200}
        />
        <TextField
          label="Research interests"
          placeholder="e.g. NLP, retrieval-augmented generation, computer vision"
          value={form.research_interests}
          onChange={update('research_interests')}
          error={errors.research_interests}
          hint="Separate interests with commas (up to 20)."
        />
        <TextField
          label="Bio"
          multiline
          rows={4}
          value={form.bio}
          onChange={update('bio')}
          error={errors.bio}
          maxLength={2000}
        />
        <div className="form-actions">
          <Button type="submit" loading={saving} disabled={!dirty}>
            <Save size={16} aria-hidden="true" /> Save changes
          </Button>
        </div>
      </form>
    </section>
  )
}

const EMPTY_PASSWORDS = { current_password: '', new_password: '', new_password_confirm: '' }

function ChangePasswordForm() {
  const { changePassword } = useAuth()
  const [form, setForm] = useState(EMPTY_PASSWORDS)
  const [errors, setErrors] = useState({})
  const [message, setMessage] = useState({ type: '', text: '' })
  const [saving, setSaving] = useState(false)

  const update = (field) => (event) => {
    setForm((f) => ({ ...f, [field]: event.target.value }))
    setErrors((e) => ({ ...e, [field]: '' }))
    setMessage({ type: '', text: '' })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const found = validate({
      current_password: () => validators.required(form.current_password, 'Current password'),
      new_password: () =>
        validators.password(form.new_password) ||
        (form.new_password === form.current_password ? 'New password must differ from the current one.' : ''),
      new_password_confirm: () => validators.match(form.new_password_confirm, form.new_password),
    })
    setErrors(found)
    if (Object.keys(found).length) return
    setSaving(true)
    try {
      await changePassword(form)
      setForm(EMPTY_PASSWORDS)
      setMessage({ type: 'success', text: 'Password changed. All your other sessions have been signed out.' })
    } catch (error) {
      const parsed = parseApiError(error)
      setErrors(parsed.fields)
      setMessage({ type: 'error', text: parsed.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="card" aria-labelledby="password-heading">
      <header className="card-header">
        <KeyRound size={20} aria-hidden="true" />
        <h2 id="password-heading">Change password</h2>
      </header>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Alert type={message.type || 'info'}>{message.text}</Alert>
        <PasswordField
          label="Current password"
          autoComplete="current-password"
          value={form.current_password}
          onChange={update('current_password')}
          error={errors.current_password}
        />
        <PasswordField
          label="New password"
          autoComplete="new-password"
          value={form.new_password}
          onChange={update('new_password')}
          error={errors.new_password}
          hint={PASSWORD_HINT}
        />
        <PasswordField
          label="Confirm new password"
          autoComplete="new-password"
          value={form.new_password_confirm}
          onChange={update('new_password_confirm')}
          error={errors.new_password_confirm}
        />
        <div className="form-actions">
          <Button type="submit" loading={saving}>
            Update password
          </Button>
        </div>
      </form>
    </section>
  )
}

export default function ProfilePage() {
  const { user } = useAuth()
  return (
    <div className="page">
      <header className="page-header">
        <h1>Your profile</h1>
        <p className="muted">
          Member since {formatDate(user.date_joined)} · Last login {formatDate(user.last_login)}
        </p>
      </header>
      <div className="page-grid">
        <ProfileForm />
        <ChangePasswordForm />
      </div>
    </div>
  )
}
