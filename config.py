"""Configurações do sistema FALL Construções"""

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'admin',
    'database': 'fall_construcoes'
}

# Tema visual moderno - Identidade Verde FALL
class ModernTheme:
    # === CORES PRINCIPAIS ===
    PRIMARY         = "#10b981"   # Verde esmeralda FALL (primária)
    PRIMARY_HOVER   = "#059669"   # Verde esmeralda escuro (hover)
    PRIMARY_LIGHT   = "#d1fae5"   # Verde muito claro (backgrounds sutis)

    SECONDARY       = "#065f46"   # Verde médio (substitui cinza ardósia)
    SUCCESS         = "#16a34a"   # Verde mantido
    SUCCESS_LIGHT   = "#dcfce7"
    DANGER          = "#dc2626"   # Vermelho mantido
    DANGER_HOVER    = "#b91c1c"   # Vermelho escuro (hover)
    DANGER_LIGHT    = "#fee2e2"
    WARNING         = "#d97706"   # Âmbar mantido
    WARNING_LIGHT   = "#fef3c7"
    INFO            = "#2563eb"   # Azul mantido
    INFO_LIGHT      = "#dbeafe"

    # === SUPERFÍCIES ===
    BG              = "#f0fdf4"   # Fundo geral verde muito claro
    SIDEBAR_BG      = "#064e3b"   # Sidebar verde escuro FALL
    SIDEBAR_HOVER   = "#065f46"   # Hover na sidebar verde médio
    SIDEBAR_ACTIVE  = "#10b981"   # Item ativo na sidebar esmeralda
    CARD_BG         = "#ffffff"   # Cards brancos mantido
    CARD_HOVER      = "#f0fdf4"   # Hover card verde claro
    HEADER_BG       = "#064e3b"   # Header verde escuro FALL

    # === TEXTO ===
    TEXT            = "#022c22"   # Texto principal verde muito escuro
    TEXT_LIGHT      = "#374151"   # Texto secundário cinza escuro
    TEXT_MUTED      = "#9ca3af"   # Texto desabilitado cinza claro
    TEXT_ON_DARK    = "#d1fae5"   # Texto sobre fundo escuro verde claro
    TEXT_ON_PRIMARY = "#ffffff"   # Texto sobre verde primário

    # === BORDAS E SEPARADORES ===
    BORDER          = "#e2e8f0"
    BORDER_FOCUS    = "#10b981"   # Borda quando input está em foco verde

    # === ESTADO / SOMBRAS ===
    SHADOW          = "#022c22"   # Cor base p/ sombras verde escuro

    # === CORES DE CONSTRUÇÃO (adaptadas para verde) ===
    DARK            = "#022c22"   # Verde muito escuro (ex-laranja/cinza)
    CIMENTO         = "#9ca3af"   # Cinza claro mantido
    TIJOLO          = "#b91c1c"   # Vermelho tijolo mantido
    MADEIRA         = "#92400e"   # Marrom madeira mantido
    FERRO           = "#334155"   # Cinza ferro mantido

    # === ESTILOS DE FONTE ===
    FONT_FAMILY     = "Segoe UI"
    FONT_SM         = ("Segoe UI", 9)
    FONT_BASE       = ("Segoe UI", 10)
    FONT_MD         = ("Segoe UI", 11)
    FONT_LG         = ("Segoe UI", 13, "bold")
    FONT_XL         = ("Segoe UI", 16, "bold")
    FONT_TITLE      = ("Segoe UI", 20, "bold")

    # === DIMENSÕES ===
    RADIUS          = 6           # Arredondamento padrão (referência; tkinter não suporta direto)
    SIDEBAR_WIDTH   = 260
    HEADER_HEIGHT   = 64
    CARD_PAD        = 16
    BTN_PAD_X       = 18
    BTN_PAD_Y       = 9


# Configurações da loja
LOJA_CONFIG = {
    'nome': 'FALL Construções',
    'cnpj': '57.839.618/0001-67',
    'endereco': 'Av. Dom Helder Câmara, 3691 - Vale Quem Tem',
    'telefone': '(86)99962-1227',
    'email': 'aurileneheberty@gmail.com'
}