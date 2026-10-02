from __future__ import annotations
from enum import StrEnum

class AnalyticsEventType(StrEnum):
    PRODUCT_VIEW = "product_view"
    PRODUCT_CLICK = "product_click"

    PRODUCT_SEARCH = "product_search"

    SALES_REP_VIEW = "sales_rep_view"
    SALES_REP_CONTACT = "sales_rep_contact"

    CATALOG_OPEN = "catalog_open"