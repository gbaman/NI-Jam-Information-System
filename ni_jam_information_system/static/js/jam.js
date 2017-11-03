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