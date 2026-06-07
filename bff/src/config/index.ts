import 'dotenv/config'

function requireEnv(name: string): string {
  const val = process.env[name]
  if (!val) throw new Error(`Missing required env var: ${name}`)
  return val
}

export const config = {
  port: parseInt(process.env.PORT ?? '3000', 10),
  keycloak: {
    url: requireEnv('KEYCLOAK_URL'),
    realm: requireEnv('KEYCLOAK_REALM'),
    clientId: requireEnv('KEYCLOAK_CLIENT_ID'),
    clientSecret: requireEnv('KEYCLOAK_CLIENT_SECRET'),
  },
  frontendUrl: process.env.FRONTEND_URL ?? 'http://localhost:5173',
  nodeEnv: process.env.NODE_ENV ?? 'development',
  backendUrl: requireEnv('BACKEND_URL'),
  internalSecret: requireEnv('INTERNAL_SECRET'),
}
