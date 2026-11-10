// The Gains by source block's currency, picked in its top right corner (Block.qml) and kept in the layout, and
// "today". Loaded only for that block.
import QtQuick

Row {
    required property var block  // the Block it's drawn in: its info, and picked() to show another currency
    height: 28; spacing: 8
    Dropdown {
        visible: !!block.info && (block.info.names || []).length > 1
        objectName: "sourcesCurrency"
        implicitWidth: 120; implicitHeight: 28
        choices: block.info && block.info.names ? block.info.names : []
        chosen: block.info ? block.info.name : ""
        onPicked: function (value) { if (value !== block.info.name) block.picked("sources:" + value) }
    }
    Text { text: "today"; color: studio.colors.faint; font.pixelSize: 13; font.weight: Font.DemiBold; anchors.verticalCenter: parent.verticalCenter }
}
