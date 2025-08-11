import sys
import traceback
import datetime
import time
import ast # use to convert string to dictionary 
from   datetime import datetime
import random
import string

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

from cryptography.fernet import Fernet
from urllib.parse import unquote_plus  # 

class auth_proc:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def
    
    def log_login(self,params):
        fk_user_id = params["fk_user_id" ] if "fk_user_id" in params else None
        state      = params["state"      ] if "state"      in params else None
        desc       = params["desc"       ] if "desc"       in params else None     
        username   = params["username"   ] if "username"   in params else None     
        log_login_rec  = database.get_record("db_log_login_auth")
        log_login_rec["fk_user_id" ] = fk_user_id
        log_login_rec["username"   ] = username
        log_login_rec["desc"       ] = desc
        log_login_rec["state"      ] = state
        self.mgdDB.db_log_login_auth.insert( log_login_rec )
        
        return True
    #end def
    
    def validate_wrong_counter(self,params):
        params_log ={
            "fk_user_id" : "",
            "state"      : "",
            "des"        : ""
        }
        username        = params["username"   ]
        state_login     = params["state_login"]        
        current_date    = int(time.time())
        day_reset_wrong_counter = 0 
        limit_wrong_counter     = 0        
        
        limit_wrong_counter_rec = self.mgdDB.db_setting_app.find_one(
                {},{"wrong_counter" : 1 , "_id" : 0}
        )
        
        if "wrong_counter" in limit_wrong_counter_rec:
            limit_wrong_counter = limit_wrong_counter_rec["wrong_counter"]
        # end if
        user_auth_rec = self.mgdDB.db_user_auth.find_one({ 
            "username" : username 
        })              
        
        if user_auth_rec  == None:
            params_log["state_login" ] = state_login
            params_log["fk_user_id"  ] = None
            params_log["desc"        ] = "Failed in validate username"
            self.log_login(params_log)
            return False
        #end if
        
        user_role_rec = self.mgdDB.db_user_role.find_one({
            "fk_user_id" : user_auth_rec["fk_user_id"]
        }) 
        
        config_role_rec = self.mgdDB.db_config_role.find_one({
            "value" : user_role_rec["role"]
        })         
               
        if state_login == "LOGIN_SUCCESS":            
            role_misc               = ast.literal_eval(config_role_rec["misc"])  
            wrong_counter           = user_auth_rec["wrong_counter"     ]
            date_last_failed_login  = user_auth_rec["date_failed_login" ]
            
            if "reload_wrong_counter" in role_misc:
                day_reset_wrong_counter = role_misc["reload_wrong_counter"] 
            # end if        
            if date_last_failed_login == None or date_last_failed_login == 0:
                date_last_failed_login = current_date
            # end if
            
            date_last_failed_login = datetime.fromtimestamp(date_last_failed_login)
            current_date           = datetime.fromtimestamp(current_date)
            totaldays              = (current_date - date_last_failed_login).days
            if int(totaldays) >= int(day_reset_wrong_counter):
                wrong_counter = 0
            #end if

            self.mgdDB.db_user_auth.update(
                {"username" : username},
                { "$set"    : {
                        "wrong_counter"     : wrong_counter,
                        "date_failed_login" : 0 ,
                        "login_status"      : "TRUE",
                        "forced_logout"     : "FALSE"
                    }
                }
            )   
            
            params_log["state_login" ] = state_login
            params_log["fk_user_id"  ] = user_auth_rec["fk_user_id"]
            params_log["desc"        ] = "login success"
            self.log_login(params_log)            
            return True
         
        """ 
         - Status login failed and user_auth is exist
        """
        if user_auth_rec["lock"] != "TRUE":
            self.mgdDB.db_user_auth.update(
                {"username" : username},
                { "$set" : {
                        "wrong_counter"     : int(user_auth_rec["wrong_counter"]) + 1,
                        "date_failed_login" : current_date
                    }
                }
            )
        #end if
            
        if int(user_auth_rec["wrong_counter"]) >= int(limit_wrong_counter) : 
            self.mgdDB.db_user_auth.update(
                {"username" : username},
                {"$set"     : {"lock" : "TRUE"}}                    
            )
        #end if
        
        params_log["state_login" ] = state_login
        params_log["fk_user_id"  ] = user_auth_rec["fk_user_id"]
        params_log["desc"        ] = "Failed in validate password"
        self.log_login(params_log)
        
        return False 
    #end def
    
    def logout(self, params):
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "LOGOUT_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }

        self.webapp.logger.debug( "auth logout params ---------------------------------------------" )
        self.webapp.logger.debug( params )
        self.webapp.logger.debug( "---------------------------------------------" )    

        try:
            fk_user_id = params["fk_user_id"]            
            self.mgdDB.db_users.update(
                {"pkey" : fk_user_id},
                { "$set"    : {
                        "login_status"      : "FALSE"
                    }
                }
            )
            
            self.mgdDB.db_cookies.update(
                {
                    "fk_user_id" : fk_user_id,
                    "active"     : "TRUE"
                },
                { "$set"    : {
                        "active" : "FALSE"
                    }
                }
            )
            
        except:
            print (traceback.format_exc())
            response["message_action"] = "LOGOUT_FAILED"
            response["message_action"] = "LOGOUT_FAILED: " + str(sys.exc_info())
        # end try
        return response

    def login(self, params) :
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "LOGIN_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }

        try:
            login_identifier = params.get("txt_l_username", "").strip()
            password         = params.get("txt_l_password", "")

            browser         = request.user_agent.browser
            xff             = request.remote_addr

            # Find user by username or email first
            user_rec = self.mgdDB.db_users.find_one({
                "$or": [
                    {"username": login_identifier},
                    {"email": login_identifier}
                ]
            })

            error_msg_rec = None
            if user_rec is None:
                # User not found
                error_msg_rec = self.mgdDB.db_config_general.find_one({"value": "ERROR_LOGIN_TYPE_001"})
            else:
                # Hash using the actual username stored for the user
                hashed_password = utils._get_passwd_hash({
                    "id": user_rec["username"],
                    "password": password
                })
                if user_rec.get("password") != hashed_password:
                    # Wrong password
                    error_msg_rec = self.mgdDB.db_config_general.find_one({"value": "ERROR_LOGIN_TYPE_001"})
                else:
                    # super admin validation
                    if user_rec['sex'] == "superadmin":
                        user_rec["role"] = "superadmin"
                    else:
                        user_rec["role"] = "customer"

                    # Premium expiry check
                    premium_expiry_str = user_rec.get("premium_expiry", "")
                    is_premium = user_rec.get("is_premium", "FALSE")

                    update_fields = {
                        "login_status": "TRUE"
                    }

                    if is_premium == "TRUE" and premium_expiry_str:
                        try:
                            expiry_date = datetime.strptime(premium_expiry_str, '%Y-%m-%d %H:%M:%S')
                            if datetime.now() > expiry_date:
                                update_fields["is_premium"] = "FALSE"
                                update_fields["subscription_type"] = "expired"
                        except Exception as e:
                            self.webapp.logger.debug(f"[Premium Check] Error: {e}")

                    # Final update
                    self.mgdDB.db_users.update_one(
                        {"pkey": user_rec["pkey"]},
                        {"$set": update_fields}
                    )

                    response["message_action"] = "LOGIN_SUCCESS"
                    response["message_code"  ] = ""
                    response["message_title" ] = ""
                    response["message_desc"  ] = ""
                    response["message_data"  ] = {
                        "fk_user_id"      : user_rec["pkey"                 ],
                        "user_id"         : user_rec["user_id"              ],
                        "username"        : user_rec["username"             ],                                        
                        "email"           : user_rec["email"                ],
                    "verify_email"    : user_rec["verify_email"         ],
                    "profile_intro"   : user_rec["profile_intro"        ],
                    "is_premium"      : user_rec["is_premium"           ],
                    "role"            : user_rec["role"                 ],
                }
                return response

                #end if                 

            #endif

            if error_msg_rec != None :
                response["message_action"] = "LOGIN_FAILED"
                response["message_code"  ] = error_msg_rec["misc"]
                response["message_title" ] = error_msg_rec["name"]
                response["message_desc"  ] = error_msg_rec["desc"]

                       
        # end try
        except :
            self.webapp.logger.debug (traceback.format_exc())
            response["message_action"] = "LOGOUT_FAILED"
            response["message_desc"  ] = "LOGOUT_FAILED: " + str(sys.exc_info())

        #end except     
        return response
    #end def

    def register_superuser(self, params):
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "REGISTER_SUPERUSER_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }
        try:
            username        = params["username"]
            password        = params["password"]
            role            = params["role"    ]
            hashed_password = utils._get_passwd_hash({
                "id"        : username,
                "password"  : password
            })
            super_user_rec  = self.mgdDB.db_super_user.find_one({
                "username"  : username
            })
            if super_user_rec != None:
                response["message_action"] = "REGISTER_SUPERUSER_FAILED"
                response["message_code"  ] = "1"
                response["message_desc"  ] = "username already taken"
                return response
            # end if
            super_user_rec = database.get_record("db_super_user")
            super_user_rec["username"] = username
            super_user_rec["password"] = hashed_password
            super_user_rec["role"    ] = role
            self.mgdDB.db_super_user.insert( super_user_rec )
        except:
            print (traceback.format_exc())
            response["message_action"] = "REGISTER_SUPERUSER_FAILED"
            response["message_action"] = "REGISTER_SUPERUSER_FAILED: " + str(sys.exc_info())
        # end try
        return response
    # end def

    def register(self, params):
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "REGISTER_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }
        try:
            username = params["username"]
            password = params["password"]
            email = params["email"]

            # Validate password length
            if len(password) < 8:
                response["message_action"] = "REGISTER_USER_FAILED"
                response["message_code"] = "1"
                response["message_desc"] = "Password min 8 karakter"
                return response

            # Validate password length
            if len(username) < 5:
                response["message_action"] = "REGISTER_USER_FAILED"
                response["message_code"] = "1"
                response["message_desc"] = "Username min 5 karakter"
                return response

            # Validate username contains no punctuation
            if any(char in string.punctuation for char in username):
                response["message_action"] = "REGISTER_USER_FAILED"
                response["message_code"] = "1"
                response["message_desc"] = "Username tidak mengadung tanda baca"
                return response

            hashed_password = utils._get_passwd_hash({
                "id": username,
                "password": password
            })

            user_rec = self.mgdDB.db_users.find_one({
                "$or": [
                    {"email": email},
                    {"username": username}
                ]
            })

            if user_rec is not None:
                response["message_action"] = "REGISTER_USER_FAILED"
                response["message_code"] = "1"
                response["message_desc"] = "Username atau email sudah ada"
                return response
            # end if                     

            mdl_register_user   = database.new(self.mgdDB, "db_users")            
            user_id          = mdl_register_user.get()["pkey"]
            
            
            mdl_register_user.put( "user_id", user_id )            
            mdl_register_user.put( "username", username    )
            mdl_register_user.put( "email"   , email)                  
            mdl_register_user.put( "password" , hashed_password)
            mdl_register_user.insert()         
        except:
            print(traceback.format_exc())
            response["message_action"] = "REGISTER_USER_FAILED"
            response["message_desc"] = "REGISTER_USER_FAILED: " + str(sys.exc_info())
        # end try
        return response
    # end def

    def check_step(self, params):
        if params.get('role') == "superadmin":            
            return '/admin/panel/customer'

        if params.get('verify_email') != "TRUE":
            self.send_verification_email(params)
            return '/otp_email'
        
        if params.get('profile_intro') != "TRUE":
            return '/profile_intro'

        return '/swipe'
        #end def

    def send_verification_email(self, params):
        result_url = "/user/dashboard"
        
        unique_4_number             = random.randint(100000,999999)
        params["unique_4_number"]   = str(unique_4_number)

        # Get the current date
        verification_date           = datetime.now().strftime('%Y-%m-%d %H:%M:%S')       
    
        # Update the document in MongoDB
        user_rec                    = self.mgdDB.db_users.update_one(
            {"user_id"              : params["user_id"]},
            {"$set"                : {"otp_4_number": unique_4_number}}
        )

        #for send email
        html                        = emailproc.send_verification_email(params)

        return result_url

    def check_verification_email(self, params):
        result = "try_again"

        # Retrieve the user record
        user_rec = self.mgdDB.db_users.find_one({"user_id": params["user_id"]})

        # Check if the provided OTP matches the stored OTP
        if int(params['otp_number']) == user_rec['otp_4_number']:
            # Update the user's email verification status
            self.mgdDB.db_users.update_one(
                {"user_id": params["user_id"]},
                {"$set": {"verify_email": "TRUE"}}
            )
            # Refresh the user record
            user_rec = self.mgdDB.db_users.find_one({"user_id": params["user_id"]})

            result = user_rec


        return result

    def _username_precheck(self, params):        

        # Update the document in MongoDB
        user_rec                    = self.mgdDB.db_users.find_one(
            {"username"           : params["username"]},{"_id":0,"username":1,"user_uuid":1,"fk_user_id":1}        
        )

        return user_rec

    #end def

    def send_reset_password_email(self, params):
        try:
            email = params.get("email")       
            base_url = "https://yourwebsite.com/emailverify"                
            
            # Send email
            email_sent = emailproc.send_reset_password_via_email(params)            
            
            if email_sent == 'success':
                return "success" 
            return "failed"                 
        except Exception as e:
            print(f"Error in send_reset_password_email: {e}")
            return "failed"
    #end def

    def confirm_new_password(self, params):
        try:
            print(params)
            print("atas adalah params")

            # Decrypt token_reset_ps
            SECRET_KEY = b'KD1wZ6X1zRb9-jVnTr_a3C_sPlkDdGo5aMu8Hq4FR3A='  # Your actual Fernet key
            fernet = Fernet(SECRET_KEY)

            encrypted_token = params.get("token_reset_ps")
            if not encrypted_token:
                return "Missing token."

            # ✅ URL decode the token (important!)
            encrypted_token = unquote_plus(encrypted_token)

            # Decrypt and extract email
            try:
                decrypted_payload = fernet.decrypt(encrypted_token.encode()).decode()
                email, timestamp = decrypted_payload.split("|")
                print("Decrypted email:", email)
            except Exception as e:
                print(f"Failed to decrypt token: {e}")
                return "Invalid or expired token."

            user_rec = self.mgdDB.db_users.find_one(
                {"email": email},
                {"username": 1, "_id": 0}
            )
            print(user_rec)

            # Validate passwords
            new_password = params.get("NewPassword")
            confirm_password = params.get("ConfirmPassword")

            hashed_password   = utils._get_passwd_hash({"id": user_rec['username'], "password": new_password})   

            if new_password != confirm_password:
                return "Passwords do not match."

            # Update user password in DB
            print(hashed_password)
            print("new hash")
            try:
                self.mgdDB.db_users.update_one(
                    {"email": email},
                    {
                        "$set": {
                            "password": hashed_password,  # Hash in production!
                            "is_confirm": "TRUE"
                        }
                    }
                )
                return "SUCCESS_CONFIRMATION"
            except Exception as e:
                print(f"DB error: {e}")
                return "FAILED_CONFIRMATION"

        except Exception as e:
            print(f"Error in confirm_new_password: {e}")
            return "Error processing verification email."


# end class

