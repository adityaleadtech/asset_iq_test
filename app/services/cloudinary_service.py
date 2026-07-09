import cloudinary
import cloudinary.uploader

from fastapi import (
    HTTPException,
    UploadFile
)

from app.config.settings import settings


# =====================================
# Cloudinary Configuration
# =====================================

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


# =====================================
# Upload Image
# =====================================

def upload_image(
    image_file: UploadFile,
    folder: str
) -> str:

    allowed_content_types = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ]

    # =====================================
    # Validate Image Type
    # =====================================

    if (
        image_file.content_type
        not in allowed_content_types
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, PNG and WEBP "
                "images are allowed"
            )
        )

    # =====================================
    # Upload Image
    # =====================================

    try:

        upload_result = (
            cloudinary.uploader.upload(
                image_file.file,
                folder=folder,
                resource_type="image"
            )
        )

        return upload_result["secure_url"]

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "Image upload failed"
                ),
                "error": str(error)
            }
        )