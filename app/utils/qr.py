import io

import qrcode
import cloudinary
import cloudinary.uploader


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
# Generate Asset QR
# =====================================
def generate_asset_qr(
    asset_id: str
) -> str:
    """
    Generate asset QR code,
    upload QR image to Cloudinary,
    and return Cloudinary secure URL.
    """

    print("\n")
    print("=" * 60)
    print("QR GENERATION STARTED")
    print("=" * 60)

    try:
        # =====================================
        # Validate Asset ID
        # =====================================
        if not asset_id:
            raise ValueError(
                "Asset ID cannot be empty"
            )

        print(
            "ASSET ID:",
            asset_id
        )

        # =====================================
        # Check Cloudinary Configuration
        # =====================================
        config = cloudinary.config()

        print(
            "CLOUD NAME:",
            config.cloud_name
        )

        print(
            "API KEY EXISTS:",
            bool(config.api_key)
        )

        print(
            "API SECRET EXISTS:",
            bool(config.api_secret)
        )

        if not config.cloud_name:
            raise ValueError(
                "Cloudinary cloud name is missing"
            )

        if not config.api_key:
            raise ValueError(
                "Cloudinary API key is missing"
            )

        if not config.api_secret:
            raise ValueError(
                "Cloudinary API secret is missing"
            )

        # =====================================
        # Create QR Code
        # =====================================
        print(
            "CREATING QR CODE..."
        )

        qr = qrcode.QRCode(
            version=1,
            error_correction=(
                qrcode.constants.ERROR_CORRECT_L
            ),
            box_size=10,
            border=5
        )

        qr.add_data(
            asset_id
        )

        qr.make(
            fit=True
        )

        # =====================================
        # Create QR Image
        # =====================================
        print(
            "CREATING QR IMAGE..."
        )

        image = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        # =====================================
        # Save QR Image In Memory
        # =====================================
        print(
            "CREATING QR IMAGE BUFFER..."
        )

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="PNG"
        )

        buffer.seek(0)

        buffer_size = len(
            buffer.getvalue()
        )

        print(
            "QR IMAGE SIZE:",
            buffer_size,
            "BYTES"
        )

        if buffer_size == 0:
            raise ValueError(
                "QR image buffer is empty"
            )

        # =====================================
        # Upload QR To Cloudinary
        # =====================================
        print(
            "UPLOADING QR TO CLOUDINARY..."
        )

        result = cloudinary.uploader.upload(
            buffer,
            folder="asset-iq/qr-codes",
            public_id=(
                f"asset-{asset_id}"
            ),
            overwrite=True,
            resource_type="image"
        )

        # =====================================
        # Get QR Secure URL
        # =====================================
        qr_url = result.get(
            "secure_url"
        )

        if not qr_url:
            raise ValueError(
                "Cloudinary did not return "
                "secure_url for QR code"
            )

        print(
            "QR UPLOAD SUCCESSFUL"
        )

        print(
            "QR URL:",
            qr_url
        )

        print("=" * 60)
        print("QR GENERATION COMPLETED")
        print("=" * 60)

        return qr_url

    except Exception as error:

        print("\n")
        print("!" * 60)
        print("QR GENERATION FAILED")
        print("!" * 60)

        print(
            "ERROR TYPE:",
            type(error).__name__
        )

        print(
            "ERROR MESSAGE:",
            str(error)
        )

        print("!" * 60)

        raise


# =====================================
# Upload Asset Image
# =====================================
def upload_asset_image(
    image_file,
    asset_id: str
) -> str:
    """
    Upload asset image to Cloudinary
    and return Cloudinary secure URL.
    """

    print("\n")
    print("=" * 60)
    print("ASSET IMAGE UPLOAD STARTED")
    print("=" * 60)

    try:
        # =====================================
        # Validate Image File
        # =====================================
        if not image_file:
            raise ValueError(
                "Image file is required"
            )

        print(
            "ASSET ID:",
            asset_id
        )

        print(
            "FILE NAME:",
            image_file.filename
        )

        print(
            "CONTENT TYPE:",
            image_file.content_type
        )

        # =====================================
        # Validate Content Type
        # =====================================
        allowed_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp"
        ]

        if (
            image_file.content_type
            not in allowed_types
        ):
            raise ValueError(
                "Only JPEG, JPG, PNG and WEBP "
                "images are allowed"
            )

        # =====================================
        # Check Cloudinary Configuration
        # =====================================
        config = cloudinary.config()

        print(
            "CLOUD NAME:",
            config.cloud_name
        )

        print(
            "API KEY EXISTS:",
            bool(config.api_key)
        )

        print(
            "API SECRET EXISTS:",
            bool(config.api_secret)
        )

        if not config.cloud_name:
            raise ValueError(
                "Cloudinary cloud name is missing"
            )

        if not config.api_key:
            raise ValueError(
                "Cloudinary API key is missing"
            )

        if not config.api_secret:
            raise ValueError(
                "Cloudinary API secret is missing"
            )

        # =====================================
        # Reset File Position
        # =====================================
        image_file.file.seek(
            0
        )

        # =====================================
        # Upload Image To Cloudinary
        # =====================================
        print(
            "UPLOADING IMAGE TO CLOUDINARY..."
        )

        result = cloudinary.uploader.upload(
            image_file.file,
            folder="asset-iq/assets",
            public_id=(
                f"asset-{asset_id}"
            ),
            overwrite=True,
            resource_type="image"
        )

        # =====================================
        # Get Image Secure URL
        # =====================================
        image_url = result.get(
            "secure_url"
        )

        if not image_url:
            raise ValueError(
                "Cloudinary did not return "
                "secure_url for asset image"
            )

        print(
            "IMAGE UPLOAD SUCCESSFUL"
        )

        print(
            "IMAGE URL:",
            image_url
        )

        print("=" * 60)
        print("ASSET IMAGE UPLOAD COMPLETED")
        print("=" * 60)

        return image_url

    except Exception as error:

        print("\n")
        print("!" * 60)
        print("ASSET IMAGE UPLOAD FAILED")
        print("!" * 60)

        print(
            "ERROR TYPE:",
            type(error).__name__
        )

        print(
            "ERROR MESSAGE:",
            str(error)
        )

        print("!" * 60)

        raise