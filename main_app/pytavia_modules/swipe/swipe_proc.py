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

    def get_user_config(self, params):
        user_type = "premium" if params.get("is_premium") == "TRUE" else "free"
        # Read from database-driven subscription config
        rec = self.mgdDB.db_subscription_config.find_one({"plan": user_type}, {"_id": 0})
        if rec:
            # Normalize keys to expected format
            return {
                "DAILY_SWIPE": int(rec.get("DAILY_SWIPE", 15)),
                "CAN_UNDO_LAST_DISLIKE": bool(rec.get("CAN_UNDO_LAST_DISLIKE", False)),
                "CAN_SEE_WHO_LIKE_USER": bool(rec.get("CAN_SEE_WHO_LIKE_USER", False)),
                "CAN_UPLOAD_ALBUM": bool(rec.get("CAN_UPLOAD_ALBUM", False)),
                "MORE_OFTEN_SEEN": bool(rec.get("MORE_OFTEN_SEEN", False)),
                "GET_INFO_TOTAL_NEW_USER": bool(rec.get("GET_INFO_TOTAL_NEW_USER", False)),
                "CAN_FILTER": bool(rec.get("CAN_FILTER", False)),
            }
        # Safe defaults
        if user_type == "premium":
            return {
                "DAILY_SWIPE": 8,
                "CAN_UNDO_LAST_DISLIKE": True,
                "CAN_SEE_WHO_LIKE_USER": True,
                "CAN_UPLOAD_ALBUM": True,
                "MORE_OFTEN_SEEN": True,
                "GET_INFO_TOTAL_NEW_USER": True,
                "CAN_FILTER": True,
            }
        return {
            "DAILY_SWIPE": 70,
            "CAN_UNDO_LAST_DISLIKE": False,
            "CAN_SEE_WHO_LIKE_USER": False,
            "CAN_UPLOAD_ALBUM": False,
            "MORE_OFTEN_SEEN": False,
            "GET_INFO_TOTAL_NEW_USER": False,
            "CAN_FILTER": False,
        }
    # end def


    def _decision_match(self, params):   
        # Get the user_id of the current session
        user_id = params.get("user_id", "")
        future_wife_id = params.get("future_wife_id", "")
        status = params.get("status", "")

        today_str = datetime.now().strftime('%Y-%m-%d')

        # UNDO SECTION - if future wife id its found remove first 
         # Find the user document by user_id
        user_doc = self.mgdDB.db_users.find_one({"user_id": user_id}, {
            "fk_user_id_like": 1,
            "fk_user_id_dislike": 1
        })

        if user_doc:
            pull_fields = {}

            # Check and prepare $pull if future_wife_id exists in like/dislike
            if future_wife_id in user_doc.get("fk_user_id_like", []):
                pull_fields["fk_user_id_like"] = future_wife_id

            if future_wife_id in user_doc.get("fk_user_id_dislike", []):
                pull_fields["fk_user_id_dislike"] = future_wife_id

            # Perform the pull operation if necessary
            if pull_fields:
                self.mgdDB.db_users.update_one(
                    {"user_id": user_id},
                    {"$pull": pull_fields}
                )
        # END REMOVE IF UNDO

        # Cek log swipe hari ini
        log_today = self.mgdDB.db_swipe_logs_daily.find_one({
            "user_id": user_id,
            "date": today_str
        })

        if log_today:            
            user_config = self.get_user_config(params)
            daily_limit = user_config["DAILY_SWIPE"]
          

            if log_today["swipe_count"] >= daily_limit:
                return {"status": "limit_exceeded", "message": "Daily swipe limit reached."}
            
            # Update swipe count
            self.mgdDB.db_swipe_logs_daily.update_one(
                {"user_id": user_id, "date": today_str},
                {"$inc": {"swipe_count": 1}, "$set": {"updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}
            )
        else:
            # Insert log baru
            self.mgdDB.db_swipe_logs_daily.insert_one({
                "user_id": user_id,
                "date": today_str,
                "swipe_count": 1,
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
                        

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

            # Step 3: Remove `user_id` from the match too
            self.mgdDB.db_users.update_one(
                {"user_id": future_wife_id},
                {"$pull": {"fk_user_id_like":user_id }}  # Remove matched ID
            )

            match_data.pop("_id", None)

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
