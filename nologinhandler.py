import urllib
import databases as my_db, handler as h


class ExploreHandler(h.Handler):
    def render_page(self, trails, selected="", tags="", error=""):
        self.render("explore.html", trails=trails, parse_content=self.parse_content, escape=urllib.quote,
                    selected=selected, tags=tags, error=error)

    def get(self):
        search_tags = self.request.get("tags")
        sort = self.request.get("sort")
        if search_tags:
            search_tags = urllib.unquote(search_tags).split("&")
            trails = my_db.Trail.query(my_db.Trail.tags.IN(search_tags))
        else:
            trails = my_db.Trail.query()

        if sort:
            if sort == "nvisitors":
                trails = trails.order(-my_db.Trail.users_visited_amt)
            elif sort == "rnvisitors":
                trails = trails.order(my_db.Trail.users_visited_amt)
            elif sort == "date":
                trails = trails.order(my_db.Trail.datetime_created)
            elif sort == "rdate":
                trails = trails.order(-my_db.Trail.datetime_created)

        self.render_page(trails=trails.fetch())

    def post(self):
        trails = my_db.Trail.query().fetch()
        self.render_page(trails=trails, error="No post requests, please.")


class MainHandler(h.Handler):
    def get(self):
        self.render("welcome.html", top_trails=my_db.Trail.get_top_trails(),
                    newest_trails=my_db.Trail.get_newest_trails())


class FeedbackHandler(h.Handler):
    def get(self):
        self.render("feedback.html")

    def post(self):
        name = self.request.get("name")
        email = self.request.get("email")
        feedback = self.request.get("feedback")

        if name and email and feedback:
            message = """
                From: anordinarydaygame@gmail.com
                To: Audrey Kintisch akintisch@gmail.com
                Subject: Ordinary Day Feedback

                User: %s %s
                %s
                """ % (name, email, feedback)
            f = my_db.Feedback.log_feedback(name=name, email=email, feedback=message)
            if f:
                self.render('feedback.html', error='Your response has been recorded.')
            else:
                self.render('feedback.html', error='Please enter a valid e-mail address.')
        else:
            self.render('feedback.html', error='Please enter values for all fields.')


class ContactHandler(h.Handler):
    def get(self):
        self.render("contact.html")


class AboutHandler(h.Handler):
    def get(self):
        self.render("about.html")


class ErrorHandler(h.Handler):
    def get(self):
        error = self.request.get("error")
        if error == "notfound":
            self.render("error.html", error="Sorry, that page could not be found.  Check the URL and try again.")
        elif error == "permissions":
            self.render("error.html", error="Sorry, you do not have permission to view this page.")
        elif error == "post":
            self.render("error.html", error="Wow, you're a nerd!!<br>Or very, very confused.<br><br>No post requests, please.")
        elif error == "fe":
            self.render("error.html", error="Sorry, but the first event cannot be deleted.  If you wish to delete the full trail,"
                                            "go the trail's start page, click edit, and then delete.")
        else:
            self.render("error.html", error="Something went wrong.  "
                                            "Please email akintisch@gmail.com with a description of how you got to this page")