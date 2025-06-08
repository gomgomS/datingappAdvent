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

class view_match:

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

        _find_match             = self._find_match(params)
        _find_likes_for_me      = self._find_likes_for_me(params)

        return render_template(
            "users/match.html",
            menu_list_html      = menu_list               ,
            core_display        = core_display            , 
            core_header         = core_header             , 
            core_footer         = core_footer             , 
            core_script         = core_script             , 
            core_css            = core_css                , 
            core_dialog_message = core_dialog_message     ,    
            find_match          = _find_match             ,
            find_likes_for_me   = _find_likes_for_me      ,
            img_dispatch_url    = config.G_IMAGE_URL_DISPATCH,
            socketio_chat_server= config.G_CHAT_URL_DISPATCH,
            sender_id           = params['user_id']
        )                
    # end def   



    def _find_match(self, params):        
        
        # The user_id you're searching for
        user_id = params['user_id']

        # Aggregation pipeline
        pipeline = [
            {
                '$match': {
                    '$or': [
                        {'user_id_1': user_id},
                        {'user_id_2': user_id}
                    ]
                }
            },
            {
                '$lookup': {
                    'from': 'db_users',
                    'let': {
                        'uid1': '$user_id_1',
                        'uid2': '$user_id_2'
                    },
                    'pipeline': [
                        {
                            '$match': {
                                '$expr': {
                                    '$or': [
                                        {'$and': [
                                            {'$eq': ['$user_id', '$$uid1']},
                                            {'$ne': ['$user_id', user_id]}
                                        ]},
                                        {'$and': [
                                            {'$eq': ['$user_id', '$$uid2']},
                                            {'$ne': ['$user_id', user_id]}
                                        ]}
                                    ]
                                }
                            }
                        },
                        {
                            '$project': {
                                '_id': 0,
                                'user_id': 1,
                                'name': 1,
                                'email': 1,
                                'profile_photo': 1
                            }
                        }
                    ],
                    'as': 'matched_user_details'
                }
            },
            {
                '$unwind': '$matched_user_details'
            },
            {
                '$project': {
                    '_id': 0,
                    'match_id': 1,
                    'is_mutual': 1,
                    'created_at': 1,
                    'matched_user': '$matched_user_details'
                }
            }
        ]

        # Execute the aggregation pipeline
        response = list(self.mgdDB.db_matches.aggregate(pipeline))                    
        print(response)
        print("Minggir")
        
        return response
    # end def

    def _find_likes_for_me(self, params):
        user_id = params['user_id']

        pipeline = [
            {
                '$match': {
                    'fk_user_id_like': user_id
                }
            },                  
            {
                '$project': {
                    '_id': 0,
                    'user_id': 1,
                    'name': 1,
                    'email': 1,
                    'profile_photo': 1,
                    'job': 1,
                    'city': 1,
                    'tribe': 1,
                    'marital_status': 1,
                    'hobbies': 1,
                    'about': 1                   
                }
            }
        ]

        response = list(self.mgdDB.db_users.aggregate(pipeline))
        return response

# end class
