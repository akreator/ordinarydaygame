import jinja2, webapp2, os, urllib, hmac, hashlib, eventhandler, nologinhandler, trailhandler, userhandler
import databases as my_db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


app = webapp2.WSGIApplication([('/', nologinhandler.MainHandler),
                               ('/signup', userhandler.SignUpHandler),
                               ('/login', userhandler.LoginHandler),
                               ('/logout', userhandler.LogoutHandler),
                               ('/feedback', nologinhandler.FeedbackHandler),
                               ('/contact', nologinhandler.ContactHandler),
                               ('/about', nologinhandler.AboutHandler),
                               ('/newtrail', trailhandler.NewTrailHandler),
                               (r'/trail/([^/]+)', trailhandler.TrailStartHandler),
                               (r'/trail/([^/]+)/walktrail', trailhandler.WalkTrailHandler),
                               (r'/trail/([^/]+)/newevent', eventhandler.NewEventHandler),
                               (r'/trail/([^/]+)/editevent', eventhandler.EditEventHandler),
                               (r'/trail/([^/]+)/edit', trailhandler.TrailEditorHandler),
                               (r'/trail/([^/]+)/save', trailhandler.SaveHandler),
                               (r'/trail/([^/]+)/delete', eventhandler.DeleteHandler),
                               ('/explore', nologinhandler.ExploreHandler),
                               ('/error', nologinhandler.ErrorHandler),
                               ('/saved', trailhandler.SavedTrailsHandler),
                               ('/user/([^/]+)', userhandler.ProfileHandler)], debug=True)
