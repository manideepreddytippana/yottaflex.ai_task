"""Customer Journey Explorer routes."""

from fastapi import APIRouter, HTTPException
from src.attribution.api.schemas import CustomerJourneyResponse
from src.attribution.services.contacts import ContactService

router = APIRouter(prefix="/api/contacts", tags=["Customer Journey"])
service = ContactService()


@router.get("/{contact_id}/journey", response_model=CustomerJourneyResponse)
def get_customer_journey(contact_id: str) -> CustomerJourneyResponse:
    res = service.get_customer_journey(contact_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Contact '{contact_id}' not found.")
    return CustomerJourneyResponse(**res)

