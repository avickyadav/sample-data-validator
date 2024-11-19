from typing import Optional

from pydantic import BaseModel


class Contract(BaseModel):
    externalid: Optional[str] = None
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


contract_model_columns = [
    "externalid", "Customer", "subsidiary", "orderstatus", "salesrep", "otherrefnum",
    "custbody_rr_startnewcontract", "custbody_rr_contract", "memo", "ismultishipto",
    "custbody_360_cus_refnum", "itemLine_item", "itemLine_quantity", "itemLine_salesPrice",
    "custcol_rr_contractrate", "itemLine_pricelevel", "itemLine_description",
    "custcol_rr_assetnumber", "custcol_rr_contracttermmonths", "custcol_rr_contractbillingfreq",
    "custcol_rr_enduser", "itemLine_department", "itemLine_class", "itemLine_location",
    "custcol_rr_startdate", "custcol_rr_enddate", "custcol_360_original_start_date",
    "custcol_rr_intitalbilling", "custcol_rr_contractlineforcoterming", "cseg_device_type",
    "cseg_manufacturer", "cseg_360_item_model", "cseg_service_offr", "cseg_support_type",
    "cseg_service_tier", "custcol_360_part_subcontractor", "custcol_360_line_po",
    "shipcarrier", "shipmethod", "shipaddressee", "shipAddr1", "shipAddr2", "shipAddr3",
    "shipCity", "shipState", "shipZip", "shipCountry", "terms", "billAddressee",
    "billAddr1", "billAddr2", "billCity", "billState", "billZip", "billCountry", "currency"
]





