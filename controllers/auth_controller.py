"""Controller de Autenticação"""
from models.usuario_model import UsuarioModel

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")

class AuthController:
    def __init__(self):
        self.model = UsuarioModel()
        self.model.create_table()
        self._current_user = None

    def login(self, username, password):
        user = self.model.authenticate(username, password)
        if user:
            self._current_user = user
            Logger.log(f"Login: {username}", 'SUCCESS')
            return True, user
        Logger.log(f"Falha login: {username}", 'ERROR')
        return False, None

    def logout(self):
        self._current_user = None

    def is_logged(self):
        return self._current_user is not None

    def get_user(self):
        return self._current_user

    def criar_usuario(self, username, password, nome='', email='', is_admin=False):
        if not username or not password:
            return False, "Username e senha são obrigatórios"
        result = self.model.create(username, password, nome, email, is_admin)
        return (True, "Usuário criado") if result else (False, "Erro ao criar usuário")
