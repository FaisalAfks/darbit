// One asset: its thumbnail (or what it is, for a point or a missing picture), its whole name, its last score against
// the similarity it needs (the white tick), and how often the code uses it. The chosen card glows; the rest dim.
import QtQuick

Rectangle {
    id: card
    property var asset: ({})
    property var score: null
    property real needs: 0.9
    property bool weak: false
    property bool chosen: false
    property bool dimmed: false
    signal clicked()
    readonly property color kindInk: asset.kind === "region" ? studio.colors.accent2 : asset.kind === "location" ? studio.colors.ok : studio.colors.accent
    height: 206
    radius: 16
    color: chosen ? Qt.rgba(studio.colors.accent.r, studio.colors.accent.g, studio.colors.accent.b, 0.1) : studio.colors.glass
    border.color: chosen ? studio.colors.accent : area.containsMouse ? Qt.tint(studio.colors.line, Qt.rgba(1, 1, 1, 0.12)) : studio.colors.line
    border.width: chosen ? 2 : 1
    opacity: dimmed ? 0.55 : 1
    scale: area.containsMouse && !chosen ? 1.025 : 1
    Behavior on scale { NumberAnimation { duration: studio.effects ? 140 : 0; easing.type: Easing.OutCubic } }
    Behavior on opacity { NumberAnimation { duration: studio.effects ? 160 : 0 } }

    Rectangle {
        id: frame
        x: 10; y: 10; width: card.width - 20; height: 112; radius: 11
        color: studio.colors.bg
        clip: true
        Image {
            anchors.fill: parent; anchors.margins: 6
            visible: !!card.asset.thumbnail && !card.asset.missing
            source: card.asset.thumbnail || ""
            sourceSize: Qt.size(320, 224)
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            cache: true
        }
        Text {
            visible: !card.asset.thumbnail || card.asset.missing
            anchors.centerIn: parent
            text: card.asset.missing ? "not taken" : card.asset.kind === "location" ? "＋" : card.asset.size ? card.asset.size[0] + " × " + card.asset.size[1] : card.asset.kind
            color: card.asset.missing ? studio.colors.danger : card.kindInk
            font.pixelSize: card.asset.kind === "location" ? 26 : 13; font.weight: Font.DemiBold
        }
        Rectangle {
            visible: card.asset.kind !== "image"
            anchors { right: parent.right; top: parent.top; margins: 6 }
            width: kindText.implicitWidth + 12; height: 18; radius: 9
            color: Qt.rgba(card.kindInk.r, card.kindInk.g, card.kindInk.b, 0.2)
            Text { id: kindText; anchors.centerIn: parent; text: card.asset.kind === "region" ? "REGION" : "LOCATION"; color: card.kindInk; font.pixelSize: 10; font.weight: Font.Bold; font.letterSpacing: 0.6 }
        }
    }
    Text {
        x: 12; y: 130; width: card.width - 24
        text: card.asset.name || ""
        color: studio.colors.text; font.pixelSize: 14; font.weight: Font.DemiBold
        elide: Text.ElideMiddle
    }
    // the score meter, with a tick at the similarity it needs
    Rectangle {
        x: 12; y: 158; width: card.width - 24; height: 5; radius: 2.5
        color: studio.colors.raisedHover
        visible: card.asset.kind === "image" && !card.asset.missing
        Rectangle {
            height: parent.height; radius: parent.radius
            width: parent.width * (card.score === null ? 0 : Math.min(card.score, 1))
            color: card.weak ? studio.colors.warn : studio.colors.ok
        }
        Rectangle { x: parent.width * card.needs - 1; y: -2; width: 2; height: 9; radius: 1; color: studio.colors.text }
    }
    Text {
        x: 12; y: 172; width: card.width - 32 - uses.implicitWidth
        elide: Text.ElideRight
        text: card.asset.missing ? "missing" : card.asset.kind !== "image" ? "" : card.score === null ? "not checked yet" : card.score.toFixed(2) + (card.weak ? " · weak" : "")
        color: card.asset.missing ? studio.colors.danger : card.weak ? studio.colors.warn : studio.colors.muted
        font.pixelSize: 12
    }
    Text {
        id: uses
        anchors { right: parent.right; rightMargin: 12 }
        y: 172
        text: card.asset.uses ? "used " + card.asset.uses + "×" : "unused"
        color: studio.colors.faint; font.pixelSize: 12
    }
    Rectangle {  // the chosen mark
        visible: card.chosen
        anchors { right: parent.right; top: parent.top; margins: -6 }
        width: 24; height: 24; radius: 12
        color: studio.colors.accent
        Text { anchors.centerIn: parent; text: "✓"; color: studio.colors.onAccent; font.pixelSize: 12; font.weight: Font.Bold }
    }
    MouseArea { id: area; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: card.clicked() }
}
