import frappe
import json
from frappe.model.document import Document
from frappe.utils import now, getdate, add_days, date_diff, cint, flt
from datetime import datetime, timedelta

class LMSStreakRecord(Document):
	def validate(self):
		self.validate_streak_data()
		self.update_longest_streak()
	
	def validate_streak_data(self):
		"""Validate streak data consistency"""
		if self.current_streak < 0:
			self.current_streak = 0
		
		if self.longest_streak < self.current_streak:
			self.longest_streak = self.current_streak
		
		if self.total_days < 0:
			self.total_days = 0
	
	def update_longest_streak(self):
		"""Update longest streak if current streak exceeds it"""
		if self.current_streak > self.longest_streak:
			self.longest_streak = self.current_streak
			self.longest_streak_start = self.streak_start_date
			
			# Check for milestone achievements
			self.check_milestone_achievements()
	
	def check_milestone_achievements(self):
		"""Check and award milestone achievements"""
		milestones = [7, 14, 30, 60, 100, 365]  # Days
		current_milestones = self.milestones_achieved.split(",") if self.milestones_achieved else []
		
		for milestone in milestones:
			if self.current_streak >= milestone and str(milestone) not in current_milestones:
				current_milestones.append(str(milestone))
				
				# Award points for milestone
				self.award_milestone_points(milestone)
				
				# Create milestone badge if applicable
				self.award_milestone_badge(milestone)
		
		self.milestones_achieved = ",".join(current_milestones)
	
	def award_milestone_points(self, milestone):
		"""Award points for reaching streak milestone"""
		try:
			points_map = {
				7: 50,    # 1 week
				14: 100,  # 2 weeks
				30: 250,  # 1 month
				60: 500,  # 2 months
				100: 1000, # 100 days
				365: 2500  # 1 year
			}
			
			points = points_map.get(milestone, 0)
			if points > 0:
				from lms.lms.doctype.lms_points_transaction.lms_points_transaction import award_points
				award_points(
					user=self.user,
					points=points,
					activity_type="streak_milestone",
					description=f"Reached {milestone}-day learning streak milestone!",
					reference_doctype="LMS Streak Record",
					reference_doc=self.name
				)
			
		except Exception as e:
			frappe.log_error(f"Error awarding milestone points: {str(e)}")
	
	def award_milestone_badge(self, milestone):
		"""Award badge for streak milestone"""
		try:
			badge_map = {
				7: "Week Warrior",
				30: "Month Master",
				100: "Streak Legend",
				365: "Year Champion"
			}
			
			badge_name = badge_map.get(milestone)
			if badge_name:
				# Check if badge exists
				badge = frappe.db.get_value("LMS Badge", {"title": badge_name})
				if badge:
					# Check if user already has this badge
					existing = frappe.db.exists("LMS Badge Assignment", {
						"badge": badge,
						"member": self.user
					})
					
					if not existing:
						badge_assignment = frappe.get_doc({
							"doctype": "LMS Badge Assignment",
							"badge": badge,
							"member": self.user,
							"assignment_date": now(),
							"reason": f"Achieved {milestone}-day learning streak"
						})
						badge_assignment.insert(ignore_permissions=True)
			
		except Exception as e:
			frappe.log_error(f"Error awarding milestone badge: {str(e)}")
	
	def record_activity(self, activity_type, activity_data=None):
		"""Record daily activity for streak tracking"""
		today = getdate()
		
		# Initialize activity log if not exists
		if not self.activity_log:
			self.activity_log = json.dumps({})
		
		activity_log = json.loads(self.activity_log)
		today_str = str(today)
		
		# Initialize today's activities if not exists
		if today_str not in activity_log:
			activity_log[today_str] = []
		
		# Add activity
		activity_entry = {
			"type": activity_type,
			"timestamp": now(),
			"data": activity_data or {}
		}
		
		activity_log[today_str].append(activity_entry)
		
		# Keep only last 30 days of activity log
		cutoff_date = add_days(today, -30)
		activity_log = {k: v for k, v in activity_log.items() if getdate(k) >= cutoff_date}
		
		self.activity_log = json.dumps(activity_log)
		self.last_activity_date = today
		
		# Update streak
		self.update_streak()
		self.save(ignore_permissions=True)
	
	def update_streak(self):
		"""Update streak based on activity"""
		today = getdate()
		
		if not self.last_activity_date:
			# First activity
			self.current_streak = 1
			self.streak_start_date = today
			self.total_days = 1
			return
		
		days_since_last = date_diff(today, self.last_activity_date)
		
		if days_since_last == 0:
			# Same day activity, no streak change
			return
		elif days_since_last == 1:
			# Consecutive day, increment streak
			self.current_streak += 1
			self.total_days += 1
		elif days_since_last > 1:
			# Gap in activity, check for freeze usage
			if self.can_use_freeze() and days_since_last <= 2:
				# Use freeze to maintain streak
				self.use_streak_freeze()
				self.current_streak += 1
				self.total_days += 1
			else:
				# Reset streak
				self.current_streak = 1
				self.streak_start_date = today
				self.total_days += 1
	
	def can_use_freeze(self):
		"""Check if user can use streak freeze"""
		return self.freeze_count > 0 and not self.freeze_used_today
	
	def use_streak_freeze(self):
		"""Use a streak freeze"""
		if self.can_use_freeze():
			self.freeze_count -= 1
			self.freeze_used_today = True
			
			# Create activity for freeze usage
			self.create_freeze_activity()
	
	def create_freeze_activity(self):
		"""Create social activity for freeze usage"""
		try:
			activity = frappe.get_doc({
				"doctype": "LMS Social Activity",
				"user": self.user,
				"activity_type": "streak_freeze_used",
				"title": "Used Streak Freeze",
				"description": f"Used a streak freeze to maintain {self.current_streak}-day learning streak",
				"reference_doctype": "LMS Streak Record",
				"reference_name": self.name,
				"activity_date": now(),
				"is_public": 0  # Private activity
			})
			activity.insert(ignore_permissions=True)
		except:
			pass  # Don't fail if social activity creation fails
	
	def reset_daily_flags(self):
		"""Reset daily flags (called by scheduler)"""
		self.freeze_used_today = False
		self.save(ignore_permissions=True)

@frappe.whitelist()
def get_user_streak(user=None):
	"""Get user's current streak information"""
	if not user:
		user = frappe.session.user
	
	streak_record = frappe.db.get_value(
		"LMS Streak Record",
		{"user": user, "is_active": 1},
		["current_streak", "longest_streak", "total_days", "last_activity_date", 
		 "freeze_count", "milestones_achieved", "streak_start_date"],
		as_dict=True
	)
	
	if not streak_record:
		# Create new streak record
		streak_record = create_streak_record(user)
	
	# Calculate streak status
	today = getdate()
	days_since_last = 0
	if streak_record.last_activity_date:
		days_since_last = date_diff(today, streak_record.last_activity_date)
	
	streak_record.update({
		"days_since_last_activity": days_since_last,
		"is_streak_active": days_since_last <= 1,
		"can_use_freeze": days_since_last > 1 and streak_record.freeze_count > 0,
		"milestones_list": streak_record.milestones_achieved.split(",") if streak_record.milestones_achieved else []
	})
	
	return streak_record

@frappe.whitelist()
def record_learning_activity(user=None, activity_type="general", activity_data=None):
	"""Record a learning activity for streak tracking"""
	if not user:
		user = frappe.session.user
	
	try:
		# Get or create streak record
		streak_record = frappe.db.get_value("LMS Streak Record", {"user": user, "is_active": 1})
		
		if not streak_record:
			streak_doc = create_streak_record(user)
		else:
			streak_doc = frappe.get_doc("LMS Streak Record", streak_record)
		
		# Record the activity
		streak_doc.record_activity(activity_type, activity_data)
		
		return {
			"success": True,
			"current_streak": streak_doc.current_streak,
			"message": f"Activity recorded! Current streak: {streak_doc.current_streak} days"
		}
		
	except Exception as e:
		frappe.log_error(f"Error recording learning activity: {str(e)}")
		return {"success": False, "message": "Failed to record activity"}

@frappe.whitelist()
def use_streak_freeze(user=None):
	"""Use a streak freeze to maintain streak"""
	if not user:
		user = frappe.session.user
	
	try:
		streak_record = frappe.db.get_value("LMS Streak Record", {"user": user, "is_active": 1})
		
		if not streak_record:
			return {"success": False, "message": "No active streak record found"}
		
		streak_doc = frappe.get_doc("LMS Streak Record", streak_record)
		
		if not streak_doc.can_use_freeze():
			return {"success": False, "message": "Cannot use freeze (no freezes available or already used today)"}
		
		streak_doc.use_streak_freeze()
		streak_doc.save(ignore_permissions=True)
		
		return {
			"success": True,
			"message": f"Streak freeze used! Remaining freezes: {streak_doc.freeze_count}",
			"remaining_freezes": streak_doc.freeze_count
		}
		
	except Exception as e:
		frappe.log_error(f"Error using streak freeze: {str(e)}")
		return {"success": False, "message": "Failed to use streak freeze"}

@frappe.whitelist()
def get_streak_leaderboard(limit=50):
	"""Get streak leaderboard"""
	leaderboard = frappe.get_all(
		"LMS Streak Record",
		filters={"is_active": 1, "current_streak": [">=", 1]},
		fields=["user", "current_streak", "longest_streak", "total_days", "streak_start_date"],
		order_by="current_streak desc, longest_streak desc",
		limit=limit
	)
	
	# Enrich with user details
	for idx, entry in enumerate(leaderboard, 1):
		user_details = frappe.db.get_value(
			"User",
			entry.user,
			["full_name", "user_image"],
			as_dict=True
		)
		entry.update(user_details or {})
		entry.rank = idx
	
	return leaderboard

@frappe.whitelist()
def get_user_activity_calendar(user=None, months=3):
	"""Get user's activity calendar for streak visualization"""
	if not user:
		user = frappe.session.user
	
	streak_record = frappe.db.get_value(
		"LMS Streak Record",
		{"user": user, "is_active": 1},
		["activity_log"],
		as_dict=True
	)
	
	if not streak_record or not streak_record.activity_log:
		return {}
	
	try:
		activity_log = json.loads(streak_record.activity_log)
		
		# Filter to requested months
		today = getdate()
		start_date = add_days(today, -30 * months)
		
		filtered_log = {}
		for date_str, activities in activity_log.items():
			if getdate(date_str) >= start_date:
				filtered_log[date_str] = {
					"activity_count": len(activities),
					"activity_types": list(set([act["type"] for act in activities])),
					"has_activity": len(activities) > 0
				}
		
		return filtered_log
		
	except Exception as e:
		frappe.log_error(f"Error getting activity calendar: {str(e)}")
		return {}

def create_streak_record(user):
	"""Create a new streak record for user"""
	streak_record = frappe.get_doc({
		"doctype": "LMS Streak Record",
		"user": user,
		"streak_type": "Daily Learning",
		"current_streak": 0,
		"longest_streak": 0,
		"total_days": 0,
		"is_active": 1,
		"freeze_count": 3,
		"activity_log": json.dumps({})
	})
	streak_record.insert(ignore_permissions=True)
	return streak_record

@frappe.whitelist()
def update_all_streaks():
	"""Update all user streaks (called by daily scheduler)"""
	today = getdate()
	yesterday = add_days(today, -1)
	
	# Get all active streak records
	active_streaks = frappe.get_all(
		"LMS Streak Record",
		filters={"is_active": 1},
		fields=["name", "user", "last_activity_date", "current_streak"]
	)
	
	updated_count = 0
	for streak in active_streaks:
		try:
			streak_doc = frappe.get_doc("LMS Streak Record", streak.name)
			
			# Reset daily flags
			streak_doc.reset_daily_flags()
			
			# Check if streak should be broken
			if streak.last_activity_date:
				days_since_last = date_diff(today, streak.last_activity_date)
				
				# Break streak if more than 2 days without activity (allowing for 1 day grace period)
				if days_since_last > 2 and streak.current_streak > 0:
					streak_doc.current_streak = 0
					streak_doc.streak_start_date = None
					streak_doc.save(ignore_permissions=True)
			
			updated_count += 1
			
		except Exception as e:
			frappe.log_error(f"Error updating streak for user {streak.user}: {str(e)}")
			continue
	
	frappe.logger().info(f"Updated {updated_count} streak records")
	return updated_count

def award_daily_streak_points():
	"""Award daily points for maintaining streaks"""
	today = getdate()
	
	# Get users with active streaks
	active_streaks = frappe.get_all(
		"LMS Streak Record",
		filters={
			"is_active": 1,
			"current_streak": [">=", 1],
			"last_activity_date": today
		},
		fields=["user", "current_streak"]
	)
	
	for streak in active_streaks:
		try:
			# Award base points for maintaining streak
			base_points = 5
			
			# Bonus points for longer streaks
			bonus_points = 0
			if streak.current_streak >= 7:
				bonus_points = 2
			if streak.current_streak >= 30:
				bonus_points = 5
			if streak.current_streak >= 100:
				bonus_points = 10
			
			total_points = base_points + bonus_points
			
			from lms.lms.doctype.lms_points_transaction.lms_points_transaction import award_points
			award_points(
				user=streak.user,
				points=total_points,
				activity_type="daily_streak",
				description=f"Daily streak bonus - {streak.current_streak} days",
				reference_doctype="LMS Streak Record",
				reference_doc=streak.name
			)
			
		except Exception as e:
			frappe.log_error(f"Error awarding streak points to user {streak.user}: {str(e)}")
			continue