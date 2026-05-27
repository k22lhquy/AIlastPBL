from services import admin_service

async def get_admin_stats_controller():
    return await admin_service.get_admin_stats_service()

async def get_all_users_controller():
    return await admin_service.get_all_users_service()
