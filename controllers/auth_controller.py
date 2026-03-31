from services import auth_service

def login(data):
    return auth_service.login(data.username, data.password)