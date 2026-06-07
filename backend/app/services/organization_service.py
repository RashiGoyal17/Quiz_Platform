from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository


class OrganizationService:
    """Read-only lookups for organizations.

    Organization provisioning (creation, slug assignment, attaching admins)
    remains an internal operational process for now — see Phase 9B design
    ("Organization Lifecycle"). This service exists so that other services
    (e.g. registration, admin context checks) can validate and resolve an
    organization without reaching into the repository directly.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.org_repo = OrganizationRepository(session)

    async def get_organization(self, organization_id: UUID) -> Organization:
        org = await self.org_repo.get_by_id(organization_id)
        if org is None:
            raise LookupError("Organization not found")
        return org

    async def get_active_organization(self, organization_id: UUID) -> Organization:
        org = await self.org_repo.get_active_by_id(organization_id)
        if org is None:
            raise LookupError("Organization not found or inactive")
        return org
