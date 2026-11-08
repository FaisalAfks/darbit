// One image of Scout's record in full, in its floating card: the image large beside the saved shot where it was last
// seen with its box, its best score against what it needs, what's wrong, and its retakes (on that shot, or on the
// screen now; only now for one never seen).
import QtQuick
import QtQuick.Layouts
import "scout.js" as Scout

Column {
    id: detail
    required property var image
    property real now: 0
    signal retakeOnShot()
    signal retakeNow()
    readonly property color ink: Scout.ink(studio.colors, image)
    readonly property bool hasShot: image !== null && image.shot !== "" && image.box !== null
    spacing: 10

    Row {
        width: parent.width
        spacing: 12
        Column {
            spacing: 5
            Text { text: "The image"; color: studio.colors.muted; font.pixelSize: 12 }
            Rectangle {
                width: 150; height: 96; radius: 10
                color: studio.colors.bg
                border.color: detail.ink; border.width: 2
                clip: true
                Image {
                    anchors.fill: parent; anchors.margins: 6
                    source: detail.image ? detail.image.file : ""
                    fillMode: Image.PreserveAspectFit; asynchronous: true; smooth: false  // its own pixels
                }
            }
        }
        Column {
            width: parent.width - 162
            spacing: 5
            Text {
                width: parent.width; elide: Text.ElideRight
                text: !detail.image || detail.image.state === "not" ? "Not seen yet: no shot of it"
                    : detail.hasShot ? "Where it was seen: " + detail.image.seenOn + ", " + Scout.ago(detail.now - detail.image.seenAt)
                    : "Seen on " + detail.image.seenOn + "; its shot is a newer one now"
                color: studio.colors.muted; font.pixelSize: 12
            }
            Rectangle {
                id: shotFrame
                width: parent.width; height: 96; radius: 10
                color: studio.colors.bg
                border.color: studio.colors.line
                clip: true
                Image {
                    id: shot
                    objectName: "scoutShot"
                    visible: detail.hasShot
                    anchors.fill: parent; anchors.margins: 4
                    source: detail.hasShot ? detail.image.shown : ""
                    fillMode: Image.PreserveAspectFit; asynchronous: true; cache: false
                    // the box where the image was, on the shot as it's drawn
                    readonly property real fit: detail.hasShot ? Math.min(width / detail.image.shotSize[0], height / detail.image.shotSize[1]) : 1
                    readonly property real padX: (width - (detail.hasShot ? detail.image.shotSize[0] : 0) * fit) / 2
                    readonly property real padY: (height - (detail.hasShot ? detail.image.shotSize[1] : 0) * fit) / 2
                    Rectangle {
                        visible: detail.hasShot
                        x: detail.hasShot ? shot.padX + detail.image.box[0] * shot.fit - 2 : 0
                        y: detail.hasShot ? shot.padY + detail.image.box[1] * shot.fit - 2 : 0
                        width: detail.hasShot ? Math.max(8, detail.image.box[2] * shot.fit + 4) : 0
                        height: detail.hasShot ? Math.max(6, detail.image.box[3] * shot.fit + 4) : 0
                        radius: 3; color: "transparent"
                        border.color: detail.ink; border.width: 2
                    }
                }
                Text {
                    visible: !detail.hasShot
                    anchors.centerIn: parent; width: parent.width - 24
                    horizontalAlignment: Text.AlignHCenter; wrapMode: Text.Wrap
                    text: detail.image && detail.image.state === "not" ? "Go to its screen in the game, and Scout keeps a shot of it"
                        : "Seen again, Scout keeps a new shot"
                    color: studio.colors.faint; font.pixelSize: 12
                }
            }
        }
    }
    Row {
        spacing: 8
        Text {
            text: detail.image ? detail.image.name : ""
            color: studio.colors.text; font.family: "monospace"; font.pixelSize: 15; font.weight: Font.Bold
            anchors.verticalCenter: parent.verticalCenter
        }
        Chip { height: 22; tone: "accent"; text: "▣ Image"; anchors.verticalCenter: parent.verticalCenter }
        Chip {
            height: 22; anchors.verticalCenter: parent.verticalCenter
            tone: !detail.image || detail.image.state === "not" ? "plain" : detail.image.state === "weak" ? "warn" : "ok"
            text: !detail.image || detail.image.state === "not" ? "not seen yet" : detail.image.state
        }
    }
    // its best score against what it needs: the bar is the best, the mark what it needs
    Item {
        width: parent.width; height: 12
        Bar {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width
            tint: detail.ink
            share: detail.image ? detail.image.best : 0
        }
        Rectangle {
            x: detail.image ? parent.width * detail.image.needs - 1 : 0
            width: 2; height: parent.height; radius: 1
            color: studio.colors.text
        }
    }
    RowLayout {
        width: parent.width
        Text {
            Layout.fillWidth: true
            text: !detail.image || detail.image.state === "not" ? "not seen yet"
                : "best " + detail.image.best.toFixed(2) + " (seen " + detail.image.times + (detail.image.times === 1 ? " time)" : " times)")
            color: studio.colors.muted; font.pixelSize: 12
        }
        Text { text: detail.image ? "needs " + detail.image.needs.toFixed(2) : ""; color: studio.colors.muted; font.pixelSize: 12 }
    }
    Text {
        visible: text !== ""
        width: parent.width; wrapMode: Text.Wrap
        text: Scout.problem(detail.image)
        color: detail.image && detail.image.state === "not" ? studio.colors.muted : studio.colors.warn
        font.pixelSize: 12
    }
    Flow {
        width: parent.width; spacing: 8
        PillButton {
            objectName: "detailRetakeOnShot"
            visible: detail.hasShot
            kind: "primary"; small: true; icon: "⟲"
            text: detail.image ? "Retake on " + detail.image.seenOn + ", where it was seen" : ""
            onClicked: detail.retakeOnShot()
        }
        PillButton {
            objectName: "detailRetakeNow"
            kind: detail.hasShot ? "plain" : "primary"; small: true; icon: "⟲"
            text: "On the screen now"
            onClicked: detail.retakeNow()
        }
    }
}
