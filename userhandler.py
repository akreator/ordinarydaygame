import handler as h
import databases as my_db
import urllib


class LoginHandler(h.Handler):
    def render_page(self, error="", username=""):
        self.render("login.html", error=error, username=username)

    def get(self):
        if self.request.get("reminder"):
            self.render_page(error="You must be logged in to view this page")
        else:
            self.render_page()

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        if username and password:
            u = my_db.Users.login(username, password)
            if u:
                uid = self.make_secure_val(u.key.id())
                self.set_cookie("userid", uid)
                self.redirect('/')
            else:
                self.render_page(error="Please double check your username and password and try again.", username=username)
        else:
            self.render_page(error="Please enter a username and a password.")


class LogoutHandler(h.Handler):
    def get(self):
        self.logout()
        self.redirect('/login')


class SignUpHandler(h.Handler):
    def render_page(self, error="", username="", email=""):
        self.render("signup.html", error=error, username=username, email=email)

    def get(self):
        self.render_page()

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")
        pronouns = self.request.get("pronouns")
        if username and pronouns and email and password and verify and password == verify:
            u = my_db.Users.register_user(username=username, password=password, email=email, pronouns=pronouns)
            if u:
                uid = self.make_secure_val(u.key.id())
                self.set_cookie("userid", uid)
                self.redirect('/')
            else:
                self.render("signup.html", error="Sorry, part or parts of your input is invalid.  "
                                                 "Please enable Javascript for details.",
                            username=username, email=email)
        else:
            self.render("signup.html", error="Please enter values for all forms.", username=username, email=email)


class ProfileHandler(h.Handler):
    def get(self, userid):
        userid = urllib.unquote_plus(userid).lower()
        profile_user = my_db.Users.get_by_id(userid)
        if profile_user:
            self.render("profile.html", profile_user=profile_user)
        else:
            self.redirect("/error?error=notfound")