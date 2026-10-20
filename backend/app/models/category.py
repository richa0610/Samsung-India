from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database.connection import Base


class Category(Base):
    """Mirrors the real `category` table (mmtbtwob_tops). A category is a form field whose options
    are its subcategories - except the zones, which are categories themselves, marked by
    `visibleOnWeb` = "Zone" (East, North, ...), whose subcategories are their regions (East 1, ...)
    - see catalog_repository.list_category_groups. States and districts come from the pincode
    directory instead (models/pincode.py)."""

    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)

    categoryUid = Column(String(100), unique=True, nullable=True)

    name = Column(String(200))
    description = Column(Text)
    visibleOnWeb = Column(String(100), nullable=False, default="No")
    updatedBy = Column(String(100))
    updatedOn = Column(DateTime, onupdate=func.now())
    token = Column(String(100))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(100), nullable=False, default="Pending")
    remarks = Column(Text)
    securityDetails = Column(Text)
    masterRemarks = Column(Text)


class SubCategory(Base):
    """Mirrors the real `subcategory` table (mmtbtwob_tops): one option of the category it
    belongs to (`categoryUid`). The Add Training form's Audience, Session Type, Training Type
    and Checklist pickers source their options from here - `conference.checklistUid` stores a
    comma-separated list of `subCategoryUid` values (see that column's comment in the schema)."""

    __tablename__ = "subcategory"

    id = Column(Integer, primary_key=True, index=True)

    subCategoryUid = Column(String(100), unique=True, nullable=True)

    categoryUid = Column(String(100))
    subCategory = Column(String(200))
    description = Column(Text)
    visibleOnWeb = Column(String(100), nullable=False, default="No")
    updatedBy = Column(String(100))
    updatedOn = Column(DateTime, onupdate=func.now())
    token = Column(String(100))
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    status = Column(String(100), nullable=False, default="Pending")
    remarks = Column(Text)
    securityDetails = Column(Text)
    masterRemarks = Column(Text)
