# DOCUMENTO DE REQUERIMIENTOS DE PRODUCTO (PRD)
## PROYECTO: PLATAFORMA DE GESTIÓN DE FEATURE FLAGS Y CONFIGURACIÓN REMOTA CONSECUTIVA (REMOTE CONFIG)
**Destinatario del Input:** Claude Code / AI Coding Agent
**Entorno Tecnológico:** NestJS (TypeScript), PostgreSQL 12+ / MySQL 8.0+, SDK JavaScript/TypeScript

## 0. MAPA CONCEPTUAL



## 1. OBJETIVO GENERAL DEL SISTEMA
El sistema tiene como objetivo desacoplar el despliegue de código del lanzamiento comercial mediante la gestión de *Feature Flags* booleanas/multivariables, y unificar el control dinámico de textos, traducciones y mensajes (Remote Config) organizados por espacios de nombres (*Namespaces*). La plataforma debe operar bajo un modelo multi-inquilino de tres niveles correlacionados (**Tenant → Compañía → Producto**), garantizando latencias de evaluación menores a 1ms en el servidor BFF (Backend For Frontend) y actualizaciones en tiempo real sin parpadeo (*flicker*) visual en las aplicaciones cliente.
## 2. MODELO DE DOMINIO Y ESQUEMA DE BASE DE DATOS UNIFICADO
Para garantizar una única implementación en el acceso a datos (DAL), el esquema es 100% compatible entre **PostgreSQL 12+** y **MySQL 8.0+**, utilizando el tipo de datos JSON nativo y tipos estandarizados.
### Esquema DDL Unificado
```sql
-- 1. Catálogo de Productos
CREATE TABLE products (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, DEPRECATED
    platform_tags VARCHAR(50) NOT NULL, -- Almacenado como CSV: 'ANGULAR,VUE,FLUTTER'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) NOT NULL
);

-- 2. Espacios de Nombres para Segmentación de Carga
CREATE TABLE namespaces (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(50) NOT NULL, -- 'common', 'page_dashboard', 'form_registro'
    scope VARCHAR(20) NOT NULL, -- 'TENANT', 'COMPANY', 'PRODUCT'
    tenant_id VARCHAR(36) NOT NULL,
    company_id VARCHAR(36) NULL,
    product_id VARCHAR(36) NULL
);

-- 3. Definición de Llaves Técnicas de Etiquetas
CREATE TABLE ui_labels (
    id VARCHAR(36) PRIMARY KEY,
    namespace_id VARCHAR(36) NOT NULL,
    label_key VARCHAR(150) NOT NULL, -- 'lbl_documento_identidad'
    description TEXT
);

-- 4. Traducciones, Variantes y Reglas de Targeting Contextual
CREATE TABLE ui_label_translations (
    id VARCHAR(36) PRIMARY KEY,
    ui_label_id VARCHAR(36) NOT NULL,
    locale VARCHAR(10) NOT NULL, -- 'es_PE', 'en_US'
    targeting_rules JSON, -- Reglas complejas: [{"role": "VIP_CUSTOMER"}]
    translated_text TEXT NOT NULL,
    default_text TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1
);

```
### Índices de Alto Rendimiento
 * **PostgreSQL:**
   ```sql
   CREATE INDEX idx_namespaces_hierarchy ON namespaces (name, tenant_id, company_id, product_id);
   CREATE INDEX idx_label_translations_rules ON ui_label_translations USING gin (targeting_rules);
   
   ```
 * **MySQL 8.0+:**
   ```sql
   CREATE INDEX idx_namespaces_hierarchy ON namespaces (name, tenant_id, company_id, product_id);
   CREATE INDEX idx_mysql_json_role ON ui_label_translations ((CAST(JSON_EXTRACT(targeting_rules, '$[0].role') AS CHAR(50))));
   
   ```
## 3. ARQUITECTURA DEL BFF (NESTJS) Y CONTRATOS DE API
El BFF expone endpoints altamente eficientes y asume el procesamiento computacional de las reglas de negocio. No expone las reglas de targeting al cliente por motivos de seguridad; solo entrega el resultado resuelto.
### A. Escudo de Seguridad: ContextGuard
Toda petición de consumo debe validar criptográficamente un token firmado (*Sealed Context Token* / JWT) enviado en la cabecera X-Context-Token. El Guard debe desencriptar, validar firma y colocar la identidad en el objeto Request.
```typescript
// Estructura del Payload del JWT Verificado
export interface VerifiedContextPayload {
  sub: string;         // user_id
  tenant_id: string;   // tenant_id
  company_id: string;  // company_id
  user_profile: string;// role (Ej: 'VIP_CUSTOMER')
  user_segment?: string; // segment
}

```
### B. Especificación de Endpoints (API Contracts)
#### 1. Carga Consolidada Inicial: POST /api/v1/features/bootstrap
 * **Propósito:** Inyectar en un solo viaje las flags de arquitectura activa y los textos esenciales para mitigar pantallas de carga y parpadeos visuales.
 * **Request Body:**
   ```json
   {
     "product_id": "prod_banca_movil_flutter",
     "current_locale": "es_PE",
     "cached_namespaces": {
       "common": "ns_hash_111"
     }
   }
   
   ```
 * **Response (200 OK):**
   * Si el hash enviado coincide con el del servidor, el nodo de datos de ese namespace retorna NOT_MODIFIED y el campo data vacío.
   ```json
   {
     "snapshot_id": "snap_master_998a",
     "feature_flags": {
       "interfaz-moderna-2026": { "enabled": true, "variant": "treatment_a" }
     },
     "namespaces": {
       "common": {
         "hash": "ns_hash_111",
         "status": "NOT_MODIFIED",
         "data": {}
       },
       "page_home": {
         "hash": "ns_hash_555",
         "status": "OK",
         "data": {
           "lbl_bienvenida": "Hola, socio VIP",
           "lbl_resumen": "Este es tu estado de cuenta"
         }
       }
     }
   }
   
   ```
#### 2. Carga Diferida: GET /api/v1/features/lazy
 * **Propósito:** Descarga asíncrona en segundo plano (*Prefetching*) de páginas secundarias o formularios pesados.
 * **Query Parameters:** ?product_id=prod_banca_movil_flutter&namespace=form_registro&locale=es_PE
 * **Response (200 OK):**
   ```json
   {
     "namespace": "form_registro",
     "data": {
       "lbl_documento_identidad": "DNI / Carnet de Extranjería",
       "val_documento_requerido": "El documento es obligatorio para clientes VIP"
     }
   }
   
   ```
## 4. ALGORITMO CORE: "SOBREESCRITURA POR CERCANÍA"
El servicio CoreEngineService de NestJS debe resolver las etiquetas cruzando las capas de datos consolidadas en memoria RAM. El algoritmo de combinación obligatoria debe seguir la precedencia lineal: **Tenant (Base) → Compañía (Media) → Producto (Máxima Prioridad)**.
### Lógica Pseudocódigo del Algoritmo
```text
FUNCIÓN evaluarEtiquetas(contexto, namespace, idioma):
    acumulador = ObjetoVacío()
    
    // Capa 1: Cargar configuraciones del Tenant Global
    etiquetasTenant = buscarEnRAM(contexto.tenantId, namespace, idioma)
    mezclarCapa(acumulador, etiquetasTenant, contexto.role)
    
    // Capa 2: Sobrescribir con configuraciones de la Compañía
    etiquetasCompany = buscarEnRAM(contexto.tenantId, contexto.companyId, namespace, idioma)
    mezclarCapa(acumulador, etiquetasCompany, contexto.role)
    
    // Capa 3: Sobrescribir con máxima prioridad del Producto específico
    etiquetasProduct = buscarEnRAM(contexto.tenantId, contexto.companyId, contexto.productId, namespace, idioma)
    mezclarCapa(acumulador, etiquetasProduct, contexto.role)
    
    RETORNAR acumulador

PROCEDIMIENTO mezclarCapa(acumulador, listadoEtiquetas, userRole):
    PARA CADA etiqueta EN listadoEtiquetas:
        // Si aplica regla de targeting por rol, tiene prioridad en su capa
        SI etiqueta.targeting_rules mapea Con userRole:
            acumulador[etiqueta.key] = etiqueta.translated_text
            CONTINUAR
        // Si no hay regla de targeting, se asigna el texto base si la llave está vacía
        SI acumulador[etiqueta.key] NO EXISTE:
            acumulador[etiqueta.key] = etiqueta.default_text

```
## 5. DISEÑO DE ARQUITECTURA DEL SDK (CLIENT-SIDE JS/TS)
El código dentro de la estructura de archivos del SDK (src/) se organiza de forma segregada en dos dominios explícitos de negocio, aislados de la infraestructura transversal:
### Distribución Física de Archivos
```text
src/
├── feature-flags/            # Módulo especializado en banderas lógicas
│   ├── types.ts              # Contratos de FeatureFlagConfig
│   └── evaluator.ts          # Evaluación de flags booleanas/multivariables
├── labeling/                 # Módulo especializado en Remote Config de textos
│   ├── types.ts              # Tipos de NamespaceBlock y LabelContext
│   └── evaluator.ts          # Algoritmo de traducción de llaves técnicas
├── client.ts                 # Fachada central (Patrón Facade): Controla Bootstrap y Lazy Loading
├── websocket.ts              # Cliente WebSocket / SSE para capturar Invalidaciones de Namespaces
├── telemetry.ts              # Registro automático de Missing Keys (Fallbacks) y estados del caché
└── index.ts                  # Punto de entrada unificado y exportaciones públicas

```
### Protocolo de Resiliencia del SDK: Stale-While-Revalidate (SWR)
 1. Al invocar el método bootstrap(), el SDK debe consultar inmediatamente la caché en disco local persistente (IndexedDB en navegadores web o Hive en dispositivos móviles).
 2. Si existen datos guardados de la sesión previa, inicializa la interfaz de la aplicación de inmediato utilizando esa data, anulando el retardo visual o parpadeos.
 3. Simultáneamente, dispara la llamada HTTP hacia el BFF en segundo plano. Si el servidor responde exitosamente, actualiza la caché local de forma silenciosa para la siguiente navegación.
 4. Si la llamada HTTP falla por caída de red o error de servidor (5xx / Timeout), el SDK se degrada automáticamente a **Modo Estable Antiguo**, activa una bandera interna isStale = true e inicia un temporizador de reintento en segundo plano cada 60 segundos.
### Protocolo de Sincronización en Caliente (Hot Reloading)
El archivo websocket.ts del SDK debe procesar eventos asíncronos distribuidos por el Gateway:
 * Al recibir un payload de tipo {"action": "INVALIDATE_NAMESPACE", "namespace": "form_registro"}:
   1. Purga exclusivamente la partición de datos mapeada a la llave form_registro dentro de la memoria RAM del cliente.
   2. No recarga la página. Si la aplicación cliente cambia de ruta o refresca un componente visual, el SDK descarga la nueva versión limpia transparentemente de forma síncrona.
 * Al recibir un payload de tipo {"action": "KILL_SWITCH", "flag_id": "nombre_flag"}:
   1. Fuerza el estado inmediato del elemento a enabled: false.
   2. Si la aplicación tiene configurado el parámetro TransitionMode.IMMEDIATE, muta el estado del componente reactivo visual en el mismo milisegundo en que se procesó el paquete.
## 6. REQUERIMIENTOS NO FUNCIONALES Y CRITERIOS DE ACEPTACIÓN (SLA)
 * **Tiempo de Propagación General (North Star Metric):** Un cambio guardado en el Panel de Administración debe verse reflejado en la memoria RAM del BFF y distribuido a los clientes en ejecución en un tiempo máximo de **500 milisegundos**.
 * **Rendimiento del Servidor BFF:** La evaluación local en la memoria RAM del BFF utilizando NestJS debe tomar menos de **1 milisegundo** por consulta.
 * **Eficiencia en Red de Dispositivos Móviles:** Los SDKs de cliente tienen estrictamente prohibido descargar diccionarios completos. Todo elemento que no pertenezca al espacio de nombres común (common) debe resolverse exclusivamente bajo demanda en bloques asíncronos controlados.

## Referencias

### Diseño UX/UI
[](design/stitch/labeling%20-%20namespaces_keys_management.html)
