from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.database import SessionLocal


CSV_PATH = Path("data/reference/activity_type_categories.csv")


def load_activity_type_categories() -> None:
    df = pd.read_csv(CSV_PATH)

    required_columns = {
        "activity_type",
        "activity_category",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required CSV columns: {sorted(missing_columns)}"
        )

    with SessionLocal() as session:
        session.execute(
            text(
                """
                create table if not exists activity_type_categories (
                    activity_type text primary key,
                    activity_category text,
                    activity_category_sort integer
                )
                """
            )
        )

        session.execute(text("delete from activity_type_categories"))

        connection = session.connection()

        df.to_sql(
            "activity_type_categories",
            connection,
            if_exists="append",
            index=False,
        )

        session.commit()

    print(
        f"Activity type categories loaded successfully: "
        f"{len(df)} rows"
    )


def find_unmapped_activity_types() -> list[str]:
    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                select distinct
                    a.sport_type
                from activities a
                left join activity_type_categories atc
                    on a.sport_type = atc.activity_type
                where a.sport_type is not null
                  and atc.activity_type is null
                order by
                    a.sport_type
                """
            )
        ).fetchall()

    return [row[0] for row in rows]


if __name__ == "__main__":
    load_activity_type_categories()

    unmapped = find_unmapped_activity_types()

    if unmapped:
        print("")
        print("Unmapped activity types:")
        for activity_type in unmapped:
            print(f"  - {activity_type}")
    else:
        print("All activity types are mapped.")