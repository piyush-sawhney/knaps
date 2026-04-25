__version__ = "0.0.1"
import frappe
from frappe.utils.user import is_website_user
def check_app_permission():
	if frappe.session.user == "Administrator":
		return True

	if is_website_user():
		return False

	return True