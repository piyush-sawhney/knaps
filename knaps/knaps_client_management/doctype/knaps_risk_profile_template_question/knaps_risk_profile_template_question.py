# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSRiskProfileTemplateQuestion(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		is_mandatory: DF.Check
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		question_code: DF.Link
		question_section: DF.Literal[
			"",
			"Financial Capacity",
			"Investment Horizon",
			"Risk Appetite",
			"Investment Experience",
			"Investment Objective",
			"Liquidity Requirement",
			"Compliance/Suitability",
			"Behavioral Profile",
			"Family Dynamics",
		]
		question_section_order_number: DF.Int
		question_text: DF.LongText | None
	# end: auto-generated types

	pass
