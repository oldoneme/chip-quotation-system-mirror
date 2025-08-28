from fastapi import APIRouter
from .endpoints import (
    machines,
    configurations,
    card_configs,
    auxiliary_equipment,
    personnel,
    quotations,
    hierarchical_data,
    suppliers,
    machine_types,
    users,
    operation_logs,
    statistics,
    confirmations,
    quotes,
    wecom_approval
)

api_router = APIRouter()

# Register all routers (使用空字符串作为prefix)
api_router.include_router(machine_types.router, prefix="", tags=["machine-types"])
api_router.include_router(suppliers.router, prefix="", tags=["suppliers"])
api_router.include_router(machines.router, prefix="", tags=["machines"])
api_router.include_router(configurations.router, prefix="", tags=["configurations"])
api_router.include_router(card_configs.router, prefix="", tags=["card-configs"])
api_router.include_router(auxiliary_equipment.router, prefix="", tags=["auxiliary-equipment"])
api_router.include_router(personnel.router, prefix="", tags=["personnel"])
api_router.include_router(quotations.router, prefix="", tags=["quotations"])
api_router.include_router(quotes.router, prefix="", tags=["quotes"])
api_router.include_router(hierarchical_data.router, prefix="", tags=["hierarchical"])
api_router.include_router(users.router, prefix="", tags=["users"])
api_router.include_router(operation_logs.router, prefix="", tags=["operation-logs"])
api_router.include_router(statistics.router, prefix="", tags=["statistics"])
api_router.include_router(confirmations.router, prefix="", tags=["confirmations"])
api_router.include_router(wecom_approval.router, prefix="/wecom-approval", tags=["wecom-approval"])