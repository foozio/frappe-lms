# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate


class LMSSocialActivity(Document):
	def before_insert(self):
		"""Set activity date if not provided"""
		if not self.activity_date:
			self.activity_date = now_datetime()

	def validate(self):
		"""Validate social activity data"""
		self.validate_user_permissions()
		self.validate_activity_content()

	def validate_user_permissions(self):
		"""Ensure user can create social activities"""
		if not frappe.has_permission("LMS Social Activity", "create", user=self.user):
			frappe.throw(_("User {0} does not have permission to create social activities").format(self.user))

	def validate_activity_content(self):
		"""Validate activity content based on type"""
		if self.activity_type in ["achievement", "badge_earned", "course_completed", "challenge_won"] and not self.reference_doc:
			frappe.throw(_("Reference document is required for activity type {0}").format(self.activity_type))

	def after_insert(self):
		"""Handle post-creation activities"""
		self.update_user_social_metrics()
		self.notify_followers()

	def update_user_social_metrics(self):
		"""Update user's social activity metrics"""
		# This could be used to update user's activity count or other social metrics
		pass

	def notify_followers(self):
		"""Notify followers about new social activity"""
		if self.visibility == "public":
			# Implementation for notifying followers would go here
			# This could integrate with existing notification system
			pass

	@frappe.whitelist()
	def add_like(self):
		"""Add a like to this social activity"""
		user = frappe.session.user
		
		# Check if user already liked this activity
		existing_like = frappe.db.exists("LMS Social Activity Like", {
			"social_activity": self.name,
			"user": user
		})
		
		if existing_like:
			frappe.throw(_("You have already liked this activity"))
		
		# Create like record (assuming we have a child table or separate doctype)
		# For now, just increment the counter
		self.likes_count = (self.likes_count or 0) + 1
		self.save(ignore_permissions=True)
		
		return {"likes_count": self.likes_count}

	@frappe.whitelist()
	def remove_like(self):
		"""Remove a like from this social activity"""
		user = frappe.session.user
		
		# Check if user has liked this activity
		existing_like = frappe.db.exists("LMS Social Activity Like", {
			"social_activity": self.name,
			"user": user
		})
		
		if not existing_like:
			frappe.throw(_("You have not liked this activity"))
		
		# Remove like record and decrement counter
		self.likes_count = max((self.likes_count or 0) - 1, 0)
		self.save(ignore_permissions=True)
		
		return {"likes_count": self.likes_count}


@frappe.whitelist()
def create_social_activity(activity_type, reference_doc=None, content=None, user=None):
	"""Create a new social activity record"""
	if not user:
		user = frappe.session.user
	
	# Validate activity type
	valid_types = ["achievement", "badge_earned", "course_completed", "challenge_won", "streak_milestone"]
	if activity_type not in valid_types:
		frappe.throw(_("Invalid activity type: {0}").format(activity_type))
	
	# Create social activity
	social_activity = frappe.get_doc({
		"doctype": "LMS Social Activity",
		"user": user,
		"activity_type": activity_type,
		"reference_doc": reference_doc,
		"content": content or get_default_content(activity_type, reference_doc),
		"activity_date": now_datetime(),
		"visibility": "public"
	})
	
	social_activity.insert(ignore_permissions=True)
	return social_activity


def get_default_content(activity_type, reference_doc=None):
	"""Generate default content for social activity"""
	content_map = {
		"achievement": "Unlocked a new achievement!",
		"badge_earned": "Earned a new badge!",
		"course_completed": f"Completed course: {reference_doc}" if reference_doc else "Completed a course!",
		"challenge_won": f"Won challenge: {reference_doc}" if reference_doc else "Won a challenge!",
		"streak_milestone": "Reached a new streak milestone!"
	}
	
	return content_map.get(activity_type, "New activity!")


@frappe.whitelist()
def get_user_social_feed(user=None, limit=20, offset=0):
	"""Get social activity feed for a user"""
	if not user:
		user = frappe.session.user
	
	# Get public activities and user's own activities
	activities = frappe.db.sql("""
		SELECT 
			sa.name,
			sa.user,
			sa.activity_type,
			sa.reference_doc,
			sa.content,
			sa.activity_date,
			sa.likes_count,
			sa.comments_count,
			u.full_name as user_name,
			u.user_image
		FROM `tabLMS Social Activity` sa
		LEFT JOIN `tabUser` u ON sa.user = u.name
		WHERE 
			(sa.visibility = 'public' OR sa.user = %(user)s)
			AND sa.docstatus = 1
		ORDER BY sa.activity_date DESC
		LIMIT %(limit)s OFFSET %(offset)s
	""", {
		"user": user,
		"limit": limit,
		"offset": offset
	}, as_dict=True)
	
	return activities


@frappe.whitelist()
def get_activity_stats(user=None):
	"""Get social activity statistics for a user"""
	if not user:
		user = frappe.session.user
	
	stats = frappe.db.sql("""
		SELECT 
			COUNT(*) as total_activities,
			SUM(likes_count) as total_likes_received,
			SUM(comments_count) as total_comments_received,
			COUNT(CASE WHEN activity_type = 'achievement' THEN 1 END) as achievements,
			COUNT(CASE WHEN activity_type = 'badge_earned' THEN 1 END) as badges_earned,
			COUNT(CASE WHEN activity_type = 'course_completed' THEN 1 END) as courses_completed,
			COUNT(CASE WHEN activity_type = 'challenge_won' THEN 1 END) as challenges_won,
			COUNT(CASE WHEN activity_type = 'streak_milestone' THEN 1 END) as streak_milestones
		FROM `tabLMS Social Activity`
		WHERE user = %(user)s AND docstatus = 1
	""", {"user": user}, as_dict=True)
	
	return stats[0] if stats else {}