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

class view_swipe:

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

        return render_template(
            "users/swipe.html",
            menu_list_html      = menu_list               ,
            core_display        = core_display            , 
            core_header         = core_header             , 
            core_footer         = core_footer             , 
            core_script         = core_script             , 
            core_css            = core_css                , 
            core_dialog_message = core_dialog_message     ,                      
            
        )                
    # end def   


    def _find_potential_match(self, params):
        now            = utils._get_current_datetime(hours = config.JKTA_TZ)
        timestamp      = utils._convert_datetime_to_timestamp(now)
        
        # Define the age range
        min_age = 0
        max_age = 50

        # Calculate birthdate range
        today = datetime.today()
        max_birthdate = today - timedelta(days=(min_age * 365))  # Oldest date of birth allowed
        min_birthdate = today - timedelta(days=(max_age * 365))  # Youngest date of birth allowed

        query = {                         
            "is_deleted": False,
            "fk_user_id_like": { "$not": { "$elemMatch": { "$eq": params['user_id'] } } },
            "fk_user_id_dislike": { "$not": { "$elemMatch": { "$eq": params['user_id'] } } },
            "dob": { 
                "$gte": min_birthdate.strftime("%Y-%m-%d"),  # Users must be at least min_age
                "$lte": max_birthdate.strftime("%Y-%m-%d")   # Users must be at most max_age
            }
        }

        # user_view = self.mgdDB.db_users.find(
        #     query,
        #     {
        #         "name": 1,
        #         "profile_photo": 1,
        #         "username": 1,
        #         "email": 1,
        #         "pkey": 1,
        #         "dob": 1,  # Include DOB for reference
        #         "_id": 0
        #     }
        # )

        
        # Step 1: Find all user_ids that appear in fk_user_id_like or fk_user_id_dislike for the given user_id
        blocked_users = self.mgdDB.db_users.aggregate([
            {
                "$match": { "user_id": params['user_id'] }  # Filter to only the specified user_id
            },
            {
                "$group": {
                    "_id": None,
                    "blocked_ids": { "$push": { "$concatArrays": ["$fk_user_id_like", "$fk_user_id_dislike"] } }
                }
            }
        ])

        # Extract and flatten blocked user IDs
        blocked_ids = []
        for doc in blocked_users:
            for user_list in doc.get("blocked_ids", []):  # Iterate through the nested lists
                blocked_ids.extend(user_list)  # Flatten the list

        # Block himself
        blocked_ids.append(params['user_id'])

        # Block because already match        
        current_user_id = params['user_id']

        # Query the db_matches collection for matches involving the current_user_id
        matches = self.mgdDB.db_matches.find({
            '$or': [
                {'user_id_1': current_user_id},
                {'user_id_2': current_user_id}
            ]
        })

        # Iterate over the matched documents
        for match in matches:
            # Determine the counterpart user_id
            if match['user_id_1'] == current_user_id:
                counterpart_user_id = match['user_id_2']
            else:
                counterpart_user_id = match['user_id_1']
            
            # Append the counterpart user_id to the blocked_ids list
            blocked_ids.append(counterpart_user_id)

        # blocked_ids now contains all user IDs matched with the current_user_id
        

        print("Blocked IDs:", blocked_ids)  # Debugging - should print a flat list of IDs

        # Step 2: Get the sex of the current user
        current_user = self.mgdDB.db_users.find_one({ "user_id": params['user_id'] }, { "sex": 1 })

        if current_user:
            current_sex = current_user.get("sex")
            target_sex = "female" if current_sex == "male" else "male"  # Search for opposite sex
        else:
            target_sex = None  # If sex is not found, don't filter by sex

        # Step 3: Exclude blocked users and filter by opposite sex
        match_query = {
            "user_id": { "$nin": blocked_ids }
        }

        if target_sex:  # Apply sex filter only if sex is found
            match_query["sex"] = target_sex

        user_view = self.mgdDB.db_users.aggregate([
            { "$match": match_query },
            {
                "$project": {
                    "name": 1,
                    "user_id": 1,
                    "img": {  
                        "$concat": [
                            config.G_IMAGE_URL_DISPATCH,  
                            "$profile_photo"  
                        ]
                    },
                    "username": 1,
                    "email": 1,
                    "pkey": 1,
                    "dob": 1,
                    "sex": 1,
                    "_id": 0
                }
            }
        ])

        response = list(user_view)
        
        return response
    # end def
# end class
