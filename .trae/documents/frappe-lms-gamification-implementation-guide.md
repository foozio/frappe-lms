# Frappe LMS - Gamification Implementation Guide

## 1. Implementation Overview

This guide provides detailed technical implementation instructions for adding the missing gamification features to Frappe LMS. The implementation follows Frappe Framework conventions and integrates seamlessly with the existing codebase.

## 2. DocType Definitions

### 2.1 LMS Points Transaction DocType

**File**: `lms/lms/doctype/lms_points_transaction/lms_points_transaction.json`

```json
{
 "actions": [],
 "allow_rename": 1,
 "autoname": "naming_series:",
 "creation": "2024-01-01 00:00:00.000000",
 "doctype": "DocType",
 "editable_grid": 1,
 "engine": "InnoDB",
 "field_order": [
  "naming_series",
  "user",
  "points",
  "transaction_type",
  "activity_type",
  "reference_doc",
  "multiplier",
  "description",
  "transaction_date"
 ],
 "fields": [
  {
   "fieldname": "naming_series",
   "fieldtype": "Select",
   "label": "Series",
   "options": "LMS-PT-.YYYY.-",
   "reqd": 1
  },
  {
   "fieldname": "user",
   "fieldtype": "Link",
   "label": "User",
   "options": "User",
   "reqd": 1
  },
  {
   "fieldname": "points",
   "fieldtype": "Int",
   "label": "Points",
   "reqd": 1
  },
  {
   "fieldname": "transaction_type",
   "fieldtype": "Select",
   "label": "Transaction Type",
   "options": "Earned\nSpent\nBonus\nPenalty",
   "reqd": 1
  },
  {
   "fieldname": "activity_type",
   "fieldtype": "Data",
   "label": "Activity Type",
   "reqd": 1
  },
  {
   "fieldname": "reference_doc",
   "fieldtype": "Dynamic Link",
   "label": "Reference Document",
   "options": "reference_doctype"
  },
  {
   "fieldname": "multiplier",
   "fieldtype": "Float",
   "label": "Multiplier",
   "default": "1.0"
  },
  {
   "fieldname": "description",
   "fieldtype": "Text",
   "label": "Description"
  },
  {
   "fieldname": "transaction_date",
   "fieldtype": "Datetime",
   "label": "Transaction Date",
   "default": "now"
  }
 ],
 "index_web_pages_for_search": 1,
 "links": [],
 "modified": "2024-01-01 00:00:00.000000",
 "modified_by": "Administrator",
 "module": "LMS",
 "name": "LMS Points Transaction",
 "naming_rule": "By "Naming Series" field",
 "owner": "Administrator",
 "permissions": [
  {
   "create": 1,
   "delete": 1,
   "email": 1,
   "export": 1,
   "print": 1,
   "read": 1,
   "report": 1,
   "role": "System Manager",
   "share": 1,
   "write": 1
  },
  {
   "read": 1,
   "role": "LMS Student"
  }
 ],
 "sort_field": "modified",
 "sort_order": "DESC",
 "states": [],
 "track_changes": 1
}
```

### 2.2 LMS Challenge DocType

**File**: `lms/lms/doctype/lms_challenge/lms_challenge.json`

```json
{
 "actions": [],
 "allow_rename": 1,
 "autoname": "field:title",
 "creation": "2024-01-01 00:00:00.000000",
 "doctype": "DocType",
 "editable_grid": 1,
 "engine": "InnoDB",
 "field_order": [
  "title",
  "description",
  "challenge_type",
  "start_date",
  "end_date",
  "target_value",
  "reward_points",
  "max_participants",
  "current_participants",
  "status",
  "created_by"
 ],
 "fields": [
  {
   "fieldname": "title",
   "fieldtype": "Data",
   "label": "Title",
   "reqd": 1,
   "unique": 1
  },
  {
   "fieldname": "description",
   "fieldtype": "Text Editor",
   "label": "Description"
  },
  {
   "fieldname": "challenge_type",
   "fieldtype": "Select",
   "label": "Challenge Type",
   "options": "Time Based\nCompletion\nQuiz Score\nStreak\nSocial",
   "reqd": 1
  },
  {
   "fieldname": "start_date",
   "fieldtype": "Datetime",
   "label": "Start Date",
   "reqd": 1
  },
  {
   "fieldname": "end_date",
   "fieldtype": "Datetime",
   "label": "End Date",
   "reqd": 1
  },
  {
   "fieldname": "target_value",
   "fieldtype": "Int",
   "label": "Target Value",
   "reqd": 1
  },
  {
   "fieldname": "reward_points",
   "fieldtype": "Int",
   "label": "Reward Points",
   "default": "0"
  },
  {
   "fieldname": "max_participants",
   "fieldtype": "Int",
   "label": "Max Participants",
   "default": "0"
  },
  {
   "fieldname": "current_participants",
   "fieldtype": "Int",
   "label": "Current Participants",
   "default": "0",
   "read_only": 1
  },
  {
   "fieldname": "status",
   "fieldtype": "Select",
   "label": "Status",
   "options": "Draft\nActive\nCompleted\nCancelled",
   "default": "Draft"
  },
  {
   "fieldname": "created_by",
   "fieldtype": "Link",
   "label": "Created By",
   "options": "User",
   "default": "user"
  }
 ],
 "index_web_pages_for_search": 1,
 "links": [],
 "modified": "2024-01-01 00:00:00.000000",
 "modified_by": "Administrator",
 "module": "LMS",
 "name": "LMS Challenge",
 "naming_rule": "By fieldname",
 "owner": "Administrator",
 "permissions": [
  {
   "create": 1,
   "delete": 1,
   "email": 1,
   "export": 1,
   "print": 1,
   "read": 1,
   "report": 1,
   "role": "System Manager",
   "share": 1,
   "write": 1
  },
  {
   "create": 1,
   "read": 1,
   "role": "Course Creator",
   "write": 1
  },
  {
   "read": 1,
   "role": "LMS Student"
  }
 ],
 "sort_field": "modified",
 "sort_order": "DESC",
 "states": [],
 "track_changes": 1
}
```

## 3. Python Controller Implementation

### 3.1 Points System Controller

**File**: `lms/lms/doctype/lms_points_transaction/lms_points_transaction.py`

```python
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
        from lms.lms.doctype.lms_points_transaction.lms_points_transaction import award_points
from lms.lms.utils import update_streak, update_user_leaderboard_position

def award_lesson_points(doc, method):
    """Award points when a lesson is completed"""
    if doc.status == "Complete":
        award_points(
            user=doc.member,
            points=10,
            activity_type="lesson_complete",
            reference_doc=doc.lesson,
            description=f"Completed lesson: {doc.lesson}"
        )
        
        # Update streak
        update_streak(doc.member)

def award_quiz_points(doc, method):
    """Award points based on quiz performance"""
    if doc.score >= 70:  # Passing score
        base_points = 20
        if doc.score == 100:  # Perfect score
            base_points = 50
        
        # Bonus for high scores
        score_multiplier = 1.0 + (doc.score - 70) / 100
        
        award_points(
            user=doc.member,
            points=base_points,
            activity_type="quiz_perfect" if doc.score == 100 else "quiz_pass",
            reference_doc=doc.quiz,
            multiplier=score_multiplier,
            description=f"Quiz score: {doc.score}% - {doc.quiz}"
        )

def check_course_completion(doc, method):
    """Check if course is completed and award completion points"""
    if doc.progress == 100:
        award_points(
            user=doc.member,
            points=100,
            activity_type="course_complete",
            reference_doc=doc.course,
            description=f"Completed course: {doc.course}"
        )

def setup_new_user_gamification(doc, method):
    """Initialize gamification fields for new users"""
    doc.total_points = 0
    doc.available_points = 0
    doc.current_streak = 0
    doc.longest_streak = 0
    doc.save(ignore_permissions=True)

def update_daily_streaks():
    """Daily job to update all user streaks"""
    # This will be called by scheduler
    users_with_activity = frappe.db.sql("""
        SELECT DISTINCT member as user
        FROM `tabLMS Course Progress`
        WHERE DATE(creation) = CURDATE()
    """, as_dict=True)
    
    for user_data in users_with_activity:
        update_streak(user_data.user)

def process_daily_challenges():
    """Process daily challenge updates"""
    from lms.lms.doctype.lms_challenge.lms_challenge import monitor_challenge
    
    active_challenges = frappe.get_all(
        "LMS Challenge",
        filters={"status": "Active"},
        fields=["name"]
    )
    
    for challenge in active_challenges:
        monitor_challenge(challenge.name)

def recalculate_leaderboards():
    """Recalculate all leaderboard rankings"""
    from lms.lms.utils import recalculate_leaderboard_rankings
    
    # Recalculate global leaderboard
    recalculate_leaderboard_rankings("global")
    
    # Recalculate course leaderboards
    courses = frappe.get_all("LMS Course", fields=["name"])
    for course in courses:
        recalculate_leaderboard_rankings("course", course.name)
    
    # Recalculate streak leaderboard
    recalculate_leaderboard_rankings("streak")

def monitor_active_challenges():
    """Hourly monitoring of active challenges"""
    from lms.lms.doctype.lms_challenge.lms_challenge import monitor_challenge
    
    active_challenges = frappe.get_all(
        "LMS Challenge",
        filters={"status": "Active"},
        fields=["name"]
    )
    
    for challenge in active_challenges:
        frappe.enqueue(
            monitor_challenge,
            challenge=challenge.name,
            queue="default"
        )
```

## 6. Database Migrations

### 6.1 User Table Modifications

**File**: `lms/patches/v1_0/add_gamification_fields_to_user.py`

```python
import frappe

def execute():
    """Add gamification fields to User doctype"""
    
    # Add custom fields to User doctype
    custom_fields = [
        {
            "fieldname": "total_points",
            "label": "Total Points",
            "fieldtype": "Int",
            "default": "0",
            "read_only": 1
        },
        {
            "fieldname": "available_points",
            "label": "Available Points",
            "fieldtype": "Int",
            "default": "0",
            "read_only": 1
        },
        {
            "fieldname": "current_streak",
            "label": "Current Streak",
            "fieldtype": "Int",
            "default": "0",
            "read_only": 1
        },
        {
            "fieldname": "longest_streak",
            "label": "Longest Streak",
            "fieldtype": "Int",
            "default": "0",
            "read_only": 1
        },
        {
            "fieldname": "last_activity_date",
            "label": "Last Activity Date",
            "fieldtype": "Date",
            "read_only": 1
        }
    ]
    
    for field in custom_fields:
        if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": field["fieldname"]}):
            custom_field = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "User",
                "fieldname": field["fieldname"],
                "label": field["label"],
                "fieldtype": field["fieldtype"],
                "default": field.get("default"),
                "read_only": field.get("read_only", 0),
                "insert_after": "last_login"
            })
            custom_field.insert()
    
    frappe.db.commit()
```

## 7. API Endpoints Summary

### 7.1 Points System APIs

```python
# Points Management
@frappe.whitelist()
def get_user_points(user=None)

@frappe.whitelist()
def award_points(user, points, activity_type, reference_doc=None, multiplier=1.0, description=None)

@frappe.whitelist()
def spend_points(user, points, description)

@frappe.whitelist()
def get_points_history(user=None, limit=50)
```

### 7.2 Leaderboard APIs

```python
# Leaderboard Management
@frappe.whitelist()
def get_leaderboard(leaderboard_type="global", reference_doc=None, period="all_time", limit=50, offset=0)

@frappe.whitelist()
def get_user_rank(user=None, leaderboard_type="global", reference_doc=None)

@frappe.whitelist()
def get_leaderboard_stats(leaderboard_type="global", reference_doc=None)
```

### 7.3 Challenge System APIs

```python
# Challenge Management
@frappe.whitelist()
def get_active_challenges(user=None)

@frappe.whitelist()
def join_challenge(challenge, user=None)

@frappe.whitelist()
def leave_challenge(challenge, user=None)

@frappe.whitelist()
def get_challenge_leaderboard(challenge)

@frappe.whitelist()
def get_user_challenges(user=None, status="Active")
```

### 7.4 Streak System APIs

```python
# Streak Management
@frappe.whitelist()
def get_user_streak_data(user=None)

@frappe.whitelist()
def get_streak_leaderboard(period="current", limit=50)

@frappe.whitelist()
def get_streak_calendar(user=None, month=None, year=None)
```

## 8. Frontend Integration

### 8.1 Router Configuration

**File**: `frontend/src/router/index.js` (Add routes)

```javascript
// Add these routes to existing router configuration
const gamificationRoutes = [
  {
    path: '/leaderboard',
    name: 'Leaderboard',
    component: () => import('@/components/Leaderboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/points',
    name: 'PointsDashboard',
    component: () => import('@/components/PointsDashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/challenges',
    name: 'Challenges',
    component: () => import('@/components/Challenges.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/streaks',
    name: 'StreakTracker',
    component: () => import('@/components/StreakTracker.vue'),
    meta: { requiresAuth: true }
  }
]
```

### 8.2 Navigation Menu Updates

**File**: `frontend/src/components/Navigation.vue` (Add menu items)

```vue
<!-- Add to existing navigation menu -->
<template>
  <nav class="main-navigation">
    <!-- Existing menu items -->
    
    <!-- Gamification Menu Section -->
    <div class="nav-section">
      <h3 class="nav-section-title">Gamification</h3>
      <ul class="nav-menu">
        <li class="nav-item">
          <router-link to="/points" class="nav-link">
            <span class="nav-icon">💎</span>
            <span class="nav-text">My Points</span>
            <span class="nav-badge">{{ userPoints }}</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link to="/leaderboard" class="nav-link">
            <span class="nav-icon">🏆</span>
            <span class="nav-text">Leaderboard</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link to="/challenges" class="nav-link">
            <span class="nav-icon">🎯</span>
            <span class="nav-text">Challenges</span>
            <span class="nav-badge" v-if="activeChallenges > 0">{{ activeChallenges }}</span>
          </router-link>
        </li>
        <li class="nav-item">
          <router-link to="/streaks" class="nav-link">
            <span class="nav-icon">🔥</span>
            <span class="nav-text">Streak</span>
            <span class="nav-badge">{{ currentStreak }}</span>
          </router-link>
        </li>
      </ul>
    </div>
  </nav>
</template>

<script>
export default {
  data() {
    return {
      userPoints: 0,
      activeChallenges: 0,
      currentStreak: 0
    }
  },
  mounted() {
    this.loadGamificationData()
  },
  methods: {
    async loadGamificationData() {
      // Load user's gamification stats for navigation badges
      try {
        const [pointsData, challengesData, streakData] = await Promise.all([
          this.$call('lms.lms.doctype.lms_points_transaction.lms_points_transaction.get_user_points'),
          this.$call('lms.lms.doctype.lms_challenge.lms_challenge.get_active_challenges'),
          this.$call('lms.lms.utils.get_user_streak_data')
        ])
        
        this.userPoints = pointsData.available_points || 0
        this.activeChallenges = challengesData.filter(c => c.user_joined).length
        this.currentStreak = streakData.current_streak || 0
      } catch (error) {
        console.error('Error loading gamification data:', error)
      }
    }
  }
}
</script>
```

## 9. Testing Strategy

### 9.1 Unit Tests

**File**: `lms/tests/test_gamification.py`

```python
import frappe
import unittest
from lms.lms.doctype.lms_points_transaction.lms_points_transaction import award_points
from lms.lms.utils import update_streak, get_user_total_points

class TestGamification(unittest.TestCase):
    def setUp(self):
        self.test_user = "test@example.com"
        
        # Create test user if not exists
        if not frappe.db.exists("User", self.test_user):
            user = frappe.get_doc({
                "doctype": "User",
                "email": self.test_user,
                "first_name": "Test",
                "last_name": "User"
            })
            user.insert(ignore_permissions=True)
    
    def test_award_points(self):
        """Test points awarding system"""
        initial_points = get_user_total_points(self.test_user)
        
        # Award points
        result = award_points(
            user=self.test_user,
            points=50,
            activity_type="lesson_complete",
            description="Test lesson completion"
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["points_awarded"], 50)
        
        # Check if points were added
        new_points = get_user_total_points(self.test_user)
        self.assertEqual(new_points, initial_points + 50)
    
    def test_streak_update(self):
        """Test streak tracking"""
        # Update streak
        streak = update_streak(self.test_user)
        
        # Check if streak was recorded
        self.assertGreaterEqual(streak, 1)
        
        # Check if user's streak was updated
        user_doc = frappe.get_doc("User", self.test_user)
        self.assertEqual(user_doc.current_streak, streak)
    
    def test_leaderboard_update(self):
        """Test leaderboard position updates"""
        from lms.lms.utils import update_user_leaderboard_position, get_leaderboard
        
        # Award some points first
        award_points(
            user=self.test_user,
            points=100,
            activity_type="test",
            description="Test points"
        )
        
        # Update leaderboard
        update_user_leaderboard_position(self.test_user)
        
        # Check leaderboard
        leaderboard = get_leaderboard(limit=10)
        user_found = any(entry["user"] == self.test_user for entry in leaderboard["leaderboard"])
        self.assertTrue(user_found)
    
    def tearDown(self):
        # Clean up test data
        frappe.db.delete("LMS Points Transaction", {"user": self.test_user})
        frappe.db.delete("LMS Leaderboard Entry", {"user": self.test_user})
        frappe.db.delete("LMS Streak Record", {"user": self.test_user})
```

## 10. Deployment Checklist

### 10.1 Pre-deployment Steps

1. **Database Setup**
   - [ ] Run database migrations
   - [ ] Create custom fields for User doctype
   - [ ] Set up indexes for performance

2. **DocType Installation**
   - [ ] Install LMS Points Transaction doctype
   - [ ] Install LMS Challenge doctype
   - [ ] Install LMS Challenge Participation doctype
   - [ ] Install LMS Leaderboard Entry doctype
   - [ ] Install LMS Streak Record doctype

3. **Permission Setup**
   - [ ] Configure role permissions for new doctypes
   - [ ] Set up user role assignments
   - [ ] Test permission restrictions

4. **Frontend Integration**
   - [ ] Build and deploy frontend components
   - [ ] Update navigation menus
   - [ ] Test responsive design

5. **Background Jobs**
   - [ ] Configure scheduler for daily/hourly tasks
   - [ ] Test background job execution
   - [ ] Set up monitoring for failed jobs

### 10.2 Post-deployment Verification

1. **Functionality Testing**
   - [ ] Test points awarding for various activities
   - [ ] Verify leaderboard calculations
   - [ ] Test challenge creation and participation
   - [ ] Verify streak tracking accuracy

2. **Performance Testing**
   - [ ] Test leaderboard loading times
   - [ ] Verify database query performance
   - [ ] Test with large datasets

3. **User Experience**
   - [ ] Test gamification UI components
   - [ ] Verify mobile responsiveness
   - [ ] Test user workflows

## 11. Maintenance and Monitoring

### 11.1 Regular Maintenance Tasks

- **Daily**: Monitor point transactions and streak updates
- **Weekly**: Review leaderboard accuracy and challenge progress
- **Monthly**: Analyze gamification engagement metrics
- **Quarterly**: Review and adjust point values based on user behavior

### 11.2 Performance Monitoring

- Monitor database query performance for leaderboards
- Track API response times for gamification endpoints
- Monitor background job execution times
- Set up alerts for failed gamification processes

### 11.3 Analytics and Reporting

- Track user engagement with gamification features
- Monitor point distribution and inflation
- Analyze challenge participation rates
- Generate reports on streak maintenance

This implementation guide provides a comprehensive foundation for adding advanced gamification features to Frappe LMS, enhancing user engagement and motivation through points, leaderboards, challenges, and streak tracking.utils import update_user_leaderboard_position
        update_user_leaderboard_position(self.user)
    
    def check_achievements(self):
        """Check if user has achieved any new milestones"""
        if self.transaction_type in ["Earned", "Bonus"]:
            from lms.lms.utils import check_points_achievements
            check_points_achievements(self.user)

@frappe.whitelist()
def award_points(user, points, activity_type, reference_doc=None, multiplier=1.0, description=None):
    """Award points to a user for completing an activity"""
    if not user:
        user = frappe.session.user
    
    # Get base points for activity type
    base_points = get_activity_points(activity_type)
    total_points = cint(base_points * flt(multiplier))
    
    if total_points > 0:
        transaction = frappe.get_doc({
            "doctype": "LMS Points Transaction",
            "user": user,
            "points": total_points,
            "transaction_type": "Earned",
            "activity_type": activity_type,
            "reference_doc": reference_doc,
            "multiplier": multiplier,
            "description": description or f"Points earned for {activity_type}"
        })
        transaction.insert(ignore_permissions=True)
        transaction.submit()
        
        return {
            "success": True,
            "points_awarded": total_points,
            "transaction": transaction.name
        }
    
    return {"success": False, "message": "No points configured for this activity"}

def get_activity_points(activity_type):
    """Get base points for an activity type"""
    points_config = {
        "lesson_complete": 10,
        "quiz_pass": 20,
        "quiz_perfect": 50,
        "assignment_submit": 15,
        "course_complete": 100,
        "daily_login": 5,
        "streak_bonus": 5,
        "challenge_complete": 25,
        "badge_earned": 30
    }
    
    return points_config.get(activity_type, 0)

@frappe.whitelist()
def get_user_points(user=None):
    """Get user's current points balance"""
    if not user:
        user = frappe.session.user
    
    user_doc = frappe.get_doc("User", user)
    
    # Get recent transactions
    recent_transactions = frappe.get_all(
        "LMS Points Transaction",
        filters={"user": user},
        fields=["name", "points", "transaction_type", "activity_type", "transaction_date", "description"],
        order_by="transaction_date desc",
        limit=10
    )
    
    return {
        "total_points": cint(user_doc.total_points or 0),
        "available_points": cint(user_doc.available_points or 0),
        "recent_transactions": recent_transactions
    }
```

### 3.2 Leaderboard System

**File**: `lms/lms/utils.py` (Add to existing file)

```python
# Add these functions to the existing utils.py file

import frappe
from frappe.utils import cint, flt, now_datetime, add_days, getdate
from datetime import datetime, timedelta

def update_user_leaderboard_position(user, leaderboard_type="global", reference_doc=None):
    """Update user's position in leaderboard"""
    # Get user's current score based on leaderboard type
    if leaderboard_type == "global":
        score = get_user_total_points(user)
    elif leaderboard_type == "course":
        score = get_user_course_points(user, reference_doc)
    elif leaderboard_type == "streak":
        score = get_user_current_streak(user)
    else:
        return
    
    # Update or create leaderboard entry
    existing_entry = frappe.db.get_value(
        "LMS Leaderboard Entry",
        {"user": user, "leaderboard_type": leaderboard_type, "reference_doc": reference_doc},
        "name"
    )
    
    if existing_entry:
        frappe.db.set_value("LMS Leaderboard Entry", existing_entry, {
            "score": score,
            "last_updated": now_datetime()
        })
    else:
        leaderboard_entry = frappe.get_doc({
            "doctype": "LMS Leaderboard Entry",
            "user": user,
            "leaderboard_type": leaderboard_type,
            "reference_doc": reference_doc,
            "score": score,
            "rank_position": 0
        })
        leaderboard_entry.insert(ignore_permissions=True)
    
    # Recalculate rankings
    recalculate_leaderboard_rankings(leaderboard_type, reference_doc)

def recalculate_leaderboard_rankings(leaderboard_type="global", reference_doc=None):
    """Recalculate all rankings for a leaderboard"""
    filters = {"leaderboard_type": leaderboard_type}
    if reference_doc:
        filters["reference_doc"] = reference_doc
    
    entries = frappe.get_all(
        "LMS Leaderboard Entry",
        filters=filters,
        fields=["name", "user", "score"],
        order_by="score desc"
    )
    
    for idx, entry in enumerate(entries, 1):
        frappe.db.set_value("LMS Leaderboard Entry", entry.name, "rank_position", idx)

def get_user_total_points(user):
    """Get user's total points"""
    user_doc = frappe.get_doc("User", user)
    return cint(user_doc.total_points or 0)

def get_user_course_points(user, course):
    """Get user's points for a specific course"""
    total_points = frappe.db.sql("""
        SELECT SUM(points * multiplier) as total
        FROM `tabLMS Points Transaction`
        WHERE user = %s AND reference_doc = %s
        AND transaction_type IN ('Earned', 'Bonus')
        AND docstatus = 1
    """, (user, course))
    
    return cint(total_points[0][0] if total_points and total_points[0][0] else 0)

def get_user_current_streak(user):
    """Get user's current learning streak"""
    user_doc = frappe.get_doc("User", user)
    return cint(user_doc.current_streak or 0)

@frappe.whitelist()
def get_leaderboard(leaderboard_type="global", reference_doc=None, period="all_time", limit=50, offset=0):
    """Get leaderboard data"""
    filters = {"leaderboard_type": leaderboard_type, "period": period}
    if reference_doc:
        filters["reference_doc"] = reference_doc
    
    leaderboard = frappe.get_all(
        "LMS Leaderboard Entry",
        filters=filters,
        fields=[
            "user", "score", "rank_position",
            "`tabUser`.full_name as user_name",
            "`tabUser`.user_image as user_image"
        ],
        order_by="rank_position asc",
        limit=limit,
        start=offset,
        as_list=False
    )
    
    # Get current user's rank
    current_user_rank = None
    if frappe.session.user != "Guest":
        user_entry = frappe.db.get_value(
            "LMS Leaderboard Entry",
            {"user": frappe.session.user, **filters},
            ["rank_position", "score"]
        )
        if user_entry:
            current_user_rank = {
                "rank": user_entry[0],
                "score": user_entry[1]
            }
    
    total_participants = frappe.db.count("LMS Leaderboard Entry", filters)
    
    return {
        "leaderboard": leaderboard,
        "current_user_rank": current_user_rank,
        "total_participants": total_participants
    }

def update_streak(user, activity_type="learning"):
    """Update user's learning streak"""
    today = getdate()
    user_doc = frappe.get_doc("User", user)
    
    # Check if user already has activity today
    existing_record = frappe.db.get_value(
        "LMS Streak Record",
        {"user": user, "activity_date": today},
        "name"
    )
    
    if existing_record:
        return  # Already recorded for today
    
    # Get yesterday's record
    yesterday = add_days(today, -1)
    yesterday_record = frappe.db.get_value(
        "LMS Streak Record",
        {"user": user, "activity_date": yesterday},
        "streak_count"
    )
    
    # Calculate new streak
    if yesterday_record:
        new_streak = cint(yesterday_record) + 1
    else:
        # Check if there's a gap in streak
        last_activity = frappe.db.get_value(
            "LMS Streak Record",
            {"user": user},
            "activity_date",
            order_by="activity_date desc"
        )
        
        if last_activity and (today - last_activity).days > 1:
            new_streak = 1  # Reset streak
        else:
            new_streak = 1
    
    # Create streak record
    streak_record = frappe.get_doc({
        "doctype": "LMS Streak Record",
        "user": user,
        "activity_date": today,
        "activity_type": activity_type,
        "streak_count": new_streak
    })
    
    # Check for milestone achievements
    milestone_points = 0
    if new_streak in [7, 14, 30, 60, 100, 365]:  # Milestone days
        milestone_points = new_streak * 2  # Bonus points for milestones
        streak_record.milestone_achieved = 1
        streak_record.bonus_points = milestone_points
    
    streak_record.insert(ignore_permissions=True)
    
    # Update user's streak info
    user_doc.current_streak = new_streak
    user_doc.longest_streak = max(cint(user_doc.longest_streak or 0), new_streak)
    user_doc.last_activity_date = today
    user_doc.save(ignore_permissions=True)
    
    # Award milestone points
    if milestone_points > 0:
        award_points(
            user=user,
            points=milestone_points,
            activity_type="streak_milestone",
            description=f"Milestone bonus for {new_streak}-day streak"
        )
    
    # Award daily streak bonus
    if new_streak > 1:
        daily_bonus = min(new_streak, 10)  # Cap at 10 points per day
        award_points(
            user=user,
            points=daily_bonus,
            activity_type="streak_bonus",
            description=f"Daily streak bonus (Day {new_streak})"
        )
    
    # Update leaderboards
    update_user_leaderboard_position(user, "streak")
    
    return new_streak

@frappe.whitelist()
def get_user_streak_data(user=None):
    """Get user's streak information"""
    if not user:
        user = frappe.session.user
    
    user_doc = frappe.get_doc("User", user)
    
    # Get recent streak records
    recent_records = frappe.get_all(
        "LMS Streak Record",
        filters={"user": user},
        fields=["activity_date", "streak_count", "milestone_achieved", "bonus_points"],
        order_by="activity_date desc",
        limit=30
    )
    
    return {
        "current_streak": cint(user_doc.current_streak or 0),
        "longest_streak": cint(user_doc.longest_streak or 0),
        "last_activity_date": user_doc.last_activity_date,
        "recent_records": recent_records
    }
```

### 3.3 Challenge System Controller

**File**: `lms/lms/doctype/lms_challenge/lms_challenge.py`

```python
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, cint, add_days, getdate
from datetime import datetime

class LMSChallenge(Document):
    def validate(self):
        self.validate_dates()
        self.validate_target_value()
    
    def validate_dates(self):
        if self.start_date >= self.end_date:
            frappe.throw("End date must be after start date")
    
    def validate_target_value(self):
        if self.target_value <= 0:
            frappe.throw("Target value must be greater than zero")
    
    def on_update(self):
        if self.status == "Active" and self.has_value_changed("status"):
            self.activate_challenge()
        elif self.status == "Completed" and self.has_value_changed("status"):
            self.complete_challenge()
    
    def activate_challenge(self):
        """Activate the challenge and start tracking"""
        # Schedule background job to monitor challenge
        frappe.enqueue(
            "lms.lms.doctype.lms_challenge.lms_challenge.monitor_challenge",
            challenge=self.name,
            queue="default",
            timeout=300
        )
    
    def complete_challenge(self):
        """Complete the challenge and award winners"""
        self.calculate_final_rankings()
        self.award_winners()
    
    def calculate_final_rankings(self):
        """Calculate final rankings for all participants"""
        participants = frappe.get_all(
            "LMS Challenge Participation",
            filters={"challenge": self.name, "status": "Active"},
            fields=["name", "user", "current_progress"],
            order_by="current_progress desc"
        )
        
        for idx, participant in enumerate(participants, 1):
            frappe.db.set_value(
                "LMS Challenge Participation",
                participant.name,
                {
                    "rank_position": idx,
                    "final_score": participant.current_progress,
                    "status": "Completed" if participant.current_progress >= self.target_value else "Failed"
                }
            )
    
    def award_winners(self):
        """Award points to challenge winners"""
        winners = frappe.get_all(
            "LMS Challenge Participation",
            filters={"challenge": self.name, "status": "Completed"},
            fields=["user", "rank_position"],
            order_by="rank_position asc",
            limit=10  # Top 10 winners
        )
        
        for winner in winners:
            # Award points based on ranking
            if winner.rank_position == 1:
                points = self.reward_points
            elif winner.rank_position <= 3:
                points = int(self.reward_points * 0.7)
            elif winner.rank_position <= 5:
                points = int(self.reward_points * 0.5)
            else:
                points = int(self.reward_points * 0.3)
            
            # Award points
            from lms.lms.doctype.lms_points_transaction.lms_points_transaction import award_points
            award_points(
                user=winner.user,
                points=points,
                activity_type="challenge_complete",
                reference_doc=self.name,
                description=f"Challenge winner - Rank #{winner.rank_position}"
            )

@frappe.whitelist()
def join_challenge(challenge, user=None):
    """Join a challenge"""
    if not user:
        user = frappe.session.user
    
    challenge_doc = frappe.get_doc("LMS Challenge", challenge)
    
    # Validate challenge status
    if challenge_doc.status != "Active":
        return {"success": False, "message": "Challenge is not active"}
    
    # Check if challenge has started
    if now_datetime() < challenge_doc.start_date:
        return {"success": False, "message": "Challenge has not started yet"}
    
    # Check if challenge has ended
    if now_datetime() > challenge_doc.end_date:
        return {"success": False, "message": "Challenge has ended"}
    
    # Check if user already joined
    existing_participation = frappe.db.get_value(
        "LMS Challenge Participation",
        {"challenge": challenge, "user": user},
        "name"
    )
    
    if existing_participation:
        return {"success": False, "message": "Already joined this challenge"}
    
    # Check participant limit
    if challenge_doc.max_participants > 0:
        if challenge_doc.current_participants >= challenge_doc.max_participants:
            return {"success": False, "message": "Challenge is full"}
    
    # Create participation record
    participation = frappe.get_doc({
        "doctype": "LMS Challenge Participation",
        "challenge": challenge,
        "user": user,
        "status": "Active"
    })
    participation.insert(ignore_permissions=True)
    
    # Update participant count
    challenge_doc.current_participants = cint(challenge_doc.current_participants) + 1
    challenge_doc.save(ignore_permissions=True)
    
    return {"success": True, "message": "Successfully joined challenge"}

@frappe.whitelist()
def get_active_challenges(user=None):
    """Get list of active challenges"""
    if not user:
        user = frappe.session.user
    
    # Get active challenges
    challenges = frappe.get_all(
        "LMS Challenge",
        filters={"status": "Active"},
        fields=[
            "name", "title", "description", "challenge_type",
            "start_date", "end_date", "target_value", "reward_points",
            "max_participants", "current_participants"
        ],
        order_by="start_date desc"
    )
    
    # Check user participation status
    for challenge in challenges:
        participation = frappe.db.get_value(
            "LMS Challenge Participation",
            {"challenge": challenge.name, "user": user},
            ["status", "current_progress"]
        )
        
        challenge["user_joined"] = bool(participation)
        challenge["user_progress"] = participation[1] if participation else 0
        challenge["user_status"] = participation[0] if participation else None
    
    return challenges

@frappe.whitelist()
def get_challenge_leaderboard(challenge):
    """Get challenge leaderboard"""
    participants = frappe.get_all(
        "LMS Challenge Participation",
        filters={"challenge": challenge},
        fields=[
            "user", "current_progress", "rank_position", "status",
            "`tabUser`.full_name as user_name",
            "`tabUser`.user_image as user_image"
        ],
        order_by="current_progress desc, joined_date asc"
    )
    
    return participants

def monitor_challenge(challenge):
    """Background job to monitor challenge progress"""
    challenge_doc = frappe.get_doc("LMS Challenge", challenge)
    
    if challenge_doc.status != "Active":
        return
    
    # Check if challenge has ended
    if now_datetime() > challenge_doc.end_date:
        challenge_doc.status = "Completed"
        challenge_doc.save(ignore_permissions=True)
        return
    
    # Update participant progress based on challenge type
    participants = frappe.get_all(
        "LMS Challenge Participation",
        filters={"challenge": challenge, "status": "Active"},
        fields=["name", "user"]
    )
    
    for participant in participants:
        progress = calculate_challenge_progress(
            challenge_doc.challenge_type,
            participant.user,
            challenge_doc.start_date,
            challenge_doc.end_date
        )
        
        frappe.db.set_value(
            "LMS Challenge Participation",
            participant.name,
            "current_progress",
            progress
        )
    
    # Schedule next monitoring
    frappe.enqueue(
        "lms.lms.doctype.lms_challenge.lms_challenge.monitor_challenge",
        challenge=challenge,
        queue="default",
        timeout=300,
        eta=add_days(now_datetime(), 0, as_datetime=True).replace(hour=0, minute=0) + timedelta(hours=1)
    )

def calculate_challenge_progress(challenge_type, user, start_date, end_date):
    """Calculate user's progress for a specific challenge type"""
    if challenge_type == "Completion":
        # Count completed lessons/courses
        return frappe.db.count(
            "LMS Course Progress",
            {
                "member": user,
                "status": "Complete",
                "creation": ["between", [start_date, end_date]]
            }
        )
    
    elif challenge_type == "Quiz Score":
        # Get average quiz score
        scores = frappe.db.sql("""
            SELECT AVG(score) as avg_score
            FROM `tabLMS Quiz Submission`
            WHERE member = %s AND creation BETWEEN %s AND %s
        """, (user, start_date, end_date))
        
        return int(scores[0][0] if scores and scores[0][0] else 0)
    
    elif challenge_type == "Streak":
        # Get current streak
        user_doc = frappe.get_doc("User", user)
        return cint(user_doc.current_streak or 0)
    
    elif challenge_type == "Time Based":
        # Count days with learning activity
        return frappe.db.count(
            "LMS Streak Record",
            {
                "user": user,
                "activity_date": ["between", [start_date.date(), end_date.date()]]
            }
        )
    
    return 0
```

## 4. Frontend Components

### 4.1 Leaderboard Component

**File**: `frontend/src/components/Leaderboard.vue`

```vue
<template>
  <div class="leaderboard-container">
    <div class="leaderboard-header">
      <h2 class="text-2xl font-bold mb-4">{{ title }}</h2>
      <div class="filters mb-4">
        <select v-model="selectedPeriod" @change="loadLeaderboard" class="mr-2 p-2 border rounded">
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="all_time">All Time</option>
        </select>
        <select v-model="selectedType" @change="loadLeaderboard" class="p-2 border rounded">
          <option value="global">Global</option>
          <option value="course">Course</option>
          <option value="streak">Streak</option>
        </select>
      </div>
    </div>
    
    <!-- Podium for top 3 -->
    <div class="podium mb-6" v-if="leaderboard.length >= 3">
      <div class="podium-positions flex justify-center items-end space-x-4">
        <!-- 2nd Place -->
        <div class="podium-position second-place text-center">
          <div class="user-avatar mb-2">
            <img :src="leaderboard[1].user_image || '/assets/lms/images/default-avatar.png'" 
                 class="w-16 h-16 rounded-full mx-auto border-4 border-gray-400">
          </div>
          <div class="user-name font-semibold">{{ leaderboard[1].user_name }}</div>
          <div class="user-score text-gray-600">{{ leaderboard[1].score }} pts</div>
          <div class="podium-base bg-gray-400 h-20 w-24 mt-2 rounded-t flex items-center justify-center">
            <span class="text-white font-bold text-xl">2</span>
          </div>
        </div>
        
        <!-- 1st Place -->
        <div class="podium-position first-place text-center">
          <div class="crown mb-2 text-yellow-500 text-2xl">👑</div>
          <div class="user-avatar mb-2">
            <img :src="leaderboard[0].user_image || '/assets/lms/images/default-avatar.png'" 
                 class="w-20 h-20 rounded-full mx-auto border-4 border-yellow-500">
          </div>
          <div class="user-name font-bold text-lg">{{ leaderboard[0].user_name }}</div>
          <div class="user-score text-gray-600">{{ leaderboard[0].score }} pts</div>
          <div class="podium-base bg-yellow-500 h-24 w-28 mt-2 rounded-t flex items-center justify-center">
            <span class="text-white font-bold text-2xl">1</span>
          </div>
        </div>
        
        <!-- 3rd Place -->
        <div class="podium-position third-place text-center">
          <div class="user-avatar mb-2">
            <img :src="leaderboard[2].user_image || '/assets/lms/images/default-avatar.png'" 
                 class="w-14 h-14 rounded-full mx-auto border-4 border-orange-400">
          </div>
          <div class="user-name font-semibold">{{ leaderboard[2].user_name }}</div>
          <div class="user-score text-gray-600">{{ leaderboard[2].score }} pts</div>
          <div class="podium-base bg-orange-400 h-16 w-20 mt-2 rounded-t flex items-center justify-center">
            <span class="text-white font-bold text-xl">3</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Full leaderboard list -->
    <div class="leaderboard-list">
      <div v-for="(user, index) in leaderboard" :key="user.user" 
           class="leaderboard-item flex items-center p-4 border-b hover:bg-gray-50"
           :class="{ 'bg-blue-50': user.user === currentUser }">
        <div class="rank-badge mr-4">
          <span class="rank-number font-bold text-lg" 
                :class="getRankClass(user.rank_position)">{{ user.rank_position }}</span>
        </div>
        <div class="user-avatar mr-4">
          <img :src="user.user_image || '/assets/lms/images/default-avatar.png'" 
               class="w-12 h-12 rounded-full">
        </div>
        <div class="user-info flex-1">
          <div class="user-name font-semibold">{{ user.user_name }}</div>
          <div class="user-details text-sm text-gray-600">
            {{ getScoreLabel() }}: {{ user.score }}
          </div>
        </div>
        <div class="user-badges">
          <span v-if="user.rank_position <= 3" class="badge" :class="getBadgeClass(user.rank_position)">
            {{ getBadgeText(user.rank_position) }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- Current user rank (if not in top list) -->
    <div v-if="currentUserRank && currentUserRank.rank > 50" 
         class="current-user-rank mt-4 p-4 bg-blue-100 rounded">
      <div class="text-center">
        <span class="font-semibold">Your Rank: #{{ currentUserRank.rank }}</span>
        <span class="ml-2 text-gray-600">{{ currentUserRank.score }} {{ getScoreLabel().toLowerCase() }}</span>
      </div>
    </div>
    
    <!-- Loading state -->
    <div v-if="loading" class="text-center py-8">
      <div class="spinner">Loading...</div>
    </div>
  </div>
</template>

<script>
import { call } from 'frappe-ui'

export default {
  name: 'Leaderboard',
  props: {
    title: {
      type: String,
      default: 'Leaderboard'
    },
    leaderboardType: {
      type: String,
      default: 'global'
    },
    referenceDoc: {
      type: String,
      default: null
    }
  },
  data() {
    return {
      leaderboard: [],
      currentUserRank: null,
      totalParticipants: 0,
      selectedPeriod: 'all_time',
      selectedType: this.leaderboardType,
      loading: false,
      currentUser: null
    }
  },
  mounted() {
    this.currentUser = window.frappe?.session?.user
    this.loadLeaderboard()
  },
  methods: {
    async loadLeaderboard() {
      this.loading = true
      try {
        const response = await call('lms.lms.utils.get_leaderboard', {
          leaderboard_type: this.selectedType,
          reference_doc: this.referenceDoc,
          period: this.selectedPeriod,
          limit: 50
        })
        
        this.leaderboard = response.leaderboard || []
        this.currentUserRank = response.current_user_rank
        this.totalParticipants = response.total_participants || 0
      } catch (error) {
        console.error('Error loading leaderboard:', error)
      } finally {
        this.loading = false
      }
    },
    getRankClass(rank) {
      if (rank === 1) return 'text-yellow-600'
      if (rank === 2) return 'text-gray-600'
      if (rank === 3) return 'text-orange-600'
      return 'text-gray-800'
    },
    getBadgeClass(rank) {
      if (rank === 1) return 'bg-yellow-500 text-white'
      if (rank === 2) return 'bg-gray-500 text-white'
      if (rank === 3) return 'bg-orange-500 text-white'
      return 'bg-gray-300 text-gray-700'
    },
    getBadgeText(rank) {
      const badges = { 1: '🥇 Gold', 2: '🥈 Silver', 3: '🥉 Bronze' }
      return badges[rank] || ''
    },
    getScoreLabel() {
      if (this.selectedType === 'streak') return 'Days'
      return 'Points'
    }
  }
}
</script>

<style scoped>
.leaderboard-container {
  max-width: 800px;
  margin: 0 auto;
}

.podium-positions {
  height: 200px;
}

.podium-position {
  position: relative;
}

.first-place .podium-base {
  height: 100px;
}

.second-place .podium-base {
  height: 80px;
}

.third-place .podium-base {
  height: 60px;
}

.badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 2s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
```

### 4.2 Points Dashboard Component

**File**: `frontend/src/components/PointsDashboard.vue`

```vue
<template>
  <div class="points-dashboard">
    <div class="points-header mb-6">
      <h2 class="text-2xl font-bold mb-4">My Points</h2>
      
      <!-- Points Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div class="points-card bg-blue-500 text-white p-6 rounded-lg">
          <div class="points-icon mb-2">💎</div>
          <div class="points-value text-3xl font-bold">{{ userPoints.total_points }}</div>
          <div class="points-label">Total Points</div>
        </div>
        
        <div class="points-card bg-green-500 text-white p-6 rounded-lg">
          <div class="points-icon mb-2">💰</div>
          <div class="points-value text-3xl font-bold">{{ userPoints.available_points }}</div>
          <div class="points-label">Available Points</div>
        </div>
        
        <div class="points-card bg-purple-500 text-white p-6 rounded-lg">
          <div class="points-icon mb-2">🏆</div>
          <div class="points-value text-3xl font-bold">{{ userRank || 'N/A' }}</div>
          <div class="points-label">Global Rank</div>
        </div>
      </div>
    </div>
    
    <!-- Recent Transactions -->
    <div class="recent-transactions mb-6">
      <h3 class="text-xl font-semibold mb-4">Recent Activity</h3>
      <div class="transactions-list">
        <div v-for="transaction in userPoints.recent_transactions" :key="transaction.name"
             class="transaction-item flex items-center justify-between p-4 border-b hover:bg-gray-50">
          <div class="transaction-info flex items-center">
            <div class="transaction-icon mr-3">
              <span class="text-2xl">{{ getActivityIcon(transaction.activity_type) }}</span>
            </div>
            <div>
              <div class="transaction-description font-medium">{{ transaction.description }}</div>
              <div class="transaction-date text-sm text-gray-600">
                {{ formatDate(transaction.transaction_date) }}
              </div>
            </div>
          </div>
          <div class="transaction-points">
            <span class="points-amount font-bold" 
                  :class="transaction.transaction_type === 'Earned' || transaction.transaction_type === 'Bonus' ? 'text-green-600' : 'text-red-600'">
              {{ transaction.transaction_type === 'Earned' || transaction.transaction_type === 'Bonus' ? '+' : '-' }}{{ transaction.points }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Points Earning Guide -->
    <div class="earning-guide">
      <h3 class="text-xl font-semibold mb-4">How to Earn Points</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="earning-method p-4 border rounded-lg">
          <div class="method-icon text-2xl mb-2">📚</div>
          <div class="method-title font-semibold">Complete Lessons</div>
          <div class="method-points text-green-600 font-bold">+10 points</div>
          <div class="method-description text-sm text-gray-600">Finish watching a lesson</div>
        </div>
        
        <div class="earning-method p-4 border rounded-lg">
          <div class="method-icon text-2xl mb-2">🧠</div>
          <div class="method-title font-semibold">Pass Quizzes</div>
          <div class="method-points text-green-600 font-bold">+20 points</div>
          <div class="method-description text-sm text-gray-600">Score 70% or higher</div>
        </div>
        
        <div class="earning-method p-4 border rounded-lg">
          <div class="method-icon text-2xl mb-2">🎯</div>
          <div class="method-title font-semibold">Perfect Quiz Score</div>
          <div class="method-points text-green-600 font-bold">+50 points</div>
          <div class="method-description text-sm text-gray-600">Score 100% on a quiz</div>
        </div>
        
        <div class="earning-method p-4 border rounded-lg">
          <div class="method-icon text-2xl mb-2">🔥</div>
          <div class="method-title font-semibold">Daily Streak</div>
          <div class="method-points text-green-600 font-bold">+5 points/day</div>
          <div class="method-description text-sm text-gray-600">Learn every day</div>
        </div>
        
        <div class="earning-method p-4 border rounded-lg">
          <div class="method-icon text-2xl mb-2">🏅</div>
          <div class="method-title font-semibold">Complete Course</div>
          <div class="method-points text-green-600 font-bold">+100 points</div>
          <div class="method-description text-sm text-gray-600">Finish entire course</div>
        </div>
        
        <div class="earning-method p-4 border rounded-lg">
          <div class="method-icon text-2xl mb-2">🏆</div>
          <div class="method-title font-semibold">Win Challenges</div>
          <div class="method-points text-green-600 font-bold">+25-500 points</div>
          <div class="method-description text-sm text-gray-600">Complete challenges</div>
        </div>
      </div>
    </div>
    
    <!-- Loading state -->
    <div v-if="loading" class="text-center py-8">
      <div class="spinner">Loading...</div>
    </div>
  </div>
</template>

<script>
import { call } from 'frappe-ui'

export default {
  name: 'PointsDashboard',
  data() {
    return {
      userPoints: {
        total_points: 0,
        available_points: 0,
        recent_transactions: []
      },
      userRank: null,
      loading: false
    }
  },
  mounted() {
    this.loadUserPoints()
    this.loadUserRank()
  },
  methods: {
    async loadUserPoints() {
      this.loading = true
      try {
        const response = await call('lms.lms.doctype.lms_points_transaction.lms_points_transaction.get_user_points')
        this.userPoints = response
      } catch (error) {
        console.error('Error loading user points:', error)
      } finally {
        this.loading = false
      }
    },
    async loadUserRank() {
      try {
        const response = await call('lms.lms.utils.get_leaderboard', {
          leaderboard_type: 'global',
          period: 'all_time',
          limit: 1
        })
        this.userRank = response.current_user_rank?.rank
      } catch (error) {
        console.error('Error loading user rank:', error)
      }
    },
    getActivityIcon(activityType) {
      const icons = {
        'lesson_complete': '📚',
        'quiz_pass': '🧠',
        'quiz_perfect': '🎯',
        'course_complete': '🏅',
        'daily_login': '📅',
        'streak_bonus': '🔥',
        'challenge_complete': '🏆',
        'badge_earned': '🏆'
      }
      return icons[activityType] || '⭐'
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
    }
  }
}
</script>

<style scoped>
.points-dashboard {
  max-width: 1000px;
  margin: 0 auto;
}

.points-card {
  text-align: center;
  transition: transform 0.2s;
}

.points-card:hover {
  transform: translateY(-2px);
}

.points-icon {
  font-size: 2rem;
}

.earning-method {
  text-align: center;
  transition: transform 0.2s;
}

.earning-method:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 2s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
```

## 5. Integration with Existing System

### 5.1 Hooks Integration

**File**: `lms/hooks.py` (Add to existing file)

```python
# Add these to existing hooks

# Document Events for Gamification
doc_events = {
    "LMS Course Progress": {
        "after_insert": "lms.lms.gamification.award_lesson_points",
        "on_update": "lms.lms.gamification.update_progress_points"
    },
    "LMS Quiz Submission": {
        "on_submit": "lms.lms.gamification.award_quiz_points"
    },
    "LMS Enrollment": {
        "after_insert": "lms.lms.gamification.award_enrollment_points",
        "on_update": "lms.lms.gamification.check_course_completion"
    },
    "User": {
        "after_insert": "lms.lms.gamification.setup_new_user_gamification"
    }
}

# Scheduled Tasks for Gamification
scheduler_events = {
    "daily": [
        "lms.lms.gamification.update_daily_streaks",
        "lms.lms.gamification.process_daily_challenges",
        "lms.lms.gamification.recalculate_leaderboards"
    ],
    "hourly": [
        "lms.lms.gamification.monitor_active_challenges"
    ]
}

# Web Pages
website_route_rules = [
    {"from_route": "/leaderboard", "to_route": "leaderboard"},
    {"from_route": "/points", "to_route": "points-dashboard"},
    {"from_route": "/challenges", "to_route": "challenges"},
    {"from_route": "/streaks", "to_route": "streak-tracker"}
]
```

### 5.2 Gamification Utils

**File**: `lms/lms/gamification.py` (New file)

```python
import frappe
from frappe.utils import now_datetime, cint, flt, getdate
from lms.lms.