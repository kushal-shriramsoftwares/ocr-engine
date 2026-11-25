from pydantic import BaseModel
from typing import Optional


class AddressResponse(BaseModel):
    full_address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


class ExtractionDataResponse(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    aadhaar_number: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[AddressResponse] = None
    father_name: Optional[str] = None
    pan_number: Optional[str] = None


class ExtractionResponse(BaseModel):
    success: bool
    document_type: str
    file_type: str
    data: ExtractionDataResponse