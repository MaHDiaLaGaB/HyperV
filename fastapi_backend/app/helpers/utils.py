from fastapi.routing import APIRoute


def simple_generate_unique_route_id(route: APIRoute) -> str:
    # tag اختياري: إن لم يوجد، نستعمل "default"
    tag = route.tags[0] if getattr(route, "tags", None) else "default"

    # method: أول ميثود بشكل ثابت لضمان ثبات الناتج (GET/POST/...)
    methods = getattr(route, "methods", None)
    method = sorted(methods)[0] if methods else "GET"

    # path: حوّله لسلسلة آمنة
    path_id = (
        route.path
        .replace("/", "-")
        .replace("{", "")
        .replace("}", "")
        .replace(":", "")
        .strip("-")
        or "root"
    )

    # name: لو مفقود نستعمل "unnamed"
    name = route.name or "unnamed"

    # المعرّف النهائي — تركيبة تضمن التفرد: tag+method+path+name
    return f"{tag}-{method}-{path_id}-{name}"
