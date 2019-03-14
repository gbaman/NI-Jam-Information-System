$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});


// From https://stackoverflow.com/questions/18405736/is-there-a-c-sharp-string-format-equivalent-in-javascript
// I like Pythons string.format() method.
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

function selectJam(jam_id) {
    $.ajax({
        type: "POST",
        url: "/admin/select_jam",
        data: {
            jam_id: jam_id,
            attendee_id: $(".form-control").val()
        },
        success: function (result) {
            alert('New Jam selected.');
            window.location.reload();
        },
        error: function (result) {
            alert('Error selecting Jam.');
            window.location.reload();
        }
    });
}


function deleteJam(jam_id) {
    $.ajax({
        type: "POST",
        url: "/admin/delete_jam",
        data: {
            jam_id: jam_id,
            attendee_id: $(".form-control").val()
        },
        success: function (result) {
            alert('Jam deleted');
            window.location.reload();
        },
        error: function (result) {
            alert('Error deleting Jam.');
            window.location.reload();
        }
    });
}


function addWorkshopBooking(workshop_id) {
    $.ajax({
        type: "POST",
        url: "/add_workshop_bookings_ajax",
        data: {
            workshop_id: workshop_id,
            attendee_id: $(".form-control").val()
        },
        success: function (result) {
            alert('Workshop booked');
            window.location.reload();
        },
        error: function (result) {
            alert('Error booking workshop. This may be because you are already booked into a workshop for that block, or tried booking a parent/guardian ticket into the workshop.');
            window.location.reload();
        }
    });
}


function removeWorkshopBooking(workshop_id) {
    $.ajax({
        type: "POST",
        url: "/remove_workshop_bookings_ajax",
        data: {
            workshop_id: workshop_id,
            attendee_id: $(".form-control").val()
        },
        success: function (result) {
            alert('Workshop unbooked');
            window.location.reload();
        },
        error: function (result) {
            alert('Error removing booking from workshop. Are you sure you were booked onto it?');
            window.location.reload();
        }
    });
}


function admin_modify_workshop(workshop_id) {
    $.ajax({
        type: "POST",
        url: "/admin/modify_workshop",
        data: {
            workshop_id: workshop_id,
            attendee_id: $(".form-control").val()
        },
        success: function (result) {
            alert('Workshop booked');
            window.location.reload();
        },
        error: function (result) {
            alert('Error booking workshop. This may be because you are already booked into a workshop for that block, or tried booking a parent/guardian ticket into the workshop.');
            window.location.reload();
        }
    });


}

function deleteJamWorkshop(workshop_id) {
    $.ajax({
        type: "POST",
        url: "/admin/delete_workshop_from_jam_ajax",
        data: {
            workshop_id: workshop_id
        },
        success: function (result) {
            alert('Workshop deleted');
            window.location.reload();
        },
        error: function (result) {
            alert('Error deleting workshop.');
            window.location.reload();
        }
    });
}

function getPasswordResetCode(user_id) {
    $.ajax({
        type: "POST",
        url: "/admin/get_password_reset_code_ajax",
        data: {
            user_id: user_id
        },
        success: function (result) {
            alert(result);
            window.location.reload();
        },
        error: function (result) {
            alert('Error getting reset code.');
            window.location.reload();
        }
    });
}


function upgradeToVolunteerPermission(user_id) {
    $.ajax({
        type: "POST",
        url: "/admin/upgrade_to_volunteer_permission_ajax",
        data: {
            user_id: user_id
        },
        success: function (result) {
            alert("User upgraded to volunteer permission level");
            window.location.reload();
        },
        error: function (result) {
            alert('Error upgrading permission');
            window.location.reload();
        }
    });
}


function disableVolunteerAccount(user_id) {
    $.ajax({
        type: "POST",
        url: "/admin/disable_volunteer_account_ajax",
        data: {
            user_id: user_id
        },
        success: function (result) {
            alert("User disabled");
            window.location.reload();
        },
        error: function (result) {
            alert('Error disabling user');
            window.location.reload();
        }
    });
}


function enableVolunteerAccount(user_id) {
    $.ajax({
        type: "POST",
        url: "/admin/enable_volunteer_account_ajax",
        data: {
            user_id: user_id
        },
        success: function (result) {
            alert("User enabled");
            window.location.reload();
        },
        error: function (result) {
            alert('Error enabling user');
            window.location.reload();
        }
    });
}


function checkOutAttendee(attendee_id) {
    $.ajax({
        type: "POST",
        url: "/admin/check_out_attendee_ajax",
        data: {
            attendee_id: attendee_id
        },
        success: function (result) {
            var row = $("#tr-" + attendee_id);
            row.attr("bgcolor","#fff60a");
            var loc = $("#loc-" + attendee_id);
            loc.text("Checked out")
        },
        error: function (result) {

            alertify.alert("Check out error", "The attendee has been unable to be checked out.",
                function(){
                    window.location.reload();
                });

        }
    });
}


function checkInAttendee(attendee_id) {
    $.ajax({
        type: "POST",
        url: "/admin/check_in_attendee_ajax",
        data: {
            attendee_id: attendee_id
        },
        success: function (result) {
            var row = $("#tr-" + attendee_id);
            row.attr("bgcolor","#c4fc9f");
            var loc = $("#loc-" + attendee_id);
            loc.text("Checked in")
        },
        error: function (result) {
            alertify.alert("Check in error", "The attendee has been unable to be checked in.",
                function(){
                    window.location.reload();
                });
        }
    });
}


function updateAttendeeInfo() {
    $.ajax({
        type: "POST",
        url: "/admin/update_attendee_info_ajax",
        success: function (result) {
            alert("Attendee info updated");
            window.location.reload();
        },
        error: function (result) {
            alert('Error updating attendee info');
            window.location.reload();
        }
    });
}


function bookWorkshop(workshop_id, attendee_id) {
    $.ajax({
        type: "POST",
        url: "/add_workshop_bookings_ajax",
        data: {
            workshop_id: workshop_id,
            attendee_id: attendee_id
        },
        success: function (result) {
            var button = $("#" + workshop_id + "-" + attendee_id);
            button.toggleClass('btn-danger btn-success');
            button.attr("onclick","unbookWorkshop('" + workshop_id + "', '" + attendee_id +" ')");
            updateBookedInCount(workshop_id);
        },
        error: function (result) {

            alertify.alert("Workshop booking error", "Workshop failed to update. This is likely due to the workshop already being full, or this attendee is already booked into another workshop in the same session.",
                function(){
                    window.location.reload();
                });

        }
    });
}


function unbookWorkshop(workshop_id, attendee_id) {
    $.ajax({
        type: "POST",
        url: "/remove_workshop_bookings_ajax",
        data: {
            workshop_id: workshop_id,
            attendee_id: attendee_id
        },
        success: function (result) {
            var button = $("#" + workshop_id + "-" + attendee_id);
            button.toggleClass('btn-success btn-danger');
            button.attr("onclick","bookWorkshop('" + workshop_id + "', '" + attendee_id +" ')");
            updateBookedInCount(workshop_id);
        },
        error: function (result) {
            alertify.alert("Workshop update error", "Workshop failed to update.",
                function(){
                    window.location.reload();
                });
        }
    });
}

function updateBookedInCount(workshop_id) {
    $.ajax({
        type: "POST",
        url: "/update_booked_in_count",
        data: {
            workshop_id: workshop_id
        },
        success: function (result) {
            $("#" + workshop_id + "-max-attendees").text(result);
        },
        error: function (result) {
            alert("Status update error", 'Error updating status');
            window.location.reload();
        }
    });
}


function selectInventory(inventory_id) {
    $.ajax({
        type: "POST",
        url: "/admin/select_inventory_ajax",
        data: {
            inventory_id: inventory_id
        },
        success: function (result) {
            window.location.reload();
        },
        error: function (result) {
            alertify.alert("Unable to select inventory, do you have permissions?",
                function(){
                    window.location.reload();
                });
        }
    });
}

function editLedgerDescription(transaction_id, description, item) {
    alertify.prompt( 'Edit description', '', description
               , function(evt, value){ updateLedgerDescription(transaction_id, value); item.textContent = value}, function() {});
    
    
}

function updateLedgerDescription(transaction_id, description){
    $.ajax({
        type: "POST",
        url: "/trustee/finance/ledger/update_description_ajax",
        data: {
            transaction_id: transaction_id,
            description: description
        },
        success: function (result) {
            //window.location.reload();
        },
        error: function (result) {
            alertify.alert("Unable to update description.",
                function(){
                    window.location.reload();
                });
        }
    });
}