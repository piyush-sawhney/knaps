# Copyright (c) 2026, KNAPS and Contributors and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class KNAPSFamilyMember(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		member_name: DF.DynamicLink
		member_role: DF.Link | None
		member_type: DF.Link
		membership_type: DF.Literal["", "Primary", "Secondary", "Beneficial"]
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		relation_with_head: DF.Link | None
	# end: auto-generated types

	pass
