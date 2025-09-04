import frappe
import json
from frappe.model.document import Document
from frappe.utils import now, getdate, cint, flt
from datetime import datetime

class LMSChallengeParticipation(Document):
	def validate(self):
		self.validate_unique_participation()
		self.validate_challenge_eligibility()
		self.set_join_date()
	
	def validate_unique_participation(self):
		"""Ensure user can only participate once in a challenge"""
		if self.is_new():
			existing = frappe.db.exists("LMS Challenge Participation", {
				"challenge": self.challenge,
				"user": self.user,
				"status": ["in", ["Active", "Completed"]]
			})
			if existing:
				frappe.throw("User is already participating in this challenge")
	
	def validate_challenge_eligibility(self):
		"""Validate if user is eligible to participate"""
		if self.is_new():
			challenge = frappe.get_doc("LMS Challenge", self.challenge)
			can_participate, message = challenge.can_participate(self.user)
			if not can_participate:
				frappe.throw(message)
	
	def set_join_date(self):
		if not self.join_date:
			self.join_date = now()
	
	def on_update(self):
		self.update_challenge_stats()
		self.update_rank_position()
	
	def update_challenge_stats(self):
		"""Update challenge statistics when participation changes"""
		if self.has_value_changed("status"):
			challenge = frappe.get_doc("LMS Challenge", self.challenge)
			
			# Update participant count
			active_participants = frappe.db.count("LMS Challenge Participation", {
				"challenge": self.challenge,
				"status": "Active"
			})
			
			challenge.current_participants = active_participants
			challenge.save(ignore_permissions=True)
	
	def update_rank_position(self):
		"""Update user's rank position in the challenge"""
		if self.status in ["Active", "Completed"]:
			rank = frappe.db.sql("""
				SELECT COUNT(*) + 1 as rank_position
				FROM `tabLMS Challenge Participation`
				WHERE challenge = %s 
				AND status IN ('Active', 'Completed')
				AND (
					progress_percentage > %s 
					OR (progress_percentage = %s AND completion_date < %s)
				)
			""", (self.challenge, self.progress_percentage, self.progress_percentage, 
				  self.completion_date or now()), as_dict=True)[0].rank_position
			
			self.db_set("rank_position", rank, update_modified=False)
	
	def update_progress(self):
		"""Update progress based on challenge criteria"""
		try:
			challenge = frappe.get_doc("LMS Challenge", self.challenge)
			
			# Check if challenge is completed
			if challenge.check_completion(self.user):
				self.complete_challenge()
			else:
				# Calculate and update progress percentage
				from lms.lms.doctype.lms_challenge.lms_challenge import calculate_challenge_progress
				progress = calculate_challenge_progress(self.user, challenge)
				self.progress_percentage = progress
				
				# Update current progress details
				self.update_progress_details(challenge)
				
				self.save(ignore_permissions=True)
			
		except Exception as e:
			frappe.log_error(f"Error updating challenge progress: {str(e)}")
	
	def update_progress_details(self, challenge):
		"""Update detailed progress information"""
		try:
			criteria = json.loads(challenge.completion_criteria)
			progress_details = {}
			
			# Track points progress
			if "points_target" in criteria:
				points_earned = frappe.db.sql("""
					SELECT COALESCE(SUM(points), 0) as total_points
					FROM `tabLMS Points Transaction`
					WHERE user = %s AND transaction_date >= %s AND transaction_date <= %s
					AND transaction_type IN ('Earned', 'Bonus') AND docstatus = 1
				""", (self.user, challenge.start_date, challenge.end_date), as_dict=True)[0].total_points
				
				progress_details["points"] = {
					"current": points_earned,
					"target": criteria["points_target"],
					"percentage": min(100, (points_earned / criteria["points_target"]) * 100)
				}
			
			# Track course completion progress
			if "courses_target" in criteria:
				completed_courses = frappe.db.count("LMS Course Progress", {
					"member": self.user,
					"status": "Complete",
					"modified": [">=", challenge.start_date],
					"modified": ["<=", challenge.end_date]
				})
				
				progress_details["courses"] = {
					"current": completed_courses,
					"target": criteria["courses_target"],
					"percentage": min(100, (completed_courses / criteria["courses_target"]) * 100)
				}
			
			# Track lesson completion progress
			if "lessons_target" in criteria:
				completed_lessons = frappe.db.count("LMS Course Progress", {
					"member": self.user,
					"status": "Complete",
					"lesson": ["!=", ""],
					"modified": [">=", challenge.start_date],
					"modified": ["<=", challenge.end_date]
				})
				
				progress_details["lessons"] = {
					"current": completed_lessons,
					"target": criteria["lessons_target"],
					"percentage": min(100, (completed_lessons / criteria["lessons_target"]) * 100)
				}
			
			self.current_progress = json.dumps(progress_details)
			
		except Exception as e:
			frappe.log_error(f"Error updating progress details: {str(e)}")
	
	def complete_challenge(self):
		"""Mark challenge as completed and award rewards"""
		self.status = "Completed"
		self.completion_date = now()
		self.progress_percentage = 100
		
		# Award rewards
		challenge = frappe.get_doc("LMS Challenge", self.challenge)
		rewards_awarded = challenge.award_completion_rewards(self.user)
		
		if rewards_awarded:
			self.points_earned = challenge.points_reward
			if challenge.badge_reward:
				self.badges_earned = challenge.badge_reward
		
		self.save(ignore_permissions=True)
		
		# Create social activity for completion
		self.create_completion_activity()
	
	def create_completion_activity(self):
		"""Create social activity for challenge completion"""
		try:
			activity = frappe.get_doc({
				"doctype": "LMS Social Activity",
				"user": self.user,
				"activity_type": "challenge_completed",
				"title": f"Completed Challenge: {frappe.db.get_value('LMS Challenge', self.challenge, 'title')}",
				"description": f"Successfully completed the challenge and earned {self.points_earned} points!",
				"reference_doctype": "LMS Challenge Participation",
				"reference_name": self.name,
				"activity_date": now(),
				"is_public": 1
			})
			activity.insert(ignore_permissions=True)
		except:
			pass  # Don't fail if social activity creation fails

@frappe.whitelist()
def get_user_participations(user=None, status=None):
	"""Get user's challenge participations"""
	if not user:
		user = frappe.session.user
	
	filters = {"user": user}
	if status:
		filters["status"] = status
	
	participations = frappe.get_all(
		"LMS Challenge Participation",
		filters=filters,
		fields=["name", "challenge", "status", "join_date", "completion_date", 
				"progress_percentage", "points_earned", "badges_earned", "rank_position"],
		order_by="join_date desc"
	)
	
	# Get challenge details
	for participation in participations:
		challenge_details = frappe.db.get_value(
			"LMS Challenge",
			participation.challenge,
			["title", "description", "challenge_type", "difficulty_level", "end_date", "image"],
			as_dict=True
		)
		participation.update(challenge_details)
	
	return participations

@frappe.whitelist()
def get_participation_details(participation_name):
	"""Get detailed information about a participation"""
	participation = frappe.get_doc("LMS Challenge Participation", participation_name)
	challenge = frappe.get_doc("LMS Challenge", participation.challenge)
	
	# Parse current progress
	current_progress = {}
	if participation.current_progress:
		try:
			current_progress = json.loads(participation.current_progress)
		except:
			pass
	
	return {
		"participation": participation.as_dict(),
		"challenge": challenge.as_dict(),
		"current_progress": current_progress
	}

@frappe.whitelist()
def abandon_challenge(participation_name):
	"""Abandon a challenge participation"""
	try:
		participation = frappe.get_doc("LMS Challenge Participation", participation_name)
		
		# Check if user owns this participation
		if participation.user != frappe.session.user:
			return {"success": False, "message": "Unauthorized"}
		
		# Check if challenge is still active
		if participation.status != "Active":
			return {"success": False, "message": "Challenge is not active"}
		
		participation.status = "Abandoned"
		participation.save(ignore_permissions=True)
		
		return {"success": True, "message": "Challenge abandoned successfully"}
		
	except Exception as e:
		frappe.log_error(f"Error abandoning challenge: {str(e)}")
		return {"success": False, "message": "Failed to abandon challenge"}

@frappe.whitelist()
def update_all_active_participations():
	"""Update progress for all active participations (called by scheduler)"""
	active_participations = frappe.get_all(
		"LMS Challenge Participation",
		filters={"status": "Active"},
		fields=["name", "user", "challenge"]
	)
	
	updated_count = 0
	for participation in active_participations:
		try:
			participation_doc = frappe.get_doc("LMS Challenge Participation", participation.name)
			participation_doc.update_progress()
			updated_count += 1
		except Exception as e:
			frappe.log_error(f"Error updating participation {participation.name}: {str(e)}")
			continue
	
	frappe.logger().info(f"Updated {updated_count} challenge participations")
	return updated_count

def expire_old_participations():
	"""Mark participations as expired when challenge end date passes"""
	expired_participations = frappe.db.sql("""
		SELECT cp.name
		FROM `tabLMS Challenge Participation` cp
		JOIN `tabLMS Challenge` c ON cp.challenge = c.name
		WHERE cp.status = 'Active' AND c.end_date < %s
	""", (now(),), as_dict=True)
	
	for participation in expired_participations:
		try:
			participation_doc = frappe.get_doc("LMS Challenge Participation", participation.name)
			participation_doc.status = "Expired"
			participation_doc.save(ignore_permissions=True)
		except Exception as e:
			frappe.log_error(f"Error expiring participation {participation.name}: {str(e)}")
			continue
	
	frappe.logger().info(f"Expired {len(expired_participations)} challenge participations")