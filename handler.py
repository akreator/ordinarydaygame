import jinja2, webapp2, os, urllib, hmac, hashlib
import databases as my_db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)


class Handler(webapp2.RequestHandler):
    def write(self, *args, **kwargs):
        self.response.out.write(*args, **kwargs)

    def render(self, template, **params):
        t = jinja_env.get_template(template)
        self.write(t.render(params, user=self.user))

    def logout(self):
        self.set_cookie("userid", "")

    def set_cookie(self, name, value):
        self.response.set_cookie(name, value, path='/')

    def make_secure_val(self, val):
        secret = str(my_db.Secret.get_secret())
        return '%s|%s' % (val, hmac.new(secret, val, hashlib.sha256).hexdigest())

    def check_secure_val(self, secure_val):
        val = secure_val.split('|')[0]
        #if hmac.compare_digest(secure_val, self.make_secure_val(val)):
        if secure_val == self.make_secure_val(val):
            return val

    def parse_content(self, content):
        if self.user:
            content = content.replace('<name>', self.user.username)
            content = content.replace('<they>', self.user.pronouns.split('/')[0]) \
                .replace('<them>', self.user.pronouns.split('/')[1]) \
                .replace('<their>', self.user.pronouns.split('/')[2]) \
                .replace('<theirs>', self.user.pronouns.split('/')[3])
            return content
        else:
            content = content.replace('<name>', "Guest")
            content = content.replace('<they>', "they") \
                .replace('<them>', "them") \
                .replace('<their>', "their") \
                .replace('<theirs>', "theirs")
            return content

    def initialize(self, *args, **kwargs):
        webapp2.RequestHandler.initialize(self, *args, **kwargs)
        uid = self.request.cookies.get("userid")
        if uid and self.check_secure_val(uid):
            uid = self.check_secure_val(uid)
            self.user = my_db.Users.get_by_id(uid)
            if not self.user:
                self.set_cookie('userid', '')
        else:
            self.set_cookie('userid', '')
            self.user = None