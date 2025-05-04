import config_core
import sys
import traceback
import random
import time    
from datetime import datetime
from bson.objectid import ObjectId

sys.path.append("pytavia_core"    )
sys.path.append("pytavia_modules" )
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib"  )
sys.path.append("pytavia_storage" )

from pytavia_stdlib   import idgen
from pytavia_stdlib   import utils
from pytavia_core     import database
from pytavia_core     import helper
from pytavia_core     import config
from pytavia_stdlib   import cfs_lib

class swipe_proc:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def validate_username(self, params) :
        username = params["add_username"]

        check_username = self.mgdDB.db_user.find_one({ "username" : username, "type" : "BO" })
        if check_username != None :
            return False
        else :
            return True


    # end def

    def _decision_match(self, params):        
        # Get the user_id of the current session
        user_id = params.get("user_id", "")
        future_wife_id = params.get("future_wife_id", "")
        status = params.get("status", "")

        # Determine which field to update
        if status == "acc":
            update_field = "fk_user_id_like"
        else:
            update_field = "fk_user_id_dislike"

        # Step 1: Check if `user_id` is already inside `fk_user_id_like` of `future_wife_id`
        future_wife = self.mgdDB.db_users.find_one({"user_id": future_wife_id}, {"fk_user_id_like": 1})

        if future_wife and user_id in future_wife.get("fk_user_id_like", []):
            # Step 2: Match Found! Insert into `db_matches`
            match_data = {
                "match_id": str(ObjectId()),  # Generate a unique match ID
                "user_id_1": user_id,
                "user_id_2": future_wife_id,
                "is_mutual": "TRUE",
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.mgdDB.db_matches.insert_one(match_data)

            # Step 3: Remove `future_wife_id` from `fk_user_id_like` of `user_id`
            self.mgdDB.db_users.update_one(
                {"user_id": user_id},
                {"$pull": {"fk_user_id_like": future_wife_id}}  # Remove matched ID
            )

            return {"status": "match_found", "message": "Mutual match created!", "match_data": match_data}

        # Step 4: If no match, just update the like/dislike list
        self.mgdDB.db_users.update_one(
            {"user_id": user_id},
            {
                "$push": {update_field: future_wife_id}, 
                "$set": {"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            }
        )

        return {"status": "success", "message": f"User {future_wife_id} added to {update_field}"}

    def _detail_match(self, params):        
        # Get the user_id of the current session        
        future_soulmate_id = params.get("future_soulmate_id", "")
            
        # Step 1: Check if `user_id` is already inside `fk_user_id_like` of `future_soulmate_id`
        future_soulmate_rec = self.mgdDB.db_users.find_one({"user_id": future_soulmate_id})

        # Convert ObjectId fields to string before returning
        if future_soulmate_rec:
            future_soulmate_rec = {k: str(v) if isinstance(v, ObjectId) else v for k, v in future_soulmate_rec.items()}
     
        return {"status": "success", "data": future_soulmate_rec }


# end class
