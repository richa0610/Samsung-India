from sqlalchemy import Column, Integer, String

from app.database.connection import Base


class Category(Base):
    """Mirrors the real `category` table (mmtbtwob_tops)."""

    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)

    categoryUid = Column(String(100), unique=True, nullable=True)

    name = Column(String(200))
    status = Column(String(100), nullable=False, default="Pending")


class SubCategory(Base):
    """Mirrors the real `subcategory` table (mmtbtwob_tops). The Add
    Training form's Checklist picker sources its options from here -
    `conference.checklistUid` stores a comma-separated list of
    `subCategoryUid` values (see that column's comment in the schema)."""

    __tablename__ = "subcategory"

    id = Column(Integer, primary_key=True, index=True)

    subCategoryUid = Column(String(100), unique=True, nullable=True)

    categoryUid = Column(String(100))
    subCategory = Column(String(200))
    status = Column(String(100), nullable=False, default="Pending")
