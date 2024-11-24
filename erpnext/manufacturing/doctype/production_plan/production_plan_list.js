<<<<<<< HEAD
frappe.listview_settings["Production Plan"] = {
=======
frappe.listview_settings['Production Plan'] = {
>>>>>>> 69d88a9212 (fix: Production Plan: load document defaults for plan items & remove name column from listview (#26584))
	hide_name_column: true,
	add_fields: ["status"],
	filters: [["status", "!=", "Closed"]],
	get_indicator: function (doc) {
		if (doc.status === "Submitted") {
			return [__("Not Started"), "orange", "status,=,Submitted"];
		} else {
			return [
				__(doc.status),
				{
					Draft: "red",
					"In Process": "orange",
					Completed: "green",
					"Material Requested": "yellow",
					Cancelled: "gray",
					Closed: "grey",
				}[doc.status],
				"status,=," + doc.status,
			];
		}
	},
};
