import re

def normalize_plate(plate: str) -> str:
    """
    Normalizes a vehicle license plate string by stripping all non-alphanumeric
    characters (spaces, dots, hyphens, underscores, etc.) and converting to uppercase.

    Examples:
        'MH 43 D 3193'  -> 'MH43D3193'
        'MH.43.D.3193'  -> 'MH43D3193'
        'TN-01-AM-6142' -> 'TN01AM6142'
    """
    if not plate:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", str(plate)).upper()
