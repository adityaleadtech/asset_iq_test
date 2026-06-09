from app.config.database import SessionLocal
from app.models.platform_admin import PlatformAdmin


db= SessionLocal()


try:
    admins = db.query(PlatformAdmin).all()

    print(f"Total Admins: {len(admins)}")

    for admin in admins:
        print(admin.id)
        print(admin.email)
        print(admin.full_name)
        print(admin.is_active)
        print(admin.created_at)

finally:
    db.close()

print("FILE RAN")