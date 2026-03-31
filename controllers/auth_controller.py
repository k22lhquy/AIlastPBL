from services import auth_service


async def register(data):
    return await auth_service.register(data.username, data.password)


async def login(data):
    return await auth_service.login(data.username, data.password)