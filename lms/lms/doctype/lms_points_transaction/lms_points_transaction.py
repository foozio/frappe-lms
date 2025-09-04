import frappe
from frappe.model.document import Document
from frappe.utils import now, cint, flt

class LMSPointsTransaction(Document):
	def validate(self):
		self.validate_points()
		self.set_transaction_date()
	
	def validate_points(self):
		if self.points <= 0:
			frappe.throw("Points must be greater than zero")
	
	def set_transaction_date(self):
		if not self.transaction_date:
			self.transaction_date = now()
	
	def on_submit(self):
		self.update_user_points()
		self.check_achievements()
	
	def on_cancel(self):
		self.reverse_user_points()
	
	def update_user_points(self):
		"""Update user's total and available points"""
		user_doc = frappe.get_doc("User", self.user)
		
		if self.transaction_type in ["Earned", "Bonus"]:
			points_to_add = cint(self.points * flt(self.multiplier))
			user_doc.total_points = cint(user_doc.total_points or 0) + points_to_add
			user_doc.available_points = cint(user_doc.available_points or 0) + points_to_add
		elif self.transaction_type in ["Spent", "Penalty"]:
			points_to_deduct = cint(self.points)
			user_doc.available_points = max(0, cint(user_doc.available_points or 0) - points_to_deduct)
		
		user_doc.save(ignore_permissions=True)
		self.update_leaderboards()
	
	def reverse_user_points(self):
		"""Reverse points when transaction is cancelled"""
		user_doc = frappe.get_doc("User", self.user)
		
		if self.transaction_type in ["Earned", "Bonus"]:
			points_to_deduct = cint(self.points * flt(self.multiplier))
			user_doc.total_points = max(0, cint(user_doc.total_points or 0) - points_to_deduct)
			user_doc.available_points = max(0, cint(user_doc.available_points or 0) - points_to_deduct)
		elif self.transaction_type in ["Spent", "Penalty"]:
			points_to_add = cint(self.points)
			user_doc.available_points = cint(user_doc.available_points or 0) + points_to_add
		
		user_doc.save(ignore_permissions=True)
		self.update_leaderboards()
	
	def update_leaderboards(self):
		"""Update leaderboard entries after points change"""
		from lms.lms.utils import update_user_leaderboard_position
		update_user_leaderboard_position(self.user)
	
	def check_achievements(self):
		"""Check if user has achieved any milestones"""
		user_doc = frappe.get_doc("User", self.user)
		total_points = cint(user_doc.total_points or 0)
		
		# Check point milestones for badge awards
		milestones = [100, 500, 1000, 2500, 5000, 10000]
		for milestone in milestones:
			if total_points >= milestone:
				# Check if badge already awarded
				badge_name = f"Points Master {milestone}"
				if not frappe.db.exists("LMS Badge Assignment", {
					"member": self.user,
					"badge": badge_name
				}):
					# Award milestone badge if it exists
					if frappe.db.exists("LMS Badge", badge_name):
						badge_assignment = frappe.get_doc({
							"doctype": "LMS Badge Assignment",
							"member": self.user,
							"badge": badge_name,
							"assignment_date": now()
						})
						badge_assignment.insert(ignore_permissions=True)

@frappe.whitelist()
def award_points(user, points, activity_type, reference_doc=None, reference_doctype=None, multiplier=1.0, description=None):
	"""Award points to a user for completing an activity"""
	try:
		points_transaction = frappe.get_doc({
			"doctype": "LMS Points Transaction",
			"user": user,
			"points": cint(points),
			"transaction_type": "Earned",
			"activity_type": activity_type,
			"reference_doc": reference_doc,
			"reference_doctype": reference_doctype,
			"multiplier": flt(multiplier),
			"description": description or f"Points earned for {activity_type}",
			"transaction_date": now()
		})
		points_transaction.insert(ignore_permissions=True)
		points_transaction.submit()
		
		return {
			"success": True,
			"points_awarded": cint(points * flt(multiplier)),
			"transaction": points_transaction.name
		}
	except Exception as e:
		frappe.log_error(f"Error awarding points: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def spend_points(user, points, description):
	"""Spend user points for rewards or purchases"""
	try:
		user_doc = frappe.get_doc("User", user)
		available_points = cint(user_doc.available_points or 0)
		
		if available_points < cint(points):
			return {
				"success": False,
				"error": "Insufficient points"
			}
		
		points_transaction = frappe.get_doc({
			"doctype": "LMS Points Transaction",
			"user": user,
			"points": cint(points),
			"transaction_type": "Spent",
			"activity_type": "reward_redemption",
			"description": description,
			"transaction_date": now()
		})
		points_transaction.insert(ignore_permissions=True)
		points_transaction.submit()
		
		return {
			"success": True,
			"points_spent": cint(points),
			"remaining_points": available_points - cint(points),
			"transaction": points_transaction.name
		}
	except Exception as e:
		frappe.log_error(f"Error spending points: {str(e)}")
		return {
			"success": False,
			"error": str(e)
		}

@frappe.whitelist()
def get_user_points(user=None):
	"""Get user's current points balance"""
	if not user:
		user = frappe.session.user
	
	user_doc = frappe.get_doc("User", user)
	
	# Get recent transactions
	recent_transactions = frappe.get_all(
		"LMS Points Transaction",
		filters={"user": user, "docstatus": 1},
		fields=["name", "points", "transaction_type", "activity_type", "description", "transaction_date"],
		order_by="transaction_date desc",
		limit=10
	)
	
	return {
		"total_points": cint(user_doc.total_points or 0),
		"available_points": cint(user_doc.available_points or 0),
		"recent_transactions": recent_transactions
	}

@frappe.whitelist()
def get_points_history(user=None, limit=50):
	"""Get user's points transaction history"""
	if not user:
		user = frappe.session.user
	
	transactions = frappe.get_all(
		"LMS Points Transaction",
		filters={"user": user, "docstatus": 1},
		fields=["name", "points", "transaction_type", "activity_type", "description", "transaction_date", "multiplier"],
		order_by="transaction_date desc",
		limit=cint(limit)
	)
	
	return {
		"transactions": transactions,
		"total_count": frappe.db.count("LMS Points Transaction", {"user": user, "docstatus": 1})
	}