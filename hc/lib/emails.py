from threading import Thread

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string as render


class EmailThread(Thread):
    def __init__(self, subject, text, html, to):
        Thread.__init__(self)
        self.subject = subject
        self.text = text
        self.html = html
        self.to = to

    def run(self):
        msg = EmailMultiAlternatives(self.subject, self.text, to=(self.to, ))
        msg.attach_alternative(self.html, "text/html")
        msg.send()


def send(name, to, ctx):
    ctx["SITE_ROOT"] = settings.SITE_ROOT

    subject = render('emails/%s-subject.html' % name, ctx).strip()
    text = render('emails/%s-body-text.html' % name, ctx)
    html = render('emails/%s-body-html.html' % name, ctx)

    t = EmailThread(subject, text, html, to)
    if hasattr(settings, "BLOCKING_EMAILS"):
        t.run()
    else:
        t.start()


def login(to, ctx):
    send("login", to, ctx)


def set_password(to, ctx):
    send("set-password", to, ctx)


def alert(to, ctx):
    send("alert", to, ctx)


def verify_email(to, ctx):
    send("verify-email", to, ctx)


def report(to, ctx):
    send("report", to, ctx)
