import sqlite3
  import logging

  logger = logging.getLogger(__name__)

  DB_FILE = "bot_database.db"


  def init_db():
    """Ma'lumotlar bazasini ishga tushirish va jadval yaratish."""
          try:
              with sqlite3.connect(DB_FILE) as conn:
                  cursor = conn.cursor()
                  cursor.execute("""
                                                 CREATE TABLE IF NOT EXISTS chats (
                                                                       chat_id INTEGER PRIMARY KEY,
                                                                       chat_type TEXT NOT NULL,
                                                                       title TEXT,
                                                                       added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                                                   )
                                             """)
                                             conn.commit()
                                             logger.info("Ma'lumotlar bazasi tayyor.")
                                     except sqlite3.Error as e:
                                         logger.error(f"DB yaratishda xato: {e}")


                                 def add_chat(chat_id: int, chat_type: str, title: str = None):
                                     """Chat ID ni bazaga qo'shish (mavjud bo'lsa e'tiborsiz qoldirish)."""
                                     try:
                                         with sqlite3.connect(DB_FILE) as conn:
                                             cursor = conn.cursor()
                                             cursor.execute(
                                                               "INSERT OR IGNORE INTO chats (chat_id, chat_type, title) VALUES (?, ?, ?)",
                                                               (chat_id, chat_type, title)
                                                           )
                                             conn.commit()
                                             if cursor.rowcount > 0:
                                                 logger.info(f"Yangi chat qo'shildi: {chat_id} ({title})")
                                     except sqlite3.Error as e:
                                         logger.error(f"Chat qo'shishda xato: {e}")


                                 def remove_chat(chat_id: int):
                                     """Chat ID ni bazadan o'chirish."""
                                     try:
                                         with sqlite3.connect(DB_FILE) as conn:
                                             cursor = conn.cursor()
                                             cursor.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
                                             conn.commit()
                                             if cursor.rowcount > 0:
                                                 logger.info(f"Chat o'chirildi: {chat_id}")
                                     except sqlite3.Error as e:
                                         logger.error(f"Chat o'chirishda xato: {e}")


                                 def get_all_chats() -> list:
                                     """Bazadagi barcha chat ID larni qaytarish."""
                                     try:
                                         with sqlite3.connect(DB_FILE) as conn:
                                             cursor = conn.cursor()
                                             cursor.execute("SELECT chat_id FROM chats")
                                             return [row[0] for row in cursor.fetchall()]
                                     except sqlite3.Error as e:
                                         logger.error(f"Chatlarni olishda xato: {e}")
                                         return []
                                 
