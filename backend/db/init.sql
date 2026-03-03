CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    google_id     VARCHAR(255) NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    name          VARCHAR(255),
    is_admin      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE models (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,     -- "Qwen2.5-0.5B"
    hf_model_id     VARCHAR(255) NOT NULL,            -- "Qwen/Qwen2.5-0.5B-Instruct"
    model_type      ENUM('llm','cnn') DEFAULT 'llm',
    parameter_count BIGINT,                           -- 500000000
    quantization    VARCHAR(20) DEFAULT 'FP16',
    description     TEXT,
    is_downloaded   BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inference_sessions (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    prompt      TEXT NOT NULL,
    model_ids   JSON NOT NULL,                        -- [1, 2, 3]
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_time (user_id, created_at)         -- for future rate limiting
);

CREATE TABLE inference_results (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    session_id        INT NOT NULL,
    model_id          INT NOT NULL,
    status            ENUM('pending','streaming','completed','failed') DEFAULT 'pending',
    response_text     TEXT,
    ttft_ms           FLOAT,          -- time to first token
    tpot_ms           FLOAT,          -- time per output token
    tokens_per_second FLOAT,
    total_tokens      INT,
    e2e_latency_ms    FLOAT,          -- end to end
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES inference_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id)
);
