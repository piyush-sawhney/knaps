# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from knaps.utils.constants import DOCTYPE_INDIVIDUAL, DOCTYPE_NON_INDIVIDUAL


class KNAPSChannelPartner(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		name: DF.Int | None
		partner: DF.DynamicLink
		partner_code: DF.Data | None
		partner_name: DF.Data | None
		partner_type: DF.Link
		relationship: DF.Literal[
			"",
			"Principal (Upstream)",
			"Associate (Horizontal)",
			"Referral (Horizontal)",
			"Sub-Agent (Downstream)",
		]
	# end: auto-generated types

	def before_save(self):
		self._set_partner_name()

	def _set_partner_name(self) -> None:
		if not self.partner or not self.partner_type:
			self.partner_name = None
			return

		if self.partner_type == DOCTYPE_INDIVIDUAL:
			self.partner_name = frappe.db.get_value(DOCTYPE_INDIVIDUAL, self.partner, "full_name")
		elif self.partner_type == DOCTYPE_NON_INDIVIDUAL:
			self.partner_name = frappe.db.get_value(DOCTYPE_NON_INDIVIDUAL, self.partner, "legal_name")
