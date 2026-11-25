/** The user's research interests as a list of strings, whatever shape the stored value has. */
export const interestsOf = (user) =>
  Array.isArray(user?.research_interests) ? user.research_interests.filter((item) => typeof item === 'string') : []
