# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSQuestionMaster(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from knaps.knaps.doctype.knaps_question_module_type.knaps_question_module_type import (
			KNAPSQuestionModuleType,
		)
		from knaps.knaps.doctype.knaps_question_option.knaps_question_option import KNAPSQuestionOption

		answer_mode: DF.Literal["", "Native Input", "Options Needed"]
		configuration: DF.JSON | None
		help_text: DF.SmallText | None
		internal_notes: DF.TextEditor | None
		module_type: DF.TableMultiSelect[KNAPSQuestionModuleType]
		options: DF.Table[KNAPSQuestionOption]
		question_text: DF.LongText | None
		question_type: DF.Literal[
			"",
			"Single Select",
			"Multi Select",
			"Yes/No",
			"Number",
			"Currency",
			"Percentage",
			"Text",
			"Date",
			"Rating",
			"File Upload",
			"Declaration",
		]
		weight: DF.Float
	# end: auto-generated types

	pass
