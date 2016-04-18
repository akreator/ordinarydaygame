import handler as h
import databases as my_db
import util


class EditEventHandler(h.Handler):
    @util.require_trail
    @util.require_login
    def get(self, trail):
        ud = my_db.UserData.get_user_data(self.user, trail)
        e = ud.event_path[-1].get()
        if self.user.username == e.creator:
            self.render("newevent.html", content=e.content, location=e.location, item_needed=e.item_needed,
                        item_found=e.item_found, action=e.action, edit=True, trail=trail, event=e)
        else:
            self.redirect("/error?error=permissions")

    @util.require_trail
    @util.require_login
    def post(self, trail):
        ud = my_db.UserData.get_user_data(self.user, trail)
        content = self.request.get("content")
        location = self.request.get("location")
        item_needed = self.request.get("item_needed").lower()
        item_found = self.request.get("item_found").lower()
        action = self.request.get("action")
        event = ud.event_path[-1].get()

        if self.user.username == event.creator:
            if content and location and action and action.lower() != 'walk your own path':
                if event.update_event(user=self.user, content=content, location=location, action=action, item_needed=item_needed,
                                      item_found=item_found):
                    return self.redirect('/trail/%s/walktrail' % trail.url)
                else:
                    return self.render("newevent.html", content=content, location=location, item_needed=item_needed, item_found=item_found,
                                       action=action, error="Sorry, your request could not be processed. Please enable Javascript for details.")
            else:
                self.render('newpath.html', error='Please make sure you have a location, action, and content', content=content,
                            location=location, item_needed=item_needed, item_found=item_found, action=action)
        else:
            self.redirect('/error?error=permissions')


class NewEventHandler(h.Handler):
    @util.require_trail
    @util.require_login
    def get(self, trail):
        self.render("newevent.html", error="")

    @util.require_trail
    @util.require_login
    def post(self, trail):
        ud = my_db.UserData.get_user_data(self.user, trail)
        content = self.request.get("content")
        location = self.request.get("location")
        item_needed = self.request.get("item_needed").lower()
        item_found = self.request.get("item_found").lower()
        action = self.request.get("action")
        parent_event = ud.event_path[-1].get()

        if content and location and action and action.lower() != 'walk your own path':
            if my_db.Event.create_event(parent_event=parent_event, content=content, location=location, action=action,
                                        creator=self.user, trail=trail, item_needed=item_needed, item_found=item_found):
                return self.redirect('/trail/%s/walktrail' % trail.url)
            else:
                return self.render("newevent.html", content=content, location=location, item_needed=item_needed,
                                   item_found=item_found, action=action,
                                   error="Sorry, your request could not be processed.  Please enable Javascript for details.")
        else:
            self.render('newpath.html', error='Please make sure you have a location, action, and content',
                        content=content, location=location, item_needed=item_needed, item_found=item_found,
                        action=action)
            

class DeleteHandler(h.Handler):
    @util.require_trail
    @util.require_login
    def get(self, trail):
        if self.user.username == trail.creator:
            t = self.request.get("t")
            if t and t.isdigit() and my_db.Event.get_by_id(int(t)):
                event = my_db.Event.get_by_id(int(t))
                if event.key != trail.first_event:
                    self.render("delete-event.html", e=event, parse_content=self.parse_content)
                else:
                    self.redirect('/error?error=fe')
            elif not t:
                self.render("delete-trail.html", trail=trail)
            else:
                self.redirect("/error?error=notfound")
        else:
            self.redirect("/error?error=permissions")

    @util.require_trail
    @util.require_login
    def post(self, trail):
        if self.user.username == trail.creator:
            t = self.request.get("t")
            if t and t.isdigit() and my_db.Event.get_by_id(int(t)):
                event = my_db.Event.get_by_id(int(t))
                my_db.Event.delete_event(event)
                self.redirect("/trail/%s" % trail.url)
            elif not t:
                my_db.Trail.delete_trail(trail)
                self.redirect("/")
            else:
                self.redirect("/error?error=notfound")
        else:
            self.redirect("/error?error=permissions")