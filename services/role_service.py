from config import SUPPORT_USER_IDS

# вручную назначенные роли, если нужно (например, из админки)
user_roles = {}


def set_user_role(user_id: int, role: str):
    user_roles[user_id] = role


def get_user_role(user_id: int) -> str:
    # если явно установлена роль — используем её
    if user_id in user_roles:
        return user_roles[user_id]

    # если в списке поддержки — автоматически support
    if user_id in SUPPORT_USER_IDS:
        return "support"

    # иначе по умолчанию — агент
    return "agent"
