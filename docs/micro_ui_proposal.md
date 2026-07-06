# Propuesta Arquitectónica: Desacoplamiento de Frontend en Micro-UIs

Este documento presenta la propuesta técnica para estructurar el frontend de la **Plataforma BackOffice Multi-Tenant** utilizando una arquitectura de Micro-Frontends (Micro-UIs). El objetivo principal es asegurar que el proyecto `portal` funcione exclusivamente como un **Shell** (orquestador ligero), delegando la lógica de negocio y las vistas a Micro-UIs desacopladas dentro del monorepo `pnpm`.

---

## 1. Diagrama Conceptual de la Arquitectura

El siguiente diagrama ilustra cómo interactúan el **Shell (Portal)**, las **Micro-UIs** remotas y el **BFF** a través de **Vite Module Federation** y la compartición de contexto en tiempo de ejecución.

```mermaid
graph TD
    %% Clientes & Capa de Entrada
    subgraph Navegador [Navegador del Usuario]
        Shell["Portal Shell (Host Vue 3)"]
        
        subgraph Remotes [Micro-UIs Remotas]
            MS["mui-security (Seguridad y Accesos)"]
            MT["mui-tenants (Gestión de Tenants)"]
            MFF["mui-feature-flags (Flags y Reglas)"]
            MC["mui-clients (Clientes y Whitelabel)"]
            MO["mui-observability (Métricas y SLAs)"]
        end
    end

    %% Relaciones de Carga
    Shell -.->|Importa Rutas e Inyecta Contenedor| MS
    Shell -.->|Importa Rutas e Inyecta Contenedor| MT
    Shell -.->|Importa Rutas e Inyecta Contenedor| MFF
    Shell -.->|Importa Rutas e Inyecta Contenedor| MC
    Shell -.->|Importa Rutas e Inyecta Contenedor| MO

    %% Recursos Compartidos
    SharedPinia["Pinia (Estado Compartido: Auth, Toast)"]
    SharedCSS["Variables CSS (Design System Stitch)"]
    
    Shell ====> SharedPinia
    Shell ====> SharedCSS
    MS -.->|Consume| SharedPinia
    MT -.->|Consume| SharedPinia
    MFF -.->|Consume| SharedPinia
    MC -.->|Consume| SharedPinia
    MO -.->|Consume| SharedPinia

    %% Backend/BFF
    BFF["BFF Proxy (Node.js - Port 3000)"]
    Backend["FastAPI Backend (Python - Port 8000)"]
    Keycloak["Keycloak IdP"]

    Shell -->|OAuth2 / PKCE| Keycloak
    Remotes -->|API Calls (HTTPS / WS)| BFF
    BFF -->|Propaga Contexto| Backend
    BFF -->|Admin REST API| Keycloak
```

---

## 2. Responsabilidades del Shell (Portal)

Para garantizar un acoplamiento mínimo, el **Portal Shell** no debe contener vistas ni lógica de negocio de ningún dominio específico. Sus únicas responsabilidades técnicas son:

1. **Autenticación Global y SSO**:
   - Inicializar el SDK de `keycloak-js`.
   - Manejar el flujo de autenticación **OAuth2 Authorization Code con PKCE**.
   - Gestionar el ciclo de vida del token JWT (almacenamiento, refresco y expiración).
2. **Layout y Estructura Global**:
   - Renderizar el marco visual común: barra de navegación superior, cajón de navegación lateral (Drawer) y pie de página.
   - Control de temas global (Toggle persistente entre Light/Dark Mode) inyectando clases de tema en el nodo `<html>`.
3. **Orquestación y Enrutamiento Dinámico**:
   - Actuar como el `Router` central de Vue 3.
   - Cargar de forma perezosa (Lazy Loading) las rutas expuestas por cada Micro-UI remota.
   - Proteger rutas mediante guardias de navegación (`beforeEach`) según los roles decodificados del JWT.
4. **Servicios Transversales (Cross-Cutting)**:
   - Proveer un bus de notificaciones global (`ToastStore`) para mensajes de éxito, advertencia y error.
   - Proveer un cliente HTTP centralizado (instancia de `axios`) preconfigurado con interceptores para inyectar cabeceras de autorización y capturar errores de red (por ejemplo, redirección automática ante un `401 Unauthorized`).
5. **Tokens de Diseño Centralizados**:
   - Declarar las variables CSS globales (`index.css`) que implementan la paleta de colores de Google Stitch, tipografía, bordes redondeados y espaciado para asegurar coherencia visual.

---

## 3. Propuesta de Agrupación de Micro-UIs

A continuación se proponen **5 Micro-UIs** basadas en la cohesión del dominio de negocio, los roles de usuario y las fases del roadmap definidas en el PRD:

### 1️⃣ `mui-security` (Gestión de Accesos e Identidad)
* **Objetivo**: Administrar usuarios internos, sus roles y la seguridad general de la cuenta/tenant.
* **Funcionalidades agrupadas**:
  - Creación y edición de usuarios por tenant.
  - Asignación de roles por tenant (`TenantOwner`, `TenantAdmin`, `TenantViewer`) y por producto (`ProductManager`, `ProductDeveloper`, `ProductQA`).
  - Activación/desactivación de perfiles de usuario.
  - Restablecimiento de credenciales y dispositivos de doble factor (MFA/TOTP/WebAuthn).
  - Consulta de logs de auditoría de seguridad específicos del usuario.
* **Roles de usuario destino**: `TenantAdmin`, `TenantOwner`, `PlatformAdmin`.
* **Fase del Roadmap**: Fase 1 (Core) y Fase 4 (MFA Avanzado).

### 2️⃣ `mui-tenants` (Administración de Organizaciones)
* **Objetivo**: Proveer la consola de control de tenants globales de la plataforma.
* **Funcionalidades agrupadas**:
  - Listado, búsqueda y filtrado avanzado de tenants registrados.
  - Creación, modificación del estado (activo, suspendido, eliminado) de tenants.
  - Asociación de productos y servicios habilitados por tenant.
  - Configuración del whitelabel básico a nivel de tenant (logotipo y colores iniciales).
* **Roles de usuario destino**: `PlatformAdmin`.
* **Fase del Roadmap**: Fase 1 (Core).

### 3️⃣ `mui-feature-flags` (Gestión de Lanzamientos y Reglas)
* **Objetivo**: Controlar la activación y evaluación de funcionalidades críticas mediante reglas.
* **Funcionalidades agrupadas**:
  - Panel de control de Feature Flags en sus 4 niveles jerárquicos (Global → Tenant → Producto → Empresa).
  - Visual **Rule Builder** con soporte para ordenación drag-and-drop de prioridades.
  - Gestor de segmentos de usuario reutilizables.
  - Simulador de evaluación determinista de reglas antes de su publicación en producción.
* **Roles de usuario destino**: `PlatformAdmin`, `TenantAdmin`, `TenantOwner`, `ProductManager`, `ProductDeveloper`, `ProductQA`.
* **Fase del Roadmap**: Fase 1 (Flags base + Rule Builder) y Fase 2 (Rollout porcentual).

### 4️⃣ `mui-clients` (Clientes Empresa, Whitelabel y Localización)
* **Objetivo**: Gestionar las identidades cliente (B2B) del tenant, permitiendo la personalización extrema de marca e idioma a nivel de empresa.
* **Funcionalidades agrupadas**:
  - CRUD de clientes (Personas naturales y Empresas).
  - Editor visual de **Doble Whitelabel** (personalización visual del tenant que puede ser sobrescrita por el cliente empresa: dominio propio, logos, paleta de colores exclusiva).
  - Gestor de localización y perfiles de idioma (configuración jerárquica de monedas, unidades, zonas horarias y traducción de etiquetas/mensajes).
* **Roles de usuario destino**: `TenantAdmin`, `CompanyAdmin`.
* **Fase del Roadmap**: Fase 2 (Clientes Empresa + Doble Whitelabel + Localización Avanzada).

### 5️⃣ `mui-observability` (Métricas de Calidad, SLAs y Estado del Servicio)
* **Objetivo**: Monitorear el rendimiento de la plataforma y garantizar el cumplimiento de los acuerdos de nivel de servicio.
* **Funcionalidades agrupadas**:
  - Dashboard de Health Checks en tiempo real de APIs, base de datos, BFF y Keycloak.
  - Gráficos de tendencias de latencia (p95/p99) y tasas de error.
  - Panel de control de objetivos de servicio (SLO) y acuerdos (SLA).
  - Alertas visuales por degradación y su correlación directa con cambios en Feature Flags.
* **Roles de usuario destino**: `PlatformAdmin`, `TenantAdmin`.
* **Fase del Roadmap**: Fase 3.

---

## 4. Estrategia de Integración Técnica

Para materializar esta separación sin penalizar la experiencia de usuario (SPA) ni sobrecargar el tamaño de descarga del cliente web, proponemos la siguiente estrategia de integración basada en **Vite Module Federation**:

### 🛠️ Configuración de Compartición de Dependencias (Vite)

Cada Micro-UI y el Shell se compilarán de forma independiente, pero compartirán las librerías fundamentales en tiempo de ejecución. 

#### Ejemplo de Configuración en el Host (`portal/vite.config.ts`):
```typescript
import { defineConfig } from 'vite';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    federation({
      name: 'portal-shell',
      remotes: {
        'mui_security': 'http://localhost:5174/assets/remoteEntry.js',
          'mui_tenants': 'http://localhost:5176/assets/remoteEntry.js',
          'mui_feature_flags': 'http://localhost:5178/assets/remoteEntry.js',
      },
      shared: ['vue', 'vue-router', 'pinia', 'axios']
    })
  ]
});
```

#### Ejemplo de Configuración en un Remote (p. ej., `microuis/mui-security/vite.config.ts`):
```typescript
import { defineConfig } from 'vite';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    federation({
      name: 'mui_security',
      filename: 'remoteEntry.js',
      exposes: {
        './routes': './src/router/routes.ts', // Expone las rutas y componentes internos
      },
      shared: ['vue', 'vue-router', 'pinia', 'axios']
    })
  ]
});
```

### 🛣️ Registro Dinámico de Rutas

Para evitar acoplar el Shell a los módulos remotos durante la compilación, el Shell importará dinámicamente las rutas expuestas por cada Micro-UI al inicializar la aplicación.

```typescript
// En portal/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true }
    }
    // Rutas fijas del shell (Login, Unauthorized, etc.)
  ]
});

// Carga dinámica de rutas desde los Micro-Frontends
const loadMicroUIRoutes = async () => {
  try {
    // Importa dinámicamente el módulo expuesto por mui-security
    const securityModule = await import('mui_security/routes');
    securityModule.routes.forEach((route: any) => {
      router.addRoute(route);
    });
  } catch (error) {
    console.error("Error cargando rutas de mui-security:", error);
  }
};

loadMicroUIRoutes();
export default router;
```

### 📦 Gestión de Estados unificada (Pinia)

El Shell creará y montará la instancia única de **Pinia** en la aplicación Vue. Dado que `pinia` se encuentra en la lista de dependencias compartidas (`shared`), cualquier Micro-UI cargada dinámicamente utilizará el mismo contexto de Pinia. 
Esto permite que:
- Las Micro-UIs accedan de forma nativa a los stores globales del Shell (como `useAuthStore` o `useToastStore`).
- Las Micro-UIs definan sus propios stores locales para gestionar su lógica interna (por ejemplo, `useRuleBuilderStore`) sin interferir con otros módulos.

---

## 5. Matriz de Resumen y Viabilidad

| Micro-UI | Dependencias BFF | Nivel de Complejidad | Fricción de Integración | Alternativa en caso de fallo de Federation |
| :--- | :--- | :--- | :--- | :--- |
| **`mui-security`** | `/bff/tenant/{id}/users`, Keycloak API | Media | Baja (Usa tokens del Shell) | Componentes Web (Custom Elements) |
| **`mui-tenants`** | `/bff/tenants` | Baja | Muy Baja | Componentes Web (Custom Elements) |
| **`mui-feature-flags`** | `/bff/tenant/{id}/product/{pid}/flags` | Alta (Rule Builder drag-and-drop) | Media (Comparte componentes visuales) | Iframe de alto rendimiento con bus de mensajes |
| **`mui-clients`** | `/api/clients`, `/api/localization` | Media | Media (Doble whitelabel requiere inyección de CSS) | Carga directa de hojas de estilo dynamic |
| **`mui-observability`** | `/bff/health/services` | Baja-Media | Baja | Widget incrustable mediante web components |
