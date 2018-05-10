var inventory_id = parseInt(window.location.pathname.split("/").pop());


$(document).ready(function(){
    getInventoryEquipment(inventory_id);
    $('#barcodeEntry').focus();

    document.getElementById('barcodeEntry').onkeypress = function(e){
    if (!e) e = window.event;
    var keyCode = e.keyCode || e.which;
    if (keyCode == '13'){
      addInventoryEquipmentEntry(inventory_id, $('#barcodeEntry').val(), 1);
      getInventoryEquipment(inventory_id);
      $('#barcodeEntry').value = "";
      return false;
    }
  };

});


function getInventoryEquipment(inventory_id) {
    $.ajax({
        type: "POST",
        url: "/admin/get_inventory_equipment",
        data: {
            inventory_id: inventory_id
        },
        success: function (result) {
            updateInventoryEquipmentTable(JSON.parse(result));
        },
        error: function (result) {


        }
    });
}


function addInventoryEquipmentEntry(inventory_id, equipment_entry_id, entry_quantity) {
    $.ajax({
        type: "POST",
        url: "/admin/add_inventory_equipment_entry",
        data: {
            inventory_id: inventory_id,
            equipment_entry_id: equipment_entry_id,
            entry_quantity:entry_quantity
        },
        success: function (result) {
            getInventoryEquipment(inventory_id);
            alertify.success('Item with ID {0} added (or quantity updated)'.format(equipment_entry_id));
        },
        error: function (result) {
            alertify.error('Failed to add item. May not exist or already been added');

        }
    });
}


function removeInventoryEquipmentEntry(inventory_id, equipment_entry_id) {
    $.ajax({
        type: "POST",
        url: "/admin/remove_inventory_equipment_entry",
        data: {
            inventory_id: inventory_id,
            equipment_entry_id: equipment_entry_id
        },
        success: function (result) {
            getInventoryEquipment(inventory_id);
            alertify.success('Item with ID {0} removed.'.format(equipment_entry_id));
        },
        error: function (result) {
            alertify.error('Failed to remove item.');

        }
    });
}


function updateInventoryEquipmentTable(equipmentData){
    var tableHTML = "";
    for (equipmentID in equipmentData){
        equipment_item = equipmentData[equipmentID];
        tableHTML = tableHTML + "<tr class='clickable' data-toggle='collapse' id='collapsed{0}' data-target='.collapsed{0}' bgcolor='#efefef'> <td><i class='glyphicon glyphicon-plus'></i></td> <td><b> {1} </b></td> <td><b> {2} </b></td> <td><b> {3}</b></td> </tr>".format(equipment_item.equipment_id, equipment_item.equipment_name, equipment_item.equipment_code, equipment_item.total_quantity);
        for (equipmentEntryID in equipment_item.equipment_entries){
            selectedEntry = equipment_item.equipment_entries[equipmentEntryID];
            removeButton = "<button class=\"btn btn-danger\" onclick=\"removeInventoryEquipmentEntry({0})\">Remove</button>".format(selectedEntry.equipment_entry_id);
            tableHTML = tableHTML + "<tr class='collapse collapsed{0}'> <td>{1}</td> <td> {2} </td> <td> {3}{4} </td> <td>{5}</td> <td>{6}</td> </tr>".format(equipment_item.equipment_id, selectedEntry.equipment_entry_id, equipment_item.equipment_name, equipment_item.equipment_code, selectedEntry.equipment_entry_number, selectedEntry.equipment_quantity, removeButton);
        }

    }
    $('#inventory_equipment_tbody').html(tableHTML);

}