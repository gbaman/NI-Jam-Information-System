$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip();
});

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
        url: "/admin_modify_workshop",
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
        url: "/delete_workshop_from_jam_ajax",
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
        url: "/admin_get_password_reset_code_ajax",
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
        url: "/admin_upgrade_to_volunteer_permission_ajax",
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


function checkOutAttendee(attendee_id) {
    $.ajax({
        type: "POST",
        url: "/admin_check_out_attendee_ajax",
        data: {
            attendee_id: attendee_id
        },
        success: function (result) {
            alert("Attendee status updated");
            window.location.reload();
        },
        error: function (result) {
            alert('Error updating status');
            window.location.reload();
        }
    });
}


function checkInAttendee(attendee_id) {
    $.ajax({
        type: "POST",
        url: "/admin_check_in_attendee_ajax",
        data: {
            attendee_id: attendee_id
        },
        success: function (result) {
            alert("Attendee status updated");
            window.location.reload();
        },
        error: function (result) {
            alert('Error updating status');
            window.location.reload();
        }
    });
}

function updateAttendeeInfo() {
    $.ajax({
        type: "POST",
        url: "/admin_update_attendee_info_ajax",
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