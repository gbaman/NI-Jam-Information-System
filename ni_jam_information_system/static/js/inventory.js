$(document).ready(function(){
    getInventoryEquipment(1)
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


function updateInventoryEquipmentTable(equipmentData){
    var tableHTML = "";
    for (equipmentID in equipmentData){
        equipment_item = equipmentData[equipmentID];
        tableHTML = tableHTML + "<tr class='clickable' data-toggle='collapse' id='collapsed{0}' data-target='.collapsed{0}' bgcolor='#90ee90'> <td><i class='glyphicon glyphicon-plus'></i></td> <td> {1} </td> <td> {2} </td> <td></td> </tr>".format(equipment_item.equipment_id, equipment_item.equipment_name, equipment_item.equipment_code);
        for (equipmentEntryID in equipment_item.equipment_entries){
            selectedEntry = equipment_item.equipment_entries[equipmentEntryID];
            tableHTML = tableHTML + "<tr class='collapse collapsed{0}'> <td></td> <td> {1} </td> <td> {2}{3} </td> <td>{4}</td> </tr>".format(equipment_item.equipment_id, equipment_item.equipment_name, equipment_item.equipment_code, selectedEntry.equipment_entry_id, selectedEntry.equipment_entry_number);
        }

    }
    $('#inventory_equipment_tbody').html(tableHTML);

}