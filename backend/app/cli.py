import argparse
from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal
from app.models.user import User
from app.services.authentication import hash_password, normalize_email


def provision_staff_user(email: str, role: str) -> None:
    try:
        normalized_email = normalize_email(str(TypeAdapter(EmailStr).validate_python(email)))
    except ValidationError as exc:
        raise SystemExit("A valid email address is required") from exc

    password = getpass("Temporary account password (12-128 characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords did not match")
    if not 12 <= len(password) <= 128:
        raise SystemExit("Password must be between 12 and 128 characters")

    db = SessionLocal()
    try:
        db.add(
            User(
                email=normalized_email,
                password_hash=hash_password(password),
                role=role,
                is_active=True,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SystemExit("An account with this email already exists") from exc
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision a restricted Nagrik Setu staff account")
    parser.add_argument("role", choices=("officer", "admin"))
    parser.add_argument("email")
    args = parser.parse_args()
    provision_staff_user(args.email, args.role)
    print("Staff account provisioned.")


if __name__ == "__main__":
    main()