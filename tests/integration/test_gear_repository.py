"""Integration test for the gear repository."""

from src.api.authenticate import StravaAuthenticator
from src.api.client import StravaClient
from src.database import SessionLocal, initialize_database
from src.etl.gear_transformer import transform_gear
from src.repositories import GearRepository


TEST_GEAR_ID = "b17417153"


def main() -> None:
    """Fetch, transform, and save one gear record."""

    authenticator = StravaAuthenticator()
    access_token = authenticator.get_access_token()
    client = StravaClient(access_token)

    athlete = client.get_logged_in_athlete()
    raw_gear = client.get_gear(TEST_GEAR_ID)

    transformed_gear = transform_gear(
        raw_gear=raw_gear,
        athlete_id=athlete["id"],
    )

    initialize_database()

    with SessionLocal() as session:
        repository = GearRepository(session)

        gear_record, was_inserted = repository.upsert(
            transformed_gear
        )
        session.commit()

        action = "Inserted" if was_inserted else "Updated"

        print(f"{action}: {gear_record.gear_id}")
        print(f"Name: {gear_record.name}")
        print(f"Brand: {gear_record.brand_name}")
        print(f"Model: {gear_record.model_name}")
        print(f"Stored gear count: {repository.count()}")


if __name__ == "__main__":
    main()