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


function bookWorkshopAlert(workshop_id, attendee_id, alert_message) {
    alertify.confirm('Warning', alert_message
        , function(){ bookWorkshop(workshop_id, attendee_id) }, function(){}).set('labels', {ok:'Confirm', cancel:'Cancel'})
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
            if (result === "Success"){
                var button = $("#" + workshop_id + "-" + attendee_id);
                button.toggleClass('btn-danger btn-success');
                button.attr("onclick","unbookWorkshop('" + workshop_id + "', '" + attendee_id +" ')");
                updateBookedInCount(workshop_id);
                alertify.success('Workshop booked');
            } else {
                alertify.alert("Workshop booking error",  result,
                function(){
                    window.location.reload();
                });
            }
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
            alertify.error('Workshop unbooked');
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

function editLedgerSupplier(transaction_id, supplier, item) {
    alertify.prompt( 'Edit supplier', '', supplier
               , function(evt, value){ updateLedgerSupplier(transaction_id, value); item.textContent = value}, function() {});
}

function editLedgerNotes(transaction_id, notes, item) {
    alertify.prompt( 'Edit notes', '', notes
               , function(evt, value){ updateLedgerNotes(transaction_id, value); item.textContent = value}, function() {});
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
            alertify.success('Updated description saved');
        },
        error: function (result) {
            alertify.alert("Unable to update description.",
                function(){
                    window.location.reload();
                });
        }
    });
}

function updateLedgerSupplier(transaction_id, supplier){
    $.ajax({
        type: "POST",
        url: "/trustee/finance/ledger/update_supplier_ajax",
        data: {
            transaction_id: transaction_id,
            supplier: supplier
        },
        success: function (result) {
            alertify.success('Updated supplier saved');
        },
        error: function (result) {
            alertify.alert("Unable to update supplier.",
                function(){
                    window.location.reload();
                });
        }
    });
}

function updateLedgerNotes(transaction_id, notes){
    $.ajax({
        type: "POST",
        url: "/trustee/finance/ledger/update_notes_ajax",
        data: {
            transaction_id: transaction_id,
            notes: notes
        },
        success: function (result) {
            alertify.success('Updated note saved');
        },
        error: function (result) {
            alertify.alert("Unable to update notes.",
                function(){
                    window.location.reload();
                });
        }
    });
}


$(function() {

  $(".transaction-category-picker").on("changed.bs.select", function(e, clickedIndex, newValue, oldValue) {

      updateLedgerCategory(this.attributes["data-transaction"].value, this.value);
      console.log(this.value, clickedIndex, newValue, oldValue)
  });

});

function updateLedgerCategory(transaction_id, category){
    $.ajax({
        type: "POST",
        url: "/trustee/finance/ledger/update_category_ajax",
        data: {
            transaction_id: transaction_id,
            category: category
        },
        success: function (result) {
            alertify.success('Category updated');
        },
        error: function (result) {
            alertify.alert("Unable to update category.",
                function(){
                    window.location.reload();
                });
        }
    });
}

function rejectExpense(expense_id, item) {
    alertify.prompt( 'Rejection reason', '', ""
               , function(evt, value){ rejectExpenseReason(expense_id, value);}, function() {});
}


function rejectExpenseReason(expense_id, rejection_reason){
    $.ajax({
        type: "POST",
        url: "/trustee/finance/expenses_list/rejection_reason",
        data: {
            expense_id: expense_id,
            rejection_reason: rejection_reason
        },
        success: function (result) {
            window.location.reload();
        },
        error: function (result) {
            alertify.alert("Unable to reject expense",
                function(){
                    window.location.reload();
                });
        }
    });
}


function editPiNetUsername(attendee_id, username, item) {
    alertify.prompt('Edit PiNet username', '', username
        , function (evt, value) {
            updatePiNetUsername(attendee_id, value);
            if (item){
                updatePiNetUsername(attendee_id, value);
                item.textContent = value;
                var element = document.getElementById("award_badge_button_{0}".format(attendee_id));
                element.className = element.className.replace(/\bdisabled\b/g, "")
            } else{
                updatePiNetUsername(attendee_id, value, true);
                
            }
        }, function () {
        });
}

    
function updatePiNetUsername(attendee_id, username, reload){
    $.ajax({
        type: "POST",
        url: "/update_pinet_username",
        data: {
            attendee_id: attendee_id,
            username: username
        },
        success: function (result) {
            
            if (reload){
                window.location.reload();
            } else{
               alertify.success('Username update successful'); 
            }
            
        },
        error: function (result) {
            alertify.alert("Error", "Unable to update username. This may be because the username was blank or does not exist in the system.",
                function(){
                    window.location.reload();
                });
        }
    });
}


function updateWorkshopBadgeAward(attendee_id, badge_id, item, attendee_login_id){
    if (item.textContent.includes('Award')) {
        item.textContent = 'Remove';
        item.classList.replace("btn-info", "btn-danger");
        item.parentNode.parentNode.style.backgroundColor = "#c4fc9f";
    } else {
        item.textContent = 'Award';
        item.classList.replace("btn-danger", "btn-info");
        item.parentNode.parentNode.style.backgroundColor = "#ffffff";
    }
    
    $.ajax({
        type: "POST",
        url: "/admin/update_workshop_badge_award",
        data: {
            attendee_id: attendee_id,
            badge_id: badge_id,
            attendee_login_id: attendee_login_id
        },
        success: function (result) {
            alertify.success('Badge updated');
        },
        error: function (result) {
            alertify.alert("Unable to update badge",
                function(){
                    window.location.reload();
                });
        }
    });
}


function recalculateBadges() {
    $.ajax({
        type: "POST",
        url: "/admin/ajax_recalculate_badges",
        success: function (result) {
            alertify.success('Badge awardees updated');
        },
        error: function (result) {
            alertify.error('Badge awardees failed to update');
        }
    });
}

function unableToBookMessage(message) {
    alertify.alert('Unable to book workshop', message, function(){});
}


function editJamPassword(jam_id, jam_password, item) {
    alertify.prompt( 'Edit password', '', jam_password
               , function(evt, value){ updateJamPassword(jam_id, value); item.textContent = value}, function() {});
}


function updateJamPassword(jam_id, jam_password){
    $.ajax({
        type: "POST",
        url: "/admin/update_jam_password_ajax",
        data: {
            jam_id: jam_id,
            jam_password: jam_password
        },
        success: function (result) {
            alertify.success('Updated password saved');
        },
        error: function (result) {
            alertify.alert("Unable to update password.",
                function(){
                    window.location.reload();
                });
        }
    });
}


function checkDobInSystem(){
    $.ajax({
        type: "POST",
        url: "/admin/verify_dob_in_system",
        success: function (result) {
            if (result === "false") {
                alertify.prompt('Please enter Date of Birth', 'Please enter your Date of Birth in DD/MM/YYYY format, as this section of NIJIS requires it.', 'DD/MM/YYYY'
                    , function (evt, value) {
                        $.ajax({
                            type: "POST",
                            url: "/admin/update_dob_in_system",
                            data: {
                                dob: value
                            },
                            success: function (result) {
                                alertify.success('DoB updated!');
                            },
                            error: function (result) {
                                alertify.error('Updating DoB failed...');
                            }
                        });
                    }
                    , function () {
                        alertify.error('No DoB entered...')
                    });
            }
        },
        error: function (result) {
            alertify.alert("Unable to do DoB check",
                function(){
                    window.location.reload();
                });
        }
    });
    
}