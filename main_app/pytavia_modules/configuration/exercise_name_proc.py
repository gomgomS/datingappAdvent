import config_core
import sys
import traceback
import requests
import json
import ast
import re
from werkzeug.utils import secure_filename
import os

sys.path.append("pytavia_core"    )
sys.path.append("pytavia_modules" )
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib"  )
sys.path.append("pytavia_storage" )

from pytavia_stdlib   import idgen
from pytavia_stdlib   import utils
from pytavia_core     import database
from pytavia_core     import config
from pytavia_core     import helper
from xml.sax    import saxutils as su

class exercise_name_proc:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def _add(self, params, request_files):
        response = helper.response_msg(
            "ADD_EXERCISE_NAME_SUCCESS", "ADD TERMS AND CONDITIONS SUCCESS", {}, "0000"
        )

        try:
            # Handle the GIF file upload
            if 'exercise_gif' in request_files:
                gif_file = request_files['exercise_gif']
                if gif_file.filename != '':
                    filename = secure_filename(gif_file.filename)
                    gif_path = os.path.join(self.webapp.root_path, 'static/assets/gif', filename)
                    gif_file.save(gif_path)
                    params["exercise_gif_path"] = gif_path.replace(self.webapp.root_path, '')  # Store relative path

            desc_html = su.unescape(params["desc"])

            clean = re.compile('<.*?>')
            params["desc"] = re.sub(clean, '', desc_html)

            tnc_rec = database.new(self.mgdDB, "db_exercise_name")
            tnc_rec.put("exercise_name", params["exercise_name"])
            tnc_rec.put("desc_html", desc_html)
            tnc_rec.put("desc", params["desc"])
            tnc_rec.put("satuan", params["satuan"])

            # Save the GIF file path if it exists
            if "exercise_gif_path" in params:
                tnc_rec.put("exercise_gif_path", params["exercise_gif_path"])

            tnc_rec.insert()

        except:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(traceback.format_exc())

            response.put("status", "ADD_EXERCISE_NAME_FAILED")
            response.put("desc", "ADD EXERCISE NAME FAILED")
            response.put("status_code", "9999")
            response.put("data", {"error_message": trace_back_msg})

        return response
        
    def _update(self, params):
        response = helper.response_msg(
            "UPDATE_EXERCISE_NAME_SUCCESS", "UPDATE TERMS AND CONDITIONS SUCCESS", {} , "0000"
        )
        try:
            
            exercise_name_html = su.unescape(params["exercise_name"])

            clean = re.compile('<.*?>')
            params["exercise_name"] = re.sub( clean, '', exercise_name_html)
            

            
            self.mgdDB.db_exercise_name.update_one(
                {"pkey" : params["fk_tnc_id"]},
                {"$set" : {
                    "name"                      : params["name"                 ],
                    "exercise_name_html" : exercise_name_html,
                    "exercise_name"      : params["exercise_name" ],
                    "misc"                      : params["misc"                 ],
                    "kategori"                  : params["kategori"             ]
                }
            })



        except :
            trace_back_msg = traceback.format_exc() 
            self.webapp.logger.debug(traceback.format_exc())

            response.put( "status"      , "UPDATE_EXERCISE_NAME_FAILED" )
            response.put( "desc"        , "UPDATE EXERCISE_NAME FAILED" )
            response.put( "status_code" , "9999" )
            response.put( "data"        , { "error_message" : trace_back_msg })

        # end try
        return response
    # end def

    def _delete(self, params):
        response = helper.response_msg(
            "DELETE_EXERCISE_NAME_SUCCESS", "DELETE TERMS AND CONDITIONS SUCCESS", {} , "0000"
        )

        try:
            
            self.mgdDB.db_exercise_name.update_one(
                { "pkey" : params["fk_exercise_name_pkey"] },
                {"$set" : { 
                    "is_deleted" : True 
                    }
                }
            )

        except :
            trace_back_msg = traceback.format_exc() 
            self.webapp.logger.debug(traceback.format_exc())

            response.put( "status"      , "DELETE_EXERCISE_NAME_FAILED" )
            response.put( "desc"        , "DELETE TERMS AND CONDITIONS FAILED" )
            response.put( "status_code" , "9999" )
            response.put( "data"        , { "error_message" : trace_back_msg })
        # end try
        return response
    # end def



    

# end class
