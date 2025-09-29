import json
import time
import pymongo
import sys
import urllib.parse
import base64
import urllib
import ast
import pdfkit
import html as html_unescape
import random
from typing import List
from string import ascii_letters

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from cryptography.fernet import Fernet
from urllib.parse import quote

from urllib.parse import urlencode
from flask_cors import CORS

sys.path.append("pytavia_core")
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib")
sys.path.append("pytavia_storage")
sys.path.append("pytavia_modules")
sys.path.append("pytavia_modules/auth")
sys.path.append("pytavia_modules/configuration")
sys.path.append("pytavia_modules/cookie")
sys.path.append("pytavia_modules/middleware")
sys.path.append("pytavia_modules/security")
sys.path.append("pytavia_modules/user")
sys.path.append("pytavia_modules/view")



##########################################################
from pytavia_core       import database
from pytavia_core       import config
from pytavia_core       import helper

from pytavia_stdlib     import utils
from pytavia_stdlib     import cfs_lib
from pytavia_stdlib     import idgen
from pytavia_stdlib     import sanitize
from pytavia_stdlib     import security_lib
from pytavia_stdlib     import emailproc


##########################################################
from auth               import auth_util
from auth               import auth_proc
from configuration      import config_all
from configuration      import config_config_general
from configuration      import config_menu_webapp_item_all
from configuration      import config_setting_menu
from configuration      import config_setting_security_timeout


from cookie             import cookie_engine
from middleware         import browser_security
from security           import security_login
from user               import user_proc

from view               import view_config
from view               import view_config_add_new
from view               import view_config_add_webapp_menu
from view               import view_config_edit_existing
from view               import view_config_general
from view              import view_config_role
from view               import view_config_setting_menu
from view               import view_dashboard
from view               import view_login
from view               import view_signup
from view               import view_forgetpassword
from view               import view_resetpassword
from view               import view_otp_email


from view               import view_error_page


##########################################################
# LANDINGPAGE
##########################################################

from view               import view_landing_page

##########################################################
# PROFILE
##########################################################

from view               import view_profile_intro
from _profile            import profile_proc

##########################################################
# SWIPE
##########################################################

from view               import view_swipe
from swipe              import swipe_proc

##########################################################
# match
##########################################################

from view               import view_match

##########################################################
# premium
##########################################################

from view               import view_premium

##########################################################
# chat
##########################################################

from view               import view_chat

##########################################################
# ADMIN
##########################################################

from view               import view_admin_panel_customer
from view               import view_admin_panel_premium_control
from view               import view_admin_panel_matches
from view               import view_admin_user_detail
from view               import view_admin_dashboard
from view               import view_admin_database_cleanup

from admin              import admin_proc

##########################################################
# DATINGAPP
##########################################################

from view               import view_general_config
from view               import view_config_menu
from view               import view_config_menu_permission
from view               import view_config_starter
from view               import view_starter

from configuration      import config_menu_proc
from configuration      import config_menu_permission_proc
from configuration      import config_starter_proc

##########################################################
# USERS
##########################################################



from flask              import request
from flask              import render_template
from flask              import Flask
from flask              import session
from flask              import make_response
from flask              import redirect
from flask              import url_for
from flask              import flash, get_flashed_messages
from flask              import abort
from flask              import jsonify 

from wtforms            import ValidationError

from flask_wtf.csrf     import CSRFProtect
from flask_wtf.csrf     import CSRFError

#
# Main app configurations
#
app                   = Flask( __name__, config.G_STATIC_URL_PATH )
app.secret_key        = config.G_FLASK_SECRET
app.session_interface = cookie_engine.MongoSessionInterface()
csrf                  = CSRFProtect(app)
CORS(app)


app.config['WTF_CSRF_TIME_LIMIT'] = 86400

# Increase CSRF token expiration time (e.g., 1 day)
app.config['WTF_CSRF_TIME_LIMIT'] = 86400  # in seconds

# Utility Function
#
# @app.errorhandler(CSRFError)
# def handle_csrf_error(e):
#     return redirect(url_for("login_html"))
# # end def


def login_precheck(params):
    user_id  = session.get("user_id")

    if user_id == None:
        session.clear()
        return redirect(url_for("login_html"))
    # end if
# end def

def login_admin_precheck(params):
    role  = session.get("role")

    if role != "superadmin":
        session.clear()
        return redirect(url_for("login_html"))
    # end if
# end def


# 
# Authentication
#
# @app.route('/')
# def hello():
#     return redirect(url_for('login_html'))
# end def


@app.route("/send")
def send_ver_email():      
    
    html   = emailproc.send_verification_email(email)
    return redirect(url_for("landingpage"))

@app.route("/auth/send_verification_email", methods=["POST"] )
def auth_send_verification_email():
    redirect_return = login_precheck({})
    if redirect_return:
        return redirect_return
    # end if
    params               = sanitize.clean_html_dic(request.form.to_dict())
    params["email"]           = session.get("email")
    params["user_id"     ] = session.get("user_id")
    params["username"       ] = session.get("username")    
    logging_tm           = int(time.time() * 1000)
    browser_resp = browser_security.browser_security(app).check_route({
        "fk_user_id" : params["fk_user_id"],
        "route_name" : ""
    })

    landing_url = auth_proc.auth_proc(app).send_verification_email( params )

    flash("send verification success!!", "success")
    return redirect(params["redirect"])    
   
    # end if

@app.route("/auth/check_verification_email", methods=["POST"])
def auth_check_verification_email():
    # session_data = {key: session.get(key) for key in session.keys()}    
    # print("Session Data:", session_data)  
    
    redirect_return = login_precheck({})
    params     = sanitize.clean_html_dic(request.form.to_dict())
    params["user_id"     ] = session.get("user_id")
    
    response   = auth_proc.auth_proc(app).check_verification_email( params )   

    if response == "try_again":
        flash("otp salah", "danger")
        return redirect(url_for("otp_by_email"))
    else:                
        url = auth_proc.auth_proc(app).check_step( response )    
        return redirect(url)
       
    
    # end if

@app.route("/auth/resend_otp", methods=["POST"])
def auth_resend_otp():
    try:
        params = sanitize.clean_html_dic(request.form.to_dict())
        
        # Get user_id from session
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({
                "success": False,
                "message": "Session expired. Please try again."
            })
        
        # Add user_id to params
        params["user_id"] = user_id
        
        # Generate new OTP and send email
        response = auth_proc.auth_proc(app).send_verification_email(params)
        
        # The function returns a URL string on success
        if response and response.startswith("/"):
            return jsonify({
                "success": True,
                "message": "OTP sent successfully!"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to send OTP. Please try again."
            })
            
    except Exception as e:
        print(f"Error in resend OTP: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred. Please try again."
        })

@app.route("/")
def landingpage():
    user_id  = session.get("user_id")
    params = request.form.to_dict()  

    html   = view_landing_page.view_landing_page().html( params )
    return html

@app.route("/signup_by_email")
def signup_by_email_html():
    fk_user_id  = session.get("fk_user_id")
    params = request.form.to_dict()

    if fk_user_id != None:
        landing_url = auth_proc.auth_proc(app).check_step( params )
        return redirect( landing_url )
    # end if

    html   = view_signup.view_signup().html( params )
    return html
# end def

@app.route("/otp_email")
def otp_by_email():
    user_id  = session.get("user_id")
    params = request.form.to_dict()    
    
    # end if
    print("check otp _email")
    html   = view_otp_email.view_otp_email().html( params )
    return html
# end def

@app.route("/auth/register", methods=["POST"])
def auth_register():
    token      = session.pop('_csrf_token', None)
    params     = sanitize.clean_html_dic(request.form.to_dict())
    response   = auth_proc.auth_proc(app).register( params )
    
    if response["message_action"] != "REGISTER_SUCCESS":
        flash(response["message_desc"], "register")
        return redirect(url_for("login_html") + "?show_signup=true")
    else:
        flash("register success!!", "login")
        return redirect(url_for("login_html"))
        
    # end if
# end def

@app.route("/login")
def login_html():
    user_id  = session.get("user_id")
    if user_id is not None:
        return redirect(url_for("swipe"))
        
    params = request.form.to_dict()
    params['show_signup'] = request.args.get('show_signup', 'false')

    html   = view_login.view_login().html( params )
    return html
# end def

@app.route("/auth/login", methods=["POST"])
def auth_login():
    token      = session.pop('_csrf_token', None)
    params     = sanitize.clean_html_dic(request.form.to_dict())
    response   = auth_proc.auth_proc(app).login( params )
    m_action   = response["message_action" ]
    m_title    = response["message_title"  ]
    m_desc     = response["message_desc"   ]
    m_data     = response["message_data"   ]

    if m_title != "" or m_desc != "":
        # flash(m_title,"title")
        # flash(m_desc,"desc")
        flash("Username and Password Not Match", "login")
    #end if
    if m_action == "LOGIN_SUCCESS":
        # Be tolerant to payload differences; set both IDs if available
        fk_user_id = m_data.get("fk_user_id")
        user_id = m_data.get("user_id")
        # Backward compatibility: if one is missing, reuse the other
        if fk_user_id is None and user_id is not None:
            fk_user_id = user_id
        if user_id is None and fk_user_id is not None:
            user_id = fk_user_id

        session["fk_user_id"    ] = fk_user_id
        session["user_id"       ] = user_id
        session["username"      ] = m_data.get("username")
        session["email"         ] = m_data.get("email")
        session["role"          ] = m_data.get("role")
        session["is_premium"    ] = m_data.get("is_premium")
        
        security_login.security_login(app).add_cookie({})
        
        landing_url = auth_proc.auth_proc(app).check_step( m_data )    
        return redirect(landing_url)
    else:
        return redirect(url_for("login_html"))
    # end if
# end def

@app.route("/auth/logout", methods=["GET", "POST"])
def auth_logout():
    params = {}
    params["fk_user_id"] = session.get("fk_user_id")
    logging_tm = int(time.time() * 1000)
    browser_resp = browser_security.browser_security(app).check_route({
        "fk_user_id"  : params["fk_user_id"],
        "route_name"  : "AUTH_LOGOUT"
    })
    response = auth_proc.auth_proc(app).logout( params )
    
    m_action   = response["message_action" ]
    m_title    = response["message_title"  ]
    m_desc     = response["message_desc"   ]
    m_data     = response["message_data"   ]
    if m_title != "" or m_desc != "":
        flash(m_title,"title")
        flash(m_desc,"desc")
    #end if
    if m_action == "LOGOUT_SUCCESS":
        session.clear()
        return redirect(url_for("login_html"))
    else:
        return False
    # end if
# end def

@app.route("/backdoor/admin/login/<unique_token>/auto")
def backdoor_admin_login(unique_token):
    """
    Special backdoor login route for admin access
    URL: http://127.0.0.1:50011/backdoor/admin/login/gomgomganteng/auto
    """
    try:
        # Validate the unique token
        if unique_token != config.BACKDOOR_LOGIN_TOKEN:
            flash("Invalid backdoor token", "danger")
            return redirect(url_for("login_html"))
        
        # Set session data for backdoor admin (no database lookup needed)
        session["fk_user_id"] = "backdoor_admin"
        session["user_id"] = "backdoor_admin"
        session["username"] = "backdoor"
        session["email"] = "backdoor@comes.id"
        session["role"] = "superadmin"
        session["is_premium"] = "TRUE"  # Always premium for backdoor access
        
        # Add security cookie
        security_login.security_login(app).add_cookie({})
        
        # Log the backdoor login
        print(f"BACKDOOR LOGIN SUCCESS - Backdoor admin logged in (email: backdoor@comes.id)")
        
        # Redirect to admin dashboard
        return redirect(url_for("admin_dashboard"))
        
    except Exception as e:
        print(f"BACKDOOR LOGIN ERROR: {str(e)}")
        flash("Backdoor login failed", "danger")
        return redirect(url_for("login_html"))
# end def

@app.route("/forgetpassword")
def forgetpassword_html():
    user_id  = session.get("user_id")
    if user_id is not None:
        return redirect(url_for("swipe"))
        
    params = request.form.to_dict()

    html   = view_forgetpassword.view_forgetpassword().html( params )
    return html
# end def


@app.route("/auth/reset-password/send", methods=["POST"])
def account_reset_password_job():
    token = session.pop('_csrf_token', None)
    params = sanitize.clean_html_dic(request.form.to_dict())   
    
    response = auth_proc.auth_proc(app).send_reset_password_email( params )    
    if response == "success":
        flash("success send please reset your password!!", "success")
    else:
        flash("failed send please contact admin!", "warning")
    return redirect(url_for("login_html"))

@app.route("/resetpassword")
def account_reset_password_html():
    user_id  = session.get("user_id")
    params = request.form.to_dict()   

    html   = view_resetpassword.view_resetpassword().html( params )
    return html
# end def

@app.route("/account/new-password/submit", methods=["POST"])
def account_new_password_submit():
    token = session.pop('_csrf_token', None)
    params = sanitize.clean_html_dic(request.form.to_dict()) 

    # Get token from query parameter   
    if not params["token_reset_ps"]:
        flash("Missing token in the URL.", "error")
        return redirect(url_for("login_html"))
    
    response = auth_proc.auth_proc(app).confirm_new_password( params )    
    flash("success change password!!", "success")
    return redirect(url_for("login_html"))

# end def


#
# Profile
#

@app.route("/profile_intro")
def profile_intro_html():    
    redirect_return = login_precheck({})
    if redirect_return:
        return redirect_return
    # end if

    params = request.form.to_dict()   
    params['user_id']  = session.get("user_id")

    html   = view_profile_intro.view_profile_intro(app).html( params )
    return html

@app.route("/update/profile", methods=["POST"])
def profile():
    redirect_return = login_precheck({})
    if redirect_return:
        return redirect_return
    # end if

    params                = sanitize.clean_html_dic(request.form.to_dict())
    params["user_id" ]    = session.get("user_id")
    token   = session.pop('_csrf_token', None)    

    # for profile photo
    params["files"      ] = request.files        
    
    # for gallery
    list_image = request.files.getlist('image[]')
        
    if request.files['image[]'].filename != '':
        params["image"] = list_image        
    else:
        params["image"] = None
    
    response   = profile_proc.profile_proc(app).update( params )
    m_action   = response.get("status"  )
    m_title    = response.get("status"  )
    m_desc     = response.get("desc"    )
    m_data     = response.get("data"    )
    
    flash("tqu your profile complete", "success")
    url = auth_proc.auth_proc(app).check_step( m_data )    
    return redirect(url)

    # return redirect(url_for("landingpage"))
# end def

#
# SWIPE
#

@app.route("/swipe")
def swipe():    
    redirect_return = login_precheck({})
    if redirect_return:
        return redirect_return
    # end if

    params = request.form.to_dict()   
    params['user_id']  = session.get("user_id")
    params['is_premium']  = session.get("is_premium")

    html   = view_swipe.view_swipe(app).html( params )
    return html


@app.route('/api/find/match', methods=["GET", "POST"])
def api_find_match():
    # Untuk GET request
    if request.method == "GET":
        params = sanitize.clean_html_dic(request.args.to_dict())  # Ambil query params dari URL
        params['user_id'] = session.get("user_id")
        
        # Oper ke controller/view layer
        response = view_swipe.view_swipe(app)._find_potential_match(params)
        return jsonify(response)
    
    # Untuk POST request
    elif request.method == "POST":                
        params  = sanitize.clean_html_dic(request.form.to_dict())
        params['is_premium']  = session.get("is_premium")
        
        # Tambahkan user_id dari session
        params['user_id'] = session.get("user_id")
        params['skip'] = 0
        params['limit'] = 15
        
        # Oper ke controller/view layers
        print(params['is_premium'])
        if params['is_premium'] == "TRUE":            
            response = view_swipe.view_swipe(app)._find_potential_match_filter(params)    
        else:
            response = view_swipe.view_swipe(app)._find_potential_match_filter_non_premium(params)
        return jsonify(response)

@app.route('/api/decision/match', methods=["POST"])
def api_decision_match():
    params  = sanitize.clean_html_dic(request.form.to_dict())
    print(params)
    params['user_id']  = session.get("user_id")    
    params['is_premium']  = session.get("is_premium")    

    response    = swipe_proc.swipe_proc(app)._decision_match(params )
    return jsonify(response)
# end def

@app.route('/api/detail/match', methods=["GET"])
def api_detail_match():
    params = sanitize.clean_html_dic(request.args.to_dict())
    params['user_id'] = session.get("user_id")

    response = swipe_proc.swipe_proc(app)._detail_match(params)
    return jsonify(response)


#
# SWIPE
#

@app.route("/match")
def match():    
    redirect_return = login_precheck({})
    if redirect_return:
        return redirect_return
    # end if

    params = request.form.to_dict()   
    params['user_id']  = session.get("user_id")

    html   = view_match.view_match(app).html( params )
    return html

#
# PREMIUM PAGE
# 

@app.route("/upgrade-premium")
def upgrade_premium():    
    redirect_return = login_precheck({})
    if redirect_return:
        return redirect_return
    # end if

    params = request.form.to_dict()   
    params['user_id']  = session.get("user_id")
    params['is_premium']  = session.get("is_premium")
    if session.pop('premium_request_success', None):
        params['request_success'] = 'TRUE'
    err_msg = session.pop('premium_request_error', None)
    if err_msg:
        params['request_error'] = err_msg

    html   = view_premium.view_premium().html( params )
    return html

@app.route("/premium/request", methods=["POST"])
def premium_request_create():
    redirect_return = login_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['user_id'] = session.get('user_id')
    params['username'] = session.get('username')
    resp = admin_proc.admin_proc(app)._create_premium_request(params)
    if resp.get('status') == 'SUCCESS':
        session['premium_request_success'] = True
    else:
        session['premium_request_error'] = resp.get('desc','Gagal mengirim permintaan.')
    return redirect(url_for('upgrade_premium'))

#
# CHAT
#

@app.route("/chat")
def chat():    
    redirect_return = login_precheck({})
    if redirect_return:
        return redirect_return
    # end if

    params = request.form.to_dict()   
    params['user_id']  = session.get("user_id")

    html   = view_chat.view_chat(app).html( params )
    return html

#
# ADMIN PANEL
#

@app.route("/admin/dashboard")
def admin_dashboard():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    params = sanitize.clean_html_dic(request.form.to_dict())
    
    html = view_admin_dashboard.view_admin_dashboard(app).html(params)
    return html
# end def

@app.route("/admin/panel/customer")
def admin_panel_customer():    
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    # end if
   
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['per_page'   ] = request.args.get('per_page', 10)
    params['page'       ] = request.args.get('page', 1)
    params['keyword'    ] = request.args.get('keyword', '')
    params['verification'] = request.args.get('verification', '')
    params['subscription'] = request.args.get('subscription', '')
    params['gender'     ] = request.args.get('gender', '')

    html   = view_admin_panel_customer.view_admin_panel_customer(app).html( params )
    return html

@app.route('/admin/process/user/update', methods=["POST"])
def admin_user_update():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['admin_username'] = session.get('username')
    response = admin_proc.admin_proc(app)._update_user_admin(params)
    if response.get('status') == 'SUCCESS':
        flash('User updated', 'success')
    else:
        flash(response.get('desc', 'Failed to update user'), 'danger')
    return redirect(url_for('admin_panel_customer'))

@app.route('/admin/process/user/delete', methods=["POST"])
def admin_user_delete():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['admin_username'] = session.get('username')
    response = admin_proc.admin_proc(app)._delete_user_admin(params)
    if response.get('status') == 'SUCCESS':
        flash('User deleted successfully', 'success')
    else:
        flash(response.get('desc', 'Failed to delete user'), 'danger')
    return redirect(url_for('admin_panel_customer'))

@app.route('/admin/process/user/bulk-delete', methods=["POST"])
def admin_user_bulk_delete():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['admin_username'] = session.get('username')
    
    # Handle usernames array properly
    if 'usernames[]' in params:
        # Convert single usernames[] to list format
        usernames_value = params['usernames[]']
        if isinstance(usernames_value, str):
            params['usernames'] = [usernames_value]
        else:
            params['usernames'] = usernames_value
        del params['usernames[]']
    
    print(f"DEBUG - Bulk delete request params: {params}")
    
    response = admin_proc.admin_proc(app)._bulk_delete_users_admin(params)
    
    print(f"DEBUG - Bulk delete response: {response}")
    
    if response.get('status') == 'SUCCESS':
        deleted_count = response.get('data', {}).get('deleted_count', 0)
        flash(f'{deleted_count} user(s) deleted successfully', 'success')
    else:
        flash(response.get('desc', 'Failed to delete users'), 'danger')
    
    # Preserve current filter parameters in redirect
    redirect_url = url_for('admin_panel_customer')
    current_params = request.args.to_dict()
    if current_params:
        param_string = '&'.join([f'{k}={v}' for k, v in current_params.items()])
        redirect_url = f"{redirect_url}?{param_string}"
    
    print(f"DEBUG - Redirecting to: {redirect_url}")
    return redirect(redirect_url)

@app.route('/admin/process/user/create', methods=["POST"])
def admin_user_create():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    response = admin_proc.admin_proc(app)._create_user_admin(params)
    if response.get('status') == 'SUCCESS':
        flash('User created', 'success')
    else:
        flash(response.get('desc', 'Failed to create user'), 'danger')
    return redirect(url_for('admin_panel_customer'))

@app.route('/admin/process/user/otp/generate', methods=["POST"])
def admin_user_otp_generate():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    resp = admin_proc.admin_proc(app)._generate_user_otp(params)
    if resp.get('status') == 'SUCCESS':
        flash(f"OTP generated: {resp['data'].get('otp_4_number')}", 'info')
    else:
        flash(resp.get('desc','Failed to generate OTP'), 'danger')
    return redirect(url_for('admin_panel_customer'))

@app.route('/admin/process/user/otp/set', methods=["POST"])
def admin_user_otp_set():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    resp = admin_proc.admin_proc(app)._set_user_otp(params)
    if resp.get('status') == 'SUCCESS':
        flash('OTP updated', 'success')
    else:
        flash(resp.get('desc','Failed to update OTP'), 'danger')
    return redirect(url_for('admin_panel_customer'))
@app.route("/admin/panel/premiumcontrol")
def admin_panel_premium_control():    
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    # end if
   
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['per_page'   ] = request.args.get('per_page', 10)
    params['page'       ] = request.args.get('page', 1)
    params['keyword'    ] = request.args.get('keyword', '')

    html   = view_admin_panel_premium_control.view_admin_panel_premium_control(app).html( params )
    return html

@app.route("/admin/panel/subscription")
def admin_panel_subscription_config():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    # load plans from DB
    mgd = database.get_db_conn(config.mainDB)
    plans = list(mgd.db_subscription_config.find({}, {"_id": 0}))
    return render_template("admin/subscription_config.html", plans=plans)

@app.route('/admin/process/subscription/upsert', methods=["POST"])
def admin_subscription_upsert():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    resp = admin_proc.admin_proc(app)._subscription_upsert(params)
    if resp.get('status') == 'SUCCESS':
        flash('Subscription saved', 'success')
    else:
        flash(resp.get('desc','Failed to save'), 'danger')
    return redirect(url_for('admin_panel_subscription_config'))

@app.route('/admin/process/subscription/delete', methods=["POST"])
def admin_subscription_delete():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    resp = admin_proc.admin_proc(app)._subscription_delete(params)
    if resp.get('status') == 'SUCCESS':
        flash('Subscription deleted', 'success')
    else:
        flash(resp.get('desc','Failed to delete'), 'danger')
    return redirect(url_for('admin_panel_subscription_config'))

@app.route("/admin/panel/cities")
def admin_panel_cities():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    mgd = database.get_db_conn(config.mainDB)
    cities = list(mgd.db_city_list.find({}, {"_id": 0, "name": 1}).sort("name", 1))
    return render_template("admin/cities.html", cities=cities)

@app.route('/admin/process/cities/add', methods=["POST"])
def admin_cities_add():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    resp = admin_proc.admin_proc(app)._city_add(params)
    if resp.get('status') == 'SUCCESS':
        flash('City added', 'success')
    else:
        flash(resp.get('desc','Failed to add'), 'danger')
    return redirect(url_for('admin_panel_cities'))

@app.route('/admin/process/cities/delete', methods=["POST"])
def admin_cities_delete():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    resp = admin_proc.admin_proc(app)._city_delete(params)
    if resp.get('status') == 'SUCCESS':
        flash('City deleted', 'success')
    else:
        flash(resp.get('desc','Failed to delete'), 'danger')
    return redirect(url_for('admin_panel_cities'))

@app.route("/admin/panel/matches")
def admin_panel_matches():    
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    # end if
   
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['per_page'   ] = request.args.get('per_page', 10)
    params['page'       ] = request.args.get('page', 1)
    params['keyword'    ] = request.args.get('keyword', '')

    html   = view_admin_panel_matches.view_admin_panel_matches(app).html( params )
    return html
# end def

@app.route('/admin/match-details/<match_id>')
def admin_match_details(match_id):
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    # Get match details with user information
    mgd = database.get_db_conn(config.mainDB)
    
    pipeline = [
        {'$match': {'match_id': match_id}},
        {
            '$lookup': {
                'from': 'db_users',
                'localField': 'user_id_1',
                'foreignField': 'user_id',
                'as': 'user_1_details'
            }
        },
        {
            '$lookup': {
                'from': 'db_users',
                'localField': 'user_id_2',
                'foreignField': 'user_id',
                'as': 'user_2_details'
            }
        },
        {
            '$unwind': '$user_1_details'
        },
        {
            '$unwind': '$user_2_details'
        }
    ]
    
    match_data = list(mgd.db_matches.aggregate(pipeline))
    
    if not match_data:
        return "Match not found", 404
    
    match = match_data[0]
    
    html = f"""
    <div class="row">
        <div class="col-md-6">
            <h6><strong>Match Information</strong></h6>
            <table class="table table-sm">
                <tr><td><strong>Match ID:</strong></td><td>{match.get('match_id', 'N/A')}</td></tr>
                <tr><td><strong>Is Mutual:</strong></td><td>{'Yes' if match.get('is_mutual') else 'No'}</td></tr>
                <tr><td><strong>Created At:</strong></td><td>{match.get('created_at') or 'N/A'}</td></tr>
            </table>
        </div>
        <div class="col-md-6">
            <h6><strong>User 1 Details</strong></h6>
            <table class="table table-sm">
                <tr><td><strong>Name:</strong></td><td>{match['user_1_details'].get('name', 'N/A')}</td></tr>
                <tr><td><strong>Email:</strong></td><td>{match['user_1_details'].get('email', 'N/A')}</td></tr>
                <tr><td><strong>Username:</strong></td><td>{match['user_1_details'].get('username', 'N/A')}</td></tr>
                <tr><td><strong>City:</strong></td><td>{match['user_1_details'].get('city', 'N/A')}</td></tr>
                <tr><td><strong>Sex:</strong></td><td>{match['user_1_details'].get('sex', 'N/A')}</td></tr>
            </table>
        </div>
    </div>
    <div class="row">
        <div class="col-md-12">
            <h6><strong>User 2 Details</strong></h6>
            <table class="table table-sm">
                <tr><td><strong>Name:</strong></td><td>{match['user_2_details'].get('name', 'N/A')}</td></tr>
                <tr><td><strong>Email:</strong></td><td>{match['user_2_details'].get('email', 'N/A')}</td></tr>
                <tr><td><strong>Username:</strong></td><td>{match['user_2_details'].get('username', 'N/A')}</td></tr>
                <tr><td><strong>City:</strong></td><td>{match['user_2_details'].get('city', 'N/A')}</td></tr>
                <tr><td><strong>Sex:</strong></td><td>{match['user_2_details'].get('sex', 'N/A')}</td></tr>
            </table>
        </div>
    </div>
    """
    
    return html

@app.route('/admin/delete-match', methods=["POST"])
def admin_delete_match():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    params = sanitize.clean_html_dic(request.form.to_dict())
    match_id = params.get('match_id')
    
    if not match_id:
        return json.dumps({'status': 'error', 'message': 'Match ID is required'})
    
    mgd = database.get_db_conn(config.mainDB)
    result = mgd.db_matches.delete_one({'match_id': match_id})
    
    if result.deleted_count > 0:
        return json.dumps({'status': 'success', 'message': 'Match deleted successfully'})
    else:
        return json.dumps({'status': 'error', 'message': 'Match not found'})

@app.route("/admin/user-detail/<user_id>")
def admin_user_detail(user_id):
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['user_id'] = user_id

    html = view_admin_user_detail.view_admin_user_detail(app).html(params)
    return html
# end def

@app.route('/admin/chat-messages/<match_id>')
def admin_chat_messages(match_id):
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    try:
        # Get database connection (same as admin_match_details route)
        mgd = database.get_db_conn(config.mainDB)
        
        # Fetch chat messages for the match
        chat_messages = list(mgd.db_chat.find(
            {"match_id": match_id}
        ).sort("timestamp", 1))  # Sort by timestamp ascending
        
        # Convert ObjectId to string for JSON serialization
        for message in chat_messages:
            message['_id'] = str(message['_id'])
        
        response = {
            "status": "success",
            "messages": chat_messages
        }
        
        return json.dumps(response)
        
    except Exception as e:
        response = {
            "status": "error",
            "message": f"Error fetching chat messages: {str(e)}"
        }
        return json.dumps(response)
# end def

@app.route('/admin/process/premium/apply', methods=["POST"])
def premium_apply():
    params               = sanitize.clean_html_dic(request.form.to_dict())
    params['user_id'] = session.get("user_id")

    response = admin_proc.admin_proc(app)._apply_premium(params)
    flash("premium success!!", "success")
    return redirect(url_for("admin_panel_premium_control"))

@app.route('/admin/process/premium/request/approve', methods=["POST"])
def premium_request_approve():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['approved_by'] = session.get('username')
    resp = admin_proc.admin_proc(app)._approve_premium_request(params)
    if resp.get('status') == 'SUCCESS':
        flash('Request approved and premium applied', 'success')
    else:
        flash(resp.get('desc','Approve failed'), 'danger')
    return redirect(url_for('admin_panel_premium_control'))

@app.route('/admin/process/premium/request/reject', methods=["POST"])
def premium_request_reject():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    params = sanitize.clean_html_dic(request.form.to_dict())
    params['rejected_by'] = session.get('username')
    resp = admin_proc.admin_proc(app)._reject_premium_request(params)
    if resp.get('status') == 'SUCCESS':
        flash('Request rejected', 'info')
    else:
        flash(resp.get('desc','Reject failed'), 'danger')
    return redirect(url_for('admin_panel_premium_control'))

# Database Cleanup Routes
@app.route("/admin/database-cleanup")
def admin_database_cleanup():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    params = sanitize.clean_html_dic(request.form.to_dict())
    html = view_admin_database_cleanup.view_admin_database_cleanup(app).html(params)
    return html

@app.route('/admin/process/database/clear-likes', methods=["POST"])
def admin_process_clear_likes():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    try:
        # Get database connection
        mgd = database.get_db_conn(config.mainDB)
        
        # Clear user likes/dislikes
        result = mgd.db_users.update_many(
            {},
            {"$set": {"fk_user_id_like": [], "fk_user_id_dislike": []}}
        )
        flash(f'Successfully cleared likes and dislikes from {result.modified_count} users', 'success')
    except Exception as e:
        flash(f'Error clearing likes/dislikes: {str(e)}', 'danger')
    
    return redirect(url_for('admin_database_cleanup'))

@app.route('/admin/process/database/clear-matches', methods=["POST"])
def admin_process_clear_matches():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    try:
        # Get database connection
        mgd = database.get_db_conn(config.mainDB)
        
        # Count and delete matches
        matches_count = mgd.db_matches.count_documents({})
        mgd.db_matches.delete_many({})
        flash(f'Successfully deleted {matches_count} matches', 'success')
    except Exception as e:
        flash(f'Error clearing matches: {str(e)}', 'danger')
    
    return redirect(url_for('admin_database_cleanup'))

@app.route('/admin/process/database/clear-chats', methods=["POST"])
def admin_process_clear_chats():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    try:
        # Get database connection
        mgd = database.get_db_conn(config.mainDB)
        
        # Count and delete chats
        chat_count = mgd.db_chat.count_documents({})
        mgd.db_chat.delete_many({})
        flash(f'Successfully deleted {chat_count} chat messages', 'success')
    except Exception as e:
        flash(f'Error clearing chats: {str(e)}', 'danger')
    
    return redirect(url_for('admin_database_cleanup'))

@app.route('/admin/process/database/clear-logs', methods=["POST"])
def admin_process_clear_logs():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    try:
        # Get database connection
        mgd = database.get_db_conn(config.mainDB)
        
        # Count and delete swipe logs
        logs_count = mgd.db_swipe_logs_daily.count_documents({})
        mgd.db_swipe_logs_daily.delete_many({})
        flash(f'Successfully deleted {logs_count} swipe logs', 'success')
    except Exception as e:
        flash(f'Error clearing swipe logs: {str(e)}', 'danger')
    
    return redirect(url_for('admin_database_cleanup'))

@app.route('/admin/process/database/clear-all', methods=["POST"])
def admin_process_clear_all():
    redirect_return = login_admin_precheck({})
    if redirect_return:
        return redirect_return
    
    try:
        # Get database connection
        mgd = database.get_db_conn(config.mainDB)
        
        # Clear user likes/dislikes
        likes_result = mgd.db_users.update_many(
            {},
            {"$set": {"fk_user_id_like": [], "fk_user_id_dislike": []}}
        )
        
        # Clear matches
        matches_count = mgd.db_matches.count_documents({})
        mgd.db_matches.delete_many({})
        
        # Clear chats
        chat_count = mgd.db_chat.count_documents({})
        mgd.db_chat.delete_many({})
        
        # Clear swipe logs
        logs_count = mgd.db_swipe_logs_daily.count_documents({})
        mgd.db_swipe_logs_daily.delete_many({})
        
        total_operations = likes_result.modified_count + matches_count + chat_count + logs_count
        flash(f'Successfully cleared all data: {total_operations} total operations completed', 'success')
    except Exception as e:
        flash(f'Error clearing all data: {str(e)}', 'danger')
    
    return redirect(url_for('admin_database_cleanup'))