import handler as h
import databases as my_db
import util, urllib


class SavedTrailsHandler(h.Handler):
    @util.require_login
    def get(self):
        self.render("savedtrails.html", parse_content=self.parse_content, escape=urllib.quote)


class NewTrailHandler(h.Handler):
    def render_page(self, trail_title="", trail_description="", trail_tags="", error="", location="", item_found="", action="",
                    content=""):
        self.render("newtrail.html", trail_title=trail_title, trail_description=trail_description, error=error,
                    location=location, item_found=item_found, action=action, content=content, trail_tags=trail_tags)

    @util.require_login
    def get(self):
        self.render_page()

    @util.require_login
    def post(self):
        content = self.request.get("content")
        location = self.request.get("location")
        action = self.request.get("action")
        title = self.request.get("trail_title")
        description = self.request.get("trail_description")
        trail_tags = self.request.get("trail_tags")
        tags = trail_tags.replace(', ', ',').split(',')

        if content and location and action and action.lower() != 'walk your own path':
            t = my_db.Trail.create_trail(title=title, creator=self.user, description=description, content=content,
                                         location=location, action=action, tags=tags)
            if t:
                self.redirect('/trail/%s' % t.url)
            else:
                self.render_page(trail_title=title, trail_description=description,
                                 error="Your trail could not be created.  Enable Javascript for details.",
                                 location=location, action=action, content=content, trail_tags=trail_tags)


class TrailEditorHandler(h.Handler):
    @util.require_trail
    @util.require_login
    def get(self, trail):
        if trail and self.user.username == trail.creator:
            trail_tags = ', '.join(trail.tags)
            self.render("traileditor.html", trail=trail, tags=trail_tags)
        else:
            self.redirect('/error?error=permissions')

    @util.require_trail
    @util.require_login
    def post(self, trail):
        if trail and self.user.username == trail.creator:
            description = self.request.get("trail_description")
            trail_tags = self.request.get("trail_tags")
            tags = trail_tags.replace(', ', ',').split(',')
            if trail.update_trail(trail=trail, tags=tags):
                self.redirect("/trail/%s" % trail.url)
            else:
                self.render("traileditor.html", description=description, tags=trail_tags, error="Please enter valid values.")
        else:
            self.redirect('/error?error=permissions')


class TrailStartHandler(h.Handler):
    @util.require_trail
    def get(self, trail):
        edited_events = trail.get_edited_events()
        events = edited_events[0]
        edits = edited_events[1]
        self.render("trailstart.html", trail=trail, parse_content=self.parse_content, events=events, edits=edits,
                    escape=urllib.quote_plus)

    @util.require_trail
    @util.require_login
    def post(self, trail):
        accept_events = self.request.get("accept_events", allow_multiple=True)
        accept_edits = self.request.get("accept_edits", allow_multiple=True)
        if not accept_edits and not accept_events:
            self.render("trailstart.html", trail=trail, parse_content=self.parse_content, escape=urllib.quote_plus,
                        error="No events were added or changed.")
        else:
            if accept_events:
                for e in accept_events:
                    event = my_db.Event.get_by_id(int(e))
                    trail.accept_event(my_db.Users.get_by_username(event.creator), event)
            if accept_edits:
                for e in accept_edits:
                    edit = my_db.EditedEvent.get_by_id(int(e))
                    trail.accept_edit(edit)
            self.render("trailstart.html", trail=trail, parse_content=self.parse_content, escape=urllib.quote_plus,
                            error="Your selections have been updated.")


class SaveHandler(h.Handler):
    @util.require_trail
    @util.require_login
    def get(self, trail):
        self.user.save_trail(trail)
        self.redirect('/trail/%s/walktrail?saved=true' % trail.url)


class WalkTrailHandler(h.Handler):
    def render_page(self, event, inventory, trail, error=""):
        self.render("event.html", event=event, inventory=inventory, parse_content=self.parse_content, error=error,
                    trail=trail)

    @util.require_trail
    @util.require_login
    def get(self, trail):
        back = self.request.get("back")
        restart = self.request.get("restart")
        saved = self.request.get("saved")
        if back:
            ud = my_db.UserData.get_user_data(self.user, trail)
            if len(ud.event_path) > 1:
                ud.event_path.pop()
                ud.put()
            self.render_page(event=ud.event_path[-1].get(), inventory=ud.inventory, trail=trail)
        elif restart:
            ud = my_db.UserData.get_user_data(self.user, trail)
            ud.event_path = [ud.event_path[0]]
            ud.put()
            self.redirect('/trail/%s' % trail.url)
        elif saved:
            ud = my_db.UserData.get_user_data(self.user, trail)
            self.render_page(event=ud.event_path[-1].get(), inventory=ud.inventory, trail=trail, error="Trail saved!")
        else:
            if not trail.check_visited(self.user):
                self.user.record_trail_visit(trail=trail)
            ud = my_db.UserData.get_user_data(self.user, trail)
            event = ud.event_path[-1].get()
            self.render_page(event=event, inventory=ud.inventory, trail=trail)

    @util.require_trail
    @util.require_login
    def post(self, trail):
        ud = my_db.UserData.get_user_data(self.user, trail)
        selected_event = self.request.get("next_event")
        if selected_event == "custom":
            self.redirect('/trail/%s/newevent' % trail.url)
        elif selected_event:
            event = my_db.Event.get_by_id(int(selected_event))
            if event and (not event.item_needed or ud.use_item(event.item_needed) or event.creator == self.user.username):
                if event.item_found:
                    ud.add_item(event.item_found)
                ud.record_event(event)
                self.render_page(event=event, inventory=ud.inventory, trail=trail)
            else:
                self.render_page(event=ud.event_path[-1].get(), inventory=ud.inventory, trail=trail,
                                 error="Sorry, but you do not have the necessary item to continue.")
        else:
            self.render_page(event=ud.event_path[-1].get(), inventory=ud.inventory, trail=trail,
                             error="Please select an action.")