import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
	"""Add gamification custom fields to User doctype"""
	
	custom_fields = {
		"User": [
			{
				"fieldname": "gamification_section",
				"label": "Gamification",
				"fieldtype": "Section Break",
				"insert_after": "user_image",
				"collapsible": 1
			},
			{
				"fieldname": "total_points",
				"label": "Total Points",
				"fieldtype": "Int",
				"default": 0,
				"read_only": 1,
				"insert_after": "gamification_section"
			},
			{
				"fieldname": "available_points",
				"label": "Available Points",
				"fieldtype": "Int",
				"default": 0,
				"read_only": 1,
				"insert_after": "total_points"
			},
			{
				"fieldname": "column_break_gamification_1",
				"fieldtype": "Column Break",
				"insert_after": "available_points"
			},
			{
				"fieldname": "current_streak",
				"label": "Current Streak",
				"fieldtype": "Int",
				"default": 0,
				"read_only": 1,
				"insert_after": "column_break_gamification_1"
			},
			{
				"fieldname": "longest_streak",
				"label": "Longest Streak",
				"fieldtype": "Int",
				"default": 0,
				"read_only": 1,
				"insert_after": "current_streak"
			},
			{
				"fieldname": "section_break_gamification_2",
				"fieldtype": "Section Break",
				"insert_after": "longest_streak"
			},
			{
				"fieldname": "last_activity_date",
				"label": "Last Activity Date",
				"fieldtype": "Date",
				"read_only": 1,
				"insert_after": "section_break_gamification_2"
			},
			{
				"fieldname": "streak_freeze_count",
				"label": "Streak Freeze Count",
				"fieldtype": "Int",
				"default": 0,
				"read_only": 1,
				"insert_after": "last_activity_date"
			},
			{
				"fieldname": "column_break_gamification_2",
				"fieldtype": "Column Break",
				"insert_after": "streak_freeze_count"
			},
			{
				"fieldname": "level",
				"label": "Level",
				"fieldtype": "Int",
				"default": 1,
				"read_only": 1,
				"insert_after": "column_break_gamification_2"
			},
			{
				"fieldname": "achievements",
				"label": "Achievements",
				"fieldtype": "Long Text",
				"read_only": 1,
				"insert_after": "level",
				"description": "JSON array of user achievements"
			}
		]
	}
	
	try:
		create_custom_fields(custom_fields, update=True)
		frappe.db.commit()
		print("Successfully added gamification custom fields to User doctype")
	except Exception as e:
		frappe.log_error(f"Error adding gamification custom fields: {str(e)}")
		print(f"Error adding gamification custom fields: {str(e)}")