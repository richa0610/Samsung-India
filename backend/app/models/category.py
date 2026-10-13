from sqlalchemy import Column, Integer, String, Text

from app.database.connection import Base


class Category(Base):
    """Mirrors the real `category` table (mmtbtwob_tops). A category is a form field whose options
    are its subcategories - except the zones and the states, which are categories themselves,
    marked by `visibleOnWeb` ("Zone": East, North, ...; "State"), whose subcategories are their
    regions (East 1, ...) and districts - see catalog_repository.list_category_groups."""

    __tablename__ = "category"

    id = Column(Integer, primary_key=True, index=True)

    categoryUid = Column(String(100), unique=True, nullable=True)

    name = Column(String(200))
    visibleOnWeb = Column(String(100))
    status = Column(String(100), nullable=False, default="Pending")
    # Who added / last changed the row and why - set by scripts/add_master_options.py.
    updatedBy = Column(String(100))
    remarks = Column(Text)


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
    status = Column(String(100), nullable=False, default="Pending")
    # Who added / last changed the row and why - set by scripts/add_master_options.py.
    updatedBy = Column(String(100))
    remarks = Column(Text)
