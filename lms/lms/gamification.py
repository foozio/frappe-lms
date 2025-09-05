import frappe
from frappe import _
from frappe.utils import now_datetime, today, add_days, getdate
import json
from datetime import datetime, timedelta

# Points Configuration
POINTS_CONFIG = {
	"lesson_completion": 10,
	"quiz_completion": 20,
	"quiz_perfect_score": 30,
	"assignment_submission": 15,
	"assignment_approval": 25,
	"discussion_topic": 5,
	"discussion_reply": 3,
	"course_completion": 100,
	"daily_login": 2,
	"streak_milestone_3": 50,
	"streak_milestone_7": 100,
	"streak_milestone_30": 500,
	"streak_milestone_100": 1000,
}

# Document Event Hooks
def award_points_for_progress(doc, method):
	"""Award points when course progress is updated"""
	try:
		if doc.progress == 100 and not doc.get("_points_awarded_for_lesson"):
			# Award points for lesson completion
			award_points(
				user=doc.member,
				points=POINTS_CONFIG["lesson_completion"],
				transaction_type="lesson_completion",
				reference_doctype="LMS Course Progress",
				reference_name=doc.name,
				description=f"Completed lesson in {doc.course}"
			)
			doc.db_set("_points_awarded_for_lesson", 1, update_modified=False)
			
			# Check if course is completed
			check_course_completion(doc.member, doc.course)
			
	except Exception as e:
		frappe.log_error(f"Error awarding points for progress: {str(e)}")

def award_points_for_quiz(doc, method):
	"""Award points when quiz is submitted"""
	try:
		if not doc.get("_points_awarded"):
			points = POINTS_CONFIG["quiz_completion"]
			description = f"Completed quiz: {doc.quiz}"
			
			# Bonus points for perfect score
			if hasattr(doc, 'percentage') and doc.percentage == 100:
				points = POINTS_CONFIG["quiz_perfect_score"]
				description = f"Perfect score on quiz: {doc.quiz}"
			
			award_points(
				user=doc.member,
				points=points,
				transaction_type="quiz_completion",
				reference_doctype="LMS Quiz Submission",
				reference_name=doc.name,
				description=description
			)
			doc.db_set("_points_awarded", 1, update_modified=False)
			
	except Exception as e:
		frappe.log_error(f"Error awarding points for quiz: {str(e)}")

def award_points_for_assignment(doc, method):
	"""Award points when assignment is submitted"""
	try:
		if not doc.get("_points_awarded"):
			points = POINTS_CONFIG["assignment_submission"]
			description = f"Submitted assignment: {doc.assignment}"
			
			# Bonus points if approved
			if doc.status == "Approved":
				points = POINTS_CONFIG["assignment_approval"]
				description = f"Assignment approved: {doc.assignment}"
			
			award_points(
				user=doc.member,
				points=points,
				transaction_type="assignment_submission",
				reference_doctype="LMS Assignment Submission",
				reference_name=doc.name,
				description=description
			)
			doc.db_set("_points_awarded", 1, update_modified=False)
			
	except Exception as e:
		frappe.log_error(f"Error awarding points for assignment: {str(e)}")

def award_points_for_discussion(doc, method):
	"""Award points when discussion topic is created"""
	try:
		if not doc.get("_points_awarded"):
			award_points(
				user=doc.owner,
				points=POINTS_CONFIG["discussion_topic"],
				transaction_type="discussion_topic",
				reference_doctype="Discussion Topic",
				reference_name=doc.name,
				description=f"Started discussion: {doc.title}"
			)
			doc.db_set("_points_awarded", 1, update_modified=False)
			
	except Exception as e:
		frappe.log_error(f"Error awarding points for discussion: {str(e)}")

def award_points_for_reply(doc, method):
	"""Award points when discussion reply is created"""
	try:
		if not doc.get("_points_awarded"):
			award_points(
				user=doc.owner,
				points=POINTS_CONFIG["discussion_reply"],
				transaction_type="discussion_reply",
				reference_doctype="Discussion Reply",
				reference_name=doc.name,
				description="Replied to discussion"
			)
			doc.db_set("_points_awarded", 1, update_modified=False)
			
	except Exception as e:
		frappe.log_error(f"Error awarding points for reply: {str(e)}")

# Core Functions
def award_points(user, points, transaction_type, reference_doctype=None, reference_name=None, description=None):
	"""Award points to a user and create transaction record"""
	try:
		# Create points transaction
		transaction = frappe.get_doc({
			"doctype": "LMS Points Transaction",
			"user": user,
			"points": points,
			"transaction_type": transaction_type,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"description": description or f"Earned {points} points for {transaction_type}",
			"date": today()
		})
		transaction.insert(ignore_permissions=True)
		
		# Update user points
		user_doc = frappe.get_doc("User", user)
		user_doc.total_points = (user_doc.total_points or 0) + points
		user_doc.available_points = (user_doc.available_points or 0) + points
		user_doc.last_activity_date = today()
		
		# Update level
		new_level = calculate_level(user_doc.total_points)
		if new_level > (user_doc.level or 1):
			user_doc.level = new_level
			# Award achievement for level up
			award_achievement(user, f"level_{new_level}", f"Reached Level {new_level}")
		
		user_doc.save(ignore_permissions=True)
		
		# Update streak
		update_user_streak(user)
		
		# Update leaderboard
		update_user_leaderboard_entry(user)
		
		# Check for achievements
		check_points_achievements(user, user_doc.total_points)
		
	except Exception as e:
		frappe.log_error(f"Error awarding points: {str(e)}")

def calculate_level(total_points):
	"""Calculate user level based on total points"""
	return max(1, (total_points or 0) // 1000 + 1)

def update_user_streak(user):
	"""Update user's daily streak"""
	try:
		user_doc = frappe.get_doc("User", user)
		last_activity = getdate(user_doc.last_activity_date) if user_doc.last_activity_date else None
		today_date = getdate(today())
		
		if not last_activity:
			# First activity
			user_doc.current_streak = 1
			user_doc.longest_streak = max(user_doc.longest_streak or 0, 1)
		elif last_activity == today_date:
			# Already active today, no change
			pass
		elif last_activity == add_days(today_date, -1):
			# Consecutive day
			user_doc.current_streak = (user_doc.current_streak or 0) + 1
			user_doc.longest_streak = max(user_doc.longest_streak or 0, user_doc.current_streak)
			
			# Check for streak milestones
			check_streak_milestones(user, user_doc.current_streak)
		else:
			# Streak broken
			user_doc.current_streak = 1
		
		user_doc.save(ignore_permissions=True)
		
		# Create/update streak record
		create_streak_record(user, user_doc.current_streak)
		
	except Exception as e:
		frappe.log_error(f"Error updating user streak: {str(e)}")

def check_streak_milestones(user, streak):
	"""Check and award points for streak milestones"""
	milestones = [3, 7, 30, 100]
	for milestone in milestones:
		if streak == milestone:
			award_points(
				user=user,
				points=POINTS_CONFIG[f"streak_milestone_{milestone}"],
				transaction_type="streak_milestone",
				description=f"Reached {milestone}-day streak milestone"
			)
			award_achievement(user, f"streak_{milestone}", f"{milestone}-Day Streak")
			break

def create_streak_record(user, streak_count):
	"""Create or update streak record for today"""
	try:
		existing = frappe.db.exists("LMS Streak Record", {
			"user": user,
			"date": today()
		})
		
		if existing:
			streak_doc = frappe.get_doc("LMS Streak Record", existing)
			streak_doc.streak_count = streak_count
			streak_doc.save(ignore_permissions=True)
		else:
			streak_doc = frappe.get_doc({
				"doctype": "LMS Streak Record",
				"user": user,
				"date": today(),
				"streak_count": streak_count,
				"activity_type": "learning"
			})
			streak_doc.insert(ignore_permissions=True)
			
	except Exception as e:
		frappe.log_error(f"Error creating streak record: {str(e)}")

def update_user_leaderboard_entry(user):
	"""Update user's leaderboard entries using the canonical utils helpers."""
	try:
		from lms.lms.utils import update_user_leaderboard_position
		# Global points leaderboard
		update_user_leaderboard_position(user, leaderboard_type="global")
		# Streak leaderboard
		update_user_leaderboard_position(user, leaderboard_type="streak")
	except Exception as e:
		frappe.log_error(f"Error updating leaderboard entry: {str(e)}")

def update_leaderboard_entry(user, period, total_points, current_streak):
	"""Compatibility shim: delegate to global leaderboard update."""
	try:
		from lms.lms.utils import update_user_leaderboard_position
		update_user_leaderboard_position(user, leaderboard_type="global")
		update_user_leaderboard_position(user, leaderboard_type="streak")
	except Exception as e:
		frappe.log_error(f"Error updating leaderboard entry (shim): {str(e)}")

def award_achievement(user, achievement_key, achievement_title):
	"""Award achievement to user"""
	try:
		user_doc = frappe.get_doc("User", user)
		achievements = json.loads(user_doc.achievements or "[]")
		
		# Check if achievement already exists
		for achievement in achievements:
			if achievement.get("key") == achievement_key:
				return
		
		# Add new achievement
		achievements.append({
			"key": achievement_key,
			"title": achievement_title,
			"date": today(),
			"timestamp": now_datetime()
		})
		
		user_doc.achievements = json.dumps(achievements)
		user_doc.save(ignore_permissions=True)
		
	except Exception as e:
		frappe.log_error(f"Error awarding achievement: {str(e)}")

def check_points_achievements(user, total_points):
	"""Check and award points-based achievements"""
	milestones = [100, 500, 1000, 5000, 10000, 50000]
	for milestone in milestones:
		if total_points >= milestone:
			award_achievement(user, f"points_{milestone}", f"{milestone:,} Points Earned")

def check_course_completion(user, course):
	"""Check if user completed the course and award points"""
	try:
		# Check if all lessons in course are completed
		total_lessons = frappe.db.count("Course Lesson", {"course": course})
		completed_lessons = frappe.db.count("LMS Course Progress", {
			"member": user,
			"course": course,
			"progress": 100
		})
		
		if total_lessons > 0 and completed_lessons >= total_lessons:
			# Award course completion points
			award_points(
				user=user,
				points=POINTS_CONFIG["course_completion"],
				transaction_type="course_completion",
				reference_doctype="LMS Course",
				reference_name=course,
				description=f"Completed course: {course}"
			)
			award_achievement(user, f"course_{course}", f"Completed {course}")
			
	except Exception as e:
		frappe.log_error(f"Error checking course completion: {str(e)}")

# Scheduled Tasks
def update_leaderboards():
	"""Update leaderboard rankings using current schema (hourly)."""
	try:
		from lms.lms.utils import recalculate_leaderboard_rankings
		recalculate_leaderboard_rankings(leaderboard_type="global")
		recalculate_leaderboard_rankings(leaderboard_type="streak")
	except Exception as e:
		frappe.log_error(f"Error updating leaderboards: {str(e)}")

def update_daily_streaks():
	"""Update daily streaks for all users (daily)"""
	try:
		# Get all users who were active yesterday but not today
		yesterday = add_days(today(), -1)
		
		users_to_reset = frappe.db.sql("""
			SELECT name, current_streak
			FROM `tabUser`
			WHERE last_activity_date = %s
			AND current_streak > 0
			AND name NOT IN (
				SELECT DISTINCT user
				FROM `tabLMS Streak Record`
				WHERE date = %s
			)
		""", (yesterday, today()), as_dict=True)
		
		# Reset streaks for inactive users
		for user_data in users_to_reset:
			frappe.db.set_value("User", user_data.name, "current_streak", 0)
			
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error updating daily streaks: {str(e)}")

def process_daily_challenges():
	"""Process daily challenges (daily)"""
	try:
		# Create new daily challenges
		create_daily_challenges()
		
		# Update challenge progress
		update_challenge_progress()
		
	except Exception as e:
		frappe.log_error(f"Error processing daily challenges: {str(e)}")

def cleanup_expired_challenges():
	"""Clean up expired challenges (daily)"""
	try:
		# Mark expired challenges as inactive
		expired_challenges = frappe.get_all(
			"LMS Challenge",
			filters={
				"end_date": ["<", today()],
				"is_active": 1
			},
			fields=["name"]
		)
		
		for challenge in expired_challenges:
			frappe.db.set_value("LMS Challenge", challenge.name, "is_active", 0)
			
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error cleaning up expired challenges: {str(e)}")

def process_weekly_challenges():
	"""Process weekly challenges (weekly)"""
	try:
		create_weekly_challenges()
		update_challenge_progress()
		
	except Exception as e:
		frappe.log_error(f"Error processing weekly challenges: {str(e)}")

def process_monthly_challenges():
	"""Process monthly challenges (monthly)"""
	try:
		create_monthly_challenges()
		update_challenge_progress()
		
	except Exception as e:
		frappe.log_error(f"Error processing monthly challenges: {str(e)}")

def generate_weekly_leaderboard_summary():
	"""Generate weekly leaderboard summary (weekly)"""
	try:
		# Reset weekly leaderboard entries
		frappe.db.sql("DELETE FROM `tabLMS Leaderboard Entry` WHERE period = 'weekly'")
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error generating weekly leaderboard summary: {str(e)}")

def generate_monthly_achievements_report():
	"""Generate monthly achievements report (monthly)"""
	try:
		# Reset monthly leaderboard entries
		frappe.db.sql("DELETE FROM `tabLMS Leaderboard Entry` WHERE period = 'monthly'")
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error generating monthly achievements report: {str(e)}")

# Helper Functions for Challenges
def create_daily_challenges():
	"""Create daily challenges"""
	daily_challenges = [
		{
			"title": "Daily Learner",
			"description": "Complete 1 lesson today",
			"challenge_type": "daily",
			"target_value": 1,
			"points_reward": 20,
			"activity_type": "lesson_completion"
		},
		{
			"title": "Quiz Master",
			"description": "Complete 2 quizzes today",
			"challenge_type": "daily",
			"target_value": 2,
			"points_reward": 30,
			"activity_type": "quiz_completion"
		}
	]
	
	for challenge_data in daily_challenges:
		# Check if challenge already exists for today
		existing = frappe.db.exists("LMS Challenge", {
			"title": challenge_data["title"],
			"start_date": today()
		})
		
		if not existing:
			challenge = frappe.get_doc({
				"doctype": "LMS Challenge",
				**challenge_data,
				"start_date": today(),
				"end_date": today(),
				"is_active": 1
			})
			challenge.insert(ignore_permissions=True)

def create_weekly_challenges():
	"""Create weekly challenges"""
	weekly_challenges = [
		{
			"title": "Weekly Warrior",
			"description": "Complete 10 lessons this week",
			"challenge_type": "weekly",
			"target_value": 10,
			"points_reward": 150,
			"activity_type": "lesson_completion"
		}
	]
	
	for challenge_data in weekly_challenges:
		existing = frappe.db.exists("LMS Challenge", {
			"title": challenge_data["title"],
			"start_date": today()
		})
		
		if not existing:
			challenge = frappe.get_doc({
				"doctype": "LMS Challenge",
				**challenge_data,
				"start_date": today(),
				"end_date": add_days(today(), 6),
				"is_active": 1
			})
			challenge.insert(ignore_permissions=True)

def create_monthly_challenges():
	"""Create monthly challenges"""
	monthly_challenges = [
		{
			"title": "Monthly Master",
			"description": "Complete 50 lessons this month",
			"challenge_type": "monthly",
			"target_value": 50,
			"points_reward": 500,
			"activity_type": "lesson_completion"
		}
	]
	
	for challenge_data in monthly_challenges:
		existing = frappe.db.exists("LMS Challenge", {
			"title": challenge_data["title"],
			"start_date": today()
		})
		
		if not existing:
			challenge = frappe.get_doc({
				"doctype": "LMS Challenge",
				**challenge_data,
				"start_date": today(),
				"end_date": add_days(today(), 29),
				"is_active": 1
			})
			challenge.insert(ignore_permissions=True)

def update_challenge_progress():
	"""Update progress for all active challenge participations"""
	try:
		active_participations = frappe.get_all(
			"LMS Challenge Participation",
			filters={"status": "active"},
			fields=["name", "challenge", "user", "current_progress"]
		)
		
		for participation in active_participations:
			challenge = frappe.get_doc("LMS Challenge", participation.challenge)
			
			# Calculate current progress based on activity type
			current_progress = calculate_challenge_progress(
				participation.user,
				challenge.activity_type,
				challenge.start_date,
				challenge.end_date
			)
			
			# Update participation
			participation_doc = frappe.get_doc("LMS Challenge Participation", participation.name)
			participation_doc.current_progress = current_progress
			
			# Check if challenge is completed
			if current_progress >= challenge.target_value:
				participation_doc.status = "completed"
				participation_doc.completion_date = today()
				
				# Award points
				award_points(
					user=participation.user,
					points=challenge.points_reward,
					transaction_type="challenge_completion",
					reference_doctype="LMS Challenge",
					reference_name=challenge.name,
					description=f"Completed challenge: {challenge.title}"
				)
				
			participation_doc.save(ignore_permissions=True)
			
	except Exception as e:
		frappe.log_error(f"Error updating challenge progress: {str(e)}")

def calculate_challenge_progress(user, activity_type, start_date, end_date):
	"""Calculate user's progress for a specific challenge"""
	try:
		if activity_type == "lesson_completion":
			return frappe.db.count("LMS Course Progress", {
				"member": user,
				"progress": 100,
				"modified": ["between", [start_date, end_date]]
			})
		elif activity_type == "quiz_completion":
			return frappe.db.count("LMS Quiz Submission", {
				"member": user,
				"creation": ["between", [start_date, end_date]]
			})
		elif activity_type == "assignment_submission":
			return frappe.db.count("LMS Assignment Submission", {
				"member": user,
				"creation": ["between", [start_date, end_date]]
			})
		else:
			return 0
			
	except Exception as e:
		frappe.log_error(f"Error calculating challenge progress: {str(e)}")
		return 0
