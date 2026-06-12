-- ============================================================
-- FALL CONSTRUÇÕES - SISTEMA COMPLETO DE ESTOQUE E VENDAS
-- Script de Criação do Banco de Dados MySQL
-- ============================================================

CREATE DATABASE IF NOT EXISTS fall_construcoes
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE fall_construcoes;

-- ============================================================
-- TABELA: CATEGORIAS
-- ============================================================
CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_categorias_nome UNIQUE (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO categorias (nome, descricao) VALUES
    ('Cimento e Argamassa', 'Cimentos, argamassas, rejuntes e massas de assentamento'),
    ('Tijolos e Blocos', 'Tijolos cerâmicos, blocos de concreto e elementos vazados'),
    ('Ferro e Aço', 'Vergalhões, arames, telas e perfis metálicos'),
    ('Madeira', 'Madeiras brutas, compensados, OSB e ripas'),
    ('Hidráulica', 'Tubos, conexões, torneiras, caixas dagua e bombas'),
    ('Elétrica', 'Fios, cabos, disjuntores, tomadas e interruptores'),
    ('Pintura', 'Tintas, solventes, rolos e pincéis'),
    ('Ferramentas', 'Ferramentas manuais e elétricas'),
    ('Pisos e Revestimentos', 'Cerâmicas, porcelanatos, pastilhas e revestimentos'),
    ('Telhas e Coberturas', 'Telhas cerâmicas, metálicas, calhas e rufos')
ON DUPLICATE KEY UPDATE id = id;

-- ============================================================
-- TABELA: PRODUTOS
-- ============================================================
CREATE TABLE IF NOT EXISTS produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL,
    codigo_barras VARCHAR(50) UNIQUE,
    nome VARCHAR(200) NOT NULL,
    descricao TEXT,
    categoria_id INT,
    quantidade INT DEFAULT 0,
    quantidade_minima INT DEFAULT 10,
    preco_custo DECIMAL(10,2) DEFAULT 0.00,
    preco_venda DECIMAL(10,2) DEFAULT 0.00,
    preco_atacado DECIMAL(10,2) DEFAULT 0.00,
    unidade VARCHAR(20) DEFAULT 'UN',
    localizacao VARCHAR(100),
    fornecedor VARCHAR(200),
    peso_kg DECIMAL(8,2),
    dimensoes VARCHAR(50),
    marca VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uk_produtos_codigo UNIQUE (codigo),
    CONSTRAINT fk_produtos_categoria FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_produtos_nome ON produtos(nome);
CREATE INDEX idx_produtos_categoria ON produtos(categoria_id);
CREATE INDEX idx_produtos_barras ON produtos(codigo_barras);

-- ============================================================
-- TABELA: CLIENTES
-- ============================================================
CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    cpf_cnpj VARCHAR(20) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(100),
    endereco VARCHAR(255),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    cep VARCHAR(10),
    tipo ENUM('fisica', 'juridica') DEFAULT 'fisica',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABELA: VENDAS (PDV)
-- ============================================================
CREATE TABLE IF NOT EXISTS vendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_venda VARCHAR(20) NOT NULL UNIQUE,
    cliente_id INT,
    vendedor_id INT,
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(10,2) DEFAULT 0.00,
    desconto DECIMAL(10,2) DEFAULT 0.00,
    total DECIMAL(10,2) DEFAULT 0.00,
    forma_pagamento ENUM('dinheiro', 'cartao_credito', 'cartao_debito', 'pix', 'boleto', 'prazo') DEFAULT 'dinheiro',
    status ENUM('pendente', 'pago', 'cancelado') DEFAULT 'pendente',
    observacoes TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABELA: ITENS DA VENDA
-- ============================================================
CREATE TABLE IF NOT EXISTS venda_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    venda_id INT NOT NULL,
    produto_id INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABELA: MOVIMENTAÇÕES DE ESTOQUE
-- ============================================================
CREATE TABLE IF NOT EXISTS movimentacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    tipo ENUM('entrada', 'saida', 'ajuste', 'venda') NOT NULL,
    quantidade INT NOT NULL,
    quantidade_anterior INT NOT NULL,
    quantidade_nova INT NOT NULL,
    motivo VARCHAR(255),
    venda_id INT,
    usuario VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE CASCADE,
    FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- TABELA: USUÁRIOS
-- ============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nome VARCHAR(100),
    email VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO usuarios (username, password_hash, nome, email, is_admin) VALUES
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'Administrador', 'admin@fall.com', TRUE),
('luan', 'df4865fca1f159162557359ef967f9502087f57527b0e030e139933e54f3061e', 'Luan', 'luan@fall.com', TRUE)
ON DUPLICATE KEY UPDATE id = id;

-- ============================================================
-- DADOS DE EXEMPLO - PRODUTOS DE CONSTRUÇÃO
-- ============================================================
INSERT INTO produtos (codigo, codigo_barras, nome, descricao, categoria_id, quantidade, quantidade_minima, preco_custo, preco_venda, preco_atacado, unidade, localizacao, fornecedor, peso_kg, dimensoes, marca) VALUES
('CIM-001', '7891234567890', 'Cimento Votoran 50kg', 'Cimento Portland de alta resistência', 1, 500, 100, 28.00, 35.00, 32.00, 'SC', 'Pátio A1', 'Votoran', 50.00, '50kg', 'Votoran'),
('CIM-002', '7891234567891', 'Cimento CSN 50kg', 'Cimento Portland CP II', 1, 300, 80, 27.00, 34.00, 31.00, 'SC', 'Pátio A1', 'CSN', 50.00, '50kg', 'CSN'),
('ARG-001', '7891234567892', 'Argamassa Colante 20kg', 'Argamassa para cerâmica interna', 1, 200, 50, 18.00, 25.00, 22.00, 'SC', 'Pátio A2', 'Quartzolit', 20.00, '20kg', 'Quartzolit'),
('TIJ-001', '7891234567893', 'Tijolo Baiano 8 Furos', 'Tijolo cerâmico 9x19x19cm', 2, 10000, 2000, 0.85, 1.20, 1.00, 'UN', 'Pátio B1', 'Cerâmica São João', 2.50, '9x19x19cm', 'São João'),
('TIJ-002', '7891234567894', 'Tijolo Maciço', 'Tijolo maciço 11x19x29cm', 2, 5000, 1000, 1.50, 2.10, 1.80, 'UN', 'Pátio B1', 'Cerâmica São João', 4.00, '11x19x29cm', 'São João'),
('BLC-001', '7891234567895', 'Bloco de Concreto 14x19x39', 'Bloco estrutural de concreto', 2, 3000, 500, 3.50, 5.00, 4.20, 'UN', 'Pátio B2', 'Bloco Forte', 18.00, '14x19x39cm', 'Bloco Forte'),
('FER-001', '7891234567896', 'Vergalhão CA-50 10mm', 'Barra de aço 12 metros', 3, 150, 30, 45.00, 58.00, 52.00, 'UN', 'Pátio C1', 'Gerdau', 12.00, '12m', 'Gerdau'),
('FER-002', '7891234567897', 'Vergalhão CA-50 6.3mm', 'Barra de aço 12 metros', 3, 200, 40, 22.00, 28.00, 25.00, 'UN', 'Pátio C1', 'Gerdau', 8.00, '12m', 'Gerdau'),
('TEL-001', '7891234567898', 'Tela Soldada Q-196', 'Tela de aço 6x30m', 3, 50, 10, 120.00, 155.00, 140.00, 'UN', 'Pátio C2', 'Belgo', 30.00, '6x30m', 'Belgo'),
('MAD-001', '7891234567899', 'Compensado Naval 18mm', 'Chapa 2.20x1.10m', 4, 80, 20, 85.00, 110.00, 100.00, 'UN', 'Pátio D1', 'Eucatex', 35.00, '2.20x1.10m', 'Eucatex'),
('MAD-002', '7891234567900', 'Caibro 5x7', 'Caibro de madeira 6 metros', 4, 300, 60, 12.00, 16.00, 14.00, 'UN', 'Pátio D2', 'Madeireira Central', 8.00, '6m', 'Central'),
('HID-001', '7891234567901', 'Tubo PVC 100mm 6m', 'Tubo esgoto série RU', 5, 200, 40, 35.00, 48.00, 42.00, 'UN', 'Pátio E1', 'Tigre', 15.00, '6m', 'Tigre'),
('HID-002', '7891234567902', 'Caixa Dagua 500L', 'Caixa polietileno Fortlev', 5, 30, 8, 120.00, 165.00, 145.00, 'UN', 'Pátio E2', 'Fortlev', 12.00, '500L', 'Fortlev'),
('ELE-001', '7891234567903', 'Fio 2,5mm Rolo 100m', 'Fio flexível amarelo', 6, 100, 25, 85.00, 115.00, 105.00, 'UN', 'Pátio F1', 'Sil', 8.00, '100m', 'Sil'),
('ELE-002', '7891234567904', 'Disjuntor Bipolar 40A', 'Disjuntor DIN Siemens', 6, 40, 10, 22.00, 32.00, 28.00, 'UN', 'Pátio F2', 'Siemens', 0.30, 'DIN', 'Siemens'),
('PIN-001', '7891234567905', 'Tinta Latex 18L Branca', 'Tinta acrílica premium', 7, 60, 15, 95.00, 135.00, 120.00, 'UN', 'Pátio G1', 'Suvinil', 20.00, '18L', 'Suvinil'),
('PIN-002', '7891234567906', 'Tinta Padrão 3,6L', 'Tinta padrão cores', 7, 100, 25, 35.00, 55.00, 48.00, 'UN', 'Pátio G1', 'Coral', 5.00, '3.6L', 'Coral'),
('FER-003', '7891234567907', 'Furadeira 550W', 'Furadeira de impacto Bosch', 8, 15, 5, 180.00, 280.00, 250.00, 'UN', 'Loja H1', 'Bosch', 2.50, '550W', 'Bosch'),
('FER-004', '7891234567908', 'Betoneira 400L', 'Betoneira elétrica', 8, 5, 2, 2800.00, 3800.00, 3400.00, 'UN', 'Pátio I1', 'Menegotti', 350.00, '400L', 'Menegotti'),
('PSR-001', '7891234567909', 'Porcelanato 60x60 Polido', 'Porcelanato retificado', 9, 300, 60, 35.00, 52.00, 45.00, 'UN', 'Pátio J1', 'Portobello', 2.00, '60x60cm', 'Portobello'),
('PSR-002', '7891234567910', 'Cerâmica 45x45', 'Cerâmica acetinada', 9, 500, 100, 18.00, 28.00, 24.00, 'UN', 'Pátio J1', 'Ceusa', 1.50, '45x45cm', 'Ceusa'),
('TEL-002', '7891234567911', 'Telha Cerâmica Portuguesa', 'Telha colonial', 10, 2000, 400, 2.50, 3.80, 3.20, 'UN', 'Pátio K1', 'Brasilit', 3.00, '49x30cm', 'Brasilit'),
('TEL-003', '7891234567912', 'Telha Metálica Trapezoidal', 'Telha zinco alumínio', 10, 100, 20, 45.00, 65.00, 55.00, 'UN', 'Pátio K2', 'Belgo', 8.00, '3.66m', 'Belgo')
ON DUPLICATE KEY UPDATE id = id;

-- ============================================================
-- TABELAS ADICIONAIS
-- ============================================================

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

-- Dados de exemplo adicionais
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

-- ============================================================
-- VIEWS
-- ============================================================

CREATE OR REPLACE VIEW vw_produtos_completos AS
SELECT 
    p.id, p.codigo, p.codigo_barras, p.nome, p.descricao,
    c.nome AS categoria_nome, p.quantidade, p.quantidade_minima,
    p.preco_custo, p.preco_venda, p.preco_atacado,
    (p.preco_venda - p.preco_custo) AS lucro_unitario,
    (p.quantidade * p.preco_custo) AS valor_estoque,
    p.unidade, p.localizacao, p.fornecedor, p.marca,
    CASE 
        WHEN p.quantidade = 0 THEN 'CRITICO'
        WHEN p.quantidade <= p.quantidade_minima THEN 'BAIXO'
        ELSE 'OK'
    END AS status_estoque
FROM produtos p
LEFT JOIN categorias c ON p.categoria_id = c.id;

CREATE OR REPLACE VIEW vw_vendas_completas AS
SELECT 
    v.id, v.numero_venda, v.data_venda,
    c.nome AS cliente_nome, c.cpf_cnpj,
    v.subtotal, v.desconto, v.total,
    v.forma_pagamento, v.status,
    COUNT(vi.id) AS total_itens,
    SUM(vi.quantidade) AS total_produtos
FROM vendas v
LEFT JOIN clientes c ON v.cliente_id = c.id
LEFT JOIN venda_itens vi ON v.id = vi.venda_id
GROUP BY v.id, v.numero_venda, v.data_venda, c.nome, c.cpf_cnpj, v.subtotal, v.desconto, v.total, v.forma_pagamento, v.status;

CREATE OR REPLACE VIEW vw_ranking_produtos AS
SELECT 
    p.id, p.nome, p.codigo,
    SUM(vi.quantidade) AS total_vendido,
    SUM(vi.subtotal) AS total_faturado,
    COUNT(DISTINCT vi.venda_id) AS total_vendas
FROM produtos p
LEFT JOIN venda_itens vi ON p.id = vi.produto_id
GROUP BY p.id, p.nome, p.codigo
ORDER BY total_vendido DESC;

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

-- ============================================================
-- PROCEDURES
-- ============================================================
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS sp_gerar_numero_venda()
BEGIN
    DECLARE v_numero VARCHAR(20);
    SET v_numero = CONCAT('FALL-', DATE_FORMAT(NOW(), '%Y%m%d'), '-', LPAD(FLOOR(RAND() * 9999), 4, '0'));
    SELECT v_numero AS numero_venda;
END //

CREATE PROCEDURE sp_relatorio_estoque()
BEGIN
    SELECT 
        c.nome AS categoria,
        COUNT(p.id) AS total_produtos,
        SUM(p.quantidade) AS total_itens,
        SUM(p.quantidade * p.preco_custo) AS valor_custo,
        SUM(p.quantidade * p.preco_venda) AS valor_venda,
        SUM(p.quantidade * (p.preco_venda - p.preco_custo)) AS lucro_potencial
    FROM categorias c
    LEFT JOIN produtos p ON c.id = p.categoria_id
    GROUP BY c.id, c.nome;
END //

CREATE PROCEDURE sp_relatorio_vendas_periodo(IN p_inicio DATE, IN p_fim DATE)
BEGIN
    SELECT 
        DATE(data_venda) AS dia,
        COUNT(*) AS total_vendas,
        SUM(total) AS total_faturado,
        SUM(desconto) AS total_descontos
    FROM vendas
    WHERE DATE(data_venda) BETWEEN p_inicio AND p_fim
      AND status != 'cancelado'
    GROUP BY DATE(data_venda)
    ORDER BY dia;
END //

DELIMITER ;

-- ============================================================
-- FIM
-- ============================================================
