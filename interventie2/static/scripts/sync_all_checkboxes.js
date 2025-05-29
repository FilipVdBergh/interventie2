function sync_all_checkboxes(id_to_sync_to = 'sync_all', classes_to_sync = 'checkbox') 
{
    var master_checkbox = document.getElementById(id_to_sync_to)
    var all_instruments = document.getElementsByClassName(classes_to_sync)
    for (var i = 0; i < all_instruments.length; i++) {
        all_instruments[i].checked = master_checkbox.checked
    }
}