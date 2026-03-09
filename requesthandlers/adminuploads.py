import json
import os
import re

import tornado

from core.config import UPLOAD_DIR
from requesthandlers.base import BaseHandler


class AdminUploadsHandler(BaseHandler):

    @tornado.web.authenticated
    async def get(self):
        """Deliver the admin/uploads page. Requires super-admin."""

        executor = tornado.ioloop.IOLoop.current()

        # Check user is super-admin
        user = await executor.run_in_executor(None, lambda: self.application.db.get_user(self.current_user))
        if not user.super_admin:
            self.write("You do not have permission to access this page.")
            return

        files = sorted(f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith('.png'))
        self.render("adminuploads.html", files=files)

    @tornado.web.authenticated
    async def post(self):
        """Handle post to the admin/uploads page. This includes both uploading files and deleting them depending on the
        Action."""

        self.set_header("Content-Type", "application/json")
        executor = tornado.ioloop.IOLoop.current()

        # Check user is super-admin
        user = await executor.run_in_executor(None, lambda: self.application.db.get_user(self.current_user))
        if not user.super_admin:
            self.set_status(403)
            self.write(json.dumps({"message": "You do not have permission to access this page."}))
            return

        action = self.get_argument("action", None)

        if action == "Delete":
            # Handle delete action

            filename = self.get_argument("filename", None)
            if not filename:
                self.set_status(400)
                self.write(json.dumps({"message": "No filename provided."}))
                return
            if not re.match(r'^[a-zA-Z0-9_\-]+\.png$', filename):
                self.set_status(400)
                self.write(json.dumps({"message": "Invalid filename."}))
                return
            filepath = os.path.join(UPLOAD_DIR, filename)
            if not os.path.isfile(filepath):
                self.set_status(404)
                self.write(json.dumps({"message": "File not found."}))
                return

            # Run out of problems, so should be OK to delete
            try:
                os.remove(filepath)
                self.set_status(200)
                self.write(json.dumps({"message": "File deleted."}))
            except Exception:
                self.set_status(500)
                self.write(json.dumps({"message": "Failed to delete file."}))

        elif action == "Upload":
            # Handle the upload action, taking the provided file and writing it to the appropriate directory provided it
            # passes checks.

            uploaded_files = self.request.files.get("file", [])
            if not uploaded_files:
                self.set_status(400)
                self.write(json.dumps({"message": "No file provided."}))
                return
            file_info = uploaded_files[0]
            original_name = file_info["filename"]
            basename = os.path.basename(original_name)
            if not re.match(r'^[a-zA-Z0-9_\-]+\.png$', basename):
                self.set_status(400)
                self.write(json.dumps({
                    "message": "Invalid filename. Use only letters, numbers, hyphens, and underscores, with a .png extension."}))
                return

            # Good to go with saving the file
            filepath = os.path.join(UPLOAD_DIR, basename)
            try:
                with open(filepath, 'wb') as f:
                    f.write(file_info["body"])
                self.set_status(200)
                self.write(json.dumps({"message": "File uploaded successfully.", "redirect_url": "/admin/uploads"}))
            except Exception:
                self.set_status(500)
                self.write(json.dumps({"message": "Failed to upload file."}))

        else:
            self.set_status(400)
            self.write(json.dumps({"message": "Invalid action."}))
