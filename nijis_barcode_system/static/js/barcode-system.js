$(function() {
    updateEntryList($('#equipment_selector').val());

    $('#equipment_selector').on("changed.bs.select", function(e, clickedIndex, newValue, oldValue) {
        updateEntryList(this.value)
    });

});


function updateEntryList(equipment_id){
    $('#equipment_entry_selector').find('option').remove();
    var equipmentData = $('#equipment-data').data().equipment;
    var options = [];
    for (var single_equipment in equipmentData){
        if (equipmentData[single_equipment]['equipment_id'] === parseInt(equipment_id)){
            for (var single_entry in equipmentData[single_equipment]['equipment_entries']){
                workingOnEntry=equipmentData[single_equipment]['equipment_entries'][single_entry];
                var option = "<option value=" + workingOnEntry['equipment_entry_id'] + ">" + equipmentData[single_equipment]['equipment_code'] + workingOnEntry['equipment_entry_number'] + "</option>";
                options.push(option);
            }
        }
    }
    $('#equipment_entry_selector').html(options);
    $('#equipment_entry_selector').selectpicker('refresh');
}


function printLabels() {
    $.ajax({
        type: "POST",
        url: "/print_labels",
        data: {
            equipment_id: $('#equipment_selector').val(),
            quantity: $('#labels_to_print').val()
        },
        success: function (result) {
            // noinspection BadExpressionStatementJS
            swal({
                  type: 'success',
                  title: 'Printing finished',
                  allowOutsideClick: false,
                  text: 'Printing now finished'
                }).then((result) => {
                    window.location.reload();
                })
        },
        error: function (result) {
            alert('Error!');
            window.location.reload();
        }
    });
}

function reprintLabel() {
    $.ajax({
        type: "POST",
        url: "/reprint_label",
        data: {
            entry_id: $('#equipment_entry_selector').val(),
            entry_code: $('#equipment_entry_selector').find("option:selected").text()
        },
        success: function (result) {
            swal({
                  type: 'success',
                  title: 'Printing finished',
                  allowOutsideClick: false,
                  text: 'Printing now finished'
                })
        },
        error: function (result) {
            alert('Error!');
            window.location.reload();
        }
    });
}

function addNewEquipment() {
    $.ajax({
        type: "POST",
        url: "/add_equipment",
        data: {
            equipment_name: $('#equipment_name').val(),
            equipment_code: $('#equipment_code').val(),
            equipment_group_id: $('#equipment_group_selector').val()
        },
        success: function (result) {
            // noinspection BadExpressionStatementJS
            swal({
                  type: 'success',
                  title: 'Equipment added',
                  allowOutsideClick: false,
                  text: 'Equipment successfuly added!'
                }).then((result) => {
                    window.location.reload();
                })
        },
        error: function (result) {
            // noinspection BadExpressionStatementJS
            swal({
                  type: 'error',
                  title: 'Error',
                  allowOutsideClick: false,
                  text: 'Error! Unable to add equipment item. Are you sure the item does not already exist? Or perhaps you a code that was not 3 characters long?'
                }).then((result) => {
                    window.location.reload();
                })
        }
    });
}