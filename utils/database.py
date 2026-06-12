"""Gerenciamento de conexão com MySQL"""
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

try:
    from utils.logger import Logger
except:
    class Logger:
        @classmethod
        def log(cls, msg, level='INFO'):
            print(f"[{level}] {msg}")

class DatabaseConnection:
    """Singleton para gerenciar a conexão com MySQL"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                Logger.log(f"Conectando ao MySQL: {DB_CONFIG['host']}", 'SQL')
                self.connection = mysql.connector.connect(**DB_CONFIG)
                Logger.log("Conexão estabelecida", 'SUCCESS')
            return self.connection
        except Error as e:
            Logger.log(f"Erro ao conectar: {e}", 'ERROR')
            return None

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            Logger.log("Conexão fechada", 'INFO')

    def execute(self, query, params=None, fetch=False):
        conn = self.connect()
        if not conn:
            return None

        cursor = conn.cursor(dictionary=True)
        try:
            query_log = query[:80] + "..." if len(query) > 80 else query
            Logger.log(f"SQL: {query_log}", 'SQL')

            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
                Logger.log(f"Retornou {len(result)} registros", 'SUCCESS')
                return result

            conn.commit()
            last_id = cursor.lastrowid
            Logger.log(f"OK (ID: {last_id}, Rows: {cursor.rowcount})", 'SUCCESS')
            return last_id

        except Error as e:
            conn.rollback()
            Logger.log(f"Erro SQL: {e}", 'ERROR')
            return None
        finally:
            cursor.close()
