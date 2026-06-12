
-- ============================================================
-- TABELAS ADICIONAIS - FALL CONSTRUÇÕES
-- ============================================================
USE fall_construcoes;

-- Tabela: Orçamentos
CREATE TABLE IF NOT EXISTS orcamentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_orcamento VARCHAR(20) NOT NULL UNIQUE,
    cliente_id INT,
    vendedor_id INT,
    data_orcamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_validade DATE,
    subtotal DECIMAL(10,2) DEFAULT 0.00,
    desconto DECIMAL(10,2) DEFAULT 0.00,
    total DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('pendente', 'aprovado', 'rejeitado', 'convertido') DEFAULT 'pendente',
    observacoes TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabela: Itens do Orçamento
CREATE TABLE IF NOT EXISTS orcamento_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    orcamento_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabela: Entregas
CREATE TABLE IF NOT EXISTS entregas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venda_id INT,
    orcamento_id INT,
    cliente_id INT NOT NULL,
    endereco_entrega VARCHAR(255) NOT NULL,
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(10),
    telefone_contato VARCHAR(20),
    data_agendada DATE,
    hora_agendada TIME,
    status ENUM('agendada', 'em_transito', 'entregue', 'cancelada') DEFAULT 'agendada',
    valor_frete DECIMAL(10,2) DEFAULT 0.00,
    tipo_veiculo ENUM('moto', 'carro', 'caminhonete', 'caminhao', 'carreta') DEFAULT 'caminhonete',
    motorista VARCHAR(100),
    placa_veiculo VARCHAR(10),
    observacoes TEXT,
    data_entrega TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE SET NULL,
    FOREIGN KEY (orcamento_id) REFERENCES orcamentos(id) ON DELETE SET NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabela: Fornecedores
CREATE TABLE IF NOT EXISTS fornecedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    cnpj VARCHAR(20) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(100),
    endereco VARCHAR(255),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(10),
    contato_nome VARCHAR(100),
    contato_telefone VARCHAR(20),
    prazo_pagamento INT DEFAULT 30,
    limite_credito DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tabela: Contas a Pagar
CREATE TABLE IF NOT EXISTS contas_pagar (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fornecedor_id INT NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    numero_documento VARCHAR(50),
    valor DECIMAL(10,2) NOT NULL,
    data_emissao DATE DEFAULT CURRENT_DATE,
    data_vencimento DATE NOT NULL,
    data_pagamento DATE,
    valor_pago DECIMAL(10,2) DEFAULT 0.00,
    juros_multa DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('pendente', 'pago', 'atrasado', 'cancelado') DEFAULT 'pendente',
    forma_pagamento VARCHAR(50),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fornecedor_id) REFERENCES fornecedores(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Dados de exemplo
INSERT INTO fornecedores (nome, cnpj, telefone, cidade, estado, prazo_pagamento, limite_credito) VALUES
('Votoran Materiais', '12.345.678/0001-01', '(11) 3333-4444', 'São Paulo', 'SP', 30, 50000.00),
('Gerdau Aço', '23.456.789/0001-02', '(11) 4444-5555', 'São Paulo', 'SP', 45, 100000.00),
('Tigre Hidráulica', '34.567.890/0001-03', '(11) 5555-6666', 'Joinville', 'SC', 30, 30000.00),
('Quartzolit', '45.678.901/0001-04', '(11) 6666-7777', 'São Paulo', 'SP', 30, 25000.00)
ON DUPLICATE KEY UPDATE id = id;

INSERT INTO contas_pagar (fornecedor_id, descricao, numero_documento, valor, data_vencimento, status) VALUES
(1, 'Cimento 500 sacos', 'NF-001', 17500.00, DATE_ADD(CURDATE(), INTERVAL 15 DAY), 'pendente'),
(2, 'Vergalhão 150 barras', 'NF-002', 8700.00, DATE_ADD(CURDATE(), INTERVAL 30 DAY), 'pendente'),
(3, 'Tubos PVC lote 200', 'NF-003', 9600.00, DATE_ADD(CURDATE(), INTERVAL 10 DAY), 'pendente'),
(4, 'Argamassa 300 sacos', 'NF-004', 7500.00, DATE_ADD(CURDATE(), INTERVAL 5 DAY), 'atrasado')
ON DUPLICATE KEY UPDATE id = id;

-- Views adicionais
CREATE OR REPLACE VIEW vw_orcamentos_completos AS
SELECT o.*, c.nome as cliente_nome, c.telefone
FROM orcamentos o
LEFT JOIN clientes c ON o.cliente_id = c.id;

CREATE OR REPLACE VIEW vw_contas_pagar_pendentes AS
SELECT cp.*, f.nome as fornecedor_nome, f.cnpj
FROM contas_pagar cp
JOIN fornecedores f ON cp.fornecedor_id = f.id
WHERE cp.status IN ('pendente', 'atrasado')
ORDER BY cp.data_vencimento;
