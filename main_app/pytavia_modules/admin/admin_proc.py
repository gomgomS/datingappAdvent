import config_core
import sys
import traceback
from datetime import datetime, timedelta
import random
import time
import re

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
            request_id = params.get("request_id", "")
            approved_by = params.get("approved_by", "")

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
            if request_id:
                mdl_log.put("request_id", request_id)
            if approved_by:
                mdl_log.put("approved_by", approved_by)
            mdl_log.put("duration_months", duration_months)
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

    def _update_user_admin(self, params):
        response = {
            "status": "FAILED",
            "desc": "",
            "data": {}
        }
        try:
            # Value provided by admin; could be intended as a new username
            username = params.get("username", "").strip()
            new_password = (params.get("new_password") or "").strip()
            new_sex = (params.get("sex") or "").strip()
            new_email = (params.get("email") or "").strip()
            new_dob = (params.get("dob") or "").strip()
            user_id = (params.get("user_id") or "").strip()

            if not username and not user_id:
                response["desc"] = "Missing username or user_id"
                return response

            update_fields = {}
            
            # Locate the existing user first to get the current username
            query = {"user_id": user_id} if user_id else {"username": username}
            existing_user = self.mgdDB.db_users.find_one(query)
            if not existing_user:
                response["desc"] = "User not found"
                return response
            existing_username = existing_user.get("username", "").strip()

            # If admin provided a different username, include it in the update
            if username and existing_username and username != existing_username:
                update_fields["username"] = username

            if new_password:
                if len(new_password) < 8:
                    response["desc"] = "Password must be at least 8 characters"
                    return response
                # Use the TARGET username for hashing: the new one if it will be updated,
                # otherwise the existing username in DB. This avoids login mismatch.
                username_for_hash = update_fields.get("username", existing_username)
                hashed_password = utils._get_passwd_hash({
                    "id": username_for_hash,
                    "password": new_password
                })
                update_fields["password"] = hashed_password
            
            if new_sex:
                # Only allow specific values
                if new_sex not in ["male", "female", "superadmin"]:
                    response["desc"] = "Invalid sex value"
                    return response
                update_fields["sex"] = new_sex

            if new_email:
                # basic email validation
                if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", new_email):
                    response["desc"] = "Invalid email"
                    return response
                update_fields["email"] = new_email

            if new_dob:
                # normalize date to YYYY-MM-DD if possible
                try:
                    dt = datetime.strptime(new_dob, '%Y-%m-%d')
                    update_fields["dob"] = dt.strftime('%Y-%m-%d')
                except Exception:
                    response["desc"] = "Invalid date format (use YYYY-MM-DD)"
                    return response

            if not update_fields:
                response["desc"] = "No changes provided"
                return response

            # Prefer user_id for targeting if provided, fallback to (possibly updated) username
            query = {"user_id": user_id} if user_id else {"username": existing_username or username}
            self.mgdDB.db_users.update_one(query, {"$set": update_fields})

            # Re-read using user_id if available, else by final username
            read_query = {"user_id": user_id} if user_id else {"username": update_fields.get("username", existing_username)}
            user_after = self.mgdDB.db_users.find_one(read_query, {"_id": 0, "username": 1, "sex": 1, "email": 1, "dob": 1})
            response["status"] = "SUCCESS"
            response["data"] = user_after or {}
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _create_user_admin(self, params):
        response = {
            "status": "FAILED",
            "desc": "",
            "data": {}
        }
        try:
            username = (params.get("username") or "").strip()
            password = (params.get("password") or "").strip()
            email = (params.get("email") or "").strip()
            sex = (params.get("sex") or "male").strip()
            dob = (params.get("dob") or "").strip()

            if len(username) < 5:
                response["desc"] = "Username must be at least 5 characters"
                return response
            if any(ch in username for ch in "!@#$%^&*()+=[]{}|\\:;\"'<>,.?/`~"):
                response["desc"] = "Username must not contain punctuation"
                return response
            if len(password) < 8:
                response["desc"] = "Password must be at least 8 characters"
                return response
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                response["desc"] = "Invalid email"
                return response
            if sex not in ["male", "female", "superadmin"]:
                response["desc"] = "Invalid sex value"
                return response

            # Prevent duplicates
            dup = self.mgdDB.db_users.find_one({
                "$or": [
                    {"username": username},
                    {"email": email}
                ]
            })
            if dup is not None:
                response["desc"] = "Username or email already exists"
                return response

            hashed_password = utils._get_passwd_hash({
                "id": username,
                "password": password
            })

            mdl_user = database.new(self.mgdDB, "db_users")
            user_id = mdl_user.get()["pkey"]
            mdl_user.put("user_id", user_id)
            mdl_user.put("username", username)
            mdl_user.put("email", email)
            mdl_user.put("password", hashed_password)
            mdl_user.put("verify_email", "FALSE")
            mdl_user.put("is_premium", "FALSE")
            mdl_user.put("subscription_type", "free")
            mdl_user.put("sex", sex)
            if dob:
                try:
                    dt = datetime.strptime(dob, '%Y-%m-%d')
                    mdl_user.put("dob", dt.strftime('%Y-%m-%d'))
                except Exception:
                    response["desc"] = "Invalid date format (use YYYY-MM-DD)"
                    return response
            mdl_user.insert()

            created = self.mgdDB.db_users.find_one({"user_id": user_id}, {"_id": 0, "user_id": 1, "username": 1, "email": 1, "sex": 1, "dob": 1})
            response["status"] = "SUCCESS"
            response["data"] = created or {}
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _delete_user_admin(self, params):
        response = {
            "status": "FAILED",
            "desc": "",
            "data": {}
        }
        try:
            username = (params.get("username") or "").strip()
            user_id = (params.get("user_id") or "").strip()

            if not username and not user_id:
                response["desc"] = "Missing username or user_id"
                return response

            # Find the user first
            query = {"user_id": user_id} if user_id else {"username": username}
            user_to_delete = self.mgdDB.db_users.find_one(query)
            
            if not user_to_delete:
                response["desc"] = "User not found"
                return response

            # Delete the user
            delete_result = self.mgdDB.db_users.delete_one(query)
            
            if delete_result.deleted_count > 0:
                response["status"] = "SUCCESS"
                response["desc"] = "User deleted successfully"
                response["data"] = {"deleted_user": username or user_id}
            else:
                response["desc"] = "Failed to delete user"
            
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _bulk_delete_users_admin(self, params):
        response = {
            "status": "FAILED",
            "desc": "",
            "data": {}
        }
        try:
            print(f"DEBUG - Bulk delete params: {params}")
            
            # Handle both 'usernames' and 'usernames[]' keys
            usernames = params.get('usernames', [])
            if not usernames:
                usernames = params.get('usernames[]', [])
            
            print(f"DEBUG - Usernames received: {usernames}")
            if not usernames:
                response["desc"] = "No users selected for deletion"
                return response

            # Convert to list if it's a single value
            if isinstance(usernames, str):
                usernames = [usernames]

            deleted_count = 0
            failed_deletions = []

            for username in usernames:
                if not username.strip():
                    continue
                    
                # Find and delete the user
                query = {"username": username.strip()}
                user_to_delete = self.mgdDB.db_users.find_one(query)
                
                print(f"DEBUG - Deleting user: {username.strip()}")
                print(f"DEBUG - User found: {user_to_delete is not None}")
                
                if user_to_delete:
                    delete_result = self.mgdDB.db_users.delete_one(query)
                    print(f"DEBUG - Delete result: {delete_result.deleted_count}")
                    if delete_result.deleted_count > 0:
                        deleted_count += 1
                        print(f"DEBUG - Successfully deleted: {username.strip()}")
                    else:
                        failed_deletions.append(username)
                        print(f"DEBUG - Failed to delete: {username.strip()}")
                else:
                    failed_deletions.append(username)
                    print(f"DEBUG - User not found: {username.strip()}")

            if deleted_count > 0:
                response["status"] = "SUCCESS"
                response["desc"] = f"Successfully deleted {deleted_count} user(s)"
                response["data"] = {
                    "deleted_count": deleted_count,
                    "failed_deletions": failed_deletions
                }
            else:
                response["desc"] = "No users were deleted"
            
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _generate_user_otp(self, params):
        response = {"status": "FAILED", "desc": "", "data": {}}
        try:
            user_id = (params.get("user_id") or "").strip()
            if not user_id:
                response["desc"] = "Missing user_id"
                return response
            otp_val = random.randint(100000, 999999)
            self.mgdDB.db_users.update_one(
                {"user_id": user_id},
                {"$set": {"otp_4_number": otp_val}}
            )
            response["status"] = "SUCCESS"
            response["data"] = {"otp_4_number": otp_val}
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _set_user_otp(self, params):
        response = {"status": "FAILED", "desc": "", "data": {}}
        try:
            user_id = (params.get("user_id") or "").strip()
            otp = (params.get("otp") or "").strip()
            if not user_id:
                response["desc"] = "Missing user_id"
                return response
            if not otp.isdigit() or len(otp) != 6:
                response["desc"] = "OTP must be 6 digits"
                return response
            self.mgdDB.db_users.update_one(
                {"user_id": user_id},
                {"$set": {"otp_4_number": int(otp)}}
            )
            response["status"] = "SUCCESS"
            response["data"] = {"otp_4_number": int(otp)}
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _create_premium_request(self, params):
        response = {
            "status": "FAILED",
            "desc": "",
            "data": {}
        }
        try:
            user_id = params.get("user_id", "").strip()
            username = params.get("username", "").strip()
            name = params.get("name", "").strip()
            email = params.get("email", "").strip()
            phone = params.get("phone", "").strip()
            plan = params.get("plan", "").strip()  # e.g., 1_month, 3_months

            if not (user_id and email):
                response["desc"] = "Missing required fields"
                return response

            now = datetime.now()
            mdl = database.new(self.mgdDB, "db_premium_requests")
            request_id = mdl.get()["pkey"]
            mdl.put("request_id", request_id)
            mdl.put("user_id", user_id)
            mdl.put("username", username)
            mdl.put("name", name)
            mdl.put("email", email)
            mdl.put("phone", phone)
            mdl.put("plan", plan)
            mdl.put("status", "pending")
            mdl.put("created_at", now.strftime('%Y-%m-%d %H:%M:%S'))
            mdl.put("updated_at", now.strftime('%Y-%m-%d %H:%M:%S'))
            mdl.insert()

            response["status"] = "SUCCESS"
            response["data"] = {"request_id": request_id}
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _approve_premium_request(self, params):
        response = {
            "status": "FAILED",
            "desc": "",
            "data": {}
        }
        try:
            request_id = params.get("request_id", "").strip()
            duration = int(params.get("duration", "1"))
            approved_by = params.get("approved_by", "")
            if not request_id:
                response["desc"] = "Missing request_id"
                return response

            req = self.mgdDB.db_premium_requests.find_one({"request_id": request_id})
            if not req:
                response["desc"] = "Request not found"
                return response

            # apply premium
            _ = self._apply_premium({
                "customer_id": req.get("user_id"),
                "subscription_type": req.get("plan", "1_month"),
                "duration": str(duration),
                "request_id": request_id,
                "approved_by": approved_by
            })

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.mgdDB.db_premium_requests.update_one(
                {"request_id": request_id},
                {"$set": {"status": "approved", "duration_months": duration, "approved_by": approved_by, "approved_at": now, "updated_at": now}}
            )

            response["status"] = "SUCCESS"
            response["data"] = {"request_id": request_id}
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _reject_premium_request(self, params):
        response = {"status": "FAILED", "desc": "", "data": {}}
        try:
            request_id = params.get("request_id", "").strip()
            rejected_by = params.get("rejected_by", "")
            if not request_id:
                response["desc"] = "Missing request_id"
                return response
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.mgdDB.db_premium_requests.update_one(
                {"request_id": request_id},
                {"$set": {"status": "rejected", "rejected_by": rejected_by, "rejected_at": now, "updated_at": now}}
            )
            response["status"] = "SUCCESS"
            response["data"] = {"request_id": request_id}
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _subscription_upsert(self, params):
        response = {"status": "FAILED", "desc": "", "data": {}}
        try:
            plan = (params.get("plan") or "").strip()
            if not plan:
                response["desc"] = "Missing plan"
                return response
            doc = {
                "plan": plan,
                "DAILY_SWIPE": int(params.get("DAILY_SWIPE", 15)),
                "CAN_UNDO_LAST_DISLIKE": True if params.get("CAN_UNDO_LAST_DISLIKE") else False,
                "CAN_SEE_WHO_LIKE_USER": True if params.get("CAN_SEE_WHO_LIKE_USER") else False,
                "CAN_UPLOAD_ALBUM": True if params.get("CAN_UPLOAD_ALBUM") else False,
                "MORE_OFTEN_SEEN": True if params.get("MORE_OFTEN_SEEN") else False,
                "GET_INFO_TOTAL_NEW_USER": True if params.get("GET_INFO_TOTAL_NEW_USER") else False,
                "CAN_FILTER": True if params.get("CAN_FILTER") else False,
            }
            self.mgdDB.db_subscription_config.update_one({"plan": plan}, {"$set": doc}, upsert=True)
            response["status"] = "SUCCESS"
            response["data"] = doc
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _subscription_delete(self, params):
        response = {"status": "FAILED", "desc": "", "data": {}}
        try:
            plan = (params.get("plan") or "").strip()
            if not plan:
                response["desc"] = "Missing plan"
                return response
            self.mgdDB.db_subscription_config.delete_one({"plan": plan})
            response["status"] = "SUCCESS"
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _city_add(self, params):
        response = {"status": "FAILED", "desc": "", "data": {}}
        try:
            name = (params.get("name") or "").strip()
            if not name:
                response["desc"] = "Missing name"
                return response
            self.mgdDB.db_city_list.update_one({"name": name}, {"$set": {"name": name}}, upsert=True)
            response["status"] = "SUCCESS"
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _city_delete(self, params):
        response = {"status": "FAILED", "desc": "", "data": {}}
        try:
            name = (params.get("name") or "").strip()
            if not name:
                response["desc"] = "Missing name"
                return response
            self.mgdDB.db_city_list.delete_one({"name": name})
            response["status"] = "SUCCESS"
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _apply_premium_with_transaction_admin(self, params):
        response = {
            "status": "FAILED",
            "desc": "",
            "data": {}
        }
        try:
            import time
            from datetime import datetime, timedelta
            
            customer_id = (params.get("customer_id") or "").strip()
            duration = int(params.get("duration", 1))
            price = float(params.get("price", 0))
            payment_method = (params.get("payment_method") or "").strip()
            notes = (params.get("notes") or "").strip()
            admin_username = (params.get("admin_username") or "").strip()

            if not customer_id:
                response["desc"] = "Missing customer_id"
                return response

            if price <= 0:
                response["desc"] = "Price must be greater than 0"
                return response

            if not payment_method:
                response["desc"] = "Payment method is required"
                return response

            # Find the user first
            user = self.mgdDB.db_users.find_one({"user_id": customer_id})
            if not user:
                response["desc"] = "User not found"
                return response

            # Calculate premium expiry date
            now = datetime.now()
            expiry_date = now + timedelta(days=duration * 30)  # Assuming 30 days per month
            expiry_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")

            # Update user premium status
            update_result = self.mgdDB.db_users.update_one(
                {"user_id": customer_id},
                {
                    "$set": {
                        "is_premium": "TRUE",
                        "premium_expiry": expiry_str,
                        "subscription_type": f"{duration}_months",
                        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )

            if update_result.modified_count == 0:
                response["desc"] = "Failed to update user premium status"
                return response

            # Create transaction record
            transaction_data = {
                "transaction_id": f"TXN_{int(time.time() * 1000)}",
                "user_id": customer_id,
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "transaction_type": "premium_subscription",
                "premium_type": f"{duration}_months",
                "duration_months": duration,
                "price": price,
                "payment_method": payment_method,
                "notes": notes,
                "admin_username": admin_username,
                "status": "completed",
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "expiry_date": expiry_str
            }

            # Insert transaction record
            transaction_result = self.mgdDB.db_trx.insert_one(transaction_data)

            if transaction_result.inserted_id:
                response["status"] = "SUCCESS"
                response["desc"] = f"Premium applied successfully for {duration} month(s)"
                response["data"] = {
                    "transaction_id": transaction_data["transaction_id"],
                    "user_id": customer_id,
                    "username": user.get("username", ""),
                    "duration": duration,
                    "price": price,
                    "expiry_date": expiry_str
                }
            else:
                response["desc"] = "Failed to record transaction"
                
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response

    def _approve_premium_request_with_transaction_admin(self, params):
        response = {
            "status": "FAILED",
            "desc": "",
            "data": {}
        }
        try:
            import time
            from datetime import datetime, timedelta
            
            request_id = (params.get("request_id") or "").strip()
            duration = int(params.get("duration", 1))
            price = float(params.get("price", 0))
            payment_method = (params.get("payment_method") or "").strip()
            notes = (params.get("notes") or "").strip()
            admin_username = (params.get("admin_username") or "").strip()

            if not request_id:
                response["desc"] = "Missing request_id"
                return response

            if price <= 0:
                response["desc"] = "Price must be greater than 0"
                return response

            if not payment_method:
                response["desc"] = "Payment method is required"
                return response

            # Find the premium request first
            premium_request = self.mgdDB.db_premium_requests.find_one({"request_id": request_id})
            if not premium_request:
                response["desc"] = "Premium request not found"
                return response

            # Find the user
            user = self.mgdDB.db_users.find_one({"user_id": premium_request.get("user_id")})
            if not user:
                response["desc"] = "User not found"
                return response

            # Calculate premium expiry date
            now = datetime.now()
            expiry_date = now + timedelta(days=duration * 30)  # Assuming 30 days per month
            expiry_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")

            # Update user premium status
            update_result = self.mgdDB.db_users.update_one(
                {"user_id": premium_request.get("user_id")},
                {
                    "$set": {
                        "is_premium": "TRUE",
                        "premium_expiry": expiry_str,
                        "subscription_type": f"{duration}_months",
                        "updated_at": now.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            )

            if update_result.modified_count == 0:
                response["desc"] = "Failed to update user premium status"
                return response

            # Update premium request status
            self.mgdDB.db_premium_requests.update_one(
                {"request_id": request_id},
                {
                    "$set": {
                        "status": "approved",
                        "approved_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "approved_by": admin_username,
                        "approved_duration": duration
                    }
                }
            )

            # Create transaction record
            transaction_data = {
                "transaction_id": f"TXN_{int(time.time() * 1000)}",
                "request_id": request_id,
                "user_id": premium_request.get("user_id"),
                "username": user.get("username", ""),
                "email": user.get("email", ""),
                "transaction_type": "premium_request_approval",
                "premium_type": f"{duration}_months",
                "duration_months": duration,
                "price": price,
                "payment_method": payment_method,
                "notes": notes,
                "admin_username": admin_username,
                "status": "completed",
                "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "expiry_date": expiry_str
            }

            # Insert transaction record
            transaction_result = self.mgdDB.db_trx.insert_one(transaction_data)

            if transaction_result.inserted_id:
                response["status"] = "SUCCESS"
                response["desc"] = f"Premium request approved successfully for {duration} month(s)"
                response["data"] = {
                    "transaction_id": transaction_data["transaction_id"],
                    "request_id": request_id,
                    "user_id": premium_request.get("user_id"),
                    "username": user.get("username", ""),
                    "duration": duration,
                    "price": price,
                    "expiry_date": expiry_str
                }
            else:
                response["desc"] = "Failed to record transaction"
                
            return response
        except Exception:
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(trace_back_msg)
            response["desc"] = "Internal error"
            return response


