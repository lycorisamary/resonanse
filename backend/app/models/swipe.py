"""
Модели для свайпов и матчей.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, PrimaryKeyConstraint
from sqlalchemy.sql import func

from app.core.database import Base


class Swipe(Base):
    """
    Свайп между двумя пользователями.

    Одна строка на пару пользователей (user_id_1 < user_id_2),
    чтобы избежать гонок и дублирования.
    """

    __tablename__ = "swipes"
    __table_args__ = (
        PrimaryKeyConstraint("user_id_1", "user_id_2", name="pk_swipes"),
    )

    user_id_1 = Column(Integer, nullable=False, comment="Меньший ID пользователя в паре")
    user_id_2 = Column(Integer, nullable=False, comment="Больший ID пользователя в паре")

    decision_1 = Column(Boolean, nullable=True, comment="Решение пользователя с id=user_id_1 (True/False/NULL)")
    decision_2 = Column(Boolean, nullable=True, comment="Решение пользователя с id=user_id_2 (True/False/NULL)")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания записи",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Дата и время последнего обновления",
    )


class Match(Base):
    """
    Матч между двумя пользователями (взаимный лайк).
    """

    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id_1 = Column(Integer, nullable=False, comment="Меньший ID пользователя в паре")
    user_id_2 = Column(Integer, nullable=False, comment="Больший ID пользователя в паре")
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Дата и время создания матча",
    )


