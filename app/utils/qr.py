import io
import qrcode
import cloudinary.uploader


def generate_asset_qr(
    asset_id: str
) -> str:
    """
    Generate QR image,
    upload to Cloudinary,
    return secure url.
    """

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5
    )

    qr.add_data(asset_id)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    result = cloudinary.uploader.upload(
        buffer,
        folder="asset-iq/qr-codes",
        public_id=f"asset-{asset_id}",
        overwrite=True,
        resource_type="image"
    )

    return result["secure_url"]