from typing import Optional

from pydantic import BaseModel


class Contract(BaseModel):
    external_id: Optional[str] = None
    Customer: Optional[str] = None
    subsidiary: Optional[str] = None
    orderstatus: Optional[str] = None
    salesrep: Optional[str] = None
    otherrefnum: Optional[str] = None
    custbody_rr_startnewcontract: Optional[str] = None
    custbody_rr_contract: Optional[str] = None
    memo: Optional[str] = None
    ismultishipto: Optional[str] = None
    custbody_360_cus_refnum: Optional[str] = None
    itemLine_item: Optional[int] = None
    itemLine_quantity: Optional[int] = None
    itemLine_salesPrice: Optional[float] = None
    custcol_rr_contractrate: Optional[float] = None
    itemLine_pricelevel: Optional[str] = None
    itemLine_description: Optional[str] = None
    custcol_rr_assetnumber: Optional[str] = None
    custcol_rr_contracttermmonths: Optional[int] = None
    custcol_rr_contractbillingfreq: Optional[str] = None
    custcol_rr_enduser: Optional[str] = None
    itemLine_department: Optional[str] = None
    itemLine_class: Optional[str] = None
    itemLine_location: Optional[str] = None
    custcol_rr_startdate: Optional[str] = None
    custcol_rr_enddate: Optional[str] = None
    custcol_360_original_start_date: Optional[str] = None
    custcol_rr_intitalbilling: Optional[str] = None
    custcol_rr_contractlineforcoterming: Optional[str] = None
    cseg_device_type: Optional[str] = None
    cseg_manufacturer: Optional[str] = None
    cseg_360_item_model: Optional[str] = None
    cseg_service_offr: Optional[str] = None
    cseg_support_type: Optional[str] = None
    cseg_service_tier: Optional[str] = None
    custcol_360_part_subcontractor: Optional[str] = None
    custcol_360_line_po: Optional[str] = None
    shipcarrier: Optional[str] = None
    shipmethod: Optional[str] = None
    shipaddressee: Optional[str] = None
    shipAddr1: Optional[str] = None
    shipAddr2: Optional[str] = None
    shipAddr3: Optional[str] = None
    shipCity: Optional[str] = None
    shipState: Optional[str] = None
    shipZip: Optional[str] = None
    shipCountry: Optional[str] = None
    terms: Optional[str] = None
    billAddressee: Optional[str] = None
    billAddr1: Optional[str] = None
    billAddr2: Optional[str] = None
    billCity: Optional[str] = None
    billState: Optional[str] = None
    billZip: Optional[str] = None
    billCountry: Optional[str] = None
    currency: Optional[str] = None





