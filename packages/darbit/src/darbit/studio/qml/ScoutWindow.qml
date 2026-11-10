// Scout's boxes: what's found on screen right now, over the game. Each image found gets its box and score; one just
// under what it needs gets a faint one. The one landed on in the pill is boxed in the accent with what's wrong, and
// the region it's searched in dashed. The Regions and Locations of the screens showing are drawn in their kinds'
// colours. Clicks go through to the game. Scout's key hides it; ScoutPill says what's been seen.
import QtQuick
import QtQuick.Shapes
import QtQuick.Window
import "scout.js" as Scout

Window {
    id: overlay
    objectName: "scoutWindow"
    visibility: scout.isOn ? Window.FullScreen : Window.Hidden
    transientParent: null  // its own window: it shows while the Studio is hidden (Windows hides a hidden window's tool windows too)
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTransparentForInput | Qt.Tool
    color: "transparent"
    title: "darbit Scout"
    readonly property real ratio: Screen.devicePixelRatio  // screen pixels to Qt's (1.5 at 150% scaling)
    readonly property var landedImage: {
        var images = scout.images
        for (var index = 0; index < images.length; index++)
            if (images[index].name === scout.landed) return images[index]
        return null
    }
    // screen pixels to the window's points
    function px(value, axis) { return value / ratio - (axis === 0 ? overlay.x : overlay.y) }

    // a dashed box, for regions
    component Dashed: Shape {
        property color ink: studio.colors.kindRegion
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: parent.ink; strokeWidth: 2; fillColor: "transparent"
            strokeStyle: ShapePath.DashLine; dashPattern: [5, 4]
            startX: 0; startY: 0
            PathLine { x: parent.width; y: 0 }
            PathLine { x: parent.width; y: parent.height }
            PathLine { x: 0; y: parent.height }
            PathLine { x: 0; y: 0 }
        }
    }

    // the Regions and Locations of the screens showing (those with an image found now)
    Repeater {
        model: scout.places.filter(function (place) { return scout.present.indexOf(place.screen) >= 0 })
        delegate: Item {
            required property var modelData
            readonly property bool region: modelData.kind === "region"
            readonly property color ink: region ? studio.colors.kindRegion : studio.colors.kindLocation
            x: overlay.px(modelData.box[0], 0) - (region ? 0 : 7)
            y: overlay.px(modelData.box[1], 1) - (region ? 0 : 7)
            width: region ? modelData.box[2] / overlay.ratio : 14
            height: region ? modelData.box[3] / overlay.ratio : 14
            Dashed { visible: parent.region; anchors.fill: parent; ink: parent.ink }
            Rectangle {
                visible: !parent.region
                anchors.fill: parent; radius: width / 2
                color: "transparent"; border.color: parent.ink; border.width: 3
                Rectangle { anchors.centerIn: parent; width: 4; height: 4; radius: 2; color: parent.border.color }
            }
            Chip {
                // a region's name inside its bottom edge (an image's label sits over its top), a location's under it
                anchors { left: parent.left; leftMargin: parent.region ? 6 : 0 }
                y: parent.region ? parent.height - height - 6 : parent.height + 4
                height: 20
                tone: parent.region ? "info" : "ok"
                text: (parent.region ? "⬚ " : "✛ ") + parent.modelData.name
            }
        }
    }

    // the region the landed-on image is searched in
    Repeater {
        model: scout.boxes.filter(function (box) { return box.name === scout.landed && box.region })
        delegate: Dashed {
            required property var modelData
            x: overlay.px(modelData.region[0], 0); y: overlay.px(modelData.region[1], 1)
            width: modelData.region[2] / overlay.ratio; height: modelData.region[3] / overlay.ratio
            ink: studio.colors.accent
        }
    }

    Repeater {
        model: scout.boxes.filter(function (box) {
            return box.shown || box.name === scout.landed && box.w || (!box.found && box.w && box.score >= box.needs - 0.15)
        })
        delegate: Item {
            id: mark
            required property var modelData
            // boxes come in screen pixels; the window counts in Qt's, which Windows' display scaling makes bigger
            x: overlay.px(modelData.x, 0); y: overlay.px(modelData.y, 1)
            width: modelData.w / overlay.ratio; height: modelData.h / overlay.ratio
            readonly property bool alike: modelData.with && modelData.with.length > 0
            readonly property bool landed: modelData.name === scout.landed
            readonly property color ink: landed ? studio.colors.accent : modelData.found && !alike ? studio.colors.ok : studio.colors.warn
            readonly property string problem: landed ? Scout.problem(overlay.landedImage) : ""
            opacity: modelData.found || landed ? 1 : 0.55
            z: landed ? 2 : 1
            Rectangle {
                anchors.fill: parent; anchors.margins: mark.landed ? -6 : -3
                radius: 6; color: "transparent"
                border.width: mark.landed ? 3 : 2
                border.color: mark.ink
            }
            Rectangle {
                x: -3; y: -height - (mark.landed ? 9 : 6)
                width: lines.implicitWidth + 14; height: lines.implicitHeight + 6; radius: 10
                color: studio.colors.solid
                border.color: mark.ink
                Column {
                    id: lines
                    anchors.centerIn: parent
                    Text {
                        text: (mark.alike ? "⚠ " : "") + mark.modelData.name + "  " + mark.modelData.score.toFixed(2)
                            + (mark.landed ? " / " + mark.modelData.needs.toFixed(2) : "")
                        color: mark.ink
                        font.pixelSize: 12; font.weight: Font.DemiBold
                    }
                    Text {
                        visible: mark.alike
                        text: "also " + (mark.modelData.with || []).join(", ")
                        color: studio.colors.muted
                        font.pixelSize: 11
                    }
                    Text {
                        visible: mark.problem !== ""
                        text: mark.problem
                        color: studio.colors.warn
                        font.pixelSize: 11
                    }
                }
            }
        }
    }
}
