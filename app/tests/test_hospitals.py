import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models import Hospital

client = TestClient(app)

# Set up the test database
@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=engine)  # Create tables
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)  # Drop tables after tests


@pytest.fixture
def mock_tomtom_response(monkeypatch):
    """
    Mock the TomTom API response for testing purposes.
    """
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.data = {
                    "results": [
                        {
                            "poi": {"name": "Apollo Hospitals"},
                            "address": {"freeformAddress": "Greams Road, Chennai, Tamil Nadu"},
                            "dist": 350.2,
                            "position": {"lat": 13.0674, "lon": 80.2785},
                        },
                        {
                            "poi": {"name": "AIIMS Patna"},
                            "address": {"freeformAddress": "Phulwari Sharif, Patna, Bihar"},
                            "dist": 450.5,
                            "position": {"lat": 25.5957, "lon": 85.1355},
                        },
                        {
                            "poi": {"name": "CMC Vellore"},
                            "address": {"freeformAddress": "Bagayam, Vellore, Tamil Nadu"},
                            "dist": 500.6,
                            "position": {"lat": 12.9333, "lon": 79.1333},
                        },
                    ]
                }

            def json(self):
                return self.data

        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get)


def test_get_nearby_hospitals_success(mock_tomtom_response, test_db):
    """
    Test a successful response from the TomTom API for nearby hospitals.
    """
    response = client.get("/hospitals/nearby?lat=13.0674&lon=80.2785&radius=5000")
    assert response.status_code == 200
    assert "hospitals" in response.json()
    hospitals = response.json()["hospitals"]
    assert len(hospitals) > 0
    assert hospitals[0]["name"] == "Apollo Hospitals"
    assert hospitals[0]["address"] == "Greams Road, Chennai, Tamil Nadu"
    assert hospitals[0]["location"]["lat"] == 13.0674
    assert hospitals[0]["location"]["lng"] == 80.2785
    assert hospitals[0]["distance"] == 350.2


def test_get_nearby_hospitals_invalid_radius():
    """
    Test validation error for an invalid radius value.
    """
    response = client.get("/hospitals/nearby?lat=13.0674&lon=80.2785&radius=100000")
    assert response.status_code == 422
    assert "radius" in response.json()["detail"][0]["loc"]


def test_get_nearby_hospitals_no_results(monkeypatch):
    """
    Test the case when no hospitals are found by the TomTom API.
    """
    def mock_get_no_results(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.data = {"results": []}

            def json(self):
                return self.data

        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get_no_results)

    response = client.get("/hospitals/nearby?lat=13.0674&lon=80.2785&radius=5000")
    assert response.status_code == 404
    assert response.json()["detail"] == "No hospitals found"


def test_get_nearby_hospitals_api_failure(monkeypatch):
    """
    Test the case when the TomTom API fails.
    """
    def mock_get_failure(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 500

            def json(self):
                return {}

        return MockResponse()

    monkeypatch.setattr("requests.get", mock_get_failure)

    response = client.get("/hospitals/nearby?lat=13.0674&lon=80.2785&radius=5000")
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch nearby hospitals from TomTom API"


def test_get_hospitals_from_database(test_db):
    """
    Test fetching hospitals stored in the database.
    """
    # Add a hospital to the database
    new_hospital = Hospital(
        name="CMC Vellore",
        address="Bagayam, Vellore, Tamil Nadu",
        lat=12.9333,
        lng=79.1333,
        rating=4.8,
    )
    test_db.add(new_hospital)
    test_db.commit()
    test_db.refresh(new_hospital)

    response = client.get("/hospitals/database?lat=12.9333&lon=79.1333&radius=5000")
    assert response.status_code == 200
    assert "hospitals" in response.json()
    hospitals = response.json()["hospitals"]
    assert len(hospitals) > 0
    assert hospitals[0]["name"] == "CMC Vellore"
    assert hospitals[0]["address"] == "Bagayam, Vellore, Tamil Nadu"
    assert hospitals[0]["location"]["lat"] == 12.9333
    assert hospitals[0]["location"]["lng"] == 79.1333
    assert hospitals[0]["rating"] == 4.8
