import frappe
from frappe import _
from frappe.email.doctype.notification.notification import Notification, get_context, json
from twilio_integration.twilio_integration.doctype.whatsapp_message.whatsapp_message import WhatsAppMessage
import urllib.parse

class SendNotification(Notification):
	def validate(self):
		self.validate_twilio_settings()

	def validate_twilio_settings(self):
		if self.enabled and self.channel == "WhatsApp" \
			and not frappe.db.get_single_value("Twilio Settings", "enabled"):
			frappe.throw(_("Please enable Twilio settings to send WhatsApp messages"))

	def send(self, doc):
		context = get_context(doc)
		context = {"doc": doc, "alert": self, "comments": None}
		if doc.get("_comments"):
			context["comments"] = json.loads(doc.get("_comments"))

		if self.is_standard:
			self.load_standard_properties(context)

		try:
			if self.channel == 'WhatsApp':
				self.send_whatsapp_msg(doc, context)
		except:
			frappe.log_error(title='Failed to send notification', message=frappe.get_traceback())

		super(SendNotification, self).send(doc)

	def send_whatsapp_msg(self, doc, context):

		# Optional: fetch media from attachments if you want to support it
		media_link = None
		if self.attach_print:
			# Example: generate PDF link

			default_format = None
			if self.print_format:
				default_format = self.print_format
			else:
				default_format = self.get_default_print_format(doctype = doc.doctype)

			media_link = (
				frappe.utils.get_url() +
				"/api/method/frappe.utils.print_format.download_pdf"
				f"?doctype={urllib.parse.quote(doc.doctype)}"
				f"&name={urllib.parse.quote(doc.name)}"
				f"&format={urllib.parse.quote(default_format)}"
				f"&no_letterhead=0"
				f"&letterhead={urllib.parse.quote('No Letterhead')}"
				f"&settings={urllib.parse.quote('{}')}"
				f"&_lang=en"
			)

		WhatsAppMessage.send_whatsapp_message(
			receiver_list=self.get_receiver_list(doc, context),
			message=frappe.render_template(self.message, context),
			doctype = self.doctype,
			docname = self.name,
			media=media_link
		)

	def get_default_print_format(self, doctype):
		default_format = frappe.db.get_value("Property Setter", {
			"doc_type": doctype,
			"property": "default_print_format"
		}, "value")

		return default_format or "Default"