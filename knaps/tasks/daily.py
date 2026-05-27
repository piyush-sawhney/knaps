import frappe
from frappe import _

from knaps.utils.constants import DOCTYPE_PO_INVESTMENT, DOCTYPE_RD_ACCOUNT


def notify_role(role: str, message: str) -> None:
	users = frappe.get_all("Has Role", filters={"role": role}, fields=["parent"])
	valid_users = set(
		frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
	)
	recipients = [u.parent for u in users if u.parent in valid_users]
	for user in recipients:
		log = frappe.new_doc("Notification Log")
		log.subject = _("RD Account Mismatch with PO Investment")
		log.email_content = message
		log.for_user = user
		log.type = "Alert"
		log.insert(ignore_permissions=True)
	if recipients:
		frappe.publish_realtime(
			event="show_alert",
			message={"message": message, "indicator": "red"},
			user=recipients,
			after_commit=True,
		)


def update_po_investment_in_rd_account() -> None:
	rd_accounts = frappe.get_all(DOCTYPE_RD_ACCOUNT, filters={"po_rd_investment": None}, pluck="name")
	for rd_account in rd_accounts:
		po_investment = frappe.db.get_value(
			DOCTYPE_PO_INVESTMENT,
			{"account_number": rd_account, "scheme_code": "RD"},
			"name",
		)
		if po_investment:
			rd_doc = frappe.get_doc(DOCTYPE_RD_ACCOUNT, rd_account)
			rd_doc.po_rd_investment = po_investment
			try:
				rd_doc.save()
			except Exception as e:
				frappe.log_error(
					message=_("Failed to link RD Account {} to PO Investment {}: {}").format(
						rd_account, po_investment, e
					),
					title="RD Account Link Failed",
				)
				if isinstance(e, frappe.ValidationError):
					frappe.clear_last_message()
					message = _("RD Account {} and PO Investment {} have {}").format(
						rd_account, po_investment, e
					)
					notify_role("KNAPS RD Manager", message)
