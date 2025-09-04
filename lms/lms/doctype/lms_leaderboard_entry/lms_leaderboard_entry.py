import frappe
import json
from frappe.model.document import Document
from frappe.utils import now, getdate, cint, flt, add_days, get_datetime
from datetime import datetime, timedelta

class LMSLeaderboardEntry(Document):
	def validate(self):
		self.validate_period_dates()
		self.set_last_updated()
	
	def validate_period_dates(self):
		"""Validate period start and end dates"""
		if self.period_start and self.period_end:
			if get_datetime(self.period_start) >= get_datetime(self.period_end):
				frappe.throw("Period start date must be before period end date")
	
	def set_last_updated(self):
		self.last_updated = now()
	
	def on_update(self):
		self.update_rank_changes()
	
	def update_rank_changes(self):
		"""Track rank position changes"""
		if self.has_value_changed("rank_position"):
			if self.get_doc_before_save():
				self.previous_rank = self.get_doc_before_save().rank_position
				
				# Create notification for significant rank changes
				if self.previous_rank and abs(self.rank_position - self.previous_rank) >= 5:
					self.create_rank_change_notification()
	
	def create_rank_change_notification(self):
		"""Create notification for rank changes"""
		try:
			rank_change = self.previous_rank - self.rank_position
			if rank_change > 0:
				message = f"Congratulations! You've moved up {rank_change} positions to rank #{self.rank_position} in {self.leaderboard_type} leaderboard!"
			else:
				message = f"You've moved down {abs(rank_change)} positions to rank #{self.rank_position} in {self.leaderboard_type} leaderboard. Keep going!"
			
			# Create notification (if notification system exists)
			frappe.get_doc({
				"doctype": "Notification Log",
				"subject": "Leaderboard Rank Update",
				"email_content": message,
				"for_user": self.user,
				"type": "Alert"
			}).insert(ignore_permissions=True)
			
		except Exception as e:
			frappe.log_error(f"Error creating rank change notification: {str(e)}")

@frappe.whitelist()
def get_leaderboard(leaderboard_type, period_type="All Time", category=None, limit=50):
	"""Get leaderboard entries for a specific type and period"""
	filters = {
		"leaderboard_type": leaderboard_type,
		"period_type": period_type,
		"is_active": 1
	}
	
	if category:
		filters["category"] = category
	
	entries = frappe.get_all(
		"LMS Leaderboard Entry",
		filters=filters,
		fields=["user", "score", "rank_position", "previous_rank", "achievements", "additional_data"],
		order_by="rank_position asc",
		limit=limit
	)
	
	# Enrich with user details
	for entry in entries:
		user_details = frappe.db.get_value(
			"User",
			entry.user,
			["full_name", "user_image", "bio"],
			as_dict=True
		)
		entry.update(user_details or {})
		
		# Parse additional data if exists
		if entry.additional_data:
			try:
				entry.additional_data = json.loads(entry.additional_data)
			except:
				entry.additional_data = {}
		
		# Calculate rank change
		if entry.previous_rank:
			entry.rank_change = entry.previous_rank - entry.rank_position
		else:
			entry.rank_change = 0
	
	return entries

@frappe.whitelist()
def get_user_leaderboard_position(user=None, leaderboard_type=None):
	"""Get user's position across different leaderboards"""
	if not user:
		user = frappe.session.user
	
	filters = {"user": user, "is_active": 1}
	if leaderboard_type:
		filters["leaderboard_type"] = leaderboard_type
	
	positions = frappe.get_all(
		"LMS Leaderboard Entry",
		filters=filters,
		fields=["leaderboard_type", "category", "score", "rank_position", "previous_rank", "period_type"],
		order_by="leaderboard_type, period_type"
	)
	
	# Calculate rank changes and add context
	for position in positions:
		if position.previous_rank:
			position.rank_change = position.previous_rank - position.rank_position
		else:
			position.rank_change = 0
		
		# Get total participants in this leaderboard
		total_participants = frappe.db.count("LMS Leaderboard Entry", {
			"leaderboard_type": position.leaderboard_type,
			"period_type": position.period_type,
			"category": position.category,
			"is_active": 1
		})
		position.total_participants = total_participants
		position.percentile = round((1 - (position.rank_position - 1) / total_participants) * 100, 1)
	
	return positions

@frappe.whitelist()
def update_leaderboard_entries(leaderboard_type, period_type="All Time", category=None):
	"""Update leaderboard entries for a specific type and period"""
	try:
		if leaderboard_type == "Points":
			update_points_leaderboard(period_type, category)
		elif leaderboard_type == "Course Completion":
			update_course_completion_leaderboard(period_type, category)
		elif leaderboard_type == "Streak":
			update_streak_leaderboard(period_type, category)
		elif leaderboard_type == "Challenge":
			update_challenge_leaderboard(period_type, category)
		elif leaderboard_type == "Badges":
			update_badges_leaderboard(period_type, category)
		elif leaderboard_type == "Activity":
			update_activity_leaderboard(period_type, category)
		elif leaderboard_type == "Engagement":
			update_engagement_leaderboard(period_type, category)
		
		return {"success": True, "message": f"{leaderboard_type} leaderboard updated successfully"}
		
	except Exception as e:
		frappe.log_error(f"Error updating {leaderboard_type} leaderboard: {str(e)}")
		return {"success": False, "message": f"Failed to update {leaderboard_type} leaderboard"}

def update_points_leaderboard(period_type="All Time", category=None):
	"""Update points leaderboard"""
	period_start, period_end = get_period_dates(period_type)
	
	# Get points data
	query = """
		SELECT 
			user,
			SUM(CASE WHEN transaction_type IN ('Earned', 'Bonus') THEN points ELSE -points END) as total_points
		FROM `tabLMS Points Transaction`
		WHERE docstatus = 1
	"""
	
	params = []
	if period_start and period_end:
		query += " AND transaction_date BETWEEN %s AND %s"
		params.extend([period_start, period_end])
	
	query += " GROUP BY user HAVING total_points > 0 ORDER BY total_points DESC"
	
	results = frappe.db.sql(query, params, as_dict=True)
	
	# Update leaderboard entries
	update_leaderboard_from_results("Points", period_type, category, results, "total_points")

def update_course_completion_leaderboard(period_type="All Time", category=None):
	"""Update course completion leaderboard"""
	period_start, period_end = get_period_dates(period_type)
	
	# Get course completion data
	query = """
		SELECT 
			member as user,
			COUNT(*) as completed_courses
		FROM `tabLMS Course Progress`
		WHERE status = 'Complete'
	"""
	
	params = []
	if period_start and period_end:
		query += " AND modified BETWEEN %s AND %s"
		params.extend([period_start, period_end])
	
	if category:
		query += " AND course IN (SELECT name FROM `tabLMS Course` WHERE category = %s)"
		params.append(category)
	
	query += " GROUP BY member ORDER BY completed_courses DESC"
	
	results = frappe.db.sql(query, params, as_dict=True)
	
	# Update leaderboard entries
	update_leaderboard_from_results("Course Completion", period_type, category, results, "completed_courses")

def update_streak_leaderboard(period_type="All Time", category=None):
	"""Update streak leaderboard"""
	# Get current streak data
	query = """
		SELECT 
			user,
			current_streak as streak_days
		FROM `tabLMS Streak Record`
		WHERE is_active = 1 AND current_streak > 0
		ORDER BY current_streak DESC
	"""
	
	results = frappe.db.sql(query, as_dict=True)
	
	# Update leaderboard entries
	update_leaderboard_from_results("Streak", period_type, category, results, "streak_days")

def update_challenge_leaderboard(period_type="All Time", category=None):
	"""Update challenge completion leaderboard"""
	period_start, period_end = get_period_dates(period_type)
	
	# Get challenge completion data
	query = """
		SELECT 
			user,
			COUNT(*) as completed_challenges,
			SUM(points_earned) as total_challenge_points
		FROM `tabLMS Challenge Participation`
		WHERE status = 'Completed'
	"""
	
	params = []
	if period_start and period_end:
		query += " AND completion_date BETWEEN %s AND %s"
		params.extend([period_start, period_end])
	
	query += " GROUP BY user ORDER BY completed_challenges DESC, total_challenge_points DESC"
	
	results = frappe.db.sql(query, params, as_dict=True)
	
	# Use completed challenges as primary score
	for result in results:
		result["score_value"] = result["completed_challenges"]
		result["additional_data"] = json.dumps({
			"completed_challenges": result["completed_challenges"],
			"total_challenge_points": result["total_challenge_points"]
		})
	
	# Update leaderboard entries
	update_leaderboard_from_results("Challenge", period_type, category, results, "score_value")

def update_badges_leaderboard(period_type="All Time", category=None):
	"""Update badges leaderboard"""
	# Get badge count data
	query = """
		SELECT 
			member as user,
			COUNT(*) as total_badges
		FROM `tabLMS Badge Assignment`
		WHERE assignment_date IS NOT NULL
		GROUP BY member
		ORDER BY total_badges DESC
	"""
	
	results = frappe.db.sql(query, as_dict=True)
	
	# Update leaderboard entries
	update_leaderboard_from_results("Badges", period_type, category, results, "total_badges")

def update_activity_leaderboard(period_type="All Time", category=None):
	"""Update activity leaderboard based on social activities"""
	period_start, period_end = get_period_dates(period_type)
	
	# Get activity data
	query = """
		SELECT 
			user,
			COUNT(*) as total_activities
		FROM `tabLMS Social Activity`
		WHERE is_public = 1
	"""
	
	params = []
	if period_start and period_end:
		query += " AND activity_date BETWEEN %s AND %s"
		params.extend([period_start, period_end])
	
	query += " GROUP BY user ORDER BY total_activities DESC"
	
	results = frappe.db.sql(query, params, as_dict=True)
	
	# Update leaderboard entries
	update_leaderboard_from_results("Activity", period_type, category, results, "total_activities")

def update_engagement_leaderboard(period_type="All Time", category=None):
	"""Update engagement leaderboard based on multiple factors"""
	period_start, period_end = get_period_dates(period_type)
	
	# Calculate engagement score based on multiple factors
	query = """
		SELECT 
			u.name as user,
			(
				COALESCE(points.total_points, 0) * 0.3 +
				COALESCE(courses.completed_courses, 0) * 50 * 0.25 +
				COALESCE(streaks.current_streak, 0) * 10 * 0.2 +
				COALESCE(challenges.completed_challenges, 0) * 30 * 0.15 +
				COALESCE(activities.total_activities, 0) * 5 * 0.1
			) as engagement_score
		FROM `tabUser` u
		LEFT JOIN (
			SELECT user, SUM(CASE WHEN transaction_type IN ('Earned', 'Bonus') THEN points ELSE -points END) as total_points
			FROM `tabLMS Points Transaction`
			WHERE docstatus = 1
			GROUP BY user
		) points ON u.name = points.user
		LEFT JOIN (
			SELECT member as user, COUNT(*) as completed_courses
			FROM `tabLMS Course Progress`
			WHERE status = 'Complete'
			GROUP BY member
		) courses ON u.name = courses.user
		LEFT JOIN (
			SELECT user, current_streak
			FROM `tabLMS Streak Record`
			WHERE is_active = 1
		) streaks ON u.name = streaks.user
		LEFT JOIN (
			SELECT user, COUNT(*) as completed_challenges
			FROM `tabLMS Challenge Participation`
			WHERE status = 'Completed'
			GROUP BY user
		) challenges ON u.name = challenges.user
		LEFT JOIN (
			SELECT user, COUNT(*) as total_activities
			FROM `tabLMS Social Activity`
			WHERE is_public = 1
			GROUP BY user
		) activities ON u.name = activities.user
		WHERE u.enabled = 1 AND u.user_type = 'System User'
		HAVING engagement_score > 0
		ORDER BY engagement_score DESC
	"""
	
	results = frappe.db.sql(query, as_dict=True)
	
	# Update leaderboard entries
	update_leaderboard_from_results("Engagement", period_type, category, results, "engagement_score")

def update_leaderboard_from_results(leaderboard_type, period_type, category, results, score_field):
	"""Update leaderboard entries from query results"""
	# Clear existing entries for this leaderboard
	filters = {
		"leaderboard_type": leaderboard_type,
		"period_type": period_type
	}
	if category:
		filters["category"] = category
	
	existing_entries = frappe.get_all("LMS Leaderboard Entry", filters=filters, fields=["name", "user", "rank_position"])
	
	# Create a map of existing entries for rank comparison
	existing_ranks = {entry.user: entry.rank_position for entry in existing_entries}
	
	# Delete existing entries
	for entry in existing_entries:
		frappe.delete_doc("LMS Leaderboard Entry", entry.name, ignore_permissions=True)
	
	# Create new entries
	period_start, period_end = get_period_dates(period_type)
	
	for idx, result in enumerate(results, 1):
		try:
			entry_data = {
				"doctype": "LMS Leaderboard Entry",
				"user": result["user"],
				"leaderboard_type": leaderboard_type,
				"category": category,
				"score": result[score_field],
				"rank_position": idx,
				"previous_rank": existing_ranks.get(result["user"]),
				"period_type": period_type,
				"period_start": period_start,
				"period_end": period_end,
				"is_active": 1,
				"last_updated": now()
			}
			
			# Add additional data if present
			if "additional_data" in result:
				entry_data["additional_data"] = result["additional_data"]
			
			entry = frappe.get_doc(entry_data)
			entry.insert(ignore_permissions=True)
			
		except Exception as e:
			frappe.log_error(f"Error creating leaderboard entry for user {result['user']}: {str(e)}")
			continue

def get_period_dates(period_type):
	"""Get start and end dates for a period type"""
	if period_type == "All Time":
		return None, None
	
	now_date = getdate()
	
	if period_type == "Daily":
		return now_date, now_date
	elif period_type == "Weekly":
		start_date = add_days(now_date, -now_date.weekday())
		end_date = add_days(start_date, 6)
		return start_date, end_date
	elif period_type == "Monthly":
		start_date = now_date.replace(day=1)
		if now_date.month == 12:
			end_date = now_date.replace(year=now_date.year + 1, month=1, day=1) - timedelta(days=1)
		else:
			end_date = now_date.replace(month=now_date.month + 1, day=1) - timedelta(days=1)
		return start_date, end_date
	elif period_type == "Quarterly":
		quarter = (now_date.month - 1) // 3 + 1
		start_month = (quarter - 1) * 3 + 1
		start_date = now_date.replace(month=start_month, day=1)
		if quarter == 4:
			end_date = now_date.replace(year=now_date.year + 1, month=1, day=1) - timedelta(days=1)
		else:
			end_date = now_date.replace(month=start_month + 3, day=1) - timedelta(days=1)
		return start_date, end_date
	elif period_type == "Yearly":
		start_date = now_date.replace(month=1, day=1)
		end_date = now_date.replace(month=12, day=31)
		return start_date, end_date
	
	return None, None

@frappe.whitelist()
def get_leaderboard_categories(leaderboard_type):
	"""Get available categories for a leaderboard type"""
	categories = frappe.get_all(
		"LMS Leaderboard Entry",
		filters={"leaderboard_type": leaderboard_type, "category": ["!=", ""]},
		fields=["category"],
		distinct=True,
		order_by="category"
	)
	
	return [cat.category for cat in categories if cat.category]

@frappe.whitelist()
def refresh_all_leaderboards():
	"""Refresh all leaderboard types (called by scheduler)"""
	leaderboard_types = ["Points", "Course Completion", "Streak", "Challenge", "Badges", "Activity", "Engagement"]
	period_types = ["All Time", "Daily", "Weekly", "Monthly"]
	
	updated_count = 0
	for leaderboard_type in leaderboard_types:
		for period_type in period_types:
			try:
				update_leaderboard_entries(leaderboard_type, period_type)
				updated_count += 1
			except Exception as e:
				frappe.log_error(f"Error updating {leaderboard_type} {period_type} leaderboard: {str(e)}")
				continue
	
	frappe.logger().info(f"Updated {updated_count} leaderboards")
	return updated_count