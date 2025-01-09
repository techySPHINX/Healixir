from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
import requests
import json

from app.core.config import settings
from app.database import init_db
from app.models import Hospital as HospitalModel

# Pydantic models
class HospitalLocation(BaseModel):
    lat: float
    lng: float


class HospitalReview(BaseModel):
    reviewer: str
    comment: str
    rating: float  # Rating given by the reviewer


class Hospital(BaseModel):
    name: str
    address: str
    distance: Optional[float] = None  # Distance in meters
    location: HospitalLocation
    rating: Optional[float] = None  # Average rating
    reviews: List[HospitalReview] = Field(default_factory=list)  # List of user reviews


class NearbyHospitalsResponse(BaseModel):
    hospitals: List[Hospital]


# Router setup
router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


# Helper function to fetch data from TomTom API
def fetch_hospitals_from_tomtom(lat: float, lon: float, radius: int, limit: int):
    url = f"https://api.tomtom.com/search/2/poiSearch/hospital.json"
    params = {
        "key": settings.TOMTOM_API_KEY,
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "limit": limit,
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail="Failed to fetch nearby hospitals from TomTom API",
        )

    data = response.json()
    if "results" not in data:
        return []

    return [
        {
            "name": result.get("poi", {}).get("name", "Unknown"),
            "address": result.get("address", {}).get("freeformAddress", "Unknown"),
            "distance": result.get("dist", None),
            "lat": result.get("position", {}).get("lat"),
            "lng": result.get("position", {}).get("lon"),
        }
        for result in data.get("results", [])
    ]


# Endpoint to fetch nearby hospitals
@router.get("/nearby", response_model=NearbyHospitalsResponse)
async def get_nearby_hospitals(
    lat: float,
    lon: float,
    radius: int = Query(5000, ge=100, le=50000, description="Search radius in meters"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    db: Session = Depends(init_db()),
):
    hospitals_data = fetch_hospitals_from_tomtom(lat, lon, radius, limit)

    hospitals = []
    for hospital_data in hospitals_data:
        existing_hospital = (
            db.query(HospitalModel)
            .filter(
                HospitalModel.name == hospital_data["name"],
                HospitalModel.address == hospital_data["address"],
                HospitalModel.lat == hospital_data["lat"],
                HospitalModel.lng == hospital_data["lng"],
            )
            .first()
        )

        if not existing_hospital:
            new_hospital = HospitalModel(
                name=hospital_data["name"],
                address=hospital_data["address"],
                lat=hospital_data["lat"],
                lng=hospital_data["lng"],
                distance=hospital_data["distance"],
                rating = 0.0,  # No initial rating
                reviews = "",  # No initial reviews
            )
            db.add(new_hospital)
            db.commit()
            db.refresh(new_hospital)
            hospitals.append(new_hospital)
        else:
            hospitals.append(existing_hospital)

    return NearbyHospitalsResponse(
        hospitals=[
            Hospital(
                name=h.name,
                address=h.address,
                distance=h.distance,
                location=HospitalLocation(lat=h.lat, lng=h.lng),
                rating=h.rating,
                reviews=[] if not h.reviews else json.loads(h.reviews),
            )
            for h in hospitals
        ]
    )


# Endpoint to add reviews and ratings for a hospital
@router.post("/{hospital_id}/review", tags=["Hospitals"])
async def add_review(
    hospital_id: int,
    review: HospitalReview,
    db: Session = Depends(init_db()),
):
    hospital = db.query(HospitalModel).filter(HospitalModel.id == hospital_id).first()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Parse existing reviews
    existing_reviews = [] if not hospital.reviews else json.loads(hospital.reviews)
    existing_reviews.append(review.model_dump())

    # Update hospital's reviews and recalculate rating
    hospital.reviews = str(existing_reviews)
    hospital.rating = sum(r["rating"] for r in existing_reviews) / len(existing_reviews)

    db.commit()
    db.refresh(hospital)

    return {"message": "Review added successfully", "hospital": hospital}
