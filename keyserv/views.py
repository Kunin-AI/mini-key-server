# MIT License

# Copyright (c) 2019 Samuel Hoffman

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os

from flask import (Blueprint, abort, current_app, flash, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required, login_user, logout_user

from keyserv.auth import Users
from keyserv.forms import AppForm, KeyForm, LoginForm
from keyserv.keymanager import cut_key_unsafe
from keyserv.models import Application, AuditLog, EarlyBirdApplication, Event, Key, db

frontend = Blueprint("frontend", __name__)


@frontend.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, "static"),
                               "favicon.ico",
                               mimetype="image/vnd.microsoft.icon")


@frontend.route("/", methods=["GET", "POST"])
def index():
    # serve the landing page when accessed via the earlyaccess subdomain
    if "firstbell" in request.host:
        return render_template("earlybird_landing.html")

    form = LoginForm(request.form)

    if request.method == "POST" and form.validate():
        current_app.logger.debug("login form was submitted")
        user = Users.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            if login_user(user):
                current_app.logger.debug(f"login for {user}")
        else:
            flash("Invalid username or password.", "error")
        return redirect(url_for("frontend.index"))

    return render_template("index.html", form=form, current_user=current_user)


@frontend.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("frontend.index"))


@frontend.route("/keys")
@login_required
def keys():
    return render_template("keys.html", keys=Key.query.all())


@frontend.route("/applications")
@login_required
def apps():
    return render_template("applications.html", apps=Application.query.all())


@frontend.route("/logs")
@login_required
def logs():
    return render_template("logs.html", logs=AuditLog.query.all())


@frontend.route("/modify/key/<int:key_id>", methods=["GET", "POST"])
@login_required
def modify_key(key_id: int):

    key = Key.query.get(key_id)
    if not key:
        abort(404)

    form = KeyForm(request.form)
    form.application.choices = [(app.id, app.name)
                                for app in Application.query.all()]

    if request.method == "POST" and form.validate_on_submit():
        changes = []

        if key.remaining != form.activations.data:
            changes.append(f"activations changed from {key.remaining}"
                           f" to {form.activations.data}")
            key.remaining = form.activations.data
        if key.memo != form.memo.data:
            changes.append(f"memo changed from {key.memo!r}"
                           f" to {form.memo.data!r}")
            key.memo = form.memo.data
        if key.app_id != form.application.data:
            changes.append(f"app changed from {key.app} to"
                           f" {form.application.data}")
            key.application = form.application.data
        if key.enabled != form.active.data:
            changes.append(f"active changed from {key.enabled}"
                           f" to {form.active.data}")
            key.enabled = form.active.data
        # if key.hwid != form.hwid.data:
        #     changes.append(f"hwid changed from {key.hwid!r} to "
        #                    f"{form.hwid.data!r}")
        #     key.hwid = form.hwid.data

        AuditLog.from_key(key, f"edited by {current_user.username} "
                          f"({request.remote_addr}):"
                          f" {', '.join(changes)}", Event.KeyModified)

        try:
            db.session.commit()
            flash("Changes successful!")
            return redirect(url_for("frontend.detail_key", key_id=key.id))
        except Exception as error:
            flash(f"Failed to update key: {error}")

    form.application.data = key.app_id
    form.active.data = key.enabled
    form.memo.data = key.memo
    form.activations.data = key.remaining
    # form.hwid.data = key.hwid

    return render_template("add_modify.html",
                           header=f"Modify Key {key.id}", form=form)


@frontend.route("/add/key", methods=["GET", "POST"])
@frontend.route("/add/key/<int:app_id>", methods=["GET", "POST"])
@login_required
def add_key(app_id=None):
    form = KeyForm(request.form)
    form.application.choices = [(app.id, app.name)
                                for app in Application.query.all()]

    if app_id:
        form.application.data = app_id

    if request.method == "POST" and form.validate_on_submit():
        try:
            token = cut_key_unsafe(form.activations.data, form.application.data,
                                   form.kunin_client_id.data,
                                   form.active.data, form.memo.data)
            flash(f"Key added! Token: {token}", "success")
        except Exception as error:
            flash(f"Unable to add key: {error}", "error")

    return render_template("add_modify.html", header="Add Key", form=form)


@frontend.route("/add/app", methods=["GET", "POST"])
@login_required
def add_app():
    form = AppForm(request.form)

    if request.method == "POST" and form.validate_on_submit():
        app = Application()
        app.name = form.name.data
        app.support_message = form.support.data

        db.session.add(app)
        try:
            db.session.commit()
            flash("Success!")
        except Exception as error:
            flash(f"Failed to add application: {error}")

    return render_template("add_modify.html",
                           form=form, header="Add Application")


@frontend.route("/modify/app/<int:app_id>", methods=["GET", "POST"])
@login_required
def modify_app(app_id: int):
    app = Application.query.get(app_id)

    if not app:
        abort(404)

    form = AppForm(request.form)
    if request.method == "POST" and form.validate_on_submit():

        app.name = form.name.data
        app.support_message = form.support.data
        try:
            db.session.commit()
            flash("Success.")
            return redirect(url_for("frontend.detail_app", app_id=app.id))
        except Exception as error:
            flash(f"Failed to modify application: {error}", "error")

    form.name.data = app.name
    form.support.data = app.support_message

    return render_template("add_modify.html", form=form)


@frontend.route("/detail/key/<int:key_id>")
@login_required
def detail_key(key_id: int):

    key = Key.query.get(key_id)

    if not key:
        abort(404)

    return render_template("detail_key.html", key=key)


@frontend.route("/detail/app/<int:app_id>")
@login_required
def detail_app(app_id: int):

    app = Application.query.get(app_id)

    if not app:
        abort(404)

    return render_template("detail_app.html", app=app)


@frontend.route("/keys/app/<int:app_id>")
@login_required
def keys_for_app(app_id):

    app = Application.query.get(app_id)

    if not app:
        abort(404)

    return render_template("keys.html", keys=app.keys)


@frontend.route("/keys/deactivate/<int:key_id>")
@login_required
def disable_key(key_id):

    key = Key.query.get(key_id)

    if not key:
        abort(404)

    key.enabled = False
    db.session.commit()

    return redirect(url_for("frontend.detail_key", key_id=key_id))


@frontend.route("/keys/activate/<int:key_id>")
@login_required
def enable_key(key_id):

    key = Key.query.get(key_id)

    if not key:
        abort(404)

    key.enabled = True
    db.session.commit()

    return redirect(url_for("frontend.detail_key", key_id=key_id))


@frontend.route("/earlybird")
@login_required
def earlybird_list():
    status_filter = request.args.get("status")
    query = EarlyBirdApplication.query.order_by(EarlyBirdApplication.applied_at.desc())
    if status_filter == "pending":
        query = query.filter_by(status=0)
    elif status_filter == "approved":
        query = query.filter_by(status=1)
    elif status_filter == "rejected":
        query = query.filter_by(status=2)
    applications = query.all()
    return render_template("earlybird_list.html", applications=applications, status_filter=status_filter)


@frontend.route("/earlybird/<int:app_id>")
@login_required
def earlybird_detail(app_id):
    application = EarlyBirdApplication.query.get_or_404(app_id)
    return render_template("earlybird_detail.html", app=application)


@frontend.route("/earlybird/<int:app_id>/approve", methods=["POST"])
@login_required
def earlybird_approve(app_id):
    from datetime import datetime
    application = EarlyBirdApplication.query.get_or_404(app_id)
    if application.status != 0:
        flash("Application already reviewed.", "error")
        return redirect(url_for("frontend.earlybird_detail", app_id=app_id))

    # find the Teacher's Pet application (app_id=1 assumed, or find by name)
    tp_app = Application.query.filter_by(name="Teacher's Pet").first()
    if not tp_app:
        tp_app = Application.query.first()

    if not tp_app:
        flash("No application configured for key allocation.", "error")
        return redirect(url_for("frontend.earlybird_detail", app_id=app_id))

    # find an unclaimed key
    key = Key.query.filter_by(app_id=tp_app.id, claimed_by=None, enabled=True) \
        .filter(Key.remaining != 0).first()

    if not key:
        flash("No keys available to allocate.", "error")
        return redirect(url_for("frontend.earlybird_detail", app_id=app_id))

    key.claimed_by = application.email
    key.claimed_at = datetime.utcnow()
    key.memo = f"first-bell: {application.name} <{application.email}>"

    application.status = 1
    application.reviewed_at = datetime.utcnow()
    application.key_id = key.id
    db.session.commit()

    flash(f"Approved! Key allocated: {key.token}", "success")
    return redirect(url_for("frontend.earlybird_detail", app_id=app_id))


@frontend.route("/earlybird/<int:app_id>/reject", methods=["POST"])
@login_required
def earlybird_reject(app_id):
    from datetime import datetime
    application = EarlyBirdApplication.query.get_or_404(app_id)
    if application.status != 0:
        flash("Application already reviewed.", "error")
        return redirect(url_for("frontend.earlybird_detail", app_id=app_id))

    application.status = 2
    application.reviewed_at = datetime.utcnow()
    application.reviewer_notes = request.form.get("reviewer_notes", "")
    db.session.commit()

    flash("Application rejected.", "info")
    return redirect(url_for("frontend.earlybird_detail", app_id=app_id))


@frontend.route("/earlyaccess")
def earlybird_landing():
    return render_template("earlybird_landing.html")
