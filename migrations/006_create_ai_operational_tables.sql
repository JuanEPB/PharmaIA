CREATE TABLE IF NOT EXISTS ia_memoria_conversacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id VARCHAR(120) NOT NULL,
    usuario_id INT NULL,
    farmacia_id INT NULL,
    contexto JSON NULL,
    ultimo_mensaje TEXT NULL,
    ultima_respuesta TEXT NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_ia_memoria_sesion (sesion_id),
    INDEX idx_ia_memoria_usuario (usuario_id),
    INDEX idx_ia_memoria_farmacia (farmacia_id),
    INDEX idx_ia_memoria_actualizado (actualizado_en),

    CONSTRAINT fk_ia_memoria_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_ia_memoria_farmacia
        FOREIGN KEY (farmacia_id)
        REFERENCES farmacia(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ia_acciones_conversacionales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id VARCHAR(120) NOT NULL,
    usuario_id INT NULL,
    farmacia_id INT NULL,
    tipo_accion VARCHAR(80) NOT NULL,
    estado ENUM(
        'PENDIENTE',
        'CONFIRMADA',
        'CANCELADA',
        'EJECUTADA',
        'ERROR'
    ) NOT NULL DEFAULT 'PENDIENTE',
    parametros JSON NULL,
    resultado JSON NULL,
    mensaje_error TEXT NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_ia_acciones_sesion (sesion_id),
    INDEX idx_ia_acciones_estado (estado),
    INDEX idx_ia_acciones_usuario (usuario_id),
    INDEX idx_ia_acciones_farmacia (farmacia_id),
    INDEX idx_ia_acciones_tipo (tipo_accion),

    CONSTRAINT fk_ia_acciones_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_ia_acciones_farmacia
        FOREIGN KEY (farmacia_id)
        REFERENCES farmacia(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ia_feedback_aprendizaje (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evento_id VARCHAR(80) NOT NULL,
    sesion_id VARCHAR(120) NULL,
    usuario_id INT NULL,
    farmacia_id INT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT NULL,
    intencion_detectada VARCHAR(120) NULL,
    intencion_esperada VARCHAR(120) NULL,
    calificacion INT NULL,
    comentario TEXT NULL,
    estado ENUM(
        'PENDIENTE_REVISION',
        'REVISADO',
        'APROBADO',
        'DESCARTADO'
    ) NOT NULL DEFAULT 'PENDIENTE_REVISION',
    metadatos JSON NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_ia_feedback_evento (evento_id),
    INDEX idx_ia_feedback_estado (estado),
    INDEX idx_ia_feedback_usuario (usuario_id),
    INDEX idx_ia_feedback_farmacia (farmacia_id),
    INDEX idx_ia_feedback_intencion (intencion_detectada),
    INDEX idx_ia_feedback_fecha (creado_en),

    CONSTRAINT fk_ia_feedback_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,

    CONSTRAINT fk_ia_feedback_farmacia
        FOREIGN KEY (farmacia_id)
        REFERENCES farmacia(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS ia_predicciones_inventario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    medicamento_id INT NOT NULL,
    farmacia_id INT NULL,
    tipo_prediccion VARCHAR(80) NOT NULL,
    riesgo VARCHAR(40) NULL,
    valor_estimado DECIMAL(12, 4) NULL,
    dias_estimados INT NULL,
    confianza DECIMAL(6, 4) NULL,
    detalles JSON NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ia_predicciones_medicamento (medicamento_id),
    INDEX idx_ia_predicciones_farmacia (farmacia_id),
    INDEX idx_ia_predicciones_tipo (tipo_prediccion),
    INDEX idx_ia_predicciones_riesgo (riesgo),
    INDEX idx_ia_predicciones_fecha (creado_en),

    CONSTRAINT fk_ia_predicciones_medicamento
        FOREIGN KEY (medicamento_id)
        REFERENCES medicamentos(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_ia_predicciones_farmacia
        FOREIGN KEY (farmacia_id)
        REFERENCES farmacia(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);
