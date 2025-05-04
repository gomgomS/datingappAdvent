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
# chat
##########################################################

from view               import view_chat

##########################################################
# ADMIN
##########################################################

from view               import view_admin_panel_customer

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
        flash(response["message_desc"], "danger")
        return redirect(url_for("login_html"))
    else:
        flash("register success!!", "success")
        return redirect(url_for("login_html"))
        
    # end if
# end def

@app.route("/login")
def login_html():
    user_id  = session.get("user_id")
    if user_id is not None:
        return redirect(url_for("swipe"))
        
    params = request.form.to_dict()

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
        flash("Username and Password Not Match", "danger")
    #end if
    if m_action == "LOGIN_SUCCESS":
        session["user_id"       ] = m_data["user_id"       ]        
        session["username"      ] = m_data["username"      ]    
        session["email"         ] = m_data["email"         ]
        session["role"         ] = m_data["role"           ]
        
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

    html   = view_swipe.view_swipe(app).html( params )
    return html


# API FOR AJAX = SWIPE
# cari data yang tidak ada di like dan dislike
@app.route('/api/find/match', methods=["GET"])
def api_find_match():
    params = sanitize.clean_html_dic(request.args.to_dict())  # Changed from request.form
    params['user_id'] = session.get("user_id")

    response = view_swipe.view_swipe(app)._find_potential_match(params)
    return jsonify(response)
# end def

@app.route('/api/decision/match', methods=["POST"])
def api_decision_match():
    params  = sanitize.clean_html_dic(request.form.to_dict())
    params['user_id']  = session.get("user_id")    

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

    html   = view_admin_panel_customer.view_admin_panel_customer(app).html( params )
    return html