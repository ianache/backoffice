import Keycloak from 'keycloak-js'

const keycloakConfig = {
  url: import.meta.env.VITE_KEYCLOAK_URL as string | undefined,
  realm: import.meta.env.VITE_KEYCLOAK_REALM as string | undefined,
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID as string | undefined,
}

const missingConfig = Object.entries(keycloakConfig)
  .filter(([, value]) => !value)
  .map(([key]) => `VITE_KEYCLOAK_${key === 'clientId' ? 'CLIENT_ID' : key.toUpperCase()}`)

if (missingConfig.length && import.meta.env.MODE !== 'test') {
  throw new Error(`Missing Keycloak frontend config: ${missingConfig.join(', ')}`)
}

const keycloak = new Keycloak({
  url: keycloakConfig.url ?? '',
  realm: keycloakConfig.realm ?? '',
  clientId: keycloakConfig.clientId ?? '',
})

export default keycloak
