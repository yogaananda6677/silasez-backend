def success(
    data=None,
    message="Success"
):
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error(
    message="Error"
):
    return {
        "success": False,
        "message": message
    }