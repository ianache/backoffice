import { execFileSync } from 'node:child_process'
import { createServer } from 'node:net'

const port = Number.parseInt(process.argv[2] ?? '', 10)

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  console.error('Usage: node scripts/free-preview-port.mjs <port>')
  process.exit(2)
}

function run(command, args) {
  try {
    return execFileSync(command, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })
  } catch (error) {
    return error.stdout?.toString() ?? ''
  }
}

function windowsListeners() {
  const command = [
    `$connections = Get-NetTCPConnection -State Listen -LocalPort ${port} -ErrorAction SilentlyContinue`,
    '$connections | Select-Object -ExpandProperty OwningProcess -Unique',
  ].join('; ')
  return run('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', command])
    .split(/\s+/)
    .filter(Boolean)
    .map(Number)
}

function unixListeners() {
  return run('lsof', ['-tiTCP:' + port, '-sTCP:LISTEN'])
    .split(/\s+/)
    .filter(Boolean)
    .map(Number)
}

function processName(pid) {
  if (process.platform === 'win32') {
    const output = run('tasklist', ['/FI', `PID eq ${pid}`, '/FO', 'CSV', '/NH'])
    return output.match(/^"([^"]+)"/)?.[1] ?? ''
  }

  return run('ps', ['-p', String(pid), '-o', 'comm=']).trim()
}

const listeners = process.platform === 'win32' ? windowsListeners() : unixListeners()

for (const pid of listeners) {
  const name = processName(pid)
  if (!/(^|[\\/])node(?:\.exe)?$/i.test(name)) {
    console.error(`Port ${port} is owned by non-Node process ${name || 'unknown'} (${pid}); refusing to stop it.`)
    process.exit(1)
  }

  console.log(`Stopping stale Node preview on port ${port} (PID ${pid})`)
  if (process.platform === 'win32') {
    execFileSync('taskkill', ['/PID', String(pid), '/T', '/F'], { stdio: 'ignore' })
  } else {
    process.kill(pid, 'SIGTERM')
  }
}

async function canListen() {
  return new Promise((resolve) => {
    const server = createServer()
    server.unref()
    server.once('error', () => resolve(false))
    server.listen(port, 'localhost', () => server.close(() => resolve(true)))
  })
}

const deadline = Date.now() + 5000
while (!(await canListen())) {
  if (Date.now() >= deadline) {
    console.error(`Port ${port} did not become available within 5 seconds.`)
    process.exit(1)
  }
  await new Promise((resolve) => setTimeout(resolve, 100))
}
