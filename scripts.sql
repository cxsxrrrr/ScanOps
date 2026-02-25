-- =============================================================================
-- Auditoría Web Automatizada para PYMES - Modelo de Base de Datos
-- Generado a partir de los modelos Django del proyecto
-- Motor: SQLite (default Django) / PostgreSQL compatible
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- APP: accounts
-- ─────────────────────────────────────────────────────────────────────────────

-- Tabla: Organization
-- Representa una organización que agrupa usuarios y activos URL.
CREATE TABLE IF NOT EXISTS accounts_organization (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(200) NOT NULL,
    plan            VARCHAR(20)  NOT NULL DEFAULT 'free',
        -- Valores permitidos: 'free', 'pro'
    url_limit       INTEGER      NOT NULL DEFAULT 5,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- Tabla: User (extiende AbstractUser de Django)
-- Usuario personalizado vinculado a Clerk Auth y a una Organization.
-- Hereda todos los campos de django.contrib.auth.models.AbstractUser:
--   id, password, last_login, is_superuser, username, first_name,
--   last_name, email, is_staff, is_active, date_joined
CREATE TABLE IF NOT EXISTS accounts_user (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,

    -- Campos heredados de AbstractUser
    password        VARCHAR(128) NOT NULL,
    last_login      DATETIME     NULL,
    is_superuser    BOOLEAN      NOT NULL DEFAULT 0,
    username        VARCHAR(150) NOT NULL UNIQUE,
    first_name      VARCHAR(150) NOT NULL DEFAULT '',
    last_name       VARCHAR(150) NOT NULL DEFAULT '',
    email           VARCHAR(254) NOT NULL DEFAULT '',
    is_staff        BOOLEAN      NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    date_joined     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Campos personalizados
    clerk_user_id   VARCHAR(200) NULL UNIQUE,
    organization_id INTEGER      NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'user',
        -- Valores permitidos: 'user', 'admin'

    CONSTRAINT fk_user_organization
        FOREIGN KEY (organization_id)
        REFERENCES accounts_organization(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_user_organization ON accounts_user(organization_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- APP: urls_manager
-- ─────────────────────────────────────────────────────────────────────────────

-- Tabla: URLAsset
-- URL registrada para auditoría de seguridad.
CREATE TABLE IF NOT EXISTS urls_manager_urlasset (
    id               INTEGER       PRIMARY KEY AUTOINCREMENT,
    organization_id  INTEGER       NOT NULL,
    url              VARCHAR(2048) NOT NULL,
    last_scan_status VARCHAR(20)   NOT NULL DEFAULT 'pending',
        -- Valores permitidos: 'pending', 'ok', 'warning', 'error'
    last_scan_at     DATETIME      NULL,
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_urlasset_organization
        FOREIGN KEY (organization_id)
        REFERENCES accounts_organization(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_organization_url
        UNIQUE (organization_id, url)
);

CREATE INDEX idx_urlasset_organization ON urls_manager_urlasset(organization_id);


-- ─────────────────────────────────────────────────────────────────────────────
-- APP: scanner
-- ─────────────────────────────────────────────────────────────────────────────

-- Tabla: Scan
-- Ejecución individual de un escaneo de seguridad.
CREATE TABLE IF NOT EXISTS scanner_scan (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    url_asset_id    INTEGER      NOT NULL,
    started_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at     DATETIME     NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
        -- Valores permitidos: 'pending', 'running', 'completed', 'error'
    error           TEXT         NOT NULL DEFAULT '',
    engine_version  VARCHAR(50)  NOT NULL DEFAULT '1.0.0',
    created_by_id   INTEGER      NULL,

    CONSTRAINT fk_scan_urlasset
        FOREIGN KEY (url_asset_id)
        REFERENCES urls_manager_urlasset(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_scan_created_by
        FOREIGN KEY (created_by_id)
        REFERENCES accounts_user(id)
        ON DELETE SET NULL
);

CREATE INDEX idx_scan_urlasset   ON scanner_scan(url_asset_id);
CREATE INDEX idx_scan_created_by ON scanner_scan(created_by_id);
CREATE INDEX idx_scan_status     ON scanner_scan(status);


-- Tabla: Finding
-- Hallazgo de seguridad detectado en un escaneo.
CREATE TABLE IF NOT EXISTS scanner_finding (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    scan_id         INTEGER      NOT NULL,
    title           VARCHAR(300) NOT NULL,
    severity        VARCHAR(10)  NOT NULL,
        -- Valores permitidos: 'HIGH', 'MEDIUM', 'LOW', 'INFO'
    category        VARCHAR(30)  NOT NULL DEFAULT 'other',
        -- Valores permitidos: 'headers', 'ssl', 'cookies',
        --   'info_disclosure', 'dns', 'mixed_content', 'redirect', 'other'
    description     TEXT         NOT NULL,
    recommendation  TEXT         NOT NULL DEFAULT '',
    evidence        TEXT         NOT NULL DEFAULT '',

    CONSTRAINT fk_finding_scan
        FOREIGN KEY (scan_id)
        REFERENCES scanner_scan(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_finding_scan     ON scanner_finding(scan_id);
CREATE INDEX idx_finding_severity ON scanner_finding(severity);
CREATE INDEX idx_finding_category ON scanner_finding(category);


-- ─────────────────────────────────────────────────────────────────────────────
-- APP: reports
-- ─────────────────────────────────────────────────────────────────────────────

-- Tabla: ExecutiveSummary
-- Resumen ejecutivo generado por IA para un escaneo.
CREATE TABLE IF NOT EXISTS reports_executivesummary (
    id           INTEGER      PRIMARY KEY AUTOINCREMENT,
    scan_id      INTEGER      NOT NULL UNIQUE,
        -- Relación OneToOne con scanner_scan
    ai_provider  VARCHAR(20)  NOT NULL DEFAULT 'gemini',
        -- Valores permitidos: 'gemini', 'openai'
    content      TEXT         NOT NULL,
    token_usage  INTEGER      NOT NULL DEFAULT 0,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_executivesummary_scan
        FOREIGN KEY (scan_id)
        REFERENCES scanner_scan(id)
        ON DELETE CASCADE
);


-- ─────────────────────────────────────────────────────────────────────────────
-- APP: notifications
-- ─────────────────────────────────────────────────────────────────────────────

-- Tabla: NotificationConfig
-- Preferencias de notificación por email para cada organización.
CREATE TABLE IF NOT EXISTS notifications_notificationconfig (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER      NOT NULL UNIQUE,
        -- Relación OneToOne con accounts_organization
    frequency       VARCHAR(20)  NOT NULL DEFAULT 'weekly',
        -- Valores permitidos: 'daily', 'weekly', 'monthly'
    enabled         BOOLEAN      NOT NULL DEFAULT 1,
    last_sent_at    DATETIME     NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notifconfig_organization
        FOREIGN KEY (organization_id)
        REFERENCES accounts_organization(id)
        ON DELETE CASCADE
);


-- Tabla: EmailLog
-- Registro histórico de correos enviados.
CREATE TABLE IF NOT EXISTS notifications_emaillog (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    organization_id INTEGER      NOT NULL,
    email_type      VARCHAR(20)  NOT NULL,
        -- Valores permitidos: 'scheduled', 'alert'
    sent_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(10)  NOT NULL DEFAULT 'sent',
        -- Valores permitidos: 'sent', 'failed'
    error           TEXT         NOT NULL DEFAULT '',
    recipients      TEXT         NOT NULL DEFAULT '',

    CONSTRAINT fk_emaillog_organization
        FOREIGN KEY (organization_id)
        REFERENCES accounts_organization(id)
        ON DELETE CASCADE
);

CREATE INDEX idx_emaillog_organization ON notifications_emaillog(organization_id);
CREATE INDEX idx_emaillog_type         ON notifications_emaillog(email_type);


-- ─────────────────────────────────────────────────────────────────────────────
-- Tablas de Django integradas (requeridas por el framework)
-- ─────────────────────────────────────────────────────────────────────────────

-- Tabla: Groups de usuario (many-to-many)
CREATE TABLE IF NOT EXISTS accounts_user_groups (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER NOT NULL,
    group_id INTEGER NOT NULL,

    CONSTRAINT fk_usergroups_user
        FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_usergroups_group
        FOREIGN KEY (group_id) REFERENCES auth_group(id) ON DELETE CASCADE,
    UNIQUE (user_id, group_id)
);

-- Tabla: Permisos de usuario (many-to-many)
CREATE TABLE IF NOT EXISTS accounts_user_user_permissions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,

    CONSTRAINT fk_userpermissions_user
        FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE,
    CONSTRAINT fk_userpermissions_permission
        FOREIGN KEY (permission_id) REFERENCES auth_permission(id) ON DELETE CASCADE,
    UNIQUE (user_id, permission_id)
);
