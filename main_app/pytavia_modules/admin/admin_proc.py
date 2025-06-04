import config_core
import sys
import traceback
from datetime import datetime, timedelta
import random
import time

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
from xml.sax            import saxutils as su

class admin_proc:

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

    def _apply_premium(self, params):
        response = helper.response_msg(
            "UPDATE_PROFILE_SUCCESS", "UPDATE PROFILE SUCCESS", {}, "0000"
        )
        try:
            print(params)
            print("check it")
            user_id = params.get("customer_id", "")
            subscription_type = params.get("subscription_type", "1_month")
            duration_months = int(params.get("duration", ""))

            now = datetime.now()
            expiry_date = now + timedelta(days=30 * duration_months)

            # === Update field premium langsung via Mongo ===
            self.mgdDB.db_users.update(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_premium": "TRUE",
                        "subscription_type": "premium",
                        "premium_expiry": expiry_date.strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
            )

            # Simpan ke log
            mdl_log = database.new(self.mgdDB, "db_premium_logs")
            log_premium_id          = mdl_log.get()["pkey"]
                        
            mdl_log.put("log_premium_id", log_premium_id)
            mdl_log.put("user_id", user_id)
            mdl_log.put("type", subscription_type)
            mdl_log.put("start_at", now.strftime('%Y-%m-%d %H:%M:%S'))
            mdl_log.put("end_at", expiry_date.strftime('%Y-%m-%d %H:%M:%S'))
            mdl_log.put("created_at", now.strftime('%Y-%m-%d %H:%M:%S'))
            mdl_log.insert()

            # Ambil ulang data user
            user_data = self.mgdDB.db_users.find_one({"user_id": user_id})
            response.put("data", user_data)

        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)

            response.put("status", "EDIT_PROFILE_FAILED")
            response.put("desc", "EDIT PROFILE FAILED")
            response.put("status_code", "9999")
            response.put("data", {"error_message": trace_back_msg})
        
        return response



