"""
Модель интересов пользователя.
"""
from sqlalchemy import Column, Integer, String, ForeignKey

from app.core.database import Base


class UserInterest(Base):
    """
    Простой список интересов пользователя (теги).

    В будущем может быть заменено на отдельную справочную таблицу интересов
    или векторное представление для AI-поиска.
    """

    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID пользователя",
    )
    tag = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Текстовый тег интереса (например, 'спорт', 'кино')",
    )



