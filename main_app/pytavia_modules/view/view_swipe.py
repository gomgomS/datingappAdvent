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
        user_rec                = self.mgdDB.db_users.find_one({"user_id": params["user_id"]},{"location":1,"profile_photo":1,"name":1,"_id":0,"user_id":1})                 

        return render_template(
            "users/swipe.html",
            menu_list_html      = menu_list               ,
            core_display        = core_display            , 
            core_header         = core_header             , 
            core_footer         = core_footer             , 
            core_script         = core_script             , 
            core_css            = core_css                , 
            core_dialog_message = core_dialog_message     ,   
            main_app_url        = config.MAIN_APP_URL     ,                   
            G_IMAGE_URL_DISPATCH       = config.G_IMAGE_URL_DISPATCH     , 
            user_rec            = user_rec,
            city_list           = config.CITY_LIST,
            is_premium          = params['is_premium']                  
            
        )                
    # end def   

    def _find_potential_match_filter_non_premium(self, params):
        print(params)
        user_id = params.get("user_id")
        today = datetime.utcnow()
        today_timestamp = int(today.timestamp() * 1000)

        # Ambil user sekarang
        current_user = self.mgdDB.db_users.find_one(
            {"user_id": user_id}, {"sex": 1, "fk_user_id_like": 1, "fk_user_id_dislike": 1}
        )

        # Inisialisasi blocked_ids
        blocked_ids = set(current_user.get("fk_user_id_like", []) + current_user.get("fk_user_id_dislike", []))
        blocked_ids.add(user_id)

        # Tambahkan pasangan yang sudah match biar tidak muncul lagi pada filter
        matched_users = self.mgdDB.db_matches.find(
            {"$or": [{"user_id_1": user_id}, {"user_id_2": user_id}]}
        )
        for match in matched_users:
            blocked_ids.add(match["user_id_2"] if match["user_id_1"] == user_id else match["user_id_1"])

        # Filter pencarian dasar
        query = {
            "user_id": {"$nin": list(blocked_ids)},
            "is_deleted": {"$ne": True}
        }

        # Filter umur (default: 0 - 50 tahun)
        max_age = int(params['max_age'])
        min_age = int(params['min_age'])
        max_birthdate = (today - timedelta(days=(min_age * 365))).strftime("%Y-%m-%d")
        min_birthdate = (today - timedelta(days=(max_age * 365))).strftime("%Y-%m-%d")
        query["dob"] = {
            "$gte": min_birthdate,
            "$lte": max_birthdate
        }

        # Filter jenis kelamin lawan
        sex = current_user.get("sex")
        if sex in ["male", "female"]:
            query["sex"] = "female" if sex == "male" else "male"

        # Filter hometown/city (kampung halaman)
        hometown = params.get("hometown")        
        if hometown:
            query['city'] = hometown

        # Filter maritalStatus (status hubungan)
        maritalStatus = params.get("maritalStatus")        
        if maritalStatus:
            query['marital_status'] = maritalStatus

        # Ambil limit dari param, fallback ke default
        try:
            limit = int(params.get("limit", 15))
        except ValueError:
            limit = 15

        # Query biasa tanpa geoNear
        user_view = self.mgdDB.db_users.find(query).limit(limit)

        # Format output
        result = []
        for user in user_view:
            dob_timestamp = int(datetime.strptime(user["dob"], "%Y-%m-%d").timestamp() * 1000)
            age = (today_timestamp - dob_timestamp) // (1000 * 60 * 60 * 24 * 365)

            result.append({
                "name": user.get("name"),
                "user_id": user.get("user_id"),
                "img": f"{config.G_IMAGE_URL_DISPATCH}{user.get('profile_photo', '')}",
                "username": user.get("username"),
                "email": user.get("email"),
                "pkey": user.get("pkey"),
                "dob": user.get("dob"),
                "sex": user.get("sex"),
                "age": age,
                "city": user.get("city"),
            })

        return result

    def _find_potential_match_filter(self, params):       
        print("[api_find_match][premium] params:", params)
        user_id = params.get("user_id")
        today = datetime.utcnow()
        today_timestamp = int(today.timestamp() * 1000)
        

        # Ambil lokasi jika tersedia
        longitude = params.get("current_position[longitude]")
        latitude = params.get("current_position[latitude]")
        current_city = params.get("current_position[city]")
        current_province = params.get("current_position[prov]")
        current_country = params.get("current_position[country]")

        if longitude and latitude and current_city:
            location_data = {
                "type": "Point",
                "coordinates": [float(longitude), float(latitude)],
                "lastGeoDate": today.strftime("%Y-%m-%d"),
                "current_city": current_city,
                "current_province": current_province,
                "current_country": current_country,
            }

            self.mgdDB.db_users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "login_status": "TRUE",
                        "location": location_data
                    }
                }
            )

        # Ambil user sekarang
        current_user = self.mgdDB.db_users.find_one(
            {"user_id": user_id}, {"sex": 1, "fk_user_id_like": 1, "fk_user_id_dislike": 1, "location":1}
        )

        # Inisialisasi blocked_ids
        blocked_ids = set(current_user.get("fk_user_id_like", []) + current_user.get("fk_user_id_dislike", []))
        blocked_ids.add(user_id)

        # Tambahkan pasangan yang sudah match biar tidak muncul lagi pada filter
        matched_users = self.mgdDB.db_matches.find(
            {"$or": [{"user_id_1": user_id}, {"user_id_2": user_id}]}
        )
        for match in matched_users:
            blocked_ids.add(match["user_id_2"] if match["user_id_1"] == user_id else match["user_id_1"])

        # Filter pencarian dasar
        query = {
            "user_id": {"$nin": list(blocked_ids)},
        }

        # Filter umur (default: 0 - 50 tahun)
        # Define the age range
        min_age = int(params['min_age'])
        max_age = int(params['max_age'])

        max_birthdate = (today - timedelta(days=(min_age * 365))).strftime("%Y-%m-%d")
        min_birthdate = (today - timedelta(days=(max_age * 365))).strftime("%Y-%m-%d")
        query["dob"] = {
            "$gte": min_birthdate,
            "$lte": max_birthdate
        }

        # Filter jenis kelamin lawan
        sex = current_user.get("sex")
        if sex in ["male", "female"]:
            query["sex"] = "female" if sex == "male" else "male"
        
        # Filter hometown/city (kampung halaman)
        hometown = params.get("hometown")        
        if hometown:
            query['city'] = hometown


        # Filter maritalStatus (status hubungan)
        maritalStatus = params.get("maritalStatus")        
        if maritalStatus:
            query['marital_status'] = maritalStatus

        
        # Tentukan koordinat untuk geoNear: prioritaskan yang datang dari request, fallback ke DB
        longitude = None
        latitude = None
        try:
            req_lng = params.get("current_position[longitude]")
            req_lat = params.get("current_position[latitude]")
            if req_lng is not None and req_lat is not None and str(req_lng) != '' and str(req_lat) != '':
                longitude = float(req_lng)
                latitude = float(req_lat)
            else:
                loc = current_user.get("location", {}) if current_user else {}
                if isinstance(loc, dict):
                    if "coordinates" in loc and isinstance(loc.get("coordinates"), (list, tuple)) and len(loc["coordinates"]) >= 2:
                        longitude = float(loc["coordinates"][0])
                        latitude = float(loc["coordinates"][1])
                    elif "longitude" in loc and "latitude" in loc:
                        longitude = float(loc.get("longitude"))
                        latitude = float(loc.get("latitude"))
        except Exception as e:
            print("[api_find_match] failed to parse coordinates:", e)
            longitude = None
            latitude = None

        # Ambil distance dan limit dari param, fallback ke default
        try:
            # distance in km from FE; convert to meters
            distance_km = int(params.get("distance", 14))
        except ValueError:
            distance_km = 14
        distance = max(0, distance_km) * 1000

        try:
            limit = int(params.get("limit", 15))
        except ValueError:
            limit = 15

        # jika distance 0 gk pake cordinate
        if distance > 0 and longitude is not None and latitude is not None:
            print(f"[api_find_match] geoNear with near=({longitude},{latitude}), maxDistance={distance}m, query={query}")
            # Use geoNear when distance is specified
            user_view = self.mgdDB.db_users.aggregate([
                {
                    "$geoNear": {
                        "near": {
                            "type": "Point",
                            "coordinates": [float(longitude), float(latitude)]
                        },
                        "distanceField": "distance",
                        "maxDistance": distance,
                        "spherical": True,
                        "query": query
                    }
                },
                {
                    "$project": {
                        "name": 1,
                        "user_id": 1,
                        "img": {"$concat": [config.G_IMAGE_URL_DISPATCH, "$profile_photo"]},
                        "username": 1,
                        "email": 1,
                        "pkey": 1,
                        "dob": 1,
                        "sex": 1,
                        "distance": 1,
                        "age": {
                            "$floor": {
                                "$divide": [
                                    {"$subtract": [today_timestamp, {"$toLong": {"$toDate": "$dob"}}]},
                                    1000 * 60 * 60 * 24 * 365
                                ]
                            }
                        },
                        "city": 1,
                        "_id": 0
                    }
                },
                {"$limit": limit}
            ])
        else:
            # Use regular match if distance is 0 (or disabled)
            print(f"[api_find_match] non-geo match, query={query}, limit={limit}")
            user_view = self.mgdDB.db_users.aggregate([
                {
                    "$match": query
                },
                {
                    "$project": {
                        "name": 1,
                        "user_id": 1,
                        "img": {"$concat": [config.G_IMAGE_URL_DISPATCH, "$profile_photo"]},
                        "username": 1,
                        "email": 1,
                        "pkey": 1,
                        "dob": 1,
                        "sex": 1,
                        "distance": {"$literal": None},
                        "age": {
                            "$floor": {
                                "$divide": [
                                    {"$subtract": [today_timestamp, {"$toLong": {"$toDate": "$dob"}}]},
                                    1000 * 60 * 60 * 24 * 365
                                ]
                            }
                        },
                        "city": 1,
                        "_id": 0
                    }
                },
                {"$limit": limit}
            ])
  
        response = list(user_view)
        print(f"[api_find_match] results={len(response)}")
        return response
        
    def _find_potential_match(self, params):
        now               = utils._get_current_datetime(hours = config.JKTA_TZ)
        timestamp         = utils._convert_datetime_to_timestamp(now)
        today_timestamp   = int(datetime.utcnow().timestamp() * 1000)        
        params["limit"]   = int(params.get('limit', 15))  # Static limit is fine because previous 15 users are already filtered out (liked/disliked won't appear again)
        
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

        # Define the age range
        min_age = 0
        max_age = 50

        # Calculate birthdate range
        today = datetime.today()
        max_birthdate = today - timedelta(days=(min_age * 365))  # Oldest date of birth allowed
        min_birthdate = today - timedelta(days=(max_age * 365))  # Youngest date of birth allowed

        # Add age range filter
        match_query["dob"] = {
            "$gte": min_birthdate.strftime("%Y-%m-%d"),  # Users must be at least min_age
            "$lte": max_birthdate.strftime("%Y-%m-%d")   # Users must be at most max_age
        }
        print(params)
        print("atas adalah aparams")

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
                    "age": {
                        "$floor": {
                            "$divide": [
                                { "$subtract": [today_timestamp, { "$toLong": { "$toDate": "$dob" } }] },
                                1000 * 60 * 60 * 24 * 365  # Convert milliseconds to years
                            ]
                        }
                    },
                    "sex": 1,
                    "city": 1,
                    "_id": 0
                }
            },            
            { "$limit": params.get("limit", 15) }
        ])

        response = list(user_view)
        
        return response
    # end def
# end class
