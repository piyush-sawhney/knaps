# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSRiskProfileTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps_client_management.doctype.knaps_risk_profile_template_question.knaps_risk_profile_template_question import (
			KNAPSRiskProfileTemplateQuestion,
		)

		amended_from: DF.Link | None
		applicable_for: DF.Link
		category_code: DF.Data | None
		effective_from: DF.Date | None
		effective_to: DF.Date | None
		is_active: DF.Check
		notes: DF.TextEditor | None
		questions: DF.Table[KNAPSRiskProfileTemplateQuestion]
		scoring_method: DF.JSON
		template_name: DF.Data
		version: DF.Int
	# end: auto-generated types

	pass
