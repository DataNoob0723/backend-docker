from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from typing import TYPE_CHECKING

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User  # noqa

class Table(Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(256), unique=True, nullable=False, index=True)
    data_type = Column(String(256))
    units = Column(JSON)
    original_file_name = Column(String(256), index=True)
    added_by = Column(String(256), index=True)
    num_of_rows = Column(Integer)
    instructions = Column(JSON)
    additional_information = Column(JSON)
    owner_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    owner = relationship("User", back_populates="tables")


