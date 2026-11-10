// Record: the new action's name (an existing one is recorded again only when asked), then the Studio steps aside.
import QtQuick
import QtQuick.Controls.Basic

Sheet {
    id: sheet
    objectName: "recordSheet"
    property bool again: false
    width: 480
    function openFor(name) { again = name !== ""; field.text = name; open() }
    onOpened: field.forceActiveFocus()
    function submit() {
        var name = field.text.trim()
        if (name === "") return
        close()
        studio.record(name, again)
    }
    contentItem: Column {
        spacing: 16
        Text { text: sheet.again ? "Record " + field.text + " again" : "Record an action"; color: studio.colors.text; font.pixelSize: 22; font.weight: Font.Bold }
        Text {
            width: parent.width; wrapMode: Text.Wrap; color: studio.colors.muted; font.pixelSize: 14
            text: "The Studio steps aside and every key, click and mouse move goes in, on one clock, until Done. Pause to add a check: an image to wait for, or a wait. Ctrl+Alt+K starts a new part."
        }
        Field {
            id: field
            width: parent.width; height: 44
            enabled: !sheet.again
            placeholderText: "Its name, e.g. dim_run"
            color: studio.colors.text; placeholderTextColor: studio.colors.faint; font.pixelSize: 15
            validator: RegularExpressionValidator { regularExpression: /[A-Za-z_][A-Za-z0-9_]*/ }
            onAccepted: sheet.submit()
        }
        Row {
            anchors.right: parent.right; spacing: 10
            PillButton { text: "Cancel"; kind: "quiet"; onClicked: sheet.close() }
            PillButton { kind: "primary"; icon: "●"; text: "Record"; enabled: field.text.trim() !== ""; onClicked: sheet.submit() }
        }
    }
}
