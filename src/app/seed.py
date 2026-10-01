"""Seed reproduzível com dados 100% fictícios (CAT-03..CAT-06, GLOBAL-07)."""
import random
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

from .models import (
    Activity, Developer, Follow, Game, GameList, Genre, ListItem, Platform, Report, Review, Like, Status, User, db,
)
from .util import slugify

GENRES = ["Ação", "Aventura", "RPG", "Estratégia", "Simulação", "Esportes", "Corrida", "Puzzle", "Plataforma",
          "Terror", "Luta", "Tiro", "Roguelike", "Indie", "Música"]
PLATFORMS = ["PC", "PlayStation 5", "PlayStation 4", "Xbox Series", "Xbox One", "Nintendo Switch", "Android", "iOS",
             "Mac", "Linux"]
ADJ = ["Sombrio", "Eterno", "Perdido", "Cósmico", "Selvagem", "Dourado", "Fantasma", "Último", "Neon", "Cristalino",
       "Ardente", "Silencioso", "Infinito", "Quebrado", "Distante", "Rebelde", "Místico", "Veloz", "Antigo", "Gélido"]
NOUN = ["Reino", "Horizonte", "Legado", "Eclipse", "Abismo", "Santuário", "Cometa", "Labirinto", "Templo", "Oásis",
        "Farol", "Círculo", "Império", "Vale", "Portal", "Cidadela", "Ruína", "Pulso", "Código", "Lenda"]
PLACE = ["Aurora", "Ônix", "Zéfiro", "Vórtice", "Atlântida", "Nimbus", "Crepúsculo", "Titã", "Ártico", "Solaris"]
DEV_A = ["Pixel", "Lume", "Arco", "Nova", "Bruma", "Faísca", "Coral", "Vento", "Rubi", "Atlas", "Gema", "Tempestade"]
DEV_B = ["Forge", "Works", "Labs", "Interativo", "Games", "Studio", "Digital"]
SYN = [
    "Em um mundo à beira do colapso, você precisa reunir aliados e desvendar os segredos de {n}.",
    "Explore territórios vastos, enfrente criaturas imprevisíveis e escreva sua própria história em {n}.",
    "Uma experiência contemplativa e desafiadora onde cada decisão em {n} muda o rumo da jornada.",
    "Construa, lute e sobreviva: {n} mistura ação intensa com exploração livre.",
    "Resolva enigmas engenhosos e descubra o que se esconde por trás de {n}.",
]
REV = [
    "Gostei bastante, a ambientação é muito boa.", "Divertido nas primeiras horas, mas fica repetitivo.",
    "Trilha sonora memorável e jogabilidade afiada.", "Esperava mais, o final deixou a desejar.",
    "Um dos melhores que joguei este ano.", "Bom para jogar com calma no fim de semana.",
    "Controles confusos, mas a história compensa.", "Visual lindo e desafio na medida certa.",
]
BASE = datetime(2026, 9, 1, 12, 0)
SEED_PASSWORD = "senha1234"


def run(seed=42):
    if Game.query.first():
        return  # idempotente: não duplica
    rng = random.Random(seed)
    genres = [Genre(name=n, slug=slugify(n)) for n in GENRES]
    platforms = [Platform(name=n, slug=slugify(n)) for n in PLATFORMS]
    dev_names = sorted({f"{a} {b}" for a in DEV_A for b in DEV_B})
    devs = [Developer(name=n, slug=slugify(n)) for n in rng.sample(dev_names, 40)]
    db.session.add_all(genres + platforms + devs)

    titles = set()
    while len(titles) < 300:
        k = rng.random()
        titles.add(f"{rng.choice(NOUN)} {rng.choice(ADJ)}" if k < .5 else
                   f"{rng.choice(NOUN)} de {rng.choice(PLACE)}" if k < .8 else
                   f"{rng.choice(PLACE)}: {rng.choice(NOUN)} {rng.choice(ADJ)}")
    games = []
    for t in sorted(titles):
        games.append(Game(
            title=t, slug=slugify(t), synopsis=rng.choice(SYN).format(n=t),
            release_date=date(1995, 1, 1) + timedelta(days=rng.randrange(0, 11000)),
            developer=rng.choice(devs), genres=rng.sample(genres, rng.randint(1, 3)),
            platforms=rng.sample(platforms, rng.randint(1, 4)),
        ))
    db.session.add_all(games)

    pw = generate_password_hash(SEED_PASSWORD)
    users = [User(username=f"jogador{i:02d}", username_lower=f"jogador{i:02d}", email=f"jogador{i:02d}@example.com",
                  password_hash=pw, display_name=f"Jogador {i:02d}", bio=rng.choice(["", "Fã de RPG.", "Platina é vida.", "Casual."]),
                  created_at=BASE - timedelta(days=rng.randint(30, 400))) for i in range(1, 31)]
    db.session.add_all(users)
    db.session.flush()

    quality = {g.id: rng.gauss(6.5, 1.6) for g in games}
    reviews = []
    for u in users:
        for g in rng.sample(games, rng.randint(8, 25)):
            at = BASE - timedelta(hours=rng.randint(1, 24 * 60))
            r = Review(user_id=u.id, game_id=g.id, score=max(0, min(10, round(rng.gauss(quality[g.id], 1.3)))),
                       text=rng.choice(REV) if rng.random() < .7 else "", spoiler=rng.random() < .05, created_at=at)
            reviews.append(r)
            db.session.add_all([r, Status(user_id=u.id, game_id=g.id, value="jogado", updated_at=at),
                                Activity(user_id=u.id, kind="avaliou", game_id=g.id, created_at=at, review=r)])
        others = rng.sample(games, 8)
        for g, v in zip(others, ["planejado"] * 4 + ["jogando"] * 2 + ["abandonado"] * 2):
            if not Review.query.filter_by(user_id=u.id, game_id=g.id).first() and not any(
                    x.user_id == u.id and x.game_id == g.id for x in reviews):
                db.session.add(Status(user_id=u.id, game_id=g.id, value=v, updated_at=BASE))
        db.session.flush()
    db.session.flush()

    for r in rng.sample(reviews, 80):
        for u in rng.sample(users, rng.randint(1, 5)):
            if u.id != r.user_id:
                db.session.add(Like(user_id=u.id, review_id=r.id))

    for u in users:
        for i in range(rng.randint(1, 3)):
            pub = rng.random() < .75
            gl = GameList(user_id=u.id, name=rng.choice(["Favoritos", "Para jogar com amigos", "Clássicos", "Jogos curtos", "Platinas"]) + f" {i + 1}",
                          description="Lista fictícia.", public=pub, created_at=BASE - timedelta(days=rng.randint(1, 100)))
            db.session.add(gl)
            db.session.flush()
            for pos, g in enumerate(rng.sample(games, rng.randint(3, 12))):
                db.session.add(ListItem(list_id=gl.id, game_id=g.id, position=pos))
            if pub:
                db.session.add(Activity(user_id=u.id, kind="lista", list_id=gl.id, created_at=gl.created_at))
        for f in rng.sample([x for x in users if x.id != u.id], rng.randint(3, 10)):
            db.session.add(Follow(follower_id=u.id, followed_id=f.id))

    for r in rng.sample([r for r in reviews if r.text], 3):  # denúncias para a fila de moderação
        db.session.add(Report(review_id=r.id, reporter_id=rng.choice([u.id for u in users if u.id != r.user_id]),
                              reason=rng.choice(["spam", "ofensivo", "spoiler"]), created_at=BASE))
    db.session.commit()
