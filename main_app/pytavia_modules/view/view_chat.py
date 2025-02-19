import sys
import traceback
import time
import json
import datetime
import statistics
from bson import Int64
from datetime import datetime, timedelta

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

class view_chat:

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

        _find_chat              = self._find_chat(params)

        return render_template(
            "users/chat.html",
            menu_list_html      = menu_list               ,
            core_display        = core_display            , 
            core_header         = core_header             , 
            core_footer         = core_footer             , 
            core_script         = core_script             , 
            core_css            = core_css                , 
            core_dialog_message = core_dialog_message     ,    
            find_chat          = _find_chat             ,
            img_dispatch_url    = config.G_IMAGE_URL_DISPATCH,
            socketio_chat_server= config.G_CHAT_URL_DISPATCH,
            sender_id           = params['user_id']
            
        )                
    # end def   


    def _find_chat(self, params):
        user_id = params["user_id"]

        # Find all chats where the user is the receiver (opponent's messages)
        chats = list(self.mgdDB.db_chat.find({"receiver_user_id": user_id}).sort("timestamp", -1))

        match_data = {}

        for chat in chats:
            match_id = chat["match_id"]
            sender_id = chat["sender_user_id"]

            # Fetch sender name from db_users
            sender = self.mgdDB.db_users.find_one({"user_id": sender_id}, {"name": 1,"_id":0,"profile_photo":1})
            sender_name = sender["name"] if sender else "Unknown"            
            print(sender)
            # If match_id not in match_data, store the latest message
            if match_id not in match_data:
                match_data[match_id] = {
                    "match_id": match_id,
                    "user_id": user_id,  # Opponent's ID
                    "sender_name": sender_name,  # Opponent's name
                    "img": sender['profile_photo'],  # Opponent's name
                    "is_read": chat["is_read"],
                    "latest_message": chat["message"],
                    "latest_timestamp": chat["timestamp"],
                    "unread_count": 0  # Initialize unread count
                }

            # Count unread messages (is_read: False) per match
            if not chat["is_read"]:
                match_data[match_id]["unread_count"] += 1

        response = {"chats": list(match_data.values())}  # Convert dict to list

        return response
# end class
