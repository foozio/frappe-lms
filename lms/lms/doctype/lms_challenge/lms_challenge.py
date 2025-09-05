import frappe
import json
from frappe.model.document import Document
from frappe.utils import now, getdate, add_days, cint, flt
from datetime import datetime, timedelta

class LMSChallenge(Document):
	def validate(self):
		self.validate_dates()
		self.validate_criteria()
		self.set_created_by()
	
	def validate_dates(self):
		if self.start_date and self.end_date:
			if getdate(self.start_date) >= getdate(self.end_date):
				frappe.throw("End date must be after start date")
	
	def validate_criteria(self):
		if self.eligibility_criteria:
			try:
				json.loads(self.eligibility_criteria)
			except json.JSONDecodeError:
				frappe.throw("Invalid JSON format in Eligibility Criteria")
		
		if self.completion_criteria:
			try:
				json.loads(self.completion_criteria)
			except json.JSONDecodeError:
				frappe.throw("Invalid JSON format in Completion Criteria")
	
	def set_created_by(self):
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.creation_date:
			self.creation_date = now()
	
	def is_active(self):
		"""Check if challenge is currently active"""
		if not self.is_active:
			return False
		
		now_date = datetime.now()
		start_date = datetime.strptime(str(self.start_date), "%Y-%m-%d %H:%M:%S")
		end_date = datetime.strptime(str(self.end_date), "%Y-%m-%d %H:%M:%S")
		
		return start_date <= now_date <= end_date
	
	def can_participate(self, user):
		"""Check if user can participate in this challenge"""
		if not self.is_active():
			return False, "Challenge is not active"
		
		# Check max participants
		if self.max_participants > 0 and self.current_participants >= self.max_participants:
			return False, "Challenge is full"
		
		# Check if already participating
		if frappe.db.exists("LMS Challenge Participation", {
			"challenge": self.name,
			"user": user,
			"status": ["in", ["Active", "Completed"]]
		}):
			return False, "Already participating in this challenge"
		
		# Check eligibility criteria
		if self.eligibility_criteria:
			try:
				criteria = json.loads(self.eligibility_criteria)
				if not self.evaluate_eligibility(user, criteria):
					return False, "Does not meet eligibility criteria"
			except:
				return False, "Error evaluating eligibility"
		
		return True, "Eligible to participate"
	
	def evaluate_eligibility(self, user, criteria):
		"""Evaluate if user meets eligibility criteria"""
		user_doc = frappe.get_doc("User", user)
		
		# Check minimum points requirement
		if "min_points" in criteria:
			user_points = cint(user_doc.total_points or 0)
			if user_points < criteria["min_points"]:
				return False
		
		# Check course enrollment requirement
		if "required_courses" in criteria:
			for course in criteria["required_courses"]:
				if not frappe.db.exists("LMS Enrollment", {
					"member": user,
					"course": course
				}):
					return False
		
		# Check badge requirement
		if "required_badges" in criteria:
			for badge in criteria["required_badges"]:
				if not frappe.db.exists("LMS Badge Assignment", {
					"member": user,
					"badge": badge
				}):
					return False
		
		return True
	
	def check_completion(self, user):
		"""Check if user has completed the challenge"""
		if not self.completion_criteria:
			return False
		
		try:
			criteria = json.loads(self.completion_criteria)
			return self.evaluate_completion(user, criteria)
		except:
			return False
	
	def evaluate_completion(self, user, criteria):
		"""Evaluate if user has completed the challenge"""
		user_doc = frappe.get_doc("User", user)
		
		# Check points target
		if "points_target" in criteria:
			# Get points earned during challenge period
			points_earned = frappe.db.sql("""
				SELECT COALESCE(SUM(points), 0) as total_points
				FROM `tabLMS Points Transaction`
				WHERE user = %s AND transaction_date >= %s AND transaction_date <= %s
				AND transaction_type IN ('Earned', 'Bonus') AND docstatus = 1
			""", (user, self.start_date, self.end_date), as_dict=True)[0].total_points
			
			if points_earned < criteria["points_target"]:
				return False
		
		# Check course completion target
		if "courses_target" in criteria:
			completed_courses = frappe.db.count("LMS Course Progress", {
				"member": user,
				"status": "Complete",
				"modified": [">=", self.start_date],
				"modified": ["<=", self.end_date]
			})
			
			if completed_courses < criteria["courses_target"]:
				return False
		
		# Check lesson completion target
		if "lessons_target" in criteria:
			completed_lessons = frappe.db.count("LMS Course Progress", {
				"member": user,
				"status": "Complete",
				"lesson": ["!=", ""],
				"modified": [">=", self.start_date],
				"modified": ["<=", self.end_date]
			})
			
			if completed_lessons < criteria["lessons_target"]:
				return False
		
		# Check streak target
		if "streak_target" in criteria:
			current_streak = cint(user_doc.current_streak or 0)
			if current_streak < criteria["streak_target"]:
				return False
		
		return True
	
	def award_completion_rewards(self, user):
		"""Award rewards for completing the challenge"""
		try:
			# Award points
			if self.points_reward > 0:
				from lms.lms.doctype.lms_points_transaction.lms_points_transaction import award_points
				award_points(
					user=user,
					points=self.points_reward,
					activity_type="challenge_completion",
					reference_doc=self.name,
					reference_doctype="LMS Challenge",
					description=f"Challenge completed: {self.title}"
				)
			
			# Award badge
			if self.badge_reward:
				if not frappe.db.exists("LMS Badge Assignment", {
					"member": user,
					"badge": self.badge_reward
				}):
					badge_assignment = frappe.get_doc({
						"doctype": "LMS Badge Assignment",
						"member": user,
						"badge": self.badge_reward,
						"assignment_date": now()
					})
					badge_assignment.insert(ignore_permissions=True)
			
			return True
		except Exception as e:
			frappe.log_error(f"Error awarding challenge rewards: {str(e)}")
			return False

@frappe.whitelist()
def get_active_challenges(user=None):
	"""Get list of active challenges"""
	if not user:
		user = frappe.session.user
	
	challenges = frappe.get_all(
		"LMS Challenge",
		filters={
			"is_active": 1,
			"start_date": ["<=", now()],
			"end_date": [">=", now()]
		},
		fields=["name", "title", "description", "challenge_type", "difficulty_level", 
				"start_date", "end_date", "target_value", "target_unit", "points_reward", 
				"badge_reward", "max_participants", "current_participants", "image"]
	)
	
	# Check participation status for each challenge
	for challenge in challenges:
		participation = frappe.db.get_value(
			"LMS Challenge Participation",
			{"challenge": challenge.name, "user": user},
			["status", "progress_percentage"],
			as_dict=True
		)
		
		challenge["participation_status"] = participation.status if participation else "Not Joined"
		challenge["progress_percentage"] = participation.progress_percentage if participation else 0
	
	return challenges

@frappe.whitelist()
def join_challenge(challenge_name, user=None):
	"""Join a challenge"""
	if not user:
		user = frappe.session.user
	
	try:
		challenge = frappe.get_doc("LMS Challenge", challenge_name)
		can_join, message = challenge.can_participate(user)
		
		if not can_join:
			return {"success": False, "message": message}
		
		# Create participation record
		participation = frappe.get_doc({
			"doctype": "LMS Challenge Participation",
			"challenge": challenge_name,
			"user": user,
			"status": "Active",
			"join_date": now(),
			"progress_percentage": 0
		})
		participation.insert(ignore_permissions=True)
		
		# Update challenge participant count
		challenge.current_participants = cint(challenge.current_participants) + 1
		challenge.save(ignore_permissions=True)
		
		return {
			"success": True,
			"message": "Successfully joined the challenge!",
			"participation_id": participation.name
		}
		
	except Exception as e:
		frappe.log_error(f"Error joining challenge: {str(e)}")
		return {"success": False, "message": "Failed to join challenge"}


@frappe.whitelist()
def leave_challenge(challenge_name, user=None):
	"""Leave a challenge (set participation inactive/cancelled)."""
	if not user:
		user = frappe.session.user

	try:
		participation_name = frappe.db.get_value(
			"LMS Challenge Participation",
			{"challenge": challenge_name, "user": user, "status": ["in", ["Active", "Completed"]]},
			"name",
		)
		if not participation_name:
			return {"success": False, "message": "No active participation found"}

		participation_doc = frappe.get_doc("LMS Challenge Participation", participation_name)
		if participation_doc.status != "Completed":
			participation_doc.status = "Cancelled"
			participation_doc.save(ignore_permissions=True)

		# Decrement challenge participants safely
		challenge = frappe.get_doc("LMS Challenge", challenge_name)
		if cint(challenge.current_participants or 0) > 0:
			challenge.current_participants = cint(challenge.current_participants) - 1
			challenge.save(ignore_permissions=True)

		return {"success": True, "message": "Left challenge"}
	except Exception as e:
		frappe.log_error(f"Error leaving challenge: {str(e)}")
		return {"success": False, "message": "Failed to leave challenge"}

@frappe.whitelist()
def get_challenge_leaderboard(challenge_name, limit=10):
	"""Get leaderboard for a specific challenge"""
	leaderboard = frappe.db.sql("""
		SELECT 
			p.user,
			u.full_name,
			u.user_image,
			p.progress_percentage,
			p.completion_date,
			p.status,
			ROW_NUMBER() OVER (ORDER BY p.progress_percentage DESC, p.completion_date ASC) as rank_position
		FROM `tabLMS Challenge Participation` p
		JOIN `tabUser` u ON p.user = u.name
		WHERE p.challenge = %s AND p.status IN ('Active', 'Completed')
		ORDER BY p.progress_percentage DESC, p.completion_date ASC
		LIMIT %s
	""", (challenge_name, limit), as_dict=True)
	
	return leaderboard

@frappe.whitelist()
def update_challenge_progress(user=None):
	"""Update progress for all active challenges for a user"""
	if not user:
		user = frappe.session.user
	
	# Get all active participations
	participations = frappe.get_all(
		"LMS Challenge Participation",
		filters={"user": user, "status": "Active"},
		fields=["name", "challenge"]
	)
	
	for participation in participations:
		try:
			challenge = frappe.get_doc("LMS Challenge", participation.challenge)
			participation_doc = frappe.get_doc("LMS Challenge Participation", participation.name)
			
			# Check if challenge is completed
			if challenge.check_completion(user):
				participation_doc.status = "Completed"
				participation_doc.completion_date = now()
				participation_doc.progress_percentage = 100
				participation_doc.save(ignore_permissions=True)
				
				# Award rewards
				challenge.award_completion_rewards(user)
			else:
				# Calculate progress percentage
				progress = calculate_challenge_progress(user, challenge)
				participation_doc.progress_percentage = progress
				participation_doc.save(ignore_permissions=True)
			
		except Exception as e:
			frappe.log_error(f"Error updating challenge progress: {str(e)}")
			continue

def calculate_challenge_progress(user, challenge):
	"""Calculate progress percentage for a challenge"""
	try:
		criteria = json.loads(challenge.completion_criteria)
		total_progress = 0
		criteria_count = 0
		
		# Calculate points progress
		if "points_target" in criteria:
			points_earned = frappe.db.sql("""
				SELECT COALESCE(SUM(points), 0) as total_points
				FROM `tabLMS Points Transaction`
				WHERE user = %s AND transaction_date >= %s AND transaction_date <= %s
				AND transaction_type IN ('Earned', 'Bonus') AND docstatus = 1
			""", (user, challenge.start_date, challenge.end_date), as_dict=True)[0].total_points
			
			points_progress = min(100, (points_earned / criteria["points_target"]) * 100)
			total_progress += points_progress
			criteria_count += 1
		
		# Calculate course completion progress
		if "courses_target" in criteria:
			completed_courses = frappe.db.count("LMS Course Progress", {
				"member": user,
				"status": "Complete",
				"modified": [">=", challenge.start_date],
				"modified": ["<=", challenge.end_date]
			})
			
			course_progress = min(100, (completed_courses / criteria["courses_target"]) * 100)
			total_progress += course_progress
			criteria_count += 1
		
		# Calculate lesson completion progress
		if "lessons_target" in criteria:
			completed_lessons = frappe.db.count("LMS Course Progress", {
				"member": user,
				"status": "Complete",
				"lesson": ["!=", ""],
				"modified": [">=", challenge.start_date],
				"modified": ["<=", challenge.end_date]
			})
			
			lesson_progress = min(100, (completed_lessons / criteria["lessons_target"]) * 100)
			total_progress += lesson_progress
			criteria_count += 1
		
		return int(total_progress / criteria_count) if criteria_count > 0 else 0
	
	except:
		return 0


@frappe.whitelist()
def get_user_challenges(user=None, status="Active"):
	"""Return challenges the user is participating in, filtered by status."""
	if not user:
		user = frappe.session.user

	valid_status = ["Active", "Completed", "Cancelled"]
	if status not in valid_status:
		status = "Active"

	participations = frappe.get_all(
		"LMS Challenge Participation",
		filters={"user": user, "status": status},
		fields=["name", "challenge", "status", "progress_percentage", "completion_date", "join_date"],
		order_by="join_date desc",
	)

	# Attach challenge details
	for p in participations:
		ch = frappe.db.get_value(
			"LMS Challenge",
			p.challenge,
			["title", "description", "challenge_type", "start_date", "end_date", "points_reward", "badge_reward", "image"],
			as_dict=True,
		)
		p.update({
			"challenge_title": ch.title if ch else None,
			"challenge_type": ch.challenge_type if ch else None,
			"start_date": ch.start_date if ch else None,
			"end_date": ch.end_date if ch else None,
			"points_reward": ch.points_reward if ch else 0,
			"badge_reward": ch.badge_reward if ch else None,
			"image": ch.image if ch else None,
		})

	return participations
