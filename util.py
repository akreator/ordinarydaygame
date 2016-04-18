import databases as my_db


def require_login(handler):
    def check_login(self, *args, **kwargs):
        uid = self.request.cookies.get("userid")
        if uid and self.check_secure_val(uid):
            uid = self.check_secure_val(uid)
            self.user = my_db.Users.get_by_id(uid)
            if not self.user:
                self.set_cookie('userid', '')
                return self.redirect("/login?reminder=true")
        else:
            self.set_cookie('userid', '')
            self.user = None
            return self.redirect("/login?reminder=true")
        return handler(self, *args, **kwargs)
    return check_login


def require_trail(handler):
    def check_trail(self, url):
        trail = my_db.Trail.get_by_url(url)
        if trail:
            return handler(self, trail)
        else:
            return self.render("error.html", error="The trail %s could not be found.  "
                                                   "If you were looking for a specific trail, check the url. "
                                                   "Otherwise, would you like to make the trail?" % url)
    return check_trail
