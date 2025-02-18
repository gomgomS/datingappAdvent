

import sys
import traceback
import datetime
import time
import ast # use to convert string to dictionary 
from   datetime import datetime
import random
import re
from werkzeug.utils import secure_filename
import os
from tempfile import NamedTemporaryFile

from view   import view_core_menu

sys.path.append("pytavia_core"    )
sys.path.append("pytavia_modules" )
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib"  )
sys.path.append("pytavia_storage" )

from pytavia_stdlib import idgen
from pytavia_stdlib import utils
from pytavia_stdlib import emailproc
from pytavia_core   import database
from pytavia_core   import config
from uuid     import uuid4
from flask import request 
from xml.sax            import saxutils as su

class profile_proc:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def send_cv(self, params):    
        result_url = "/profile"
        
        unique_4_number             = random.randint(1000,9999)
        params["unique_4_number"]   = str(unique_4_number)

        # Get the current date
        apply_date           = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    

        # cv_user_html
        cv_user_html        = su.unescape(params["cv_user"])

        clean               = re.compile('<.*?>')
        params["cv_user"]   = re.sub( clean, '',cv_user_html)

        list_cv_user        = params["cv_user"].split(' ')
        list_cv_user        = list_cv_user[0:10]
        list_cv_user.append("...")
        cv_user_preview     = " ".join(list_cv_user)


        query   = {            
            "cv_user"            : params["cv_user"],
            "cv_user_html"       : cv_user_html,
            "cv_user_preview"    : cv_user_preview,
            "cv_link"            : params["cv_link"]
        }

        summery_status_applying   = self.mgdDB.db_user.find_one(
            {"fk_user_id"         : params["fk_user_id"]},
            {"_id":0,"summery_status_applying":1, "register_trainer":1}
        )

        #if already approve by admin, trainer not neccesesry for waiting
        if summery_status_applying['register_trainer'] != 'TRUE':
            query['summery_status_applying']  = "WAITING"

        update_doc = {
            "$set": query
        }
        
        #if already approve by admin, trainer not neccesesry for waiting
        if summery_status_applying['register_trainer'] != 'TRUE':     
            if summery_status_applying["summery_status_applying"] != "WAITING":
                
                status_applying = {
                    "status"            : "WAITING",
                    "apply_date"        : apply_date                
                }     

                update_doc["$push"] = {"status_applying": status_applying}
      
        # Update the document in MongoDB
        user_rec                    = self.mgdDB.db_user.update_one(
            {"fk_user_id"         : params["fk_user_id"]},            
            update_doc            
        )
        
        return result_url
        
    def update_cv(self, params, request_files):    
        result_url = "/profile"       

        query = {
            "phone": params["phone"],
            "name": params["name"],
            "username": params["username"],     
            "email": params["email"]
        }

        file = request_files.get('profile_image')
        current_image_path = None

        # Retrieve current user data to get the old image path
        current_user = self.mgdDB.db_user.find_one({"fk_user_id": params["fk_user_id"]})
        if current_user and "image" in current_user:
            current_image_path = current_user["image"]

        if file:
            # # Read the file into memory and get its size
            # file_stream = BytesIO(file.read())
            # file_size = len(file_stream.getvalue())
            
            # # Debug: Log file size
            # print(f"File size: {file_size} bytes")

            # # Check file size
            # if file_size > 2 * 1024 * 1024:  # 2MB
            #     return {
            #         "result_url": result_url,
            #         "notif_type": "danger",
            #         "msg": "File is too large. Please upload a file smaller than 2MB."
            #     }

            # # Reset the file stream position to the beginning
            # file_stream.seek(0)         
            
            # Check file format
            if not self.allowed_file(file.filename):
                return {
                    "result_url": result_url,
                    "notif_type": "danger",
                    "msg": "Invalid file format. Please upload a PNG, JPG, or JPEG image."
                }

            file = request_files.get('profile_image')
            # Handle the image file upload
            if file.filename != '':
                filename = secure_filename(file.filename)
                file_path = os.path.join(self.webapp.root_path, 'static/assets/profile_image', filename)
                file.save(file_path)
                query["image"] = file_path.replace(self.webapp.root_path, '')  # Store relative path

                # Remove the old file if it exists
            if current_image_path:
                old_file_path = os.path.join(self.webapp.root_path, current_image_path.lstrip('/'))  # Remove leading slash if present
                print(f"Attempting to remove: {old_file_path}")  # Debug: Print the path to verify

                if os.path.isfile(old_file_path):
                    try:
                        os.remove(old_file_path)
                        print(f"Successfully removed: {old_file_path}")
                    except Exception as e:
                        print(f"Error removing file: {e}")
                else:
                    print(f"File not found: {old_file_path}")


        # Check if email has changed
        if params["email"] != params.get("old_email", ""):
            query["ver_email"] = "FALSE"

        update_doc = {
            "$set": query
        }

        # Update the document in MongoDB
        self.mgdDB.db_user.update_one(
            {"fk_user_id": params["fk_user_id"]},            
            update_doc            
        )

        return {
            "result_url": result_url,
            "notif_type": "success",
            "msg": "Update profile/cv success"
        }
    

    def allowed_file(self, filename):
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

    def change_portal_trainer(self, params):    
        result_url = "/user/dashboard"

        query ={}

        register_teacher   = self.mgdDB.db_user.find_one(
            {"fk_user_id"         : params["fk_user_id"]},
            {"_id":0,"register_teacher":1}
        )        
    
        if register_teacher["register_teacher"] == "TRUE":        
            query["role"] = "TRAINER"

        update_doc = {
            "$set": query
        }
    
        # Update the document in MongoDB
        user_rec                    = self.mgdDB.db_user.update_one(
            {"fk_user_id"         : params["fk_user_id"]},            
            update_doc            
        )
        
        return result_url

    def change_portal_trainee(self, params):    
        result_url = "/user/dashboard"        

        update_doc = {
            "$set": {"role"  : "TRAINEE"}
        }
      
        # Update the document in MongoDB
        user_rec                    = self.mgdDB.db_user.update_one(
            {"fk_user_id"         : params["fk_user_id"]},            
            update_doc            
        )
        
        return result_url

        