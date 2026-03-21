USER_REGION_SCOPES = {
    ("t-1", "u-1"): ["华东", "华南"],
    ("t-1", "u-south"): ["华南"],
}


def resolve_allowed_regions(user_id: str, tenant_id: str) -> list[str]:
    return USER_REGION_SCOPES.get((tenant_id, user_id), [])
