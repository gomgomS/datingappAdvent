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

class view_admin_panel_transactions:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def html(self, params):
        page = int(params.get('page', 1))
        per_page = int(params.get('per_page', 10))
        transaction_type = params.get('transaction_type')
        payment_method = params.get('payment_method')
        
        # Build query for filtering
        query = {}
        if transaction_type and transaction_type != 'all':
            query['transaction_type'] = transaction_type
        if payment_method and payment_method != 'all':
            query['payment_method'] = payment_method
        
        # Debug: Print the query being used
        print(f"DEBUG - Filter parameters: transaction_type={transaction_type}, payment_method={payment_method}")
        print(f"DEBUG - MongoDB query: {query}")
        
        exec_command = self.mgdDB.db_trx.find(query)
        numb_recs = exec_command.count()
        transaction_records = exec_command.skip((page - 1) * per_page).limit(per_page)
        
        # Calculate total price for all matching records (not just current page)
        total_price_query = self.mgdDB.db_trx.find(query)
        total_price = 0
        for txn in total_price_query:
            price = txn.get('price', 0)
            if isinstance(price, (int, float)):
                total_price += price
        
        result = []
        for txn in transaction_records:
            i = {
                'transaction_id': txn.get('transaction_id', ''),
                'request_id': txn.get('request_id', ''),
                'user_id': txn.get('user_id', ''),
                'username': txn.get('username', ''),
                'email': txn.get('email', ''),
                'transaction_type': txn.get('transaction_type', ''),
                'premium_type': txn.get('premium_type', ''),
                'duration_months': txn.get('duration_months', 0),
                'price': txn.get('price', 0),
                'payment_method': txn.get('payment_method', ''),
                'notes': txn.get('notes', ''),
                'admin_username': txn.get('admin_username', ''),
                'status': txn.get('status', ''),
                'created_at': txn.get('created_at', ''),
                'expiry_date': txn.get('expiry_date', ''),
            }
            result.append(i)

        total_page = (numb_recs // per_page) + (1 if numb_recs % per_page != 0 else 0)

        return render_template(
            "admin/transactions.html",
            transactions=result,
            page=page,
            per_page=per_page,
            total_page=total_page,
            total_transactions=numb_recs,
            total_price=total_price,
            transaction_type=transaction_type,
            payment_method=payment_method
        )             
    # end def   

# end class
