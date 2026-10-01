from flask import Blueprint, abort, flash, redirect, request

from .models import REPORT_REASONS, Activity, Like, Report, Review, Status, db, visible_games
from .util import current_user, login_required

bp = Blueprint("avaliacoes", __name__)


def back(game, review=None):
    return redirect(f"/jogos/{game.slug}" + (f"#av-{review.id}" if review else ""))


def own_or_403(review):
    if review.user_id != current_user().id:
        abort(403)


def delete_review(review):
    """Remove a avaliação e tudo que depende dela (AVA-04)."""
    Like.query.filter_by(review_id=review.id).delete()
    Report.query.filter_by(review_id=review.id).delete()
    Activity.query.filter_by(review_id=review.id).delete()
    db.session.delete(review)


@bp.route("/jogos/<slug>/avaliar", methods=["POST"])
@login_required
def rate(slug):
    game = visible_games().filter_by(slug=slug).first_or_404()
    me = current_user()
    f = request.form
    try:
        score = int(f.get("score", ""))
        if not 0 <= score <= 10:
            raise ValueError
    except ValueError:
        flash("A nota é obrigatória e deve ser um inteiro de 0 a 10.", "erro")  # AVA-01
        return back(game)
    text = f.get("text", "").strip()
    if len(text) > 5000:
        flash("A resenha deve ter até 5000 caracteres.", "erro")  # AVA-03
        return back(game)
    review = Review.query.filter_by(user_id=me.id, game_id=game.id).first()
    if review:  # AVA-02: nova submissão edita a existente
        review.score, review.text, review.spoiler, review.edited = score, text, bool(f.get("spoiler")), True
    else:
        review = Review(user_id=me.id, game_id=game.id, score=score, text=text, spoiler=bool(f.get("spoiler")))
        db.session.add(review)
        db.session.flush()
        db.session.add(Activity(user_id=me.id, kind="avaliou", game_id=game.id, review_id=review.id))
    if not Status.query.filter_by(user_id=me.id, game_id=game.id).first():  # AVA-11
        db.session.add(Status(user_id=me.id, game_id=game.id, value="jogado"))
    db.session.commit()
    flash("Avaliação salva.", "ok")
    return back(game, review)


@bp.route("/avaliacoes/<int:rid>/apagar", methods=["POST"])
@login_required
def delete(rid):
    review = db.get_or_404(Review, rid)
    own_or_403(review)
    game = review.game
    delete_review(review)
    db.session.commit()
    flash("Avaliação apagada.", "ok")
    return back(game)


@bp.route("/avaliacoes/<int:rid>/curtir", methods=["POST"])
@login_required
def like(rid):
    review = db.get_or_404(Review, rid)
    me = current_user()
    if review.user_id == me.id:
        flash("Você não pode curtir a própria resenha.", "erro")  # AVA-06
    elif review.hidden:
        abort(404)
    elif not Like.query.filter_by(user_id=me.id, review_id=rid).first():
        db.session.add(Like(user_id=me.id, review_id=rid))
        db.session.commit()
    return back(review.game, review)


@bp.route("/avaliacoes/<int:rid>/descurtir", methods=["POST"])
@login_required
def unlike(rid):
    review = db.get_or_404(Review, rid)
    Like.query.filter_by(user_id=current_user().id, review_id=rid).delete()
    db.session.commit()
    return back(review.game, review)


@bp.route("/avaliacoes/<int:rid>/denunciar", methods=["POST"])
@login_required
def report(rid):
    review = db.get_or_404(Review, rid)
    me = current_user()
    reason, comment = request.form.get("reason", ""), request.form.get("comment", "").strip()
    if reason not in REPORT_REASONS:
        flash("Escolha o motivo da denúncia.", "erro")  # AVA-08
    elif len(comment) > 500:
        flash("O comentário deve ter até 500 caracteres.", "erro")
    elif Report.query.filter_by(review_id=rid, reporter_id=me.id).first():
        flash("Você já denunciou esta avaliação.", "erro")
    else:
        db.session.add(Report(review_id=rid, reporter_id=me.id, reason=reason, comment=comment))
        db.session.commit()
        flash("Denúncia enviada. Obrigado!", "ok")
    return back(review.game, review)
