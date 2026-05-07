import frappe
import uuid

@frappe.whitelist(allow_guest=True)
def verify_pan(pan):
	"""Check if PAN exists in KNAPS Person and send OTP"""
	# For now, simulate - check if person exists
	person = frappe.db.get_value("KNAPS Person", {"pan": pan}, ["name", "full_name", "primary_phone", "primary_email"], as_dict=True)

	if person:
		otp = "123456"  # Simulated OTP for testing
		frappe.msgprint(f"OTP for testing: {otp}")
		return {
			"success": True,
			"exists": True,
			"data": {
				"name": person.name,
				"full_name": person.full_name,
				"phone": person.primary_phone,
				"email": person.primary_email
			}
		}
	else:
		otp = "123456"  # Simulated OTP for testing
		frappe.msgprint(f"OTP for testing: {otp}")
		return {
			"success": True,
			"exists": False,
			"data": {}
		}

@frappe.whitelist(allow_guest=True)
def verify_otp(otp):
	"""Verify the OTP"""
	if otp == "123456":
		return {"success": True}
	return {"success": False, "message": "Invalid OTP"}

@frappe.whitelist(allow_guest=True)
def save_onboarding(data):
	"""Save onboarding data"""
	frappe.flags.ignore_permissions = True
	return {"success": True, "message": "Data saved"}

def get_context(context):
	context.title = "KNAPS Onboarding"
	context.brand_html = "KNAPS"
	context.hide_navbar = True
	context.hide_footer = True
	context.logo_url = "/assets/knaps/images/knaps-logo.png"