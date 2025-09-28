import sys
import traceback
import time
import json
import datetime
import statistics
from bson import Int64
from datetime import datetime, timedelta
import re

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

class view_admin_user_detail:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def html(self, params):
        user_id = params.get('user_id')
        
        if not user_id:
            return render_template("admin/user_detail.html", 
                                 user_data=None, 
                                 error="User ID is required",
                                 image_base_url=config.G_IMAGE_URL_DISPATCH)
        
        # Get user data with all details
        user_data = self._get_user_detail(user_id)
        
        if not user_data:
            return render_template("admin/user_detail.html", 
                                 user_data=None, 
                                 error="User not found",
                                 image_base_url=config.G_IMAGE_URL_DISPATCH)

        return render_template(
            "admin/user_detail.html",
            user_data=user_data,
            image_base_url=config.G_IMAGE_URL_DISPATCH
        )             
    # end def   

    def _get_user_detail(self, user_id):
        """
        Get complete user details for admin view
        """
        # Get user basic info
        user = self.mgdDB.db_users.find_one({'user_id': user_id})
        
        if not user:
            return None
        
        # Calculate age from DOB if available
        age = None
        if user.get('dob'):
            try:
                dob = datetime.strptime(user['dob'], '%Y-%m-%d')
                today = datetime.now()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except:
                pass
        
        # Get user's matches count
        matches_count = self.mgdDB.db_matches.count_documents({
            '$or': [
                {'user_id_1': user_id},
                {'user_id_2': user_id}
            ]
        })
        
        # Get user's likes given count (from fk_user_id_like array)
        likes_given = len(user.get('fk_user_id_like', []))
        
        # Get user's likes received count (users who have this user in their fk_user_id_like array)
        likes_received = self.mgdDB.db_users.count_documents({
            'fk_user_id_like': user_id
        })
        
        # Get user's images
        images = []
        if user.get('image') and isinstance(user['image'], list):
            images = user['image']
        
        # Get user's matches with other users
        user_matches = self._get_user_matches(user_id)
        
        # Get users who liked this user (likes received)
        likes_received_users = self._get_likes_received(user_id)
        
        # Get users that this user has liked (likes given)
        likes_given_users = self._get_likes_given(user_id)
        
        # Format user data
        user_data = {
            'user_id': user.get('user_id', ''),
            'username': user.get('username', ''),
            'name': user.get('name', ''),
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'dob': user.get('dob', ''),
            'age': age,
            'sex': user.get('sex', ''),
            'city': user.get('city', ''),
            'job': user.get('job', ''),
            'profile_photo': user.get('profile_photo', ''),
            'images': images,
            'hobbies': user.get('hobbies', ''),
            'tribe': user.get('tribe', ''),
            'marital_status': user.get('marital_status', ''),
            'congregation': user.get('congregation', ''),
            'about': user.get('about', ''),
            'is_premium': user.get('is_premium', False),
            'verify_email': user.get('verify_email', False),
            'rec_timestamp': user.get('rec_timestamp', ''),
            'last_login': user.get('last_login', ''),
            'location': user.get('location', {}),
            'matches_count': matches_count,
            'likes_given': likes_given,
            'likes_received': likes_received,
            'otp_4_number': user.get('otp_4_number', ''),
            'pkey': user.get('pkey', ''),
            'matches': user_matches,
            'likes_received_users': likes_received_users,
            'likes_given_users': likes_given_users
        }
        
        return user_data

    def _get_user_matches(self, user_id):
        """
        Get user's matches with other users
        """
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
                                'username': 1,
                                'email': 1,
                                'profile_photo': 1,
                                'city': 1,
                                'sex': 1
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
            },
            {
                '$sort': {'created_at': -1}
            }
        ]
        
        matches = list(self.mgdDB.db_matches.aggregate(pipeline))
        return matches

    def _get_likes_received(self, user_id):
        """
        Get users who liked this user (likes received)
        """
        # Find all users who have this user_id in their fk_user_id_like array
        likes_pipeline = [
            {
                '$match': {
                    'fk_user_id_like': user_id  # Users who liked this user
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'user_id': 1,
                    'name': 1,
                    'username': 1
                }
            },
            {
                '$sort': {'rec_timestamp': -1}
            }
        ]
        
        likes = list(self.mgdDB.db_users.aggregate(likes_pipeline))
        
        # Format the data to match the expected structure
        formatted_likes = []
        for like in likes:
            formatted_likes.append({
                'liker': {
                    'user_id': like.get('user_id', ''),
                    'name': like.get('name', ''),
                    'username': like.get('username', '')
                },
                'created_at': like.get('rec_timestamp', '')
            })
        
        return formatted_likes

    def _get_likes_given(self, user_id):
        """
        Get users that this user has liked (likes given)
        """
        # Get the current user's fk_user_id_like array
        current_user = self.mgdDB.db_users.find_one({'user_id': user_id}, {'fk_user_id_like': 1})
        
        if not current_user or not current_user.get('fk_user_id_like'):
            return []
        
        liked_user_ids = current_user['fk_user_id_like']
        
        # Find all users that this user has liked
        likes_pipeline = [
            {
                '$match': {
                    'user_id': {'$in': liked_user_ids}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'user_id': 1,
                    'name': 1,
                    'username': 1
                }
            },
            {
                '$sort': {'rec_timestamp': -1}
            }
        ]
        
        likes = list(self.mgdDB.db_users.aggregate(likes_pipeline))
        
        # Format the data to match the expected structure
        formatted_likes = []
        for like in likes:
            formatted_likes.append({
                'liked_user': {
                    'user_id': like.get('user_id', ''),
                    'name': like.get('name', ''),
                    'username': like.get('username', '')
                },
                'created_at': like.get('rec_timestamp', '')
            })
        
        return formatted_likes

# end class
