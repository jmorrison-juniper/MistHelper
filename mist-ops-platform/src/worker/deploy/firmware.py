"""Firmware upgrade orchestration (T081).

Golden image validation and staged deployment for AP, switch,
and gateway firmware upgrades per FR-029.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.config.constants import GoldenImageStatus
from src.shared.mist.endpoints import ApiResult, MistEndpointService
from src.shared.models.governance import GoldenImage
from src.shared.models.inventory import Device

logger = logging.getLogger(__name__)


class FirmwareOrchestrator:
    """Manage firmware deployment with golden image validation.

    Validates that target devices match the golden image
    device model and that the image is in approved state.
    """

    def __init__(
        self, db: Session, mist: MistEndpointService,
    ) -> None:
        self._db = db
        self._mist = mist

    def validate_upgrade(
        self, image_id: UUID, target_device_ids: list[UUID],
    ) -> dict:
        """Validate firmware upgrade eligibility."""
        image = self._load_image(image_id)
        errors = _validate_image_state(image)
        if errors:
            return {"valid": False, "errors": errors}

        devices = self._load_devices(target_device_ids)
        compat_errors = _check_compatibility(image, devices)
        if compat_errors:
            return {"valid": False, "errors": compat_errors}

        return {
            "valid": True,
            "image_version": image.version,
            "device_count": len(devices),
            "device_model": image.device_model,
        }

    def build_upgrade_payload(
        self, image_id: UUID, target_device_ids: list[UUID],
    ) -> dict:
        """Build the change payload for a firmware upgrade."""
        image = self._load_image(image_id)
        return {
            "firmware_version": image.version,
            "image_type": image.image_type,
            "device_model": image.device_model,
            "target_device_ids": [str(d) for d in target_device_ids],
            "content_hash": image.content_hash,
        }

    def execute_upgrade(
        self,
        site_id: str,
        image_id: UUID,
        target_device_ids: list[UUID],
    ) -> ApiResult:
        """Execute firmware upgrade via Mist SDK (safety-gated).

        MUST call validate_upgrade() before this method.
        Constitution III: firmware is a destructive operation.
        """
        validation = self.validate_upgrade(image_id, target_device_ids)
        if not validation["valid"]:
            msg = f"Pre-upgrade validation failed: {validation['errors']}"
            raise RuntimeError(msg)

        payload = self.build_upgrade_payload(image_id, target_device_ids)
        result = self._mist.write_entity(
            entity_type="firmware_site",
            ids={"site_id": site_id},
            body=payload,
        )
        if result.success:
            logger.info(
                "Firmware upgrade initiated: site=%s devices=%d",
                site_id, len(target_device_ids),
            )
        else:
            logger.error(
                "Firmware upgrade failed: site=%s error=%s",
                site_id, result.error,
            )
        return result

    # -- Private ---

    def _load_image(self, image_id: UUID) -> GoldenImage:
        """Load golden image or raise."""
        stmt = select(GoldenImage).where(
            GoldenImage.image_id == image_id,
        )
        image = self._db.execute(stmt).scalar_one_or_none()
        if image is None:
            msg = f"Golden image {image_id} not found"
            raise ValueError(msg)
        return image

    def _load_devices(
        self, device_ids: list[UUID],
    ) -> list[Device]:
        """Load devices by IDs."""
        stmt = select(Device).where(Device.device_id.in_(device_ids))
        return list(self._db.execute(stmt).scalars().all())


def _validate_image_state(image: GoldenImage) -> list[str]:
    """Check that the image is in a deployable state."""
    errors: list[str] = []
    if image.lifecycle_state != GoldenImageStatus.APPROVED.value:
        errors.append(
            f"Image must be approved, current: {image.lifecycle_state}"
        )
    return errors


def _check_compatibility(
    image: GoldenImage, devices: list[Device],
) -> list[str]:
    """Check device model compatibility with golden image."""
    errors: list[str] = []
    for device in devices:
        model = (device.extra_fields or {}).get("model", "")
        if model and model != image.device_model:
            errors.append(
                f"Device {device.device_id} model '{model}' "
                f"incompatible with image model '{image.device_model}'"
            )
    return errors
