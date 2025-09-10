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
			file_url = frappe.db.get_value(
				"File",
				{"file_name": doc.name + ".pdf"},
				"file_url"
			)
			media_link = frappe.utils.get_url() + file_url

		link_text = ""
		if media_link:
			link_text = ", Link : " + media_link
		WhatsAppMessage.send_whatsapp_message(
			receiver_list=self.get_receiver_list(doc, context),
			message=frappe.render_template(self.message + link_text, context),
			doctype = self.doctype,
			docname = self.name,
			media=media_link
		)