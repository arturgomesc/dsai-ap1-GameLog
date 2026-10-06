import importlib

MODULES = ["auth", "catalogo", "busca", "jogo", "avaliacoes", "listas", "social", "recomendacoes", "afinidade", "admin"]


def register(app):
    for name in MODULES:
        try:
            mod = importlib.import_module(f"{__package__}.{name}")
        except ModuleNotFoundError as e:
            if e.name != f"{__package__}.{name}":
                raise
            continue  # parte ainda não implementada
        app.register_blueprint(mod.bp)
