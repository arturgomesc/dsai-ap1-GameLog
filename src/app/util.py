import hashlib
from functools import wraps

from flask import abort, g, redirect, request, session, url_for

from .models import User, db

PER_PAGE = 20


class Page:
    def __init__(self, items, page, pages, total):
        self.items, self.page, self.pages, self.total = items, page, pages, total

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages


def paginate(query, page, per_page=PER_PAGE):
    """Página fora do intervalo cai na última válida, nunca erro (GLOBAL-04, BUS-04)."""
    total = query.order_by(None).count()
    pages = max(1, -(-total // per_page))
    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 1
    page = min(max(page, 1), pages)
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    return Page(items, page, pages, total)


def current_user():
    if "user" not in g:
        uid = session.get("uid")
        u = db.session.get(User, uid) if uid else None
        # logout incrementa session_version e invalida cookies antigos no servidor (CAD-05)
        g.user = u if u and u.session_version == session.get("sv") else None
    return g.user


def _login_redirect():
    # volta à ação depois do login (GLOBAL-02): POST volta à página de origem
    nxt = request.full_path.rstrip("?") if request.method == "GET" else (request.referrer or "/")
    return redirect(url_for("auth.login", next=nxt))


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not current_user():
            return _login_redirect()
        return f(*a, **kw)

    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        u = current_user()
        if not u:
            return _login_redirect()
        if not u.is_admin:
            abort(403)
        return f(*a, **kw)

    return wrapper


def safe_next(url):
    """Só aceita caminho local, evita open redirect."""
    if url and url.startswith("/") and not url.startswith("//"):
        return url
    return "/"


def slugify(text):
    import re
    import unicodedata

    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def fold(text):
    """Minúsculas sem acento, para busca (BUS-01)."""
    import unicodedata

    return unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()


def cover_svg(slug, title=""):
    """Capa determinística a partir do slug (CAT-06)."""
    h = hashlib.sha256(slug.encode()).digest()
    h1, h2 = h[0] * 360 // 256, h[1] * 360 // 256
    shapes = "".join(
        f'<circle cx="{h[2 + i] * 300 // 256}" cy="{h[8 + i] * 400 // 256}" r="{20 + h[14 + i] % 60}" '
        f'fill="hsl({(h1 + h[20 + i]) % 360},70%,65%)" opacity=".35"/>'
        for i in range(5)
    )
    initials = "".join(w[0] for w in title.split()[:2]).upper() or slug[:2].upper()
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="hsl({h1},65%,35%)"/><stop offset="1" stop-color="hsl({h2},65%,20%)"/>'
        f'</linearGradient></defs><rect width="300" height="400" fill="url(#g)"/>{shapes}'
        f'<text x="150" y="225" font-size="90" font-family="sans-serif" font-weight="700" '
        f'fill="#fff" fill-opacity=".85" text-anchor="middle">{initials}</text></svg>'
    )


def avatar_style(username):
    """Cor derivada do nome de usuário (CAD-08)."""
    return f"hsl({hashlib.sha256(username.lower().encode()).digest()[0] * 360 // 256},55%,40%)"
