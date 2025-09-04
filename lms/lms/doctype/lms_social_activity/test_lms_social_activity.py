# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

import frappe
import unittest
from frappe.utils import now_datetime, add_days


class TestLMSSocialActivity(unittest.TestCase):
	def setUp(self):
		"""Set up test data"""
		self.test_user = "test@example.com"
		
		# Create test user if not exists
		if not frappe.db.exists("User", self.test_user):
			test_user_doc = frappe.get_doc({
				"doctype": "User",
				"email": self.test_user,
				"first_name": "Test",
				"last_name": "User",
				"send_welcome_email": 0
			})
			test_user_doc.insert(ignore_permissions=True)

	def tearDown(self):
		"""Clean up test data"""
		# Delete test social activities
		frappe.db.delete("LMS Social Activity", {"user": self.test_user})
		frappe.db.commit()

	def test_create_social_activity(self):
		"""Test creating a social activity"""
		social_activity = frappe.get_doc({
			"doctype": "LMS Social Activity",
			"user": self.test_user,
			"activity_type": "achievement",
			"content": "Test achievement unlocked!",
			"visibility": "public"
		})
		
		social_activity.insert()
		
		self.assertEqual(social_activity.user, self.test_user)
		self.assertEqual(social_activity.activity_type, "achievement")
		self.assertEqual(social_activity.visibility, "public")
		self.assertIsNotNone(social_activity.activity_date)

	def test_activity_validation(self):
		"""Test social activity validation"""
		# Test missing reference_doc for achievement
		with self.assertRaises(frappe.ValidationError):
			social_activity = frappe.get_doc({
				"doctype": "LMS Social Activity",
				"user": self.test_user,
				"activity_type": "achievement",
				"visibility": "public"
			})
			social_activity.insert()

	def test_like_functionality(self):
		"""Test like/unlike functionality"""
		social_activity = frappe.get_doc({
			"doctype": "LMS Social Activity",
			"user": self.test_user,
			"activity_type": "streak_milestone",
			"content": "Reached 7-day streak!",
			"visibility": "public"
		})
		
		social_activity.insert()
		
		# Test adding like
		result = social_activity.add_like()
		self.assertEqual(result["likes_count"], 1)
		
		# Test removing like
		result = social_activity.remove_like()
		self.assertEqual(result["likes_count"], 0)

	def test_create_social_activity_api(self):
		"""Test create_social_activity API function"""
		from lms.lms.doctype.lms_social_activity.lms_social_activity import create_social_activity
		
		# Set current user
		frappe.set_user(self.test_user)
		
		social_activity = create_social_activity(
			activity_type="course_completed",
			reference_doc="Test Course",
			content="Completed Test Course successfully!"
		)
		
		self.assertEqual(social_activity.user, self.test_user)
		self.assertEqual(social_activity.activity_type, "course_completed")
		self.assertEqual(social_activity.reference_doc, "Test Course")

	def test_get_user_social_feed(self):
		"""Test getting user social feed"""
		from lms.lms.doctype.lms_social_activity.lms_social_activity import get_user_social_feed
		
		# Create test activities
		for i in range(3):
			social_activity = frappe.get_doc({
				"doctype": "LMS Social Activity",
				"user": self.test_user,
				"activity_type": "streak_milestone",
				"content": f"Test activity {i+1}",
				"visibility": "public"
			})
			social_activity.insert()
			social_activity.submit()
		
		# Get social feed
		feed = get_user_social_feed(user=self.test_user, limit=5)
		
		self.assertGreaterEqual(len(feed), 3)
		self.assertEqual(feed[0]["user"], self.test_user)

	def test_get_activity_stats(self):
		"""Test getting activity statistics"""
		from lms.lms.doctype.lms_social_activity.lms_social_activity import get_activity_stats
		
		# Create test activities of different types
		activity_types = ["achievement", "badge_earned", "course_completed"]
		
		for activity_type in activity_types:
			social_activity = frappe.get_doc({
				"doctype": "LMS Social Activity",
				"user": self.test_user,
				"activity_type": activity_type,
				"reference_doc": "Test Reference" if activity_type != "streak_milestone" else None,
				"content": f"Test {activity_type}",
				"visibility": "public"
			})
			social_activity.insert()
			social_activity.submit()
		
		# Get activity stats
		stats = get_activity_stats(user=self.test_user)
		
		self.assertGreaterEqual(stats.get("total_activities", 0), 3)
		self.assertGreaterEqual(stats.get("achievements", 0), 1)
		self.assertGreaterEqual(stats.get("badges_earned", 0), 1)
		self.assertGreaterEqual(stats.get("courses_completed", 0), 1)

	def test_visibility_settings(self):
		"""Test different visibility settings"""
		# Create private activity
		private_activity = frappe.get_doc({
			"doctype": "LMS Social Activity",
			"user": self.test_user,
			"activity_type": "streak_milestone",
			"content": "Private achievement",
			"visibility": "private"
		})
		private_activity.insert()
		
		# Create public activity
		public_activity = frappe.get_doc({
			"doctype": "LMS Social Activity",
			"user": self.test_user,
			"activity_type": "streak_milestone",
			"content": "Public achievement",
			"visibility": "public"
		})
		public_activity.insert()
		
		self.assertEqual(private_activity.visibility, "private")
		self.assertEqual(public_activity.visibility, "public")