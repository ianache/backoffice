import { createRemoteJWKSet } from 'jose'
import { config } from '../config/index.js'

export const JWKS = createRemoteJWKSet(
  new URL(`${config.keycloak.url}/realms/${config.keycloak.realm}/protocol/openid-connect/certs`)
)

export const KEYCLOAK_ISSUER = `${config.keycloak.url}/realms/${config.keycloak.realm}`
