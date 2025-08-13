import sys
import traceback
import time
import json
import datetime
import statistics
from bson import Int64

sys.path.append("pytavia_core"    )
sys.path.append("pytavia_modules" )
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib"  )
sys.path.append("pytavia_storage" )
sys.path.append("pytavia_modules/view" )

from flask          import render_template
from flask          import session
from pytavia_stdlib import idgen
from pytavia_stdlib import utils
from pytavia_core   import database
from pytavia_core   import config

from view import view_core_menu
from view import view_core_display
from view import view_core_header
from view import view_core_footer
from view import view_core_script
from view import view_core_css
from view import view_core_dialog_message

class view_profile_intro:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def html(self, params):
        menu_list               = view_core_menu.view_core_menu().html(params)
        core_display            = view_core_display.view_core_display().html(params)
        params["core_display"]  = core_display         
        core_header             = view_core_header.view_core_header().html(params)
        core_footer             = view_core_footer.view_core_footer().html(params)
        core_script             = view_core_script.view_core_script().html(params)
        core_css                = view_core_css.view_core_css().html(params)
        core_dialog_message     = view_core_dialog_message.view_core_dialog_message().html(params)                  

        data_user        = self.data_user( params )

        # Fetch city list from DB instead of config
        city_docs = list(self.mgdDB.db_city_list.find({}, {"_id": 0, "name": 1}).sort("name", 1))
        city_list = [c.get("name") for c in city_docs]

        return render_template(
            "users/profile_intro.html",
            menu_list_html      = menu_list               ,
            core_display        = core_display            , 
            core_header         = core_header             , 
            core_footer         = core_footer             , 
            core_script         = core_script             , 
            core_css            = core_css                , 
            core_dialog_message = core_dialog_message     , 
            data_user           = data_user,        
            image_base_url      = config.G_IMAGE_URL_DISPATCH,
            city_list           = city_list  
        )                
    # end def
    def data_user(self,params):              
        query = { "user_id": params["user_id"]}
        user = self.mgdDB.db_users.find_one(query)       
              
        if user['profile_photo'] != None:
            user["profile_photo"] = config.G_IMAGE_URL_DISPATCH + user["profile_photo"]

        return user
# end class
