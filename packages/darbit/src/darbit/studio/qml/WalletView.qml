// The Wallet block's body (Block.qml): each currency's balance now and today's change (d.record.balance,
// d.record.gain). Loaded only when a Wallet is on the Overview.
import QtQuick
import "format.js" as Format

Column {
    id: wallet
    required property var block  // the Block it's drawn in: its info and tone()
    width: parent ? parent.width : 0
    readonly property var items: block.info.items || []
    Text { visible: wallet.items.length === 0; text: "No balance read yet."; color: studio.colors.faint; font.pixelSize: 13 }
    Repeater {
        model: wallet.items
        delegate: Item {
            required property var modelData
            required property int index
            width: wallet.width; height: 56
            Rectangle { visible: index > 0; width: parent.width; height: 1; color: studio.colors.line }
            Rectangle {
                id: coin
                anchors.verticalCenter: parent.verticalCenter
                width: 24; height: 24; radius: 7
                color: block.tone(index)
                Text {
                    anchors.centerIn: parent
                    text: modelData.icon || String(modelData.name).charAt(0).toUpperCase()
                    color: studio.colors.onAccent; font.pixelSize: 12; font.weight: Font.Bold
                }
            }
            Column {
                anchors { left: coin.right; leftMargin: 12; right: change.left; rightMargin: 12; verticalCenter: parent.verticalCenter }
                Text {
                    CountUp { id: balance; to: Number(modelData.value) || 0 }
                    text: Format.compact(balance.counting ? balance.value : modelData.value)
                    color: studio.colors.text; font.pixelSize: 20; font.weight: Font.Bold
                }
                Text { width: parent.width; elide: Text.ElideRight; text: modelData.name; color: studio.colors.muted; font.pixelSize: 12 }
            }
            Column {
                id: change
                anchors { right: parent.right; verticalCenter: parent.verticalCenter }
                Text {
                    anchors.right: parent.right
                    text: Format.signed(modelData.today)
                    color: modelData.today > 0 ? studio.colors.ok : modelData.today < 0 ? studio.colors.danger : studio.colors.muted
                    font.pixelSize: 13; font.weight: Font.DemiBold
                }
                Text { anchors.right: parent.right; text: "today"; color: studio.colors.faint; font.pixelSize: 11 }
            }
        }
    }
}
