"""Interactive utility for adding trail-system mapping rules."""

# Update this import only if your project uses a different session module.
from src.database.session import SessionLocal
from src.services.trail_mapping_rule_service import TrailMappingRuleService
from src.services.trail_system_service import TrailSystemService


def prompt_float(label: str) -> float:
    """Prompt until a valid float is entered."""

    while True:
        try:
            return float(input(label).strip())
        except ValueError:
            print("Enter a valid number.")


def run() -> None:
    """Prompt for and create one mapping rule."""

    with SessionLocal() as session:
        trail_service = TrailSystemService(session)
        rule_service = TrailMappingRuleService(session)

        trail_systems = trail_service.get_all_trail_systems()

        if not trail_systems:
            print("Create a trail system before adding rules.")
            return

        print()
        print("Trail systems")
        print("-" * 50)

        for trail in trail_systems:
            print(
                f"{trail.trail_system_id}: "
                f"{trail.name}"
            )

        trail_system_id = int(
            input("\nTrail-system ID: ").strip()
        )

        print()
        print("Rule types")
        print("1. CITY")
        print("2. STATE")
        print("3. NAME_EQUALS")
        print("4. NAME_CONTAINS")
        print("5. BOUNDING_BOX")

        choices = {
            "1": "CITY",
            "2": "STATE",
            "3": "NAME_EQUALS",
            "4": "NAME_CONTAINS",
            "5": "BOUNDING_BOX",
        }

        rule_type = choices.get(
            input("\nRule type: ").strip()
        )

        if rule_type is None:
            print("Invalid rule type.")
            return

        priority_text = input(
            "Priority [100]: "
        ).strip()

        confidence_text = input(
            "Confidence [0.90]: "
        ).strip()

        priority = int(priority_text or "100")
        confidence = float(confidence_text or "0.90")
        notes = input("Notes [optional]: ").strip() or None

        kwargs = {
            "trail_system_id": trail_system_id,
            "rule_type": rule_type,
            "priority": priority,
            "confidence": confidence,
            "notes": notes,
        }

        if rule_type == "BOUNDING_BOX":
            kwargs.update(
                min_latitude=prompt_float("Minimum latitude: "),
                max_latitude=prompt_float("Maximum latitude: "),
                min_longitude=prompt_float("Minimum longitude: "),
                max_longitude=prompt_float("Maximum longitude: "),
            )
        else:
            kwargs["match_value"] = input(
                "Match value: "
            ).strip()

        rule = rule_service.create_rule(**kwargs)

        print()
        print(
            f"Created rule {rule.rule_id}: "
            f"{rule.rule_type} -> trail system "
            f"{rule.trail_system_id}"
        )


if __name__ == "__main__":
    run()
